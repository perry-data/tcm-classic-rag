#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.commentarial.layer import (
    DEFAULT_COMMENTARIAL_CONFIG_PATH,
    extract_anchor_segment,
    extract_original_text,
    normalize_commentarial_anchor_text,
    resolve_project_path,
    snippet_text,
)


DEFAULT_CANONICAL_PASSAGES_PATH = "data/processed/zjshl_dataset_v2/passages.json"

MANUAL_SOURCE_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    (
        "hao_wanshan_shanghan_lectures_2007",
        "PASSAGE_NO:104A",
    ): {
        "canonical_passage_id": "ZJSHL-CH-009-P-0253",
        "note": "104上 在当前 canonical 数据中落到拆分后的前半段 passage。",
    },
    (
        "liu_duzhou_shanghan_lectures_2007",
        "PASSAGE_NO:234",
    ): {
        "canonical_passage_id": "ZJSHL-CH-011-P-0101",
        "note": "刘渡舟该条原文截断，仅保留尾句，按唯一命中的 canonical 全条人工回填。",
    },
    (
        "hao_wanshan_shanghan_lectures_2007",
        "PASSAGE_NO:263",
    ): {
        "canonical_passage_id": "ZJSHL-CH-012-P-0213",
        "note": "郝万山此处 PASSAGE_NO 口径与刘渡舟不同，按 source-aware 方式回填少阳病提纲条文。",
    },
    (
        "liu_duzhou_shanghan_lectures_2007",
        "PASSAGE_NO:276",
    ): {
        "canonical_passage_id": "ZJSHL-CH-012-P-0213",
        "note": "canonical 中带版本校勘插字，按唯一命中的少阳病提纲条文回填。",
    },
    (
        "liu_duzhou_shanghan_lectures_2007",
        "PASSAGE_NO:334",
    ): {
        "canonical_passage_id": "ZJSHL-CH-014-P-0180",
        "note": "该条在 canonical 中嵌入上条注释段内，按唯一命中的少阴急下条文回填。",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build source-aware commentarial anchor resolution artifacts.")
    parser.add_argument("--config", default=DEFAULT_COMMENTARIAL_CONFIG_PATH, help="Path to commentarial layer config.")
    parser.add_argument(
        "--canonical-passages",
        default=DEFAULT_CANONICAL_PASSAGES_PATH,
        help="Path to canonical passages JSON.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def choose_anchor_evidence(anchor_key: str, units: list[dict[str, Any]]) -> dict[str, Any]:
    ranked: list[dict[str, Any]] = []
    for unit in units:
        anchor_candidates = [key for key in unit.get("anchor_candidates") or [] if key.startswith("PASSAGE_NO:")]
        quote = extract_original_text(unit)
        segment = extract_anchor_segment(anchor_key, quote) if quote else ""
        ranked.append(
            {
                "unit_id": unit["unit_id"],
                "commentator": unit.get("commentator"),
                "anchor_type": unit.get("anchor_type"),
                "anchor_count": len(anchor_candidates),
                "is_primary": anchor_key in (unit.get("primary_anchor_candidates") or []),
                "quote": quote,
                "segment": segment or quote,
            }
        )
    ranked.sort(
        key=lambda item: (
            item["anchor_count"] != 1,
            item["anchor_type"] not in {"exact", "excerpt"},
            not item["is_primary"],
            len(item["segment"] or ""),
        )
    )
    return ranked[0]


def score_candidate(anchor_text: str, canonical_text: str) -> float:
    anchor_norm = normalize_commentarial_anchor_text(anchor_text)
    canonical_norm = normalize_commentarial_anchor_text(canonical_text)
    if not anchor_norm or not canonical_norm:
        return 0.0
    if anchor_norm == canonical_norm:
        return 100.0
    if anchor_norm in canonical_norm or canonical_norm in anchor_norm:
        ratio = min(len(anchor_norm), len(canonical_norm)) / max(len(anchor_norm), len(canonical_norm))
        return 90.0 + ratio * 10.0
    matcher = SequenceMatcher(None, anchor_norm, canonical_norm)
    ratio_score = matcher.ratio() * 100.0
    if ratio_score < 62.0:
        return 0.0
    longest_block = max((block.size for block in matcher.get_matching_blocks()), default=0)
    overlap_boost = longest_block / max(1, min(len(anchor_norm), len(canonical_norm))) * 10.0
    return ratio_score + overlap_boost


def find_best_candidate(anchor_text: str, passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for passage in passages:
        score = score_candidate(anchor_text, passage["text"])
        if score <= 0:
            continue
        candidates.append(
            {
                "canonical_passage_id": passage["passage_id"],
                "chapter_id": passage["chapter_id"],
                "chapter_name": passage["chapter_name"],
                "text_preview": snippet_text(passage["text"], limit=140),
                "score": round(score, 3),
            }
        )
    candidates.sort(key=lambda row: (-row["score"], row["canonical_passage_id"]))
    return candidates


def resolve_anchor(
    *,
    source_id: str,
    anchor_key: str,
    units: list[dict[str, Any]],
    passages: list[dict[str, Any]],
) -> dict[str, Any]:
    chosen = choose_anchor_evidence(anchor_key, units)
    override = MANUAL_SOURCE_OVERRIDES.get((source_id, anchor_key))
    if override:
        return {
            "status": "resolved_manual_override",
            "canonical_passage_id": override["canonical_passage_id"],
            "chapter_id": next(
                (row["chapter_id"] for row in passages if row["passage_id"] == override["canonical_passage_id"]),
                None,
            ),
            "resolution_method": "manual_override",
            "source_unit_id": chosen["unit_id"],
            "source_quote_preview": snippet_text(chosen["segment"], limit=140),
            "top_candidates": [],
            "note": override["note"],
        }

    top_candidates = find_best_candidate(chosen["segment"], passages)[:3]
    if not top_candidates:
        return {
            "status": "unresolved_no_candidate",
            "canonical_passage_id": None,
            "chapter_id": None,
            "resolution_method": "text_match_failed",
            "source_unit_id": chosen["unit_id"],
            "source_quote_preview": snippet_text(chosen["segment"], limit=140),
            "top_candidates": [],
            "note": "未找到可接受的 canonical passage 候选。",
        }

    top = top_candidates[0]
    gap = top["score"] - (top_candidates[1]["score"] if len(top_candidates) > 1 else 0.0)
    if top["score"] >= 95.0:
        status = "resolved_auto_high"
    elif top["score"] >= 80.0 and gap >= 3.0:
        status = "resolved_auto_medium"
    elif len(top_candidates) == 1 and top["score"] >= 75.0:
        status = "resolved_auto_medium"
    else:
        return {
            "status": "unresolved_manual_review",
            "canonical_passage_id": None,
            "chapter_id": None,
            "resolution_method": "text_match_ambiguous",
            "source_unit_id": chosen["unit_id"],
            "source_quote_preview": snippet_text(chosen["segment"], limit=140),
            "top_candidates": top_candidates,
            "note": "候选不够稳定，保留 unresolved 以避免错绑。",
        }

    return {
        "status": status,
        "canonical_passage_id": top["canonical_passage_id"],
        "chapter_id": top["chapter_id"],
        "resolution_method": "single_anchor_text_match" if chosen["anchor_count"] == 1 else "source_scoped_segment_match",
        "source_unit_id": chosen["unit_id"],
        "source_quote_preview": snippet_text(chosen["segment"], limit=140),
        "top_candidates": top_candidates,
        "note": "",
    }


def build_global_status(by_source: dict[str, dict[str, Any]]) -> dict[str, Any]:
    anchors = sorted({anchor for mapping in by_source.values() for anchor in mapping})
    global_map: dict[str, Any] = {}
    conflicts: dict[str, Any] = {}
    for anchor_key in anchors:
        per_source_rows = []
        resolved_ids = []
        for source_id, mapping in by_source.items():
            row = mapping.get(anchor_key)
            if row is None:
                continue
            per_source_rows.append(
                {
                    "source_id": source_id,
                    "status": row["status"],
                    "canonical_passage_id": row.get("canonical_passage_id"),
                    "chapter_id": row.get("chapter_id"),
                }
            )
            if row.get("canonical_passage_id"):
                resolved_ids.append(row["canonical_passage_id"])
        unique_ids = sorted(set(resolved_ids))
        all_sources_resolved = per_source_rows and all(row["canonical_passage_id"] for row in per_source_rows)
        if len(unique_ids) == 1 and all_sources_resolved:
            global_map[anchor_key] = {
                "status": "resolved_global",
                "canonical_passage_id": unique_ids[0],
                "source_variants": per_source_rows,
            }
            continue
        if len(unique_ids) == 1 and per_source_rows:
            global_map[anchor_key] = {
                "status": "partial_source_resolution",
                "canonical_passage_id": unique_ids[0],
                "source_variants": per_source_rows,
            }
            continue
        if len(unique_ids) > 1:
            global_map[anchor_key] = {
                "status": "conflicting_source_scope",
                "canonical_passage_id": None,
                "source_variants": per_source_rows,
            }
            conflicts[anchor_key] = global_map[anchor_key]
            continue
        global_map[anchor_key] = {
            "status": "unresolved",
            "canonical_passage_id": None,
            "source_variants": per_source_rows,
        }
    return {"global": global_map, "conflicts": conflicts}


def main() -> int:
    args = parse_args()
    config = load_json(resolve_project_path(args.config))
    bundle_dir = resolve_project_path(str(config["bundle_dir"]))
    resolution_path = resolve_project_path(str(config["resolution_file"]))
    resolved_links_path = resolve_project_path(str(config["resolved_links_file"]))
    passages = load_json(resolve_project_path(args.canonical_passages))
    sources = load_json(bundle_dir / "commentarial_sources.json")
    units = load_jsonl(bundle_dir / "commentarial_units.jsonl")
    links = load_jsonl(bundle_dir / "commentarial_anchor_links.jsonl")

    units_by_id = {row["unit_id"]: row for row in units}
    units_by_source_anchor: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for unit in units:
        source_id = str(unit["source_id"])
        for anchor_key in unit.get("anchor_candidates") or []:
            if not str(anchor_key).startswith("PASSAGE_NO:"):
                continue
            units_by_source_anchor[source_id][str(anchor_key)].append(unit)

    by_source: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_id = str(source["source_id"])
        source_mapping: dict[str, Any] = {}
        for anchor_key, anchor_units in sorted(units_by_source_anchor[source_id].items()):
            source_mapping[anchor_key] = resolve_anchor(
                source_id=source_id,
                anchor_key=anchor_key,
                units=anchor_units,
                passages=passages,
            )
        by_source[source_id] = source_mapping

    global_payload = build_global_status(by_source)
    resolution_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy_version": "commentarial_anchor_resolution_v1",
        "notes": [
            "PASSAGE_NO resolution is source-aware because the two lecture corpora do not share a perfectly identical numbering scope.",
            "When both sources resolve to the same canonical passage_id, the global status is resolved_global.",
            "When sources diverge, global status is conflicting_source_scope and runtime should use source-scoped resolution only.",
        ],
        "by_source": by_source,
        "global": global_payload["global"],
        "conflicts": global_payload["conflicts"],
        "stats": {
            "source_count": len(by_source),
            "resolved_source_scoped_count": sum(
                1
                for mapping in by_source.values()
                for row in mapping.values()
                if str(row["status"]).startswith("resolved")
            ),
            "unresolved_source_scoped_count": sum(
                1
                for mapping in by_source.values()
                for row in mapping.values()
                if not str(row["status"]).startswith("resolved")
            ),
            "global_conflict_count": len(global_payload["conflicts"]),
        },
    }

    resolved_links: list[dict[str, Any]] = []
    for link in links:
        unit = units_by_id.get(str(link["unit_id"]))
        source_id = str(unit.get("source_id") or "") if unit else ""
        source_mapping = by_source.get(source_id, {})
        resolution = source_mapping.get(str(link.get("anchor_passage_id") or ""))
        global_status = resolution_payload["global"].get(str(link.get("anchor_passage_id") or ""), {})
        resolved_links.append(
            {
                **link,
                "source_id": source_id,
                "commentator": unit.get("commentator") if unit else None,
                "resolution_scope": "source_scoped",
                "resolution_status": (
                    resolution["status"]
                    if resolution and str(link.get("anchor_key_kind")) == "passage_no"
                    else "theme_only_no_passage_resolution"
                ),
                "global_resolution_status": global_status.get("status"),
                "resolved_canonical_passage_id": resolution.get("canonical_passage_id") if resolution else None,
                "resolved_chapter_id": resolution.get("chapter_id") if resolution else None,
                "resolution_method": resolution.get("resolution_method") if resolution else None,
            }
        )

    resolution_path.parent.mkdir(parents=True, exist_ok=True)
    resolution_path.write_text(json.dumps(resolution_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with resolved_links_path.open("w", encoding="utf-8") as handle:
        for row in resolved_links:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "resolution_path": str(resolution_path),
                "resolved_links_path": str(resolved_links_path),
                "stats": resolution_payload["stats"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
