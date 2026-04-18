#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import re
import shlex
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib import request as urllib_request
from urllib.parse import parse_qs, urlsplit

from backend.answers.assembler import (
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_EXAMPLES,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    AnswerAssembler,
    json_dumps,
    log,
)
from backend.chat_history import ConversationStore, DEFAULT_CONVERSATIONS_DB_PATH
from backend.llm import LLMConfigError, ModelStudioLLMConfig, load_modelstudio_llm_config
from backend.perf import (
    current_trace,
    load_perf_settings,
    new_request_trace,
    persist_request_log,
    reset_current_trace,
    set_current_trace,
    stage_timer,
)


API_PATH = "/api/v1/answers"
API_STREAM_PATH = "/api/v1/answers/stream"
CONVERSATIONS_API_PATH = "/api/v1/conversations"
CLIENT_ID_HEADER = "X-TCM-Client-Id"
CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
BENIGN_DISCONNECT_ERRNOS = {32, 53, 54, 104}
DEFAULT_API_EXAMPLES_OUT = "artifacts/api_examples.json"
DEFAULT_API_SMOKE_OUT = "artifacts/api_smoke_checks.md"
DEFAULT_LLM_API_EXAMPLES_OUT = "artifacts/llm_api_examples_modelstudio.json"
DEFAULT_LLM_API_SMOKE_OUT = "artifacts/llm_api_smoke_checks_modelstudio.md"
DEFAULT_FRONTEND_DIR = "frontend"
DEFAULT_FRONTEND_DIST_SUBDIR = "dist"
CHAT_ROUTE_PREFIX = "/chat"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PAYLOAD_FIELDS = [
    "query",
    "answer_mode",
    "answer_text",
    "primary_evidence",
    "secondary_evidence",
    "review_materials",
    "disclaimer",
    "review_notice",
    "refuse_reason",
    "suggested_followup_questions",
    "citations",
    "display_sections",
]
STREAM_STAGE_LABELS = {
    "retrieving_evidence": "正在检索依据",
    "organizing_evidence": "正在组织证据",
    "generating_answer": "正在生成回答",
    "completed": "已完成",
}
STREAM_STAGE_SEQUENCE = [
    "retrieving_evidence",
    "organizing_evidence",
    "generating_answer",
    "completed",
]
STREAM_MIN_CHUNK_SIZE = 20
STREAM_MAX_CHUNK_SIZE = 48
STREAM_CHUNK_DELAY_SECONDS = 0.03
LLM_SMOKE_EXAMPLES = [
    {
        "example_id": "source_lookup_strong",
        "query_text": "黄连汤方的条文是什么？",
        "expected_mode": "strong",
    },
    {
        "example_id": "meaning_explanation_weak",
        "query_text": "烧针益阳而损阴是什么意思？",
        "expected_mode": "weak_with_review_notice",
    },
    {
        "example_id": "general_overview_strong",
        "query_text": "太阳病应该怎么办？",
        "expected_mode": "strong",
    },
    {
        "example_id": "comparison_strong",
        "query_text": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
        "expected_mode": "strong",
    },
    {
        "example_id": "refuse_boundary",
        "query_text": "书中有没有提到量子纠缠？",
        "expected_mode": "refuse",
    },
]


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the minimal HTTP transport adapter for answer payloads.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind the HTTP server.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind the HTTP server.")
    parser.add_argument("--smoke", action="store_true", help="Run local HTTP smoke checks and exit.")
    parser.add_argument("--llm-smoke", action="store_true", help="Run local Model Studio LLM smoke checks and exit.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument(
        "--policy-json",
        default=DEFAULT_POLICY_PATH,
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_API_EXAMPLES_OUT,
        help="Where to write HTTP API example results JSON in smoke mode.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_API_SMOKE_OUT,
        help="Where to write HTTP API smoke check markdown in smoke mode.",
    )
    parser.add_argument(
        "--llm-examples-out",
        default=DEFAULT_LLM_API_EXAMPLES_OUT,
        help="Where to write LLM smoke example results JSON.",
    )
    parser.add_argument(
        "--llm-smoke-checks-out",
        default=DEFAULT_LLM_API_SMOKE_OUT,
        help="Where to write LLM smoke check markdown.",
    )
    parser.add_argument(
        "--llm-enabled",
        action="store_true",
        help="Enable Model Studio answer_text rendering. This is kept for backward compatibility; runtime now enables LLM by default.",
    )
    parser.add_argument(
        "--llm-disabled",
        action="store_true",
        help="Disable Model Studio answer_text rendering and force rule-only answer_text generation.",
    )
    parser.add_argument("--llm-model", default=None, help="Model Studio model override for this release.")
    parser.add_argument("--llm-base-url", default=None, help="Model Studio base URL override.")
    parser.add_argument("--llm-timeout-seconds", type=float, default=None, help="Model Studio request timeout.")
    parser.add_argument(
        "--llm-max-output-tokens",
        type=int,
        default=None,
        help="Max output tokens for Model Studio answer_text rendering.",
    )
    parser.add_argument(
        "--conversations-db-path",
        default=DEFAULT_CONVERSATIONS_DB_PATH,
        help="Path to the decoupled conversation history sqlite database.",
    )
    return parser.parse_args()


class ApiRequestError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def normalize_client_id(raw_client_id: Any) -> str:
    client_id = str(raw_client_id or "").strip()
    if not client_id:
        raise ApiRequestError(400, "missing_client_id", "Missing anonymous client id.")
    if not CLIENT_ID_RE.fullmatch(client_id):
        raise ApiRequestError(400, "invalid_client_id", "Anonymous client id is invalid.")
    return client_id


