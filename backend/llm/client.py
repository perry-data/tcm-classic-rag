from __future__ import annotations

import http.client
import json
import os
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from backend.perf import load_perf_settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_STUDIO_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL_STUDIO_MODEL = "qwen-plus"
DEFAULT_LLM_TIMEOUT_SECONDS = 20.0
DEFAULT_LLM_MAX_OUTPUT_TOKENS = 900
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_MAX_PRIMARY_ITEMS = 3
DEFAULT_MAX_SECONDARY_ITEMS = 3
DEFAULT_MAX_REVIEW_ITEMS = 2

ENV_LLM_ENABLED = "TCM_RAG_LLM_ENABLED"
ENV_API_KEY = "TCM_RAG_LLM_API_KEY"
ENV_MODEL = "TCM_RAG_LLM_MODEL"
ENV_BASE_URL = "TCM_RAG_LLM_BASE_URL"


class LLMConfigError(RuntimeError):
    pass


class ModelStudioLLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelStudioLLMConfig:
    enabled: bool
    api_key: str | None
    model: str
    base_url: str
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_LLM_MAX_OUTPUT_TOKENS
    temperature: float = DEFAULT_LLM_TEMPERATURE
    max_primary_items: int = DEFAULT_MAX_PRIMARY_ITEMS
    max_secondary_items: int = DEFAULT_MAX_SECONDARY_ITEMS
    max_review_items: int = DEFAULT_MAX_REVIEW_ITEMS
    enable_thinking: bool = False

    @property
    def provider_name(self) -> str:
        return "Alibaba Cloud Model Studio"

    @property
    def interface_name(self) -> str:
        return "OpenAI-compatible Chat Completions"

    @property
    def mode_name(self) -> str:
        return "non-thinking"

    def public_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider_name,
            "interface": self.interface_name,
            "model": self.model,
            "mode": self.mode_name,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "enable_thinking": self.enable_thinking,
        }


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _load_local_env(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = _strip_quotes(raw_value)
        os.environ.setdefault(key, value)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _looks_like_openrouter_url(base_url: str) -> bool:
    netloc = urlsplit(base_url).netloc.lower()
    return netloc.endswith("openrouter.ai")


def load_modelstudio_llm_config(
    *,
    enabled_override: bool | None = None,
    model_override: str | None = None,
    base_url_override: str | None = None,
    timeout_override: float | None = None,
    max_output_tokens_override: int | None = None,
) -> ModelStudioLLMConfig:
    _load_local_env(PROJECT_ROOT / ".env")

    enabled = enabled_override if enabled_override is not None else _parse_bool(os.environ.get(ENV_LLM_ENABLED), default=True)
    model = _clean_optional_text(model_override if model_override is not None else os.environ.get(ENV_MODEL))
    base_url = _clean_optional_text(
        base_url_override if base_url_override is not None else os.environ.get(ENV_BASE_URL, DEFAULT_MODEL_STUDIO_BASE_URL)
    )
    api_key = os.environ.get(ENV_API_KEY)

    timeout_seconds = timeout_override if timeout_override is not None else DEFAULT_LLM_TIMEOUT_SECONDS
    max_output_tokens = max_output_tokens_override if max_output_tokens_override is not None else DEFAULT_LLM_MAX_OUTPUT_TOKENS
    resolved_model = model or DEFAULT_MODEL_STUDIO_MODEL
    resolved_base_url = (base_url or DEFAULT_MODEL_STUDIO_BASE_URL).rstrip("/")

    if _looks_like_openrouter_url(resolved_base_url):
        raise LLMConfigError(
            "LLM provider is fixed to Alibaba Cloud Model Studio. Replace "
            f"{ENV_BASE_URL} with a DashScope OpenAI-compatible endpoint such as {DEFAULT_MODEL_STUDIO_BASE_URL}."
        )

    if resolved_model != DEFAULT_MODEL_STUDIO_MODEL:
        raise LLMConfigError(
            f"LLM model is fixed to {DEFAULT_MODEL_STUDIO_MODEL!r} for this release. "
            f"Received {resolved_model!r} from {ENV_MODEL} / CLI overrides."
        )

    if not enabled:
        return ModelStudioLLMConfig(
            enabled=False,
            api_key=None,
            model=resolved_model,
            base_url=resolved_base_url,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )

    if not api_key:
        raise LLMConfigError(
            f"LLM is enabled but {ENV_API_KEY} is missing. Populate .env or export the variable before starting the service. "
            f"If you need an offline fallback, explicitly set {ENV_LLM_ENABLED}=false or start the API with --llm-disabled."
        )

    return ModelStudioLLMConfig(
        enabled=True,
        api_key=api_key,
        model=resolved_model,
        base_url=resolved_base_url,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
    )


def _extract_content_from_choice(message_content: Any) -> str:
    if isinstance(message_content, str):
        return message_content
    if isinstance(message_content, list):
        parts: list[str] = []
        for item in message_content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str):
                    parts.append(text_value)
        return "".join(parts)
    return ""


