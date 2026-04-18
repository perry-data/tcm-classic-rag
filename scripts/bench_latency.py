#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_ENDPOINT_PATH = "/api/v1/answers"
DEFAULT_OUTPUT_PATH = "artifacts/perf/latency_baseline.json"
DEFAULT_TIMEOUT_SECONDS = 90.0
DEFAULT_ROUNDS = 5
DEFAULT_QUERY_SET = [
    {
        "query_id": "strong_formula_lookup",
        "category": "strong",
        "expected_mode": "strong",
        "query": "黄连汤方的条文是什么？",
    },
    {
        "query_id": "strong_general_management",
        "category": "strong",
        "expected_mode": "strong",
        "query": "太阳病应该怎么办？",
    },
    {
        "query_id": "weak_meaning_explanation",
        "category": "weak",
        "expected_mode": "weak_with_review_notice",
        "query": "烧针益阳而损阴是什么意思？",
    },
    {
        "query_id": "weak_fragment_guidance",
        "category": "weak",
        "expected_mode": "weak_with_review_notice",
        "query": "若噎者怎么办？",
    },
    {
        "query_id": "refuse_out_of_book",
        "category": "refuse",
        "expected_mode": "refuse",
        "query": "书中有没有提到量子纠缠？",
    },
    {
        "query_id": "refuse_personalized_treatment",
        "category": "refuse",
        "expected_mode": "refuse",
        "query": "我发烧了能不能用麻黄汤？",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark end-to-end latency for POST /api/v1/answers.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of the running API server.")
    parser.add_argument("--endpoint-path", default=DEFAULT_ENDPOINT_PATH, help="Relative endpoint path.")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help="How many times to replay the full query set.")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Per-request timeout.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH, help="Where to write the benchmark JSON.")
    parser.add_argument("--label", default="baseline", help="Scenario label stored in the report.")
    return parser.parse_args()


def percentile(values: list[float], ratio: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 3)
    ordered = sorted(values)
    index = (len(ordered) - 1) * ratio
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(ordered[lower], 3)
    fraction = index - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 3)


def stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "p50": None, "p90": None, "p95": None, "max": None, "avg": None}
    return {
        "count": len(values),
        "p50": percentile(values, 0.50),
        "p90": percentile(values, 0.90),
        "p95": percentile(values, 0.95),
        "max": round(max(values), 3),
        "avg": round(sum(values) / len(values), 3),
    }


def parse_server_timing(raw_header: str | None) -> dict[str, float]:
    if not raw_header:
        return {}
    parsed: dict[str, float] = {}
    for part in raw_header.split(","):
        item = part.strip()
        if not item:
            continue
        metric, *attrs = item.split(";")
        for attr in attrs:
            attr = attr.strip()
            if not attr.startswith("dur="):
                continue
            try:
                parsed[metric] = round(float(attr.split("=", 1)[1]), 3)
            except ValueError:
                continue
    return parsed


def post_json(url: str, payload: dict[str, Any], timeout_seconds: float) -> tuple[int, dict[str, str], dict[str, Any], float]:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib_request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started_at = time.perf_counter()
    with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))
        elapsed_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        return response.status, dict(response.headers.items()), body, elapsed_ms


def summarize_stage_timings(results: list[dict[str, Any]]) -> dict[str, Any]:
    values_by_stage: dict[str, list[float]] = {}
    for row in results:
        for stage_name, duration_ms in row.get("server_timing", {}).items():
            values_by_stage.setdefault(stage_name, []).append(duration_ms)
    return {
        stage_name: {
            "avg_ms": round(sum(stage_values) / len(stage_values), 3),
            "p95_ms": percentile(stage_values, 0.95),
        }
        for stage_name, stage_values in sorted(values_by_stage.items())
    }


def main() -> int:
    args = parse_args()
    url = f"{args.base_url.rstrip('/')}{args.endpoint_path}"
    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = (PROJECT_ROOT / output_path).resolve()

    results: list[dict[str, Any]] = []
    print(
        f"[bench] target={url} rounds={args.rounds} query_count={len(DEFAULT_QUERY_SET)} total_requests={args.rounds * len(DEFAULT_QUERY_SET)}",
        flush=True,
    )

    for round_index in range(1, args.rounds + 1):
        for query_spec in DEFAULT_QUERY_SET:
            try:
                status_code, headers, body, elapsed_ms = post_json(
                    url,
                    {"query": query_spec["query"]},
                    timeout_seconds=args.timeout_seconds,
                )
                record = {
                    "round": round_index,
                    "query_id": query_spec["query_id"],
                    "category": query_spec["category"],
                    "query": query_spec["query"],
                    "expected_mode": query_spec["expected_mode"],
                    "status_code": status_code,
                    "actual_mode": body.get("answer_mode"),
                    "mode_match": body.get("answer_mode") == query_spec["expected_mode"],
                    "elapsed_ms": elapsed_ms,
                    "request_id": headers.get("X-Request-Id"),
                    "server_timing": parse_server_timing(headers.get("Server-Timing")),
                }
                results.append(record)
                print(
                    f"[bench] round={round_index}/{args.rounds} query_id={record['query_id']} mode={record['actual_mode']} elapsed_ms={elapsed_ms:.3f} request_id={record['request_id']}",
                    flush=True,
                )
            except urllib_error.HTTPError as exc:
                response_text = exc.read().decode("utf-8", errors="replace")
                print(
                    f"[bench:error] round={round_index} query_id={query_spec['query_id']} http={exc.code} body={response_text}",
                    file=sys.stderr,
                    flush=True,
                )
                return 1
            except Exception as exc:  # pragma: no cover - operational guard
                print(
                    f"[bench:error] round={round_index} query_id={query_spec['query_id']} error={exc}",
                    file=sys.stderr,
                    flush=True,
                )
                return 1

    overall_values = [row["elapsed_ms"] for row in results]
    by_category = {
        category: stats([row["elapsed_ms"] for row in results if row["category"] == category])
        for category in ("strong", "weak", "refuse")
    }
    by_query = {
        query_spec["query_id"]: stats([row["elapsed_ms"] for row in results if row["query_id"] == query_spec["query_id"]])
        for query_spec in DEFAULT_QUERY_SET
    }
    mode_mismatches = [row for row in results if not row["mode_match"]]

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "base_url": args.base_url,
        "endpoint_path": args.endpoint_path,
        "rounds": args.rounds,
        "query_count": len(DEFAULT_QUERY_SET),
        "total_requests": len(results),
        "overall_latency_ms": stats(overall_values),
        "by_category_latency_ms": by_category,
        "by_query_latency_ms": by_query,
        "server_timing_summary": summarize_stage_timings(results),
        "mode_mismatch_count": len(mode_mismatches),
        "mode_mismatches": mode_mismatches,
        "queries": DEFAULT_QUERY_SET,
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overall = report["overall_latency_ms"]
    print(
        f"[bench:summary] label={args.label} p50={overall['p50']}ms p90={overall['p90']}ms p95={overall['p95']}ms max={overall['max']}ms mode_mismatch_count={report['mode_mismatch_count']}",
        flush=True,
    )
    print(f"[bench:output] {output_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