@dataclass
class MinimalApiService:
    db_path: Path
    policy_path: Path
    embed_model: str
    rerank_model: str
    cache_dir: Path
    dense_chunks_index: Path
    dense_chunks_meta: Path
    dense_main_index: Path
    dense_main_meta: Path
    llm_config: ModelStudioLLMConfig
    conversations_db_path: Path
    last_llm_debug: dict[str, Any] | None = None
    conversation_store: ConversationStore = field(init=False)

    def __post_init__(self) -> None:
        self.assembler = AnswerAssembler(
            db_path=self.db_path,
            policy_path=self.policy_path,
            embed_model=self.embed_model,
            rerank_model=self.rerank_model,
            cache_dir=self.cache_dir,
            dense_chunks_index=self.dense_chunks_index,
            dense_chunks_meta=self.dense_chunks_meta,
            dense_main_index=self.dense_main_index,
            dense_main_meta=self.dense_main_meta,
            llm_config=self.llm_config,
        )
        self.conversation_store = ConversationStore(self.conversations_db_path)

    def close(self) -> None:
        self.conversation_store.close()
        self.assembler.close()

    def _normalize_query_payload(self, payload: Any) -> str:
        self.last_llm_debug = None
        if not isinstance(payload, dict):
            raise ApiRequestError(400, "invalid_json", "Request body must be a JSON object.")

        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ApiRequestError(400, "invalid_request", "Field 'query' must be a non-empty string.")
        return query.strip()

    def answer_query(
        self,
        query: str,
        *,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        response_payload = self.assembler.assemble(query, progress_callback=progress_callback)
        self.last_llm_debug = self.assembler.get_last_llm_debug()
        return response_payload

    def answer(
        self,
        payload: Any,
        *,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        query = self._normalize_query_payload(payload)
        return self.answer_query(query, progress_callback=progress_callback)

    def create_conversation(self, client_id: str, payload: Any) -> dict[str, Any]:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise ApiRequestError(400, "invalid_json", "Request body must be a JSON object.")

        raw_title = payload.get("title")
        if raw_title is not None and not isinstance(raw_title, str):
            raise ApiRequestError(400, "invalid_request", "Field 'title' must be a string when provided.")

        return self.conversation_store.create_conversation(client_id, raw_title)

    def list_conversations(self, client_id: str, search: str | None = None) -> dict[str, Any]:
        normalized_search = search.strip() if isinstance(search, str) else ""
        return {
            "items": self.conversation_store.list_conversations(client_id, normalized_search),
            "search": normalized_search,
        }

    def get_conversation(self, client_id: str, conversation_id: str) -> dict[str, Any]:
        conversation = self.conversation_store.get_conversation_detail(client_id, conversation_id)
        if conversation is None:
            raise ApiRequestError(404, "not_found", "Conversation not found.")
        return conversation

    def delete_conversation(self, client_id: str, conversation_id: str) -> dict[str, Any]:
        deleted = self.conversation_store.delete_conversation(client_id, conversation_id)
        if not deleted:
            raise ApiRequestError(404, "not_found", "Conversation not found.")
        return {"id": conversation_id, "deleted": True}

    def delete_all_conversations(self, client_id: str) -> dict[str, Any]:
        deleted_count = self.conversation_store.delete_all_conversations(client_id)
        return {"deleted": True, "deleted_count": deleted_count}

    def append_conversation_message(self, client_id: str, conversation_id: str, payload: Any) -> dict[str, Any]:
        if self.conversation_store.get_conversation_summary(client_id, conversation_id) is None:
            raise ApiRequestError(404, "not_found", "Conversation not found.")

        query = self._normalize_query_payload(payload)
        answer_payload = self.answer_query(query)
        log_answer_diagnostics(
            request_path=f"{CONVERSATIONS_API_PATH}/:conversation_id/messages",
            query=query,
            response_payload=answer_payload,
            llm_debug=self.last_llm_debug,
        )
        conversation_update = self.conversation_store.append_exchange(client_id, conversation_id, query, answer_payload)
        if conversation_update is None:
            raise ApiRequestError(404, "not_found", "Conversation not found.")
        return conversation_update


def is_benign_disconnect_exception(exc: BaseException | None) -> bool:
    seen: set[int] = set()
    current = exc

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return True
        if isinstance(current, OSError) and getattr(current, "errno", None) in BENIGN_DISCONNECT_ERRNOS:
            return True
        current = current.__cause__ or current.__context__

    return False


class MinimalApiHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def handle_error(self, request: Any, client_address: tuple[str, int] | str) -> None:
        exc = sys.exc_info()[1]
        if is_benign_disconnect_exception(exc):
            return
        super().handle_error(request, client_address)


def build_stream_phase_event(stage: str, detail: str | None = None) -> dict[str, Any]:
    return {
        "type": "phase",
        "stage": stage,
        "label": STREAM_STAGE_LABELS.get(stage, stage),
        "detail": detail or "",
        "step_index": STREAM_STAGE_SEQUENCE.index(stage) + 1 if stage in STREAM_STAGE_SEQUENCE else None,
        "step_count": len(STREAM_STAGE_SEQUENCE),
    }


def log_answer_diagnostics(
    *,
    request_path: str,
    query: str,
    response_payload: dict[str, Any],
    llm_debug: dict[str, Any] | None,
) -> None:
    debug = dict(llm_debug or {})
    fallback_reason = debug.get("fallback_reason") or debug.get("skipped_reason")
    request_id = current_trace().request_id if current_trace() is not None else "n/a"
    log(
        "[api:answer] "
        f"request_id={request_id} "
        f"path={request_path} "
        f"mode={response_payload.get('answer_mode')} "
        f"answer_source={debug.get('answer_source') or 'unknown'} "
        f"llm_attempted={bool(debug.get('attempted'))} "
        f"llm_call_succeeded={bool(debug.get('used_llm'))} "
        f"llm_provider={json_dumps(debug.get('provider') or 'unknown')} "
        f"llm_model={json_dumps(debug.get('model') or 'unknown')} "
        f"fallback_used={bool(debug.get('fallback_used'))} "
        f"fallback_reason={json_dumps(fallback_reason)} "
        f"query={json_dumps(query)}"
    )


def split_answer_text_for_stream(answer_text: str) -> list[str]:
    if not answer_text:
        return []

    chunks: list[str] = []
    current: list[str] = []
    break_chars = {"，", "。", "！", "？", "；", "：", "\n"}

    for char in answer_text:
        current.append(char)
        current_text = "".join(current)
        if len(current_text) < STREAM_MIN_CHUNK_SIZE:
            continue
        if char in break_chars or len(current_text) >= STREAM_MAX_CHUNK_SIZE:
            chunks.append(current_text)
            current = []

    if current:
        chunks.append("".join(current))

    return chunks or [answer_text]


def is_frontend_shell_route(request_path: str) -> bool:
    return request_path in {"/", "/index.html", "/frontend", "/frontend/", CHAT_ROUTE_PREFIX, f"{CHAT_ROUTE_PREFIX}/"} or request_path.startswith(
        f"{CHAT_ROUTE_PREFIX}/"
    )


def is_frontend_asset_route(request_path: str) -> bool:
    if request_path.startswith("/assets/"):
        return True
    suffix = Path(request_path).suffix
    return bool(suffix) and not request_path.startswith("/api/")


def resolve_frontend_asset_path(frontend_root: Path, request_path: str) -> Path | None:
    relative_path = request_path.lstrip("/")
    if not relative_path:
        relative_path = "index.html"
    target_path = (frontend_root / relative_path).resolve()
    try:
        target_path.relative_to(frontend_root.resolve())
    except ValueError:
        return None
    return target_path


def match_conversation_detail_route(request_path: str) -> str | None:
    prefix = f"{CONVERSATIONS_API_PATH}/"
    if not request_path.startswith(prefix):
        return None
    suffix = request_path.removeprefix(prefix)
    if not suffix or "/" in suffix:
        return None
    return suffix


def match_conversation_messages_route(request_path: str) -> str | None:
    prefix = f"{CONVERSATIONS_API_PATH}/"
    if not request_path.startswith(prefix):
        return None
    suffix = request_path.removeprefix(prefix)
    parts = [part for part in suffix.split("/") if part]
    if len(parts) == 2 and parts[1] == "messages":
        return parts[0]
    return None


def make_handler(service: MinimalApiService, frontend_root: Path) -> type[BaseHTTPRequestHandler]:
    class MinimalApiHandler(BaseHTTPRequestHandler):
        server_version = "TCMClassicRAGMinimalAPI/0.1"
        protocol_version = "HTTP/1.1"

        def handle_one_request(self) -> None:
            try:
                super().handle_one_request()
            except Exception as exc:
                if self._is_client_disconnect(exc):
                    self.close_connection = True
                    return
                raise

        def finish(self) -> None:
            try:
                super().finish()
            except Exception as exc:
                if self._is_client_disconnect(exc):
                    self.close_connection = True
                    return
                raise

        def do_POST(self) -> None:  # noqa: N802
            request_path = urlsplit(self.path).path
            if request_path == API_STREAM_PATH:
                self._handle_stream_post()
                return

            if request_path == CONVERSATIONS_API_PATH:
                try:
                    client_id = self._read_client_id_header()
                    payload = self._read_json_body()
                    response_payload = {"conversation": service.create_conversation(client_id, payload)}
                except ApiRequestError as exc:
                    self._send_json(exc.status_code, {"error": {"code": exc.code, "message": exc.message}})
                    return
                except Exception as exc:  # pragma: no cover - defensive transport guard
                    log(f"[api:error] {exc}")
                    self._send_json(
                        500,
                        {"error": {"code": "internal_error", "message": "Internal server error."}},
                    )
                    return

                self._send_json(201, response_payload)
                return

            conversation_id = match_conversation_messages_route(request_path)
            if conversation_id is not None:
                try:
                    client_id = self._read_client_id_header()
                    payload = self._read_json_body()
                    response_payload = service.append_conversation_message(client_id, conversation_id, payload)
                except ApiRequestError as exc:
                    self._send_json(exc.status_code, {"error": {"code": exc.code, "message": exc.message}})
                    return
                except Exception as exc:  # pragma: no cover - defensive transport guard
                    log(f"[api:error] {exc}")
                    self._send_json(
                        500,
                        {"error": {"code": "internal_error", "message": "Internal server error."}},
                    )
                    return

                self._send_json(200, response_payload)
                return

            if request_path != API_PATH:
                self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
                return

            perf_trace = new_request_trace(request_path=request_path)
            perf_trace.set_metadata(
                "perf_flags",
                {
                    "disable_llm": load_perf_settings().disable_llm,
                    "disable_rerank": load_perf_settings().disable_rerank,
                    "retrieval_mode": load_perf_settings().retrieval_mode,
                    "rerank_top_n": load_perf_settings().rerank_top_n,
                    "enable_query_embed_cache": load_perf_settings().enable_query_embed_cache,
                    "enable_llm_keepalive": load_perf_settings().enable_llm_keepalive,
                },
            )
            trace_token = set_current_trace(perf_trace)
            status_code = 500
            response_payload: dict[str, Any] | None = None
            error_payload: dict[str, Any] | None = None
            try:
                with stage_timer("request_parse"):
                    payload = self._read_json_body()
                    query = service._normalize_query_payload(payload)
                perf_trace.query = query
                response_payload = service.answer_query(query)
                perf_trace.set_metadata("answer_mode", response_payload.get("answer_mode"))
                perf_trace.set_metadata("answer_text_length", len(response_payload.get("answer_text") or ""))
                perf_trace.set_metadata("citations_count", len(response_payload.get("citations") or []))
                perf_trace.set_metadata("llm_debug", service.last_llm_debug or {})
                log_answer_diagnostics(
                    request_path=request_path,
                    query=query,
                    response_payload=response_payload,
                    llm_debug=service.last_llm_debug,
                )
                status_code = 200
            except ApiRequestError as exc:
                perf_trace.set_metadata("error", {"code": exc.code, "message": exc.message})
                status_code = exc.status_code
                error_payload = {"error": {"code": exc.code, "message": exc.message}}
            except Exception as exc:  # pragma: no cover - defensive transport guard
                log(f"[api:error] {exc}")
                perf_trace.set_metadata("error", {"code": "internal_error", "message": str(exc)})
                status_code = 500
                error_payload = {"error": {"code": "internal_error", "message": "Internal server error."}}

            try:
                if error_payload is not None:
                    self._send_json(status_code, error_payload)
                    return
                self._send_json(200, response_payload or {})
            finally:
                perf_trace.status_code = status_code
                record = perf_trace.to_log_record()
                persist_request_log(record, log_path=load_perf_settings().log_path)
                log(json.dumps(record, ensure_ascii=False))
                reset_current_trace(trace_token)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlsplit(self.path)
            request_path = parsed.path
            if request_path == CONVERSATIONS_API_PATH:
                query_params = parse_qs(parsed.query)
                search = query_params.get("search", [""])[0]
                try:
                    client_id = self._read_client_id_header()
                    response_payload = service.list_conversations(client_id, search)
                except ApiRequestError as exc:
                    self._send_json(exc.status_code, {"error": {"code": exc.code, "message": exc.message}})
                    return
                self._send_json(200, response_payload)
                return

            conversation_id = match_conversation_detail_route(request_path)
            if conversation_id is not None:
                try:
                    client_id = self._read_client_id_header()
                    response_payload = service.get_conversation(client_id, conversation_id)
                except ApiRequestError as exc:
                    self._send_json(exc.status_code, {"error": {"code": exc.code, "message": exc.message}})
                    return
                self._send_json(200, response_payload)
                return

            if is_frontend_shell_route(request_path):
                self._send_frontend_shell()
                return

            if is_frontend_asset_route(request_path):
                self._send_frontend_asset(request_path)
                return

            self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})

        def do_HEAD(self) -> None:  # noqa: N802
            request_path = urlsplit(self.path).path
            if is_frontend_shell_route(request_path):
                self._send_frontend_shell(include_body=False)
                return

            if is_frontend_asset_route(request_path):
                self._send_frontend_asset(request_path, include_body=False)
                return

            if request_path in {API_PATH, API_STREAM_PATH, CONVERSATIONS_API_PATH} or match_conversation_detail_route(request_path) or match_conversation_messages_route(request_path):
                self.send_response(405)
                self._send_cache_headers()
                self.send_header("Allow", "GET, POST, DELETE")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})

        def do_DELETE(self) -> None:  # noqa: N802
            request_path = urlsplit(self.path).path
            if request_path == CONVERSATIONS_API_PATH:
                try:
                    client_id = self._read_client_id_header()
                    response_payload = service.delete_all_conversations(client_id)
                except ApiRequestError as exc:
                    self._send_json(exc.status_code, {"error": {"code": exc.code, "message": exc.message}})
                    return
                except Exception as exc:  # pragma: no cover - defensive transport guard
                    log(f"[api:error] {exc}")
                    self._send_json(
                        500,
                        {"error": {"code": "internal_error", "message": "Internal server error."}},
                    )
                    return

                self._send_json(200, response_payload)
                return

            conversation_id = match_conversation_detail_route(request_path)
            if conversation_id is None:
                self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
                return

            try:
                client_id = self._read_client_id_header()
                response_payload = service.delete_conversation(client_id, conversation_id)
            except ApiRequestError as exc:
                self._send_json(exc.status_code, {"error": {"code": exc.code, "message": exc.message}})
                return
            except Exception as exc:  # pragma: no cover - defensive transport guard
                log(f"[api:error] {exc}")
                self._send_json(
                    500,
                    {"error": {"code": "internal_error", "message": "Internal server error."}},
                )
                return

            self._send_json(200, response_payload)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _read_json_body(self) -> Any:
            content_length = self.headers.get("Content-Length")
            if content_length is None:
                raise ApiRequestError(400, "invalid_request", "Request body is required.")

            try:
                body_size = int(content_length)
            except ValueError as exc:
                raise ApiRequestError(400, "invalid_request", "Invalid Content-Length header.") from exc

            raw_body = self.rfile.read(body_size)
            if not raw_body:
                raise ApiRequestError(400, "invalid_request", "Request body is required.")

            try:
                return json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ApiRequestError(400, "invalid_json", "Request body must be valid JSON.") from exc

        def _read_client_id_header(self) -> str:
            return normalize_client_id(self.headers.get(CLIENT_ID_HEADER))

        @staticmethod
        def _is_client_disconnect(exc: BaseException) -> bool:
            return is_benign_disconnect_exception(exc)

        def _send_json(
            self,
            status_code: int,
            payload: dict[str, Any],
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            try:
                with stage_timer("response_build/serialize"):
                    body = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
                    self.send_response(status_code)
                    self._send_cache_headers()
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    for header_name, header_value in self._build_request_perf_headers(extra_headers).items():
                        self.send_header(header_name, header_value)
                    self.end_headers()
                    self.wfile.write(body)
            except BaseException as exc:
                if self._is_client_disconnect(exc):
                    self.close_connection = True
                    return
                raise

        def _build_request_perf_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
            headers = dict(extra_headers or {})
            trace = current_trace()
            if trace is not None:
                headers.setdefault("X-Request-Id", trace.request_id)
                headers.setdefault("Server-Timing", trace.server_timing_value())
            return headers

        def _send_frontend_shell(self, include_body: bool = True) -> None:
            index_path = frontend_root / "index.html"
            if index_path.exists() and index_path.is_file():
                self._send_file(index_path, include_body=include_body)
                return
            self._send_frontend_missing(include_body=include_body)

        def _send_frontend_asset(self, request_path: str, include_body: bool = True) -> None:
            target_path = resolve_frontend_asset_path(frontend_root, request_path)
            if target_path is None:
                self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
                return
            self._send_file(target_path, include_body=include_body)

        def _send_file(self, file_path: Path, include_body: bool = True) -> None:
            if not file_path.exists() or not file_path.is_file():
                self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
                return

            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = "application/octet-stream"

            body = file_path.read_bytes()
            self.send_response(200)
            self._send_cache_headers()
            self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
            self.send_header("Content-Length", str(len(body)))
            try:
                self.end_headers()
                if include_body:
                    self.wfile.write(body)
            except BaseException as exc:
                if self._is_client_disconnect(exc):
                    self.close_connection = True
                    return
                raise

        def _send_frontend_missing(self, include_body: bool = True) -> None:
            message = (
                "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" />"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />"
                "<title>Frontend Build Required</title></head><body>"
                "<main style=\"max-width:720px;margin:48px auto;padding:0 20px;"
                "font:16px/1.7 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;"
                "color:#241d15;\">"
                "<h1 style=\"font-size:28px;line-height:1.3;\">前端构建产物不存在</h1>"
                "<p>当前后端只托管 React 构建产物 <code>frontend/dist/</code>。</p>"
                "<p>请先在项目根目录运行：</p>"
                "<pre style=\"padding:14px 16px;border:1px solid #ddd;border-radius:12px;"
                "background:#faf7f2;overflow:auto;\">cd frontend\nnpm install\nnpm run build</pre>"
                "<p>若你正在开发并想要热更新，请运行 <code>python scripts/dev.py</code>，"
                "然后访问 <code>http://127.0.0.1:5173/</code>。</p>"
                "<p>构建完成后，重新刷新当前页面即可。</p>"
                "</main></body></html>"
            ).encode("utf-8")

            self.send_response(503)
            self._send_cache_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(message) if include_body else 0))
            try:
                self.end_headers()
                if include_body:
                    self.wfile.write(message)
            except BaseException as exc:
                if self._is_client_disconnect(exc):
                    self.close_connection = True
                    return
                raise

        def _send_cache_headers(self) -> None:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")

        def _handle_stream_post(self) -> None:
            try:
                payload = self._read_json_body()
                query = service._normalize_query_payload(payload)
            except ApiRequestError as exc:
                self._send_json(exc.status_code, {"error": {"code": exc.code, "message": exc.message}})
                return

            try:
                self.send_response(200)
                self._send_cache_headers()
                self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True

                def progress_callback(progress_event: dict[str, Any]) -> None:
                    self._write_stream_event(
                        build_stream_phase_event(
                            progress_event.get("stage", ""),
                            progress_event.get("detail"),
                        )
                    )

                response_payload = service.answer_query(query, progress_callback=progress_callback)
                log_answer_diagnostics(
                    request_path=API_STREAM_PATH,
                    query=query,
                    response_payload=response_payload,
                    llm_debug=service.last_llm_debug,
                )
                self._write_stream_event({"type": "evidence_ready", "payload": response_payload})
                for chunk in split_answer_text_for_stream(response_payload.get("answer_text", "")):
                    self._write_stream_event({"type": "answer_delta", "delta": chunk})
                    time.sleep(STREAM_CHUNK_DELAY_SECONDS)
                self._write_stream_event(
                    {
                        **build_stream_phase_event("completed", "回答已准备完成，正在切换到最终展示。"),
                        "type": "completed",
                        "payload": response_payload,
                    }
                )
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return
            except ApiRequestError as exc:
                self._write_stream_error(exc.status_code, exc.code, exc.message)
            except Exception as exc:  # pragma: no cover - defensive transport guard
                log(f"[api:stream_error] {exc}")
                self._write_stream_error(500, "internal_error", "Internal server error.")

        def _write_stream_event(self, payload: dict[str, Any]) -> None:
            body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
            self.wfile.write(body)
            self.wfile.flush()

        def _write_stream_error(self, status_code: int, code: str, message: str) -> None:
            try:
                self._write_stream_event(
                    {
                        "type": "error",
                        "status_code": status_code,
                        "error": {"code": code, "message": message},
                    }
                )
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return

    return MinimalApiHandler


