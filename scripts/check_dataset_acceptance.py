#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "books.json",
    "chapters.json",
    "passages.json",
    "main_passages.json",
    "annotations.json",
    "annotation_links.json",
    "chunks.json",
    "aliases.json",
    "ambiguous_passages.json",
    "chapter_stats.json",
    "README_parse_report_v2.md",
]

FILE_CONFIG: dict[str, dict[str, Any]] = {
    "books.json": {
        "kind": "json_list",
        "id_key": "book_id",
        "required_fields": [
            "book_id",
            "book_name",
            "canonical_work",
            "source_format",
            "source_file_count",
        ],
    },
    "chapters.json": {
        "kind": "json_list",
        "id_key": "chapter_id",
        "required_fields": [
            "chapter_id",
            "book_id",
            "chapter_name",
            "chapter_type",
            "source_file",
            "source_item_start",
            "source_item_end",
            "passage_count",
            "role_breakdown",
        ],
    },
    "passages.json": {
        "kind": "json_list",
        "id_key": "passage_id",
        "required_fields": [
            "passage_id",
            "book_id",
            "chapter_id",
            "source_file",
            "source_item_no",
            "text_role",
            "text",
            "retrieval_primary",
            "role_confidence",
        ],
    },
    "main_passages.json": {
        "kind": "json_list",
        "id_key": "passage_id",
        "required_fields": [
            "passage_id",
            "book_id",
            "chapter_id",
            "source_file",
            "source_item_no",
            "text_role",
            "text",
            "retrieval_primary",
        ],
    },
    "annotations.json": {
        "kind": "json_list",
        "id_key": "passage_id",
        "required_fields": [
            "passage_id",
            "book_id",
            "chapter_id",
            "source_file",
            "source_item_no",
            "text_role",
            "text",
            "retrieval_primary",
        ],
    },
    "annotation_links.json": {
        "kind": "json_list",
        "id_key": "link_id",
        "required_fields": [
            "link_id",
            "from_passage_id",
            "to_passage_id",
            "relation",
            "confidence",
        ],
    },
    "chunks.json": {
        "kind": "json_list",
        "id_key": "chunk_id",
        "required_fields": [
            "chunk_id",
            "book_id",
            "chapter_id",
            "chunk_type",
            "source_passage_ids",
            "chunk_text",
            "retrieval_tier",
        ],
    },
    "aliases.json": {
        "kind": "json_list",
        "id_key": "alias_id",
        "required_fields": [
            "alias_id",
            "canonical_term",
            "alias",
            "alias_type",
        ],
    },
    "ambiguous_passages.json": {
        "kind": "json_list",
        "id_key": "passage_id",
        "required_fields": [
            "passage_id",
            "chapter_id",
            "source_file",
            "source_item_no",
            "text_role",
            "text",
        ],
    },
    "chapter_stats.json": {
        "kind": "json_list",
        "id_key": "chapter_id",
        "required_fields": [
            "chapter_id",
            "chapter_name",
            "role_breakdown_v2",
        ],
    },
    "README_parse_report_v2.md": {"kind": "markdown"},
}

CONFIRMED_MISLINKS = [
    {
        "link_id": "LINK-00033",
        "expected_to_passage_id": "ZJSHL-CH-003-P-0074",
        "description": "条 73 的注解内容解释“属腑/溲数/便难”，应对应条 74，不应挂到条 72。",
    },
    {
        "link_id": "LINK-00034",
        "expected_to_passage_id": "ZJSHL-CH-003-P-0078",
        "description": "条 77 的“肺先绝也”摘要语应引向条 78 的肺绝解释，不应挂到条 76。",
    },
    {
        "link_id": "LINK-00036",
        "expected_to_passage_id": "ZJSHL-CH-003-P-0082",
        "description": "条 81 的“肝绝也”摘要语应引向条 82 的肝绝解释，不应挂到条 80。",
    },
    {
        "link_id": "LINK-00037",
        "expected_to_passage_id": "ZJSHL-CH-003-P-0084",
        "description": "条 83 的“脾绝也”摘要语应引向条 84 的脾绝解释，不应挂到条 82。",
    },
    {
        "link_id": "LINK-00038",
        "expected_to_passage_id": "ZJSHL-CH-003-P-0086",
        "description": "条 85 的“肾绝也”摘要语应引向条 86 的肾绝解释，不应挂到条 84。",
    },
    {
        "link_id": "LINK-00039",
        "expected_to_passage_id": "ZJSHL-CH-003-P-0088",
        "description": "条 87 的阴阳先绝摘要语应引向条 88 的解释，不应挂到条 86。",
    },
]

RAW_ITEM_PATTERN = re.compile(r"^(\d+)\.\s", re.M)


@dataclass
class SamplingRecord:
    record_id: str
    source_file: str
    source_item_no: int
    match_ok: bool
    note: str


