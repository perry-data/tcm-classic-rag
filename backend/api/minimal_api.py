#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import shlex
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib import request as urllib_request
from urllib.parse import urlsplit

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
from backend.llm import LLMConfigError, ModelStudioLLMConfig, load_modelstudio_llm_config


API_PATH = "/api/v1/answers"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_API_EXAMPLES_OUT = "artifacts/api_examples.json"
DEFAULT_API_SMOKE_OUT = "artifacts/api_smoke_checks.md"
DEFAULT_LLM_API_EXAMPLES_OUT = "artifacts/llm_api_examples_modelstudio.json"
DEFAULT_LLM_API_SMOKE_OUT = "artifacts/llm_api_smoke_checks_modelstudio.md"
DEFAULT_FRONTEND_DIR = "frontend"
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
    parser.add_argument("--llm-enabled", action="store_true", help="Enable Model Studio answer_text rendering.")
    parser.add_argument("--llm-model", default=None, help="Model Studio model override for this release.")
    parser.add_argument("--llm-base-url", default=None, help="Model Studio base URL override.")
    parser.add_argument("--llm-timeout-seconds", type=float, default=None, help="Model Studio request timeout.")
    parser.add_argument(
        "--llm-max-output-tokens",
        type=int,
        default=None,
        help="Max output tokens for Model Studio answer_text rendering.",
    )
    return parser.parse_args()


class ApiRequestError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


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
    last_llm_debug: dict[str, Any] | None = None

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

    def close(self) -> None:
        self.assembler.close()

    def answer(self, payload: Any) -> dict[str, Any]:
        self.last_llm_debug = None
        if not isinstance(payload, dict):
            raise ApiRequestError(400, "invalid_json", "Request body must be a JSON object.")

        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ApiRequestError(400, "invalid_request", "Field 'query' must be a non-empty string.")

        response_payload = self.assembler.assemble(query.strip())
        self.last_llm_debug = self.assembler.get_last_llm_debug()
        return response_payload


class MinimalApiHTTPServer(HTTPServer):
    allow_reuse_address = True


def make_handler(service: MinimalApiService, frontend_root: Path) -> type[BaseHTTPRequestHandler]:
    class MinimalApiHandler(BaseHTTPRequestHandler):
        server_version = "TCMClassicRAGMinimalAPI/0.1"
        protocol_version = "HTTP/1.1"

        def do_POST(self) -> None:  # noqa: N802
            if urlsplit(self.path).path != API_PATH:
                self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
                return

            try:
                payload = self._read_json_body()
                response_payload = service.answer(payload)
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

        def do_GET(self) -> None:  # noqa: N802
            request_path = urlsplit(self.path).path
            if request_path in {"/", "/index.html", "/frontend", "/frontend/"}:
                self._send_file(frontend_root / "index.html")
                return

            if request_path.startswith("/frontend/"):
                relative_path = request_path.removeprefix("/frontend/")
                target_path = (frontend_root / relative_path).resolve()
                try:
                    target_path.relative_to(frontend_root.resolve())
                except ValueError:
                    self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
                    return
                self._send_file(target_path)
                return

            self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})

        def do_HEAD(self) -> None:  # noqa: N802
            request_path = urlsplit(self.path).path
            if request_path in {"/", "/index.html", "/frontend", "/frontend/"}:
                self._send_file(frontend_root / "index.html", include_body=False)
                return

            if request_path.startswith("/frontend/"):
                relative_path = request_path.removeprefix("/frontend/")
                target_path = (frontend_root / relative_path).resolve()
                try:
                    target_path.relative_to(frontend_root.resolve())
                except ValueError:
                    self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
                    return
                self._send_file(target_path, include_body=False)
                return

            if request_path == API_PATH:
                self.send_response(405)
                self._send_cache_headers()
                self.send_header("Allow", "POST")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            self._send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})

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

        def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
            body = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            self.send_response(status_code)
            self._send_cache_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

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
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def _send_cache_headers(self) -> None:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")

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
    return {
        "db_path": resolve_project_path(args.db_path),
        "policy_path": resolve_project_path(args.policy_json),
        "cache_dir": resolve_project_path(args.cache_dir),
        "dense_chunks_index": resolve_project_path(args.dense_chunks_index),
        "dense_chunks_meta": resolve_project_path(args.dense_chunks_meta),
        "dense_main_index": resolve_project_path(args.dense_main_index),
        "dense_main_meta": resolve_project_path(args.dense_main_meta),
        "frontend_root": resolve_project_path(DEFAULT_FRONTEND_DIR),
        "examples_out": resolve_project_path(args.examples_out),
        "smoke_out": resolve_project_path(args.smoke_checks_out),
        "llm_examples_out": resolve_project_path(args.llm_examples_out),
        "llm_smoke_out": resolve_project_path(args.llm_smoke_checks_out),
    }


def create_llm_config(args: argparse.Namespace, *, force_enabled: bool | None = None) -> ModelStudioLLMConfig:
    enabled_override = force_enabled if force_enabled is not None else (True if args.llm_enabled else None)
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
        log(f"[2/3] Serving frontend on http://{args.host}:{args.port}/ and POST {API_PATH}")
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