def build_examples_payload(base_url: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "endpoint": API_PATH,
        "method": "POST",
        "examples": results,
    }


def build_smoke_markdown(command: str, base_url: str, results: list[dict[str, Any]]) -> str:
    strong = next(result for result in results if result["example_id"] == "strong_chunk_backref")
    weak = next(result for result in results if result["example_id"] == "weak_with_review_notice")
    refuse = next(result for result in results if result["example_id"] == "refuse_no_match")

    lines = [
        "# Minimal API Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## Endpoint",
        "",
        f"- base_url: `{base_url}`",
        f"- method: `POST`",
        f"- path: `{API_PATH}`",
        "",
        "## 结论",
        "",
    ]

    for result in results:
        body = result["response_body"]
        lines.append(
            f"- `{result['request_body']['query']}` -> status=`{result['response_status']}`, "
            f"mode=`{body['answer_mode']}`, primary={len(body['primary_evidence'])}, "
            f"secondary={len(body['secondary_evidence'])}, review={len(body['review_materials'])}, "
            f"citations={len(body['citations'])}"
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- route_callable: `{all(result['response_status'] == 200 for result in results)}`",
            f"- request_body_only_query: `{all(result['request_keys'] == ['query'] for result in results)}`",
            f"- payload_fields_stable: `{all(result['response_keys'] == EXPECTED_PAYLOAD_FIELDS for result in results)}`",
            f"- strong_mode_kept: `{strong['response_body']['answer_mode'] == 'strong'}`",
            f"- weak_review_mode_kept: `{weak['response_body']['answer_mode'] == 'weak_with_review_notice'}`",
            f"- refuse_mode_kept: `{refuse['response_body']['answer_mode'] == 'refuse'}`",
        ]
    )

    for result in results:
        body = result["response_body"]
        lines.extend(
            [
                "",
                f"## Query: {result['request_body']['query']}",
                "",
                f"- request_body: `{json_dumps(result['request_body'])}`",
                f"- response_status: `{result['response_status']}`",
                f"- response_keys: `{json_dumps(result['response_keys'])}`",
                f"- answer_mode: `{body['answer_mode']}`",
                f"- disclaimer: {body['disclaimer'] or 'None'}",
                f"- review_notice: {body['review_notice'] or 'None'}",
                f"- refuse_reason: {body['refuse_reason'] or 'None'}",
                f"- evidence_summary: primary={len(body['primary_evidence'])}, secondary={len(body['secondary_evidence'])}, review={len(body['review_materials'])}",
                f"- citations_summary: `{json_dumps([citation['record_id'] for citation in body['citations']])}`",
            ]
        )

    return "\n".join(lines) + "\n"