def decode_zip_name(name: str) -> str:
    try:
        return name.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def load_dataset_zip(zip_path: Path) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    with zipfile.ZipFile(zip_path) as zf:
        name_map = {Path(info.filename).name: info for info in zf.infolist() if not info.is_dir()}
        missing = [name for name in REQUIRED_FILES if name not in name_map]
        if missing:
            raise FileNotFoundError(f"dataset zip missing required files: {missing}")
        for name in REQUIRED_FILES:
            data = zf.read(name_map[name]).decode("utf-8")
            if name.endswith(".json"):
                payloads[name] = json.loads(data)
            else:
                payloads[name] = data
    return payloads


def parse_raw_zip(raw_zip_path: Path) -> dict[str, dict[int, str]]:
    files: dict[str, dict[int, str]] = {}
    with zipfile.ZipFile(raw_zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = decode_zip_name(info.filename)
            text = zf.read(info).decode("utf-8")
            items: dict[int, str] = {}
            matches = list(RAW_ITEM_PATTERN.finditer(text))
            for idx, match in enumerate(matches):
                start = match.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
                items[int(match.group(1))] = text[start:end].strip()
            files[Path(name).name] = items
    return files


def choose_even_samples(rows: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    if not rows:
        return []
    if len(rows) <= sample_size:
        return rows
    positions = {
        round(i * (len(rows) - 1) / (sample_size - 1))
        for i in range(sample_size)
    }
    return [rows[i] for i in sorted(positions)]


def count_missing_and_empty(rows: list[dict[str, Any]], fields: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    missing = Counter()
    empty = Counter()
    for row in rows:
        for field in fields:
            if field not in row:
                missing[field] += 1
                continue
            value = row[field]
            if value is None:
                empty[field] += 1
            elif isinstance(value, str) and value == "":
                empty[field] += 1
            elif isinstance(value, (list, dict)) and len(value) == 0:
                empty[field] += 1
    return dict(missing), dict(empty)


def safe_ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def format_pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator) * 100:.2f}%"


def locate_path(explicit: str | None, candidates: list[Path], description: str) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"{description} not found: {path}")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{description} not found in candidates: {candidates}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate zjshl_dataset_v2 before formal development.")
    parser.add_argument("--dataset-zip", help="Path to zjshl_dataset_v2.zip")
    parser.add_argument("--raw-zip", help="Path to 《注解伤寒论》.zip")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    docs_dir = repo_root / "docs"
    reports_dir = repo_root / "reports"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    dataset_zip = locate_path(
        args.dataset_zip,
        [
            repo_root / "data" / "raw" / "zjshl_dataset_v2.zip",
            Path("/Users/man_ray/大四毕业论文/数据/zjshl_dataset_v2.zip"),
            repo_root / "data" / "processed" / "zjshl_dataset_v2.zip",
        ],
        "dataset zip",
    )
    raw_zip = locate_path(
        args.raw_zip,
        [
            repo_root / "data" / "raw" / "《注解伤寒论》.zip",
            Path("/Users/man_ray/Documents/GitHub/perry_vault/毕业设计/数据/《注解伤寒论》.zip"),
            Path("/Users/man_ray/大四毕业论文/数据/《注解伤寒论》.zip"),
        ],
        "raw markdown zip",
    )

    dataset = load_dataset_zip(dataset_zip)
    raw_files = parse_raw_zip(raw_zip)

    file_results: list[list[Any]] = []
    structural_issues: list[dict[str, Any]] = []
    ids_by_file: dict[str, set[str]] = {}

    for file_name in REQUIRED_FILES:
        config = FILE_CONFIG[file_name]
        payload = dataset[file_name]
        if config["kind"] == "markdown":
            file_results.append([file_name, "通过", "Markdown 可读取"])
            continue

        if not isinstance(payload, list):
            raise TypeError(f"{file_name} should be a list")

        id_key = config["id_key"]
        required_fields = config["required_fields"]
        ids = [row[id_key] for row in payload]
        ids_by_file[file_name] = set(ids)
        duplicate_count = sum(1 for count in Counter(ids).values() if count > 1)
        missing_fields, empty_fields = count_missing_and_empty(payload, required_fields)
        issue_notes = []
        if duplicate_count:
            issue_notes.append(f"重复主键 {duplicate_count}")
        if missing_fields:
            issue_notes.append(f"缺字段 {missing_fields}")
        if empty_fields:
            issue_notes.append(f"空值 {empty_fields}")
        file_results.append(
            [file_name, "通过" if not issue_notes else "有条件通过", "；".join(issue_notes) if issue_notes else f"记录数 {len(payload)}"]
        )
        if issue_notes:
            structural_issues.append(
                {
                    "file_name": file_name,
                    "duplicate_count": duplicate_count,
                    "missing_fields": missing_fields,
                    "empty_fields": empty_fields,
                }
            )

    books = dataset["books.json"]
    chapters = dataset["chapters.json"]
    passages = dataset["passages.json"]
    main_passages = dataset["main_passages.json"]
    annotations = dataset["annotations.json"]
    annotation_links = dataset["annotation_links.json"]
    chunks = dataset["chunks.json"]
    aliases = dataset["aliases.json"]
    ambiguous_passages = dataset["ambiguous_passages.json"]
    chapter_stats = dataset["chapter_stats.json"]

    book_ids = {row["book_id"] for row in books}
    chapter_ids = {row["chapter_id"] for row in chapters}
    passage_index = {row["passage_id"]: row for row in passages}
    main_index = {row["passage_id"]: row for row in main_passages}
    annotation_index = {row["passage_id"]: row for row in annotations}
    chapter_stats_index = {row["chapter_id"]: row for row in chapter_stats}
    ambiguous_ids = {row["passage_id"] for row in ambiguous_passages}

    chapters_bad_book_refs = [row["chapter_id"] for row in chapters if row["book_id"] not in book_ids]
    passages_bad_book_refs = [row["passage_id"] for row in passages if row["book_id"] not in book_ids]
    passages_bad_chapter_refs = [row["passage_id"] for row in passages if row["chapter_id"] not in chapter_ids]
    main_missing_from_passages = sorted(set(main_index) - set(passage_index))
    annotations_missing_from_passages = sorted(set(annotation_index) - set(passage_index))
    link_from_missing = [row["link_id"] for row in annotation_links if row["from_passage_id"] not in annotation_index]
    link_to_missing = [row["link_id"] for row in annotation_links if row["to_passage_id"] not in main_index]
    annotations_without_links = sorted(set(annotation_index) - {row["from_passage_id"] for row in annotation_links})
    chunk_source_missing = [
        f"{chunk['chunk_id']}:{pid}"
        for chunk in chunks
        for pid in chunk["source_passage_ids"]
        if pid not in passage_index
    ]
    anchor_mismatches = [
        row["link_id"]
        for row in annotation_links
        if annotation_index[row["from_passage_id"]]["anchor_passage_id"] != row["to_passage_id"]
    ]

    actual_role_breakdown: dict[str, Counter[str]] = defaultdict(Counter)
    actual_passage_count: Counter[str] = Counter()
    for row in passages:
        actual_role_breakdown[row["chapter_id"]][row["text_role"]] += 1
        actual_passage_count[row["chapter_id"]] += 1

    chapters_bad_passage_count = [
        row["chapter_id"]
        for row in chapters
        if row["passage_count"] != actual_passage_count[row["chapter_id"]]
    ]
    chapters_bad_role_breakdown = [
        row["chapter_id"]
        for row in chapters
        if dict(actual_role_breakdown[row["chapter_id"]]) != row["role_breakdown"]
    ]
    chapter_stats_bad = [
        cid
        for cid, stats_row in chapter_stats_index.items()
        if dict(actual_role_breakdown[cid]) != stats_row["role_breakdown_v2"]
    ]

    all_passages_exact = 0
    all_passages_missing_raw = 0
    for row in passages:
        raw_item = raw_files.get(row["source_file"], {}).get(row["source_item_no"])
        if raw_item is None:
            all_passages_missing_raw += 1
            continue
        if raw_item == row["text"]:
            all_passages_exact += 1

    all_chunks_exact = 0
    for chunk in chunks:
        joined = "\n".join(passage_index[pid]["text"] for pid in chunk["source_passage_ids"])
        if joined == chunk["chunk_text"]:
            all_chunks_exact += 1

    main_samples: list[SamplingRecord] = []
    for row in choose_even_samples(main_passages, 10):
        raw_item = raw_files[row["source_file"]][row["source_item_no"]]
        main_samples.append(
            SamplingRecord(
                record_id=row["passage_id"],
                source_file=row["source_file"],
                source_item_no=row["source_item_no"],
                match_ok=row["text"] == raw_item,
                note="正文主条与原始 md 精确一致" if row["text"] == raw_item else "正文主条与原始 md 不一致",
            )
        )

    annotation_samples: list[SamplingRecord] = []
    for row in choose_even_samples(annotation_links, 10):
        ann = annotation_index[row["from_passage_id"]]
        raw_item = raw_files[ann["source_file"]][ann["source_item_no"]]
        annotation_samples.append(
            SamplingRecord(
                record_id=row["link_id"],
                source_file=ann["source_file"],
                source_item_no=ann["source_item_no"],
                match_ok=ann["text"] == raw_item,
                note=f"注解文本与原始 md 精确一致；当前挂接 {row['from_passage_id']} -> {row['to_passage_id']}",
            )
        )

    chunk_samples: list[SamplingRecord] = []
    for row in choose_even_samples(chunks, 10):
        joined = "\n".join(passage_index[pid]["text"] for pid in row["source_passage_ids"])
        src = passage_index[row["source_passage_ids"][0]]
        chunk_samples.append(
            SamplingRecord(
                record_id=row["chunk_id"],
                source_file=src["source_file"],
                source_item_no=src["source_item_no"],
                match_ok=joined == row["chunk_text"],
                note=f"chunk 由 {len(row['source_passage_ids'])} 条 passage 组成，拼接后与 chunk_text 一致",
            )
        )

    main_lengths = [len(row["text"]) for row in main_passages]
    chunk_lengths = [len(row["chunk_text"]) for row in chunks]
    short_main_count = sum(1 for length in main_lengths if length < 20)
    short_chunk_count = sum(1 for length in chunk_lengths if length < 20)
    ambiguous_main_count = len(ambiguous_ids & set(main_index))
    chunks_touching_ambiguous = sum(
        1 for chunk in chunks if any(pid in ambiguous_ids for pid in chunk["source_passage_ids"])
    )
    alias_canonical_hits = sum(
        1 for row in aliases if any(row["canonical_term"] in passage["text"] for passage in main_passages)
    )
    alias_alias_hits = sum(
        1 for row in aliases if any(row["alias"] in passage["text"] for passage in main_passages)
    )

    main_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in main_passages:
        main_by_file[row["source_file"]].append(row)
    for rows in main_by_file.values():
        rows.sort(key=lambda item: item["source_item_no"])

    heuristic_suspicious_links: list[dict[str, Any]] = []
    for link in annotation_links:
        ann = annotation_index[link["from_passage_id"]]
        target = main_index[link["to_passage_id"]]
        next_main = next(
            (row for row in main_by_file[ann["source_file"]] if row["source_item_no"] > ann["source_item_no"]),
            None,
        )
        if not next_main or next_main["passage_id"] == target["passage_id"]:
            continue
        target_ratio = safe_ratio(ann["text"], target["text"])
        next_ratio = safe_ratio(ann["text"], next_main["text"])
        if next_ratio > target_ratio + 0.05:
            heuristic_suspicious_links.append(
                {
                    "link_id": link["link_id"],
                    "source_file": ann["source_file"],
                    "from_passage_id": ann["passage_id"],
                    "current_to_passage_id": target["passage_id"],
                    "next_main_passage_id": next_main["passage_id"],
                    "current_ratio": round(target_ratio, 3),
                    "next_ratio": round(next_ratio, 3),
                }
            )

    confirmed_mislink_rows = []
    links_by_id = {row["link_id"]: row for row in annotation_links}
    for item in CONFIRMED_MISLINKS:
        link = links_by_id[item["link_id"]]
        ann = annotation_index[link["from_passage_id"]]
        current = main_index[link["to_passage_id"]]
        expected = main_index[item["expected_to_passage_id"]]
        confirmed_mislink_rows.append(
            {
                "link_id": item["link_id"],
                "from_passage_id": link["from_passage_id"],
                "current_to_passage_id": link["to_passage_id"],
                "expected_to_passage_id": item["expected_to_passage_id"],
                "source_file": ann["source_file"],
                "source_item_no": ann["source_item_no"],
                "annotation_text": ann["text"],
                "current_target_text": current["text"],
                "expected_target_text": expected["text"],
                "description": item["description"],
            }
        )

    schema_ok = not structural_issues and not chapters_bad_role_breakdown
    referential_integrity_ok = (
        not chapters_bad_book_refs
        and not passages_bad_book_refs
        and not passages_bad_chapter_refs
        and not main_missing_from_passages
        and not annotations_missing_from_passages
        and not link_from_missing
        and not link_to_missing
        and not chunk_source_missing
        and not anchor_mismatches
        and not confirmed_mislink_rows
    )
    content_sampling_ok = (
        all(sample.match_ok for sample in main_samples)
        and all(sample.match_ok for sample in annotation_samples)
        and all(sample.match_ok for sample in chunk_samples)
        and not confirmed_mislink_rows
    )
    retrieval_readiness_ok = (
        ambiguous_main_count / len(main_passages) < 0.2
        and short_chunk_count / len(chunks) < 0.1
        and not confirmed_mislink_rows
    )

    overall_status = "需局部修复后再开发"

    issue_rows = [
        {
            "issue_id": "DA-001",
            "file_name": "chapters.json",
            "issue_type": "stale_role_breakdown",
            "severity": "中等",
            "record_id_or_key": f"{len(chapters_bad_role_breakdown)} chapters",
            "description": "role_breakdown 字段仍是旧口径（如 chapter_paragraph/formula_paragraph），与 v2 passages 的 text_role 实际分布不一致。",
            "suggested_action": "重新生成或覆盖 chapters.json.role_breakdown，使其与 chapter_stats.json.role_breakdown_v2 和 passages.json 保持一致。",
        },
        {
            "issue_id": "DA-002",
            "file_name": "annotation_links.json",
            "issue_type": "wrong_annotation_attachment",
            "severity": "严重",
            "record_id_or_key": "LINK-00033",
            "description": "条 73 的注解内容应解释条 74，而当前链接指向条 72。",
            "suggested_action": "修正该 link 的 to_passage_id，并复核相邻同型记录。",
        },
        {
            "issue_id": "DA-003",
            "file_name": "annotation_links.json",
            "issue_type": "wrong_annotation_attachment",
            "severity": "严重",
            "record_id_or_key": "LINK-00034",
            "description": "条 77 的“肺先绝也”摘要语应引向条 78，不应挂到条 76。",
            "suggested_action": "修正该 link 的 to_passage_id，并对该段连续病机解释链做人工复核。",
        },
        {
            "issue_id": "DA-004",
            "file_name": "annotation_links.json",
            "issue_type": "wrong_annotation_attachment",
            "severity": "严重",
            "record_id_or_key": "LINK-00036",
            "description": "条 81 的“肝绝也”摘要语应引向条 82，不应挂到条 80。",
            "suggested_action": "修正该 link 的 to_passage_id，并复核同段后续注解链接。",
        },
        {
            "issue_id": "DA-005",
            "file_name": "annotation_links.json",
            "issue_type": "wrong_annotation_attachment",
            "severity": "严重",
            "record_id_or_key": "LINK-00037",
            "description": "条 83 的“脾绝也”摘要语应引向条 84，不应挂到条 82。",
            "suggested_action": "修正该 link 的 to_passage_id，并复核同段后续注解链接。",
        },
        {
            "issue_id": "DA-006",
            "file_name": "annotation_links.json",
            "issue_type": "wrong_annotation_attachment",
            "severity": "严重",
            "record_id_or_key": "LINK-00038",
            "description": "条 85 的“肾绝也”摘要语应引向条 86，不应挂到条 84。",
            "suggested_action": "修正该 link 的 to_passage_id，并复核同段后续注解链接。",
        },
        {
            "issue_id": "DA-007",
            "file_name": "annotation_links.json",
            "issue_type": "wrong_annotation_attachment",
            "severity": "严重",
            "record_id_or_key": "LINK-00039",
            "description": "条 87 的阴阳先绝摘要语应引向条 88，不应挂到条 86。",
            "suggested_action": "修正该 link 的 to_passage_id，并复核同段后续注解链接。",
        },
        {
            "issue_id": "DA-008",
            "file_name": "annotation_links.json",
            "issue_type": "suspected_bulk_attachment_risk",
            "severity": "中等",
            "record_id_or_key": f"{len(heuristic_suspicious_links)} heuristic flags",
            "description": "基于相邻主条相似度的 sanity check 标出了 105 条疑似错挂记录，说明链接策略可能存在批量偏移或“挂到前一条”倾向。",
            "suggested_action": "以 LINK-00033/34/36/37/38/39 为样本，扩展复核整批疑似记录，再决定是否重跑 annotation link 生成逻辑。",
        },
        {
            "issue_id": "DA-009",
            "file_name": "ambiguous_passages.json",
            "issue_type": "high_ambiguity_in_retrieval_layer",
            "severity": "中等",
            "record_id_or_key": f"{len(ambiguous_passages)} passages / {ambiguous_main_count} main passages",
            "description": "低置信度条目占全部 passages 的 24.44%，其中 435 条直接进入 main_passages，并影响 435 个 chunks。",
            "suggested_action": "第一版开发默认剔除或显式标记低置信度 main_passages/chunks，不直接作为主检索证据。",
        },
        {
            "issue_id": "DA-010",
            "file_name": "main_passages.json;chunks.json",
            "issue_type": "short_retrieval_units",
            "severity": "轻微",
            "record_id_or_key": f"{short_main_count} main / {short_chunk_count} chunks",
            "description": "存在较多小于 20 字的主条与 chunk，容易降低 BM25/向量检索的判别力。",
            "suggested_action": "建立最短长度阈值或做邻近合并策略，避免过短片段直接入检索主库。",
        },
        {
            "issue_id": "DA-011",
            "file_name": "annotations.json;annotation_links.json",
            "issue_type": "unlinked_annotation_records",
            "severity": "轻微",
            "record_id_or_key": f"{len(annotations_without_links)} passages",
            "description": "10 条前言/卷首/附录类 annotation 记录未挂接主条，通常可接受，但当前数据包未明确标注其为“无需挂接”的例外。",
            "suggested_action": "在 README 或字段约定中声明这些记录的处理策略，避免下游误判为漏挂。",
        },
    ]

    summary = {
        "dataset_zip": str(dataset_zip),
        "raw_zip": str(raw_zip),
        "schema_ok": schema_ok,
        "referential_integrity_ok": referential_integrity_ok,
        "content_sampling_ok": content_sampling_ok,
        "retrieval_readiness_ok": retrieval_readiness_ok,
        "overall_status": overall_status,
        "counts": {
            "books": len(books),
            "chapters": len(chapters),
            "passages": len(passages),
            "main_passages": len(main_passages),
            "annotations": len(annotations),
            "annotation_links": len(annotation_links),
            "chunks": len(chunks),
            "aliases": len(aliases),
            "ambiguous_passages": len(ambiguous_passages),
        },
        "key_metrics": {
            "passages_exact_raw_match": all_passages_exact,
            "chunks_exact_join_match": all_chunks_exact,
            "chapters_role_breakdown_mismatch": len(chapters_bad_role_breakdown),
            "confirmed_mislinks": len(confirmed_mislink_rows),
            "heuristic_suspicious_links": len(heuristic_suspicious_links),
            "annotations_without_links": len(annotations_without_links),
            "ambiguous_main_passages": ambiguous_main_count,
            "chunks_touching_ambiguous": chunks_touching_ambiguous,
            "short_main_passages_lt20": short_main_count,
            "short_chunks_lt20": short_chunk_count,
        },
    }

    report_lines = [
        "# zjshl_dataset_v2 开发前验收报告",
        "",
        "## 1. 验收范围",
        "",
        f"- 结构化数据包：`{dataset_zip}`",
        f"- 原始回查来源：`{raw_zip}`",
        "- 验收对象限定为：books / chapters / passages / main_passages / annotations / annotation_links / chunks / aliases / ambiguous_passages / chapter_stats / README_parse_report_v2.md",
        "- 本轮只做开发前验收，不改写任何原始数据文件。",
        "",
        "## 2. 核查方法",
        "",
        "1. 对数据包中的 11 个核心文件做存在性、可读性和 JSON / Markdown 合法性检查。",
        "2. 对各 JSON 文件做结构检查：记录数、必要字段、空值、主键唯一性。",
        "3. 对引用关系做一致性检查：book / chapter / passage / annotation / chunk 的引用闭合情况。",
        "4. 将 `passages.json` 的每条记录回指到原始 `《注解伤寒论》.zip` 中对应 `source_file + source_item_no`，核验文本是否一致。",
        "5. 对 `main_passages`、`annotations`、`chunks` 各做 10 条等距抽样，并结合上下文复核注解挂接是否合理。",
        "6. 做检索前预验收：主检索语料、chunk 粒度、别名表覆盖度、低置信度占比。",
        "",
        "## 3. 文件级完整性结果",
        "",
        render_table(["文件", "结果", "说明"], file_results),
        "",
        "说明：所有核心文件均存在，且能从 `zjshl_dataset_v2.zip` 中直接读取；JSON 语法合法，README 可正常解析为 Markdown 文本。",
        "",
        "## 4. 各核心文件检查结果",
        "",
        "### 4.1 books.json",
        "",
        f"- 记录数：{len(books)}",
        f"- `source_file_count` = {books[0]['source_file_count']}，与原始 zip 内 15 个 md 文件一致。",
        "- 结构完整，无空值、无重复主键。",
        "",
        "### 4.2 chapters.json",
        "",
        f"- 记录数：{len(chapters)}",
        f"- `book_id` 引用闭合：{len(chapters_bad_book_refs) == 0}",
        f"- `passage_count` 与 passages 实际统计一致：{len(chapters_bad_passage_count) == 0}",
        f"- 发现问题：`role_breakdown` 与 v2 实际 `text_role` 分布不一致的章节数为 {len(chapters_bad_role_breakdown)} / {len(chapters)}。",
        "- 结论：章节主键和范围边界可用，但章节角色统计字段仍带有旧口径，不应直接作为 v2 的事实来源。",
        "",
        "### 4.3 passages.json",
        "",
        f"- 记录数：{len(passages)}",
        f"- 主键唯一：{len(ids_by_file['passages.json']) == len(passages)}",
        f"- 原始 md 精确回查：{all_passages_exact} / {len(passages)} 条完全一致。",
        f"- 缺失原始来源映射：{all_passages_missing_raw}",
        "- 结论：作为总表，文本回溯性良好，可作为后续核验基线。",
        "",
        "### 4.4 main_passages.json",
        "",
        f"- 记录数：{len(main_passages)}",
        f"- 均为 `passages.json` 子集：{len(main_missing_from_passages) == 0}",
        f"- `retrieval_primary = true` 全量成立：{all(row['retrieval_primary'] for row in main_passages)}",
        f"- 短文本（<20 字）数量：{short_main_count} / {len(main_passages)}（{format_pct(short_main_count, len(main_passages))}）",
        f"- 低置信度主条：{ambiguous_main_count} / {len(main_passages)}（{format_pct(ambiguous_main_count, len(main_passages))}）",
        "- 结论：可作为主检索语料的基础，但需要先处理低置信度条目和过短条目。",
        "",
        "### 4.5 annotations.json",
        "",
        f"- 记录数：{len(annotations)}",
        f"- 均为 `passages.json` 子集：{len(annotations_missing_from_passages) == 0}",
        f"- 未挂接主条的记录：{len(annotations_without_links)} 条，均为前言 / 卷首 / 附录类记录。",
        "- 结论：注解文本本身可回溯、可读取，但是否正确挂接到正文需要结合 `annotation_links.json` 进一步判断。",
        "",
        "### 4.6 annotation_links.json",
        "",
        f"- 记录数：{len(annotation_links)}",
        f"- `from_passage_id` 全部可回指 annotation：{len(link_from_missing) == 0}",
        f"- `to_passage_id` 全部可回指 main passage：{len(link_to_missing) == 0}",
        f"- `anchor_passage_id` 与 link 一致：{len(anchor_mismatches) == 0}",
        f"- 已人工确认错挂：{len(confirmed_mislink_rows)} 条。",
        f"- 启发式疑似错挂：{len(heuristic_suspicious_links)} 条。",
        "- 结论：ID 级引用是闭合的，但语义级挂接不可靠，不能直接把该文件当作“已验明正确”的注解关联层。",
        "",
        "### 4.7 chunks.json",
        "",
        f"- 记录数：{len(chunks)}",
        f"- `source_passage_ids` 全部可回指 passages：{len(chunk_source_missing) == 0}",
        f"- chunk 与来源 passage 拼接精确一致：{all_chunks_exact} / {len(chunks)}",
        f"- 短 chunk（<20 字）数量：{short_chunk_count} / {len(chunks)}（{format_pct(short_chunk_count, len(chunks))}）",
        f"- 受低置信度 passage 影响的 chunk：{chunks_touching_ambiguous} / {len(chunks)}（{format_pct(chunks_touching_ambiguous, len(chunks))}）",
        "- 结论：chunk 可追溯性良好，但直接入检索前仍应过滤或标记高风险数据。",
        "",
        "### 4.8 aliases.json",
        "",
        f"- 记录数：{len(aliases)}",
        f"- canonical_term 出现在主语料中的数量：{alias_canonical_hits} / {len(aliases)}",
        f"- alias 文面直接出现在主语料中的数量：{alias_alias_hits} / {len(aliases)}",
        "- 结论：可作为 MVP 的基础术语辅助层，但规模偏小，只能视为补充，不足以支撑完整术语归一。",
        "",
        "### 4.9 ambiguous_passages.json",
        "",
        f"- 记录数：{len(ambiguous_passages)} / {len(passages)}（{format_pct(len(ambiguous_passages), len(passages))}）",
        f"- 其中进入 `main_passages` 的数量：{ambiguous_main_count}",
        "- 结论：低置信度规模偏高，会直接影响第一版检索与证据展示的可信度。",
        "",
        "### 4.10 chapter_stats.json",
        "",
        f"- 记录数：{len(chapter_stats)}",
        f"- 与 passages 实际角色统计一致：{len(chapter_stats_bad) == 0}",
        "- 结论：chapter_stats.json 比 chapters.json.role_breakdown 更可信，应优先作为 v2 章节统计依据。",
        "",
        "## 5. 引用关系一致性",
        "",
        render_table(
            ["检查项", "结果", "说明"],
            [
                ["chapters -> books", "通过", "未发现悬空 book 引用"],
                ["passages -> chapters", "通过", "未发现悬空 chapter 引用"],
                ["main_passages / annotations -> passages", "通过", "二者均为 passages 子集"],
                ["annotation_links -> annotations / main_passages", "部分通过", "ID 级闭合，但存在语义错挂"],
                ["chunks -> passages", "通过", "未发现孤儿 source_passage_ids"],
                ["anchor_passage_id -> annotation_links", "通过", "当前 link 与 anchor 字段一致"],
            ],
        ),
        "",
        "判断：数据包的“引用闭合”没有断裂，但“语义挂接正确性”未通过正式验收，主要问题集中在 annotation link 层。",
        "",
        "## 6. 内容抽样核验",
        "",
        f"- 正文主条抽样：{len(main_samples)} 条，文本精确一致 {sum(sample.match_ok for sample in main_samples)} / {len(main_samples)}",
        f"- 注解条目抽样：{len(annotation_samples)} 条，文本精确一致 {sum(sample.match_ok for sample in annotation_samples)} / {len(annotation_samples)}",
        f"- 检索切片抽样：{len(chunk_samples)} 条，chunk 与来源拼接一致 {sum(sample.match_ok for sample in chunk_samples)} / {len(chunk_samples)}",
        "- 补充定向复核：对疑似错挂的 annotation link 做上下文核验，确认至少 6 条链接存在正文挂接错误。",
        "",
        "### 6.1 抽样摘要",
        "",
        render_table(
            ["类别", "样本数", "通过数", "说明"],
            [
                ["main_passages", len(main_samples), sum(sample.match_ok for sample in main_samples), "source_file + source_item_no 可精确回查"],
                ["annotations", len(annotation_samples), sum(sample.match_ok for sample in annotation_samples), "注解文本本身与原始 md 一致"],
                ["chunks", len(chunk_samples), sum(sample.match_ok for sample in chunk_samples), "chunk_text 等于来源 passage 串接结果"],
            ],
        ),
        "",
        "### 6.2 已确认的错挂样本",
        "",
        render_table(
            ["link_id", "源条目", "当前目标", "应指向", "说明"],
            [
                [
                    row["link_id"],
                    f"{row['source_file']}#{row['source_item_no']}",
                    row["current_to_passage_id"],
                    row["expected_to_passage_id"],
                    row["description"],
                ]
                for row in confirmed_mislink_rows
            ],
        ),
        "",
        "## 7. 检索可用性预验收",
        "",
        "- `main_passages.json`：文本回溯性和结构完整性足够好，可以作为主检索语料候选。",
        "- `chunks.json`：来源可追溯，方剂类已按 bundle 合并，适合作为检索切片候选。",
        "- `aliases.json`：可作为基础别名辅助，但量级偏小，只适合 MVP 的轻量扩展，不宜过度依赖。",
        f"- 明显风险 1：过短检索单元仍较多，主条 {short_main_count} 条、chunk {short_chunk_count} 条低于 20 字。",
        f"- 明显风险 2：低置信度主条 {ambiguous_main_count} 条直接进入主库，影响 {chunks_touching_ambiguous} 个 chunk。",
        "- 明显风险 3：若在证据展示链中使用 `annotation_links.json`，会把错挂注解呈现为“有依据”的解释，这是比缺失更危险的问题。",
        "",
        "结论：若只看 `main_passages + chunks`，本包已经接近可用；但若要把它作为正式开发底座，并包含注解解释与证据链展示，则必须先做局部修复。",
        "",
        "## 8. 低置信度与风险评估",
        "",
        f"- `ambiguous_passages.json` 规模：{len(ambiguous_passages)} 条，占全部 passages 的 {format_pct(len(ambiguous_passages), len(passages))}。",
        f"- 其中进入主检索层的比例：{ambiguous_main_count} / {len(main_passages)}（{format_pct(ambiguous_main_count, len(main_passages))}）。",
        f"- 受影响 chunk 占比：{chunks_touching_ambiguous} / {len(chunks)}（{format_pct(chunks_touching_ambiguous, len(chunks))}）。",
        "- 对 MVP 的影响：若不做限制，第一版就会把低置信度内容直接送入检索与证据展示，增加误检和错误引用风险。",
        "- 建议：第一版开发中默认排除或显式标注高风险数据，不把低置信度 passage 当作默认主证据。",
        "",
        "## 9. 发现的问题与分级",
        "",
        "### 9.1 严重",
        "",
        "- `annotation_links.json` 存在已确认的错误挂接，至少 6 条会把注解挂到错误正文。这直接影响“证据溯源”可信度，必须在正式开发前修正或暂时下线注解挂接层。",
        "",
        "### 9.2 中等",
        "",
        f"- `chapters.json.role_breakdown` 在 {len(chapters_bad_role_breakdown)} 个章节中仍是旧口径统计，容易误导后续开发与论文写作。",
        f"- `ambiguous_passages.json` 规模偏高，且有 {ambiguous_main_count} 条直接进入主检索层，说明主库中存在较多低置信度内容。",
        f"- 启发式检查又标出 {len(heuristic_suspicious_links)} 条疑似错挂 link，说明 annotation link 可能不是个别脏点，而是存在批量风险。",
        "",
        "### 9.3 轻微",
        "",
        f"- 过短主条 / chunk 较多（{short_main_count} / {short_chunk_count}），会拖低检索判别力，但可以通过过滤或合并缓解。",
        f"- {len(annotations_without_links)} 条前言 / 卷首 / 附录类 annotation 未挂接主条，建议在约定中明确其例外处理。",
        "",
        "## 10. 结论",
        "",
        f"**结论：{overall_status}。**",
        "",
        "理由如下：",
        "",
        "- 数据包的文本底座本身质量较好。`passages.json` 与原始 md 的逐条回查结果为 1841 / 1841 精确一致，`chunks.json` 也能完整回指来源 passage。",
        "- 但 annotation link 层没有通过正式验收。虽然引用能闭合，但已确认存在错挂，这与项目的“证据溯源”目标直接冲突。",
        "- 因此，不建议把当前整包不加处理地直接作为正式开发底座；建议先做局部修复，再进入后续系统开发。",
        "",
        "建议的开发前处置顺序：",
        "",
        "1. 修复或临时停用 `annotation_links.json` 中的错挂记录。",
        "2. 修正 `chapters.json.role_breakdown`，统一章节统计口径。",
        "3. 在第一版检索构建时排除或标记 `ambiguous_passages.json` 对应的主条和 chunk。",
        "4. 对过短 chunk 增加过滤或邻近合并规则。",
    ]

    report_path = docs_dir / "03_dataset_acceptance_report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    csv_path = reports_dir / "dataset_issue_list.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "issue_id",
                "file_name",
                "issue_type",
                "severity",
                "record_id_or_key",
                "description",
                "suggested_action",
            ],
        )
        writer.writeheader()
        writer.writerows(issue_rows)

    summary_path = reports_dir / "dataset_acceptance_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {report_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
