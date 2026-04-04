#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib import request as urllib_request
from urllib.parse import urlsplit

from run_answer_assembler import (
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


API_PATH = "/api/v1/answers"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_API_EXAMPLES_OUT = "artifacts/api_examples.json"
DEFAULT_API_SMOKE_OUT = "artifacts/api_smoke_checks.md"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the minimal HTTP transport adapter for answer payloads.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind the HTTP server.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind the HTTP server.")
    parser.add_argument("--smoke", action="store_true", help="Run local HTTP smoke checks and exit.")
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
        )

    def close(self) -> None:
        self.assembler.close()

    def answer(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ApiRequestError(400, "invalid_json", "Request body must be a JSON object.")

        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ApiRequestError(400, "invalid_request", "Field 'query' must be a non-empty string.")

        return self.assembler.assemble(query.strip())


class MinimalApiHTTPServer(HTTPServer):
    allow_reuse_address = True


def make_handler(service: MinimalApiService) -> type[BaseHTTPRequestHandler]:
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
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

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
    repo_root = Path.cwd()
    return {
        "db_path": (repo_root / args.db_path).resolve(),
        "policy_path": (repo_root / args.policy_json).resolve(),
        "cache_dir": (repo_root / args.cache_dir).resolve(),
        "dense_chunks_index": (repo_root / args.dense_chunks_index).resolve(),
        "dense_chunks_meta": (repo_root / args.dense_chunks_meta).resolve(),
        "dense_main_index": (repo_root / args.dense_main_index).resolve(),
        "dense_main_meta": (repo_root / args.dense_main_meta).resolve(),
        "examples_out": (repo_root / args.examples_out).resolve(),
        "smoke_out": (repo_root / args.smoke_checks_out).resolve(),
    }


def create_service(args: argparse.Namespace, paths: dict[str, Path]) -> MinimalApiService:
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
    )


def run_smoke_mode(args: argparse.Namespace, paths: dict[str, Path]) -> int:
    paths["examples_out"].parent.mkdir(parents=True, exist_ok=True)
    paths["smoke_out"].parent.mkdir(parents=True, exist_ok=True)

    service = create_service(args, paths)
    server = MinimalApiHTTPServer((args.host, 0), make_handler(service))
    try:
        log(f"[1/4] Loaded minimal API service from {paths['db_path']}")
        log(f"[2/4] Bound temporary HTTP server on http://{args.host}:{server.server_address[1]}{API_PATH}")
        base_url, results = run_http_examples(server, args.host)
        assert_smoke_expectations(results)
        paths["examples_out"].write_text(
            json_dumps(build_examples_payload(base_url, results)) + "\n",
            encoding="utf-8",
        )
        command = f"{Path(sys.executable).name} {Path(__file__).name} --smoke"
        paths["smoke_out"].write_text(build_smoke_markdown(command, base_url, results), encoding="utf-8")
        log("[3/4] Ran HTTP API smoke examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {paths['examples_out']} and {paths['smoke_out']}")
        return 0
    finally:
        server.server_close()
        service.close()


def run_server_mode(args: argparse.Namespace, paths: dict[str, Path]) -> int:
    service = create_service(args, paths)
    server = MinimalApiHTTPServer((args.host, args.port), make_handler(service))
    try:
        log(f"[1/3] Loaded minimal API service from {paths['db_path']}")
        log(f"[2/3] Serving POST {API_PATH} on http://{args.host}:{args.port}")
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

    if args.smoke:
        return run_smoke_mode(args, paths)
    return run_server_mode(args, paths)


if __name__ == "__main__":
    raise SystemExit(main())