def build_llm_examples_payload(config: ModelStudioLLMConfig, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": config.provider_name,
        "interface": config.interface_name,
        "model": config.model,
        "mode": config.mode_name,
        "base_url": config.base_url,
        "endpoint": API_PATH,
        "examples": results,
    }


def _slot_record_ids(payload: dict[str, Any], slot_name: str) -> list[str]:
    return [row["record_id"] for row in payload.get(slot_name, []) if isinstance(row, dict) and row.get("record_id")]


def _citation_pairs(payload: dict[str, Any]) -> list[dict[str, str | None]]:
    return [
        {
            "record_id": citation.get("record_id"),
            "citation_role": citation.get("citation_role"),
        }
        for citation in payload.get("citations", [])
        if isinstance(citation, dict)
    ]


def build_llm_smoke_markdown(command: str, config: ModelStudioLLMConfig, results: list[dict[str, Any]]) -> str:
    lines = [
        "# Minimal LLM API Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## LLM Config",
        "",
        f"- provider: `{config.provider_name}`",
        f"- interface: `{config.interface_name}`",
        f"- model: `{config.model}`",
        f"- mode: `{config.mode_name}`",
        f"- base_url: `{config.base_url}`",
        f"- llm_enabled: `{config.enabled}`",
        f"- enable_thinking: `{config.enable_thinking}`",
        "",
        "## 结论",
        "",
    ]

    for result in results:
        llm_body = result["llm_response_body"]
        llm_debug = result["llm_debug"]
        lines.append(
            f"- `{result['request_body']['query']}` -> mode=`{llm_body['answer_mode']}`, "
            f"attempted=`{result['llm_attempted']}`, answer_source=`{llm_debug.get('answer_source')}`, "
            f"fallback=`{result['fallback_used']}`, "
            f"evidence_unchanged=`{result['evidence_unchanged']}`, citations_unchanged=`{result['citations_unchanged']}`"
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- mode_match_kept: `{all(result['mode_match'] for result in results)}`",
            f"- evidence_unchanged: `{all(result['evidence_unchanged'] for result in results)}`",
            f"- citations_unchanged: `{all(result['citations_unchanged'] for result in results)}`",
            f"- refuse_skips_llm: `{all(result['refuse_skipped'] for result in results if result['expected_mode'] == 'refuse')}`",
            f"- llm_attempted_for_non_refuse: `{all(result['llm_attempted'] for result in results if result['expected_mode'] != 'refuse')}`",
            f"- at_least_one_non_refuse_llm_used: `{any(result['llm_used'] for result in results if result['expected_mode'] != 'refuse')}`",
            f"- answer_text_non_empty: `{all(bool(result['llm_response_body']['answer_text']) for result in results)}`",
        ]
    )

    for result in results:
        llm_body = result["llm_response_body"]
        lines.extend(
            [
                "",
                f"## Query: {result['request_body']['query']}",
                "",
                f"- expected_mode: `{result['expected_mode']}`",
                f"- baseline_mode: `{result['baseline_response_body']['answer_mode']}`",
                f"- llm_mode: `{llm_body['answer_mode']}`",
                f"- llm_attempted: `{result['llm_attempted']}`",
                f"- llm_used: `{result['llm_used']}`",
                f"- fallback_used: `{result['fallback_used']}`",
                f"- answer_text_changed: `{result['answer_text_changed']}`",
                f"- evidence_unchanged: `{result['evidence_unchanged']}`",
                f"- citations_unchanged: `{result['citations_unchanged']}`",
                f"- llm_debug: `{json_dumps(result['llm_debug'])}`",
                f"- baseline_citations: `{json_dumps(_citation_pairs(result['baseline_response_body']))}`",
                f"- llm_citations: `{json_dumps(_citation_pairs(llm_body))}`",
            ]
        )

    return "\n".join(lines) + "\n"


