from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

DEFAULT_CONVERSATIONS_DB_PATH = "artifacts/chat_history_v1.db"
DEFAULT_PLACEHOLDER_TITLE = "新对话"
MAX_AUTO_TITLE_LENGTH = 24
MAX_PREVIEW_LENGTH = 72


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collapse_whitespace(value: str) -> str:
    return " ".join(string_part for string_part in str(value or "").split())


def truncate_with_ellipsis(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def build_auto_title(query: str) -> str:
    normalized = collapse_whitespace(query)
    if not normalized:
        return DEFAULT_PLACEHOLDER_TITLE
    return truncate_with_ellipsis(normalized, MAX_AUTO_TITLE_LENGTH)


def build_preview_text(content: str) -> str:
    normalized = collapse_whitespace(content)
    return truncate_with_ellipsis(normalized, MAX_PREVIEW_LENGTH) if normalized else ""


class ConversationStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = Lock()
        self._initialize()

    def close(self) -> None:
        self.conn.close()

    def _initialize(self) -> None:
        with self.conn:
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    title_source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_message_at TEXT,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    preview_text TEXT
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    answer_payload_json TEXT,
                    created_at TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
                """
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conversation_position ON messages(conversation_id, position)"
            )

    def create_conversation(self, title: str | None = None) -> dict[str, Any]:
        now = utc_now_iso()
        title_value = collapse_whitespace(title or "")
        conversation_id = f"conv_{uuid.uuid4().hex}"
        stored_title = title_value or DEFAULT_PLACEHOLDER_TITLE
        title_source = "user" if title_value else "placeholder"

        with self.lock, self.conn:
            self.conn.execute(
                """
                INSERT INTO conversations (
                    id,
                    title,
                    title_source,
                    created_at,
                    updated_at,
                    last_message_at,
                    message_count,
                    preview_text
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, '')
                """,
                (
                    conversation_id,
                    stored_title,
                    title_source,
                    now,
                    now,
                    None,
                ),
            )
            row = self._fetch_conversation_row(conversation_id)

        return self._conversation_row_to_dict(row)

    def list_conversations(self, search: str | None = None, *, limit: int = 200) -> list[dict[str, Any]]:
        search_text = collapse_whitespace(search or "").lower()

        with self.lock:
            if search_text:
                like_term = f"%{search_text}%"
                rows = self.conn.execute(
                    """
                    SELECT c.*
                    FROM conversations AS c
                    WHERE lower(c.title) LIKE ?
                        OR EXISTS (
                            SELECT 1
                            FROM messages AS m
                            WHERE m.conversation_id = c.id
                                AND lower(m.content) LIKE ?
                        )
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                    """,
                    (like_term, like_term, limit),
                ).fetchall()
            else:
                rows = self.conn.execute(
                    """
                    SELECT c.*
                    FROM conversations AS c
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [self._conversation_row_to_dict(row) for row in rows]

    def get_conversation_summary(self, conversation_id: str) -> dict[str, Any] | None:
        with self.lock:
            row = self._fetch_conversation_row(conversation_id)
        if row is None:
            return None
        return self._conversation_row_to_dict(row)

    def get_conversation_detail(self, conversation_id: str) -> dict[str, Any] | None:
        with self.lock:
            conversation_row = self._fetch_conversation_row(conversation_id)
            if conversation_row is None:
                return None
            message_rows = self.conn.execute(
                """
                SELECT id, role, content, answer_payload_json, created_at, position
                FROM messages
                WHERE conversation_id = ?
                ORDER BY position ASC
                """,
                (conversation_id,),
            ).fetchall()

        return {
            "conversation": self._conversation_row_to_dict(conversation_row),
            "messages": [self._message_row_to_dict(row) for row in message_rows],
        }

    def append_exchange(
        self,
        conversation_id: str,
        query: str,
        answer_payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        answer_text = str(answer_payload.get("answer_text") or "")
        user_content = str(query).strip()
        if not user_content:
            raise ValueError("query must be non-empty")

        user_created_at = utc_now_iso()
        assistant_created_at = utc_now_iso()
        serialized_payload = json.dumps(answer_payload, ensure_ascii=False)

        with self.lock, self.conn:
            conversation_row = self._fetch_conversation_row(conversation_id)
            if conversation_row is None:
                return None

            next_position = int(conversation_row["message_count"]) + 1
            title = str(conversation_row["title"])
            title_source = str(conversation_row["title_source"])

            if title_source == "placeholder" and int(conversation_row["message_count"]) == 0:
                title = build_auto_title(user_content)
                title_source = "auto"

            user_row = {
                "id": f"msg_{uuid.uuid4().hex}",
                "conversation_id": conversation_id,
                "role": "user",
                "content": user_content,
                "answer_payload_json": None,
                "created_at": user_created_at,
                "position": next_position,
            }
            assistant_row = {
                "id": f"msg_{uuid.uuid4().hex}",
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": answer_text,
                "answer_payload_json": serialized_payload,
                "created_at": assistant_created_at,
                "position": next_position + 1,
            }

            self.conn.execute(
                """
                INSERT INTO messages (
                    id,
                    conversation_id,
                    role,
                    content,
                    answer_payload_json,
                    created_at,
                    position
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_row["id"],
                    user_row["conversation_id"],
                    user_row["role"],
                    user_row["content"],
                    user_row["answer_payload_json"],
                    user_row["created_at"],
                    user_row["position"],
                ),
            )
            self.conn.execute(
                """
                INSERT INTO messages (
                    id,
                    conversation_id,
                    role,
                    content,
                    answer_payload_json,
                    created_at,
                    position
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assistant_row["id"],
                    assistant_row["conversation_id"],
                    assistant_row["role"],
                    assistant_row["content"],
                    assistant_row["answer_payload_json"],
                    assistant_row["created_at"],
                    assistant_row["position"],
                ),
            )
            self.conn.execute(
                """
                UPDATE conversations
                SET title = ?,
                    title_source = ?,
                    updated_at = ?,
                    last_message_at = ?,
                    message_count = ?,
                    preview_text = ?
                WHERE id = ?
                """,
                (
                    title,
                    title_source,
                    assistant_created_at,
                    assistant_created_at,
                    next_position + 1,
                    build_preview_text(user_content),
                    conversation_id,
                ),
            )
            updated_row = self._fetch_conversation_row(conversation_id)

        return {
            "conversation": self._conversation_row_to_dict(updated_row),
            "messages": [
                self._message_dict_to_public(user_row),
                self._message_dict_to_public(assistant_row, answer_payload=answer_payload),
            ],
        }

    def delete_conversation(self, conversation_id: str) -> bool:
        with self.lock, self.conn:
            result = self.conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        return result.rowcount > 0

    def _fetch_conversation_row(self, conversation_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT
                id,
                title,
                title_source,
                created_at,
                updated_at,
                last_message_at,
                message_count,
                preview_text
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()

    def _conversation_row_to_dict(self, row: sqlite3.Row | None) -> dict[str, Any]:
        if row is None:
            raise ValueError("conversation row is required")
        return {
            "id": row["id"],
            "title": row["title"],
            "title_source": row["title_source"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_message_at": row["last_message_at"],
            "message_count": int(row["message_count"]),
            "preview_text": row["preview_text"] or "",
        }

    def _message_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        answer_payload = None
        if row["answer_payload_json"]:
            answer_payload = json.loads(row["answer_payload_json"])
        return {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
            "position": int(row["position"]),
            "answer_payload": answer_payload,
        }

    def _message_dict_to_public(
        self,
        payload: dict[str, Any],
        *,
        answer_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "id": payload["id"],
            "role": payload["role"],
            "content": payload["content"],
            "created_at": payload["created_at"],
            "position": int(payload["position"]),
            "answer_payload": answer_payload,
        }