class ModelStudioLLMClient:
    def __init__(self, config: ModelStudioLLMConfig) -> None:
        self.config = config
        self._perf_settings = load_perf_settings()
        self._base_url_parts = urlsplit(self.config.base_url)
        self._base_path = self._base_url_parts.path.rstrip("/")
        self._connections: dict[int, http.client.HTTPConnection] = {}
        self._connections_lock = threading.Lock()
        self._thread_local = threading.local()

    def close(self) -> None:
        with self._connections_lock:
            connections = list(self._connections.values())
            self._connections.clear()
        for connection in connections:
            try:
                connection.close()
            except OSError:
                continue

    def get_last_request_metrics(self) -> dict[str, Any] | None:
        metrics = getattr(self._thread_local, "last_request_metrics", None)
        if not isinstance(metrics, dict):
            return None
        return dict(metrics)

    def _set_last_request_metrics(self, metrics: dict[str, Any]) -> None:
        self._thread_local.last_request_metrics = metrics

    def _build_headers(self, *, keepalive_enabled: bool) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        headers["Connection"] = "keep-alive" if keepalive_enabled else "close"
        return headers

    def _endpoint_path(self) -> str:
        if not self._base_path:
            return "/chat/completions"
        return f"{self._base_path}/chat/completions"

    def _create_connection(self) -> http.client.HTTPConnection:
        connection_cls = http.client.HTTPSConnection if self._base_url_parts.scheme == "https" else http.client.HTTPConnection
        host = self._base_url_parts.hostname
        if not host:
            raise ModelStudioLLMError(f"Invalid Model Studio base URL: {self.config.base_url}")
        return connection_cls(
            host,
            self._base_url_parts.port,
            timeout=self.config.timeout_seconds,
        )

    def _get_pooled_connection(self) -> tuple[int, http.client.HTTPConnection]:
        thread_id = threading.get_ident()
        with self._connections_lock:
            connection = self._connections.get(thread_id)
            if connection is None:
                connection = self._create_connection()
                self._connections[thread_id] = connection
        return thread_id, connection

    def _discard_connection(self, thread_id: int, connection: http.client.HTTPConnection) -> None:
        with self._connections_lock:
            current = self._connections.get(thread_id)
            if current is connection:
                self._connections.pop(thread_id, None)
        try:
            connection.close()
        except OSError:
            return

    def render_answer_text(self, *, system_instruction: str, user_prompt: str) -> str:
        if not self.config.enabled:
            raise ModelStudioLLMError("ModelStudioLLMClient called while disabled.")

        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "enable_thinking": self.config.enable_thinking,
        }
        request_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        keepalive_enabled = self._perf_settings.enable_llm_keepalive
        endpoint_path = self._endpoint_path()

        for attempt_number in (1, 2):
            pooled_connection = False
            thread_id = threading.get_ident()
            connection: http.client.HTTPConnection | None = None
            started_at = time.perf_counter()
            try:
                if keepalive_enabled:
                    pooled_connection = True
                    thread_id, connection = self._get_pooled_connection()
                else:
                    connection = self._create_connection()

                connection.request(
                    "POST",
                    endpoint_path,
                    body=request_body,
                    headers=self._build_headers(keepalive_enabled=keepalive_enabled),
                )
                response = connection.getresponse()
                ttfb_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
                response_bytes = response.read()
                total_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
                metrics = {
                    "attempt": attempt_number,
                    "keepalive_enabled": keepalive_enabled,
                    "status_code": response.status,
                    "ttfb_ms": ttfb_ms,
                    "total_ms": total_ms,
                }
                self._set_last_request_metrics(metrics)

                if response.will_close and pooled_connection:
                    self._discard_connection(thread_id, connection)
                elif not pooled_connection:
                    connection.close()

                if response.status >= 400:
                    response_text = response_bytes.decode("utf-8", errors="replace")
                    raise ModelStudioLLMError(f"Model Studio returned HTTP {response.status}: {response_text}")

                try:
                    payload = json.loads(response_bytes.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise ModelStudioLLMError("Model Studio returned invalid JSON.") from exc
                break
            except (http.client.HTTPException, OSError, socket.timeout, TimeoutError) as exc:
                if connection is not None:
                    if pooled_connection:
                        self._discard_connection(thread_id, connection)
                    else:
                        try:
                            connection.close()
                        except OSError:
                            pass
                self._set_last_request_metrics(
                    {
                        "attempt": attempt_number,
                        "keepalive_enabled": keepalive_enabled,
                        "error": str(exc),
                        "ttfb_ms": None,
                        "total_ms": round((time.perf_counter() - started_at) * 1000.0, 3),
                    }
                )
                if keepalive_enabled and attempt_number == 1:
                    continue
                raise ModelStudioLLMError(f"Model Studio request failed: {exc}") from exc
        else:  # pragma: no cover - defensive loop guard
            raise ModelStudioLLMError("Model Studio request failed after retries.")

        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ModelStudioLLMError("Model Studio response did not include choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ModelStudioLLMError("Model Studio response choice is malformed.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ModelStudioLLMError("Model Studio response message is missing.")

        content = _extract_content_from_choice(message.get("content"))
        if not content:
            raise ModelStudioLLMError("Model Studio response content is empty.")
        return content