def assert_smoke_expectations(results: list[dict[str, Any]]) -> None:
    if len(results) != len(DEFAULT_EXAMPLES):
        raise AssertionError("HTTP smoke results count does not match default examples")

    for result in results:
        if result["response_status"] != 200:
            raise AssertionError(f"unexpected HTTP status for {result['example_id']}: {result['response_status']}")
        if result["request_keys"] != ["query"]:
            raise AssertionError(f"request body drift detected for {result['example_id']}")
        if result["response_keys"] != EXPECTED_PAYLOAD_FIELDS:
            raise AssertionError(f"payload contract drift detected for {result['example_id']}")
        if result["response_body"]["query"] != result["request_body"]["query"]:
            raise AssertionError(f"query echo mismatch for {result['example_id']}")
        if result["response_body"]["answer_mode"] != result["expected_mode"]:
            raise AssertionError(f"mode drift detected for {result['example_id']}")

    strong = next(result for result in results if result["example_id"] == "strong_chunk_backref")
    if not strong["response_body"]["primary_evidence"]:
        raise AssertionError("strong example missing primary evidence")

    weak = next(result for result in results if result["example_id"] == "weak_with_review_notice")
    if weak["response_body"]["primary_evidence"]:
        raise AssertionError("weak_with_review_notice should not contain primary evidence")
    if not weak["response_body"]["review_notice"]:
        raise AssertionError("weak_with_review_notice missing review_notice")

    refuse = next(result for result in results if result["example_id"] == "refuse_no_match")
    if refuse["response_body"]["primary_evidence"]:
        raise AssertionError("refuse should not contain primary evidence")
    if not refuse["response_body"]["refuse_reason"]:
        raise AssertionError("refuse missing refuse_reason")


