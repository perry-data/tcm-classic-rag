from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"
DEFAULT_LLM_TIMEOUT_SECONDS = 12.0
DEFAULT_LLM_MAX_OUTPUT_TOKENS = 480
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


class OpenRouterLLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenRouterLLMConfig:
    enabled: bool
    api_key: str | None
    model: str | None
    base_url: str
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_LLM_MAX_OUTPUT_TOKENS
    temperature: float = DEFAULT_LLM_TEMPERATURE
    max_primary_items: int = DEFAULT_MAX_PRIMARY_ITEMS
    max_secondary_items: int = DEFAULT_MAX_SECONDARY_ITEMS
    max_review_items: int = DEFAULT_MAX_REVIEW_ITEMS

    @property
    def provider_name(self) -> str:
        return "OpenRouter"

    def public_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider_name,
            "model": self.model,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
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


def load_openrouter_llm_config(
    *,
    enabled_override: bool | None = None,
    model_override: str | None = None,
    base_url_override: str | None = None,
    timeout_override: float | None = None,
    max_output_tokens_override: int | None = None,
) -> OpenRouterLLMConfig:
    _load_local_env(PROJECT_ROOT / ".env")

    enabled = enabled_override if enabled_override is not None else _parse_bool(os.environ.get(ENV_LLM_ENABLED), default=False)
    model = model_override if model_override is not None else os.environ.get(ENV_MODEL)
    base_url = base_url_override if base_url_override is not None else os.environ.get(ENV_BASE_URL, DEFAULT_OPENROUTER_BASE_URL)
    api_key = os.environ.get(ENV_API_KEY)

    timeout_seconds = timeout_override if timeout_override is not None else DEFAULT_LLM_TIMEOUT_SECONDS
    max_output_tokens = max_output_tokens_override if max_output_tokens_override is not None else DEFAULT_LLM_MAX_OUTPUT_TOKENS

    if not enabled:
        return OpenRouterLLMConfig(
            enabled=False,
            api_key=None,
            model=model or DEFAULT_OPENROUTER_MODEL,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )

    if not api_key:
        raise LLMConfigError(
            f"LLM is enabled but {ENV_API_KEY} is missing. Populate .env or export the variable before starting the service."
        )

    if not model:
        raise LLMConfigError(
            f"LLM is enabled but {ENV_MODEL} is missing. The only supported model for this release is {DEFAULT_OPENROUTER_MODEL}."
        )

    if model != DEFAULT_OPENROUTER_MODEL:
        raise LLMConfigError(
            f"Unsupported LLM model: {model}. This release only supports {DEFAULT_OPENROUTER_MODEL} via OpenRouter."
        )

    return OpenRouterLLMConfig(
        enabled=True,
        api_key=api_key,
        model=model,
        base_url=base_url.rstrip("/"),
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


class OpenRouterLLMClient:
    def __init__(self, config: OpenRouterLLMConfig) -> None:
        self.config = config

    def render_answer_text(self, *, system_instruction: str, user_prompt: str) -> str:
        if not self.config.enabled:
            raise OpenRouterLLMError("OpenRouterLLMClient called while disabled.")

        endpoint = f"{self.config.base_url}/chat/completions"
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
        }

        request = urllib_request.Request(
            endpoint,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
                "HTTP-Referer": "https://localhost/tcm-classic-rag",
                "X-Title": "tcm-classic-rag",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            response_text = exc.read().decode("utf-8", errors="replace")
            raise OpenRouterLLMError(f"OpenRouter returned HTTP {exc.code}: {response_text}") from exc
        except urllib_error.URLError as exc:
            raise OpenRouterLLMError(f"OpenRouter request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OpenRouterLLMError("OpenRouter request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise OpenRouterLLMError("OpenRouter returned invalid JSON.") from exc

        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenRouterLLMError("OpenRouter response did not include choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenRouterLLMError("OpenRouter response choice is malformed.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenRouterLLMError("OpenRouter response message is missing.")

        content = _extract_content_from_choice(message.get("content"))
        if not content:
            raise OpenRouterLLMError("OpenRouter response content is empty.")
        return content
