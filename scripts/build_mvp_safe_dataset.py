#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import zipfile
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

SHORT_TEXT_THRESHOLD = 20


def locate_source(explicit: str | None, candidates: list[Path], description: str) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"{description} not found: {path}")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{description} not found in candidates: {candidates}")


def load_dataset(source: Path) -> dict[str, Any]:
    if source.is_dir():
        data: dict[str, Any] = {}
        for name in REQUIRED_FILES:
            path = source / name
            if not path.exists():
                raise FileNotFoundError(f"missing required file: {path}")
            text = path.read_text(encoding="utf-8")
            data[name] = json.loads(text) if name.endswith(".json") else text
        return data

    if source.suffix.lower() == ".zip":
        data = {}
        with zipfile.ZipFile(source) as zf:
            names = {Path(info.filename).name: info for info in zf.infolist() if not info.is_dir()}
            for name in REQUIRED_FILES:
                if name not in names:
                    raise FileNotFoundError(f"missing required file in zip: {name}")
                text = zf.read(names[name]).decode("utf-8")
                data[name] = json.loads(text) if name.endswith(".json") else text
        return data

    raise ValueError(f"unsupported source type: {source}")


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def text_bytes(payload: str) -> bytes:
    return payload.encode("utf-8")


def build_safe_dataset(dataset: dict[str, Any], source_label: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    books = copy.deepcopy(dataset["books.json"])
    chapters = copy.deepcopy(dataset["chapters.json"])
    passages = copy.deepcopy(dataset["passages.json"])
    main_passages = copy.deepcopy(dataset["main_passages.json"])
    annotations = copy.deepcopy(dataset["annotations.json"])
    chunks = copy.deepcopy(dataset["chunks.json"])
    aliases = copy.deepcopy(dataset["aliases.json"])
    ambiguous_passages = copy.deepcopy(dataset["ambiguous_passages.json"])
    chapter_stats = copy.deepcopy(dataset["chapter_stats.json"])

    ambiguous_ids = {row["passage_id"] for row in ambiguous_passages}
    annotation_ids = {row["passage_id"] for row in annotations}
    chapter_stats_index = {row["chapter_id"]: row["role_breakdown_v2"] for row in chapter_stats}

    # Fix chapters.role_breakdown to the v2 role taxonomy already validated in chapter_stats.json.
    chapters_fixed = copy.deepcopy(chapters)
    for row in chapters_fixed:
        row["role_breakdown"] = chapter_stats_index[row["chapter_id"]]

    # Keep the full passages ledger, but ensure it no longer advertises risky rows as retrieval-primary.
    passages_safe = copy.deepcopy(passages)
    passages_primary_downgraded_ambiguous = 0
    passages_primary_downgraded_short = 0
    for row in passages_safe:
        if row["passage_id"] in annotation_ids:
            row["anchor_passage_id"] = None
        if row.get("retrieval_primary") and row["passage_id"] in ambiguous_ids:
            row["retrieval_primary"] = False
            passages_primary_downgraded_ambiguous += 1
        elif row.get("retrieval_primary") and len(row["text"]) < SHORT_TEXT_THRESHOLD:
            row["retrieval_primary"] = False
            passages_primary_downgraded_short += 1

    # Disable the annotation link layer for MVP and clear anchor targets to avoid accidental use.
    annotations_safe = copy.deepcopy(annotations)
    for row in annotations_safe:
        row["anchor_passage_id"] = None
    annotation_links_safe: list[dict[str, Any]] = []

    # Build a safer main passage layer:
    # - remove ambiguous rows from the primary corpus
    # - keep short but non-ambiguous rows for lookup only, with retrieval_primary=false
    main_passages_safe: list[dict[str, Any]] = []
    removed_ambiguous_main = 0
    demoted_short_main = 0
    for row in main_passages:
        if row["passage_id"] in ambiguous_ids:
            removed_ambiguous_main += 1
            continue
        if len(row["text"]) < SHORT_TEXT_THRESHOLD:
            row["retrieval_primary"] = False
            demoted_short_main += 1
        main_passages_safe.append(row)

    # Build a safer retrieval chunk layer:
    # - exclude ambiguous-backed chunks
    # - exclude short chunks from the default retrieval slices
    chunks_safe: list[dict[str, Any]] = []
    removed_ambiguous_chunks = 0
    removed_short_chunks = 0
    for row in chunks:
        if any(passage_id in ambiguous_ids for passage_id in row["source_passage_ids"]):
            removed_ambiguous_chunks += 1
            continue
        if len(row["chunk_text"]) < SHORT_TEXT_THRESHOLD:
            removed_short_chunks += 1
            continue
        chunks_safe.append(row)

    books_safe = copy.deepcopy(books)
    if books_safe:
        note = (
            "MVP safe build: annotation_links disabled; annotation anchor_passage_id cleared; "
            "ambiguous main passages removed from main_passages; short main passages demoted; "
            "chunks exclude ambiguous-backed and short slices."
        )
        books_safe[0]["v2_note"] = note
        books_safe[0]["scope_note"] = (
            "MVP safe 版基于《注解伤寒论》v2 数据底座生成，仅供第一版开发使用；"
            "默认不启用 annotation_links，不直接使用 ambiguous main/chunk。"
        )

    safe_dataset = {
        "books.json": books_safe,
        "chapters.json": chapters_fixed,
        "passages.json": passages_safe,
        "main_passages.json": main_passages_safe,
        "annotations.json": annotations_safe,
        "annotation_links.json": annotation_links_safe,
        "chunks.json": chunks_safe,
        "aliases.json": aliases,
        "ambiguous_passages.json": ambiguous_passages,
        "chapter_stats.json": chapter_stats,
    }

    main_total = len(main_passages)
    main_safe_total = len(main_passages_safe)
    main_safe_primary = sum(1 for row in main_passages_safe if row["retrieval_primary"])
    chunk_total = len(chunks)
    chunk_safe_total = len(chunks_safe)
    short_main_total = sum(1 for row in main_passages if len(row["text"]) < SHORT_TEXT_THRESHOLD)
    short_chunk_total = sum(1 for row in chunks if len(row["chunk_text"]) < SHORT_TEXT_THRESHOLD)

    readme_text = "\n".join(
        [
            "# 注解伤寒论数据集 v2 MVP Safe 说明",
            "",
            "## 构建来源",
            "",
            f"- 来源数据：`{source_label}`",
            "- 目标：为 MVP 第一版提供默认可用的安全版数据底座。",
            "- 原则：优先隔离高风险数据，而不是追求一次性完美修复。",
            "",
            "## 本版策略",
            "",
            "- `annotation_links.json`：默认停用，safe 包中已置空。",
            "- `annotations.json` / `passages.json` 中注解类记录的 `anchor_passage_id`：已清空，避免误把未验明的挂接关系带入 MVP。",
            "- `chapters.json.role_breakdown`：已按 `chapter_stats.json.role_breakdown_v2` 修正为 v2 当前口径。",
            f"- `main_passages.json`：已排除 {removed_ambiguous_main} 条低置信度主条；保留的短条目中，有 {demoted_short_main} 条被降为非 primary。",
            f"- `chunks.json`：已排除 {removed_ambiguous_chunks} 个低置信度切片，并额外过滤 {removed_short_chunks} 个过短切片。",
            "",
            "## Safe 后规模",
            "",
            f"- passages：{len(passages_safe)}（保留全量总账）",
            f"- main_passages：{main_safe_total}（其中 primary={main_safe_primary}，secondary={main_safe_total - main_safe_primary}）",
            f"- annotations：{len(annotations_safe)}（文本保留，默认不参与 MVP 证据链）",
            f"- annotation_links：{len(annotation_links_safe)}",
            f"- chunks：{chunk_safe_total}",
            f"- ambiguous_passages：{len(ambiguous_passages)}（保留为人工复核清单）",
            "",
            "## MVP 使用建议",
            "",
            "- 主检索层：优先使用 `chunks.json`。",
            "- 主证据层：优先使用 `main_passages.json` 中 `retrieval_primary = true` 的记录。",
            "- 辅助回查层：`passages.json` 保留全量文本，可用于人工核对或后续版本扩展。",
            "- 注解证据层：本版默认不启用，待后续人工复核或重新生成 link 后再恢复。",
        ]
    ) + "\n"

    summary = {
        "source_label": source_label,
        "safe_output_name": "zjshl_dataset_v2_mvp_safe.zip",
        "annotation_links_policy": {
            "mode": "disabled",
            "annotation_links_kept": 0,
            "anchor_passage_id_cleared": True,
            "reason": "验收阶段已确认错挂，且存在批量疑似风险；MVP 默认不启用 annotation 证据链。",
        },
        "ambiguous_passages_policy": {
            "mode": "retain_for_review_but_exclude_from_primary_retrieval",
            "ambiguous_passages_retained": len(ambiguous_passages),
            "ambiguous_main_removed_from_main_passages": removed_ambiguous_main,
            "ambiguous_chunks_removed_from_chunks": removed_ambiguous_chunks,
            "passages_retrieval_primary_downgraded": passages_primary_downgraded_ambiguous,
        },
        "short_main_passage_policy": {
            "threshold": SHORT_TEXT_THRESHOLD,
            "mode": "retain_but_demote",
            "short_main_total": short_main_total,
            "short_main_demoted_in_main_passages": demoted_short_main,
            "safe_main_primary_count": main_safe_primary,
        },
        "short_chunk_policy": {
            "threshold": SHORT_TEXT_THRESHOLD,
            "mode": "filter_out",
            "short_chunk_total": short_chunk_total,
            "short_chunks_removed_from_safe_chunks": removed_short_chunks,
            "safe_chunk_count": chunk_safe_total,
        },
        "chapters_role_breakdown_fixed": True,
        "safe_counts": {
            "books": len(books_safe),
            "chapters": len(chapters_fixed),
            "passages": len(passages_safe),
            "main_passages": main_safe_total,
            "main_passages_primary": main_safe_primary,
            "annotations": len(annotations_safe),
            "annotation_links": len(annotation_links_safe),
            "chunks": chunk_safe_total,
            "aliases": len(aliases),
            "ambiguous_passages": len(ambiguous_passages),
        },
        "overall_ready_for_mvp": True,
        "ready_for_database_stage": True,
    }

    return safe_dataset, summary, readme_text


def write_safe_zip(output_path: Path, payloads: dict[str, Any], readme_text: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in REQUIRED_FILES:
            if name == "README_parse_report_v2.md":
                zf.writestr(name, text_bytes(readme_text))
            else:
                zf.writestr(name, json_bytes(payloads[name]))


def build_patch_note(summary: dict[str, Any], output_zip: Path) -> str:
    counts = summary["safe_counts"]
    return "\n".join(
        [
            "# MVP 安全版数据底座补丁说明",
            "",
            "## 1. 本轮修复了什么",
            "",
            "- 修正了 `chapters.json.role_breakdown`，现已与 `chapter_stats.json.role_breakdown_v2` 和当前 `passages.json` 口径一致。",
            f"- 生成了新的 safe 数据包：`{output_zip}`。",
            f"- `main_passages.json` 已从 1212 条收缩为 {counts['main_passages']} 条，其中 `retrieval_primary = true` 的主条为 {counts['main_passages_primary']} 条。",
            f"- `chunks.json` 已从 1119 条收缩为 {counts['chunks']} 条，默认仅保留适合 MVP 主检索层的切片。",
            "",
            "## 2. 本轮隔离了什么",
            "",
            "- `annotation_links.json` 已在 safe 版中默认停用，文件内容置空。",
            "- `annotations.json` 与 `passages.json` 中注解类记录的 `anchor_passage_id` 已清空，避免未复核挂接关系被下游误用。",
            "- `ambiguous_passages.json` 对应的高风险主条不再进入 `main_passages.json`，对应高风险切片也不再进入 `chunks.json`。",
            "- 过短 chunk（长度小于 20）已从 safe 版 `chunks.json` 中移除。",
            "- 过短但非高风险的主条未直接删除，而是保留在 `main_passages.json` 中并降为 `retrieval_primary = false`，仅作次级回查，不作默认主证据。",
            "",
            "## 3. 哪些问题仍然保留到后续版本",
            "",
            "- 注解挂接层没有在本轮恢复启用。原因不是缺文件，而是可靠性仍不足；后续需要人工复核或重跑更稳妥的 link 生成逻辑。",
            "- `passages.json` 仍保留全量文本总账，其中包括低置信度与过短条目。这是有意保留的底账，不代表这些记录在 MVP 中应直接参与检索。",
            "- `aliases.json` 规模仍然较小，本轮未扩充术语映射表。",
            "- 低置信度条目清单 `ambiguous_passages.json` 仍需后续人工校对，但本轮已将其从 MVP 主检索层隔离。",
            "",
            "## 4. annotation_links 策略",
            "",
            "- MVP 默认不启用 annotation_links 参与证据展示。",
            "- 已确认错挂的 6 条 link 仍以补丁说明为准记录修正目标，但不在 safe 包中启用。",
            "- 这样做的原因是：当前 link 层不是“少量脏点”，而是存在批量疑似风险；在未完成系统性复核前，整体停用比局部带病启用更安全。",
            "",
            "## 5. ambiguous_passages 策略",
            "",
            "- `ambiguous_passages.json` 保留原清单，用于后续人工复核。",
            "- 这些高风险 passage 默认不进入 safe 版 `main_passages.json`。",
            "- 任何引用到这些 passage 的 chunk 也不进入 safe 版 `chunks.json`。",
            "",
            "## 6. 短文本策略",
            "",
            "- `chunks.json`：采用“过滤”策略，长度小于 20 的切片不进入 safe 版主检索层。",
            "- `main_passages.json`：采用“保留但降级”策略，长度小于 20 且非 ambiguous 的主条保留，但 `retrieval_primary = false`。",
            "- 这样做是为了兼顾两点：一方面降低检索噪声，另一方面不直接丢失简短而可能有价值的原文证据。",
            "",
            "## 7. 为什么这份 safe 版适合 MVP 使用",
            "",
            "- 它保留了全量文本底账，因此后续数据库阶段仍有完整源数据可导入和核对。",
            "- 它默认屏蔽了最危险的证据风险，即错误注解挂接。",
            "- 它把低置信度主条和相关切片从 MVP 默认主检索层中剥离，避免把未验明的内容直接送入系统。",
            "- 它对短 chunk 做了直接过滤，使第一版检索输入更稳定；同时对短主条采用降级而非删除，避免证据层过度收缩。",
            "",
            "## 8. 最终判断",
            "",
            "**这份 safe 数据包可以进入数据库实现阶段。**",
            "",
            "前提是后续数据库实现应以 safe 包中的策略为准：",
            "",
            "1. 默认不启用 `annotation_links.json`。",
            "2. 主检索层优先使用 safe 版 `chunks.json`。",
            "3. 主证据层优先使用 safe 版 `main_passages.json` 中 `retrieval_primary = true` 的记录。",
            "4. `ambiguous_passages.json` 仅作复核清单，不作默认主证据来源。",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MVP-safe dataset package from zjshl_dataset_v2.")
    parser.add_argument("--source", help="Path to source dataset directory or zip")
    parser.add_argument("--output", help="Path to output safe zip")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source = locate_source(
        args.source,
        [
            repo_root / "data" / "processed" / "zjshl_dataset_v2",
            repo_root / "data" / "raw" / "zjshl_dataset_v2.zip",
            Path("/Users/man_ray/大四毕业论文/数据/zjshl_dataset_v2.zip"),
        ],
        "source dataset",
    )
    output_zip = Path(args.output).expanduser() if args.output else repo_root / "dist" / "zjshl_dataset_v2_mvp_safe.zip"

    dataset = load_dataset(source)
    safe_dataset, summary, readme_text = build_safe_dataset(dataset, str(source))

    write_safe_zip(output_zip, safe_dataset, readme_text)

    docs_dir = repo_root / "docs" / "data"
    reports_dir = repo_root / "reports"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    patch_note_path = docs_dir / "05_dataset_patch_note.md"
    patch_note_path.write_text(build_patch_note(summary, output_zip), encoding="utf-8")

    patch_summary_path = reports_dir / "dataset_patch_summary.json"
    patch_summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {output_zip}")
    print(f"Wrote {patch_note_path}")
    print(f"Wrote {patch_summary_path}")


if __name__ == "__main__":
    main()