def assert_llm_smoke_expectations(results: list[dict[str, Any]]) -> None:
    if len(results) != len(LLM_SMOKE_EXAMPLES):
        raise AssertionError("LLM smoke results count does not match expected examples")

    non_refuse_results = [result for result in results if result["expected_mode"] != "refuse"]

    for result in results:
        if result["llm_response_keys"] != EXPECTED_PAYLOAD_FIELDS:
            raise AssertionError(f"payload contract drift detected for {result['example_id']}")
        if not result["mode_match"]:
            raise AssertionError(f"mode drift detected for {result['example_id']}")
        if not result["evidence_unchanged"]:
            raise AssertionError(f"evidence slots changed for {result['example_id']}")
        if not result["citations_unchanged"]:
            raise AssertionError(f"citations changed for {result['example_id']}")
        if not result["llm_response_body"]["answer_text"]:
            raise AssertionError(f"answer_text is empty for {result['example_id']}")
        if result["expected_mode"] != "refuse" and not result["llm_attempted"]:
            raise AssertionError(f"LLM was not attempted for {result['example_id']}")
        if result["expected_mode"] != "refuse" and not (result["llm_used"] or result["fallback_used"]):
            raise AssertionError(f"LLM outcome is unclear for {result['example_id']}")

    refuse = next(result for result in results if result["expected_mode"] == "refuse")
    if not refuse["refuse_skipped"]:
        raise AssertionError("refuse path should skip LLM rendering")
    if non_refuse_results and not any(result["llm_used"] for result in non_refuse_results):
        raise AssertionError("at least one non-refuse LLM sample must render successfully without fallback")


def post_json(url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib_request.Request(
        url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(request) as response:
        response_body = json.loads(response.read().decode("utf-8"))
        return response.status, response_body


def run_http_examples(server: MinimalApiHTTPServer, host: str) -> tuple[str, list[dict[str, Any]]]:
    base_url = f"http://{host}:{server.server_address[1]}"
    endpoint_url = f"{base_url}{API_PATH}"
    results: list[dict[str, Any]] = []
    failures: list[BaseException] = []

    def client_worker() -> None:
        try:
            for example in DEFAULT_EXAMPLES:
                request_body = {"query": example["query_text"]}
                response_status, response_body = post_json(endpoint_url, request_body)
                results.append(
                    {
                        "example_id": example["example_id"],
                        "expected_mode": example["expected_mode"],
                        "request_path": API_PATH,
                        "request_keys": list(request_body.keys()),
                        "request_body": request_body,
                        "response_status": response_status,
                        "response_keys": list(response_body.keys()),
                        "response_body": response_body,
                    }
                )
        except BaseException as exc:  # pragma: no cover - smoke runner bridge
            failures.append(exc)

    client = threading.Thread(target=client_worker, name="minimal-api-smoke-client")
    client.start()
    for _ in DEFAULT_EXAMPLES:
        server.handle_request()
    client.join()

    if failures:
        raise failures[0]

    return base_url, results


def resolve_runtime_paths(args: argparse.Namespace) -> dict[str, Path]:
    frontend_root = resolve_project_path(DEFAULT_FRONTEND_DIR)
    return {
        "db_path": resolve_project_path(args.db_path),
        "conversations_db_path": resolve_project_path(args.conversations_db_path),
        "policy_path": resolve_project_path(args.policy_json),
        "cache_dir": resolve_project_path(args.cache_dir),
        "dense_chunks_index": resolve_project_path(args.dense_chunks_index),
        "dense_chunks_meta": resolve_project_path(args.dense_chunks_meta),
        "dense_main_index": resolve_project_path(args.dense_main_index),
        "dense_main_meta": resolve_project_path(args.dense_main_meta),
        "frontend_root": frontend_root / DEFAULT_FRONTEND_DIST_SUBDIR,
        "examples_out": resolve_project_path(args.examples_out),
        "smoke_out": resolve_project_path(args.smoke_checks_out),
        "llm_examples_out": resolve_project_path(args.llm_examples_out),
        "llm_smoke_out": resolve_project_path(args.llm_smoke_checks_out),
    }


def create_llm_config(args: argparse.Namespace, *, force_enabled: bool | None = None) -> ModelStudioLLMConfig:
    enabled_override = force_enabled if force_enabled is not None else (False if args.llm_disabled else None)
    return load_modelstudio_llm_config(
        enabled_override=enabled_override,
        model_override=args.llm_model,
        base_url_override=args.llm_base_url,
        timeout_override=args.llm_timeout_seconds,
        max_output_tokens_override=args.llm_max_output_tokens,
    )


def create_service(
    args: argparse.Namespace,
    paths: dict[str, Path],
    *,
    llm_enabled_override: bool | None = None,
) -> MinimalApiService:
    return MinimalApiService(
        db_path=paths["db_path"],
        conversations_db_path=paths["conversations_db_path"],
        policy_path=paths["policy_path"],
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=paths["cache_dir"],
        dense_chunks_index=paths["dense_chunks_index"],
        dense_chunks_meta=paths["dense_chunks_meta"],
        dense_main_index=paths["dense_main_index"],
        dense_main_meta=paths["dense_main_meta"],
        llm_config=create_llm_config(args, force_enabled=llm_enabled_override),
    )


def run_llm_examples(
    baseline_service: MinimalApiService,
    llm_service: MinimalApiService,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in LLM_SMOKE_EXAMPLES:
        request_body = {"query": example["query_text"]}
        baseline_payload = baseline_service.answer(request_body)
        llm_payload = llm_service.answer(request_body)
        llm_debug = dict(llm_service.last_llm_debug or {})
        llm_attempted = bool(llm_debug.get("attempted"))
        llm_used = bool(llm_debug.get("used_llm"))
        fallback_used = bool(llm_debug.get("fallback_used"))
        evidence_unchanged = (
            _slot_record_ids(baseline_payload, "primary_evidence") == _slot_record_ids(llm_payload, "primary_evidence")
            and _slot_record_ids(baseline_payload, "secondary_evidence")
            == _slot_record_ids(llm_payload, "secondary_evidence")
            and _slot_record_ids(baseline_payload, "review_materials") == _slot_record_ids(llm_payload, "review_materials")
        )
        citations_unchanged = _citation_pairs(baseline_payload) == _citation_pairs(llm_payload)
        results.append(
            {
                "example_id": example["example_id"],
                "expected_mode": example["expected_mode"],
                "request_body": request_body,
                "baseline_response_keys": list(baseline_payload.keys()),
                "llm_response_keys": list(llm_payload.keys()),
                "baseline_response_body": baseline_payload,
                "llm_response_body": llm_payload,
                "llm_debug": llm_debug,
                "llm_attempted": llm_attempted,
                "llm_used": llm_used,
                "fallback_used": fallback_used,
                "mode_match": baseline_payload["answer_mode"] == llm_payload["answer_mode"] == example["expected_mode"],
                "evidence_unchanged": evidence_unchanged,
                "citations_unchanged": citations_unchanged,
                "answer_text_changed": baseline_payload["answer_text"] != llm_payload["answer_text"],
                "refuse_skipped": (
                    example["expected_mode"] != "refuse"
                    or (not llm_attempted and llm_debug.get("skipped_reason") == "refuse_mode")
                ),
            }
        )
    return results


def run_smoke_mode(args: argparse.Namespace, paths: dict[str, Path]) -> int:
    paths["examples_out"].parent.mkdir(parents=True, exist_ok=True)
    paths["smoke_out"].parent.mkdir(parents=True, exist_ok=True)

    service = create_service(args, paths)
    server = MinimalApiHTTPServer((args.host, 0), make_handler(service, paths["frontend_root"]))
    try:
        log(f"[1/4] Loaded minimal API service from {paths['db_path']}")
        log(f"[2/4] Bound temporary HTTP server on http://{args.host}:{server.server_address[1]}{API_PATH}")
        base_url, results = run_http_examples(server, args.host)
        assert_smoke_expectations(results)
        paths["examples_out"].write_text(
            json_dumps(build_examples_payload(base_url, results)) + "\n",
            encoding="utf-8",
        )
        command = f"{Path(sys.executable).name} -m backend.api.minimal_api --smoke"
        paths["smoke_out"].write_text(build_smoke_markdown(command, base_url, results), encoding="utf-8")
        log("[3/4] Ran HTTP API smoke examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {paths['examples_out']} and {paths['smoke_out']}")
        return 0
    finally:
        server.server_close()
        service.close()


def run_llm_smoke_mode(args: argparse.Namespace, paths: dict[str, Path]) -> int:
    paths["llm_examples_out"].parent.mkdir(parents=True, exist_ok=True)
    paths["llm_smoke_out"].parent.mkdir(parents=True, exist_ok=True)

    baseline_service = create_service(args, paths, llm_enabled_override=False)
    llm_service = create_service(args, paths, llm_enabled_override=True)
    try:
        llm_config = llm_service.llm_config
        log(f"[1/4] Loaded baseline service from {paths['db_path']}")
        log(f"[2/4] Loaded {llm_config.provider_name} config for {llm_config.model} ({llm_config.mode_name})")
        results = run_llm_examples(baseline_service, llm_service)
        assert_llm_smoke_expectations(results)
        paths["llm_examples_out"].write_text(
            json_dumps(build_llm_examples_payload(llm_config, results)) + "\n",
            encoding="utf-8",
        )
        command_parts = [Path(sys.executable).name, "-m", "backend.api.minimal_api", "--llm-smoke", "--llm-enabled"]
        if args.llm_model:
            command_parts.extend(["--llm-model", args.llm_model])
        if args.llm_base_url:
            command_parts.extend(["--llm-base-url", args.llm_base_url])
        if args.llm_timeout_seconds is not None:
            command_parts.extend(["--llm-timeout-seconds", str(args.llm_timeout_seconds)])
        if args.llm_max_output_tokens is not None:
            command_parts.extend(["--llm-max-output-tokens", str(args.llm_max_output_tokens)])
        command = " ".join(shlex.quote(part) for part in command_parts)
        paths["llm_smoke_out"].write_text(build_llm_smoke_markdown(command, llm_config, results), encoding="utf-8")
        log("[3/4] Ran Model Studio LLM smoke examples and validated mode / evidence / citations stability")
        log(f"[4/4] Wrote {paths['llm_examples_out']} and {paths['llm_smoke_out']}")
        return 0
    finally:
        baseline_service.close()
        llm_service.close()


def run_server_mode(args: argparse.Namespace, paths: dict[str, Path]) -> int:
    service = create_service(args, paths)
    server = MinimalApiHTTPServer((args.host, args.port), make_handler(service, paths["frontend_root"]))
    try:
        log(f"[1/3] Loaded minimal API service from {paths['db_path']}")
        log(
            f"[2/3] Serving frontend on http://{args.host}:{args.port}/ and POST "
            f"{API_PATH} / {API_STREAM_PATH} plus {CONVERSATIONS_API_PATH}"
        )
        log("[3/3] Press Ctrl+C to stop")
        server.serve_forever()
        return 0
    except KeyboardInterrupt:
        log("Shutting down minimal API server")
        return 0
    finally:
        server.server_close()
        service.close()


def main() -> int:
    args = parse_args()
    paths = resolve_runtime_paths(args)

    if args.llm_smoke:
        try:
            return run_llm_smoke_mode(args, paths)
        except LLMConfigError as exc:
            log(f"[llm:config_error] {exc}")
            return 2
    try:
        if args.smoke:
            return run_smoke_mode(args, paths)
        return run_server_mode(args, paths)
    except LLMConfigError as exc:
        log(f"[llm:config_error] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
