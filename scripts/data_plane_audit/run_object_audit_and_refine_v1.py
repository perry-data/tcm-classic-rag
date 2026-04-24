#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data_plane_optimization.build_data_plane_objects_v1 import (  # noqa: E402
    build_definition_records,
    build_formula_risk_summary,
    build_learner_lexicon_records,
    build_sentence_role_registry,
    build_summary_payload,
    build_term_alias_records,
    compact_text,
    create_schema,
    insert_records,
    load_source_rows,
    resolve_project_path,
    write_json,
)


DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_BEFORE_DB_PATH = "/tmp/zjshl_v1_before_data_plane_audit_v1.db"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_audit"
DEFAULT_DOC_PATH = "docs/data_plane_audit/data_plane_audit_and_refine_v1.md"

FORMULA_UPGRADE_SET = {
    "四逆加人参汤",
    "四逆加猪胆汁汤",
    "柴胡加芒硝汤",
    "桂枝加浓朴杏子汤",
    "桂枝加芍药汤",
    "桂枝去桂加茯苓白术汤",
    "桂枝去芍药加附子汤",
    "桂枝去芍药汤",
}

DEFINITION_REFINED_TERMS = {
    "四逆",
    "湿痹",
    "风温",
    "阳易",
    "阴易",
    "胆瘅",
}

DEFINITION_EXPLICIT_AUDITS: dict[str, dict[str, Any]] = {
    "下药": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "来源于 mixed-role risk passage，但抽出的类属句自足且 learner short-query 受益明显。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 safe primary；不升 high 的原因是原 passage 尾部混有《金匮玉函》警示材料。",
    },
    "两感": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句极短且闭合，但来源层仍是 records_passages。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保留 medium safe primary；若后续找到干净 main passage 再考虑升 high。",
    },
    "代阴": {
        "audit_label": "boundary_unclear",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句所在主 passage 含 inline 版本差异标记，句段可抽出但不够高置信。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保留 medium；不升 high 的根因是同句带 variant note。",
    },
    "伏气": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句完整，但来源仍在 risk/full 层。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保留 safe primary；definition chain 可审计到单句。",
    },
    "内烦": {
        "audit_label": "context_dependent",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "主句是吐后语境里的症状命名句，能解释 term，但依赖临床上下文。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "继续保持 medium safe primary，不宜升 high。",
    },
    "发汗药": {
        "audit_label": "context_dependent",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "当前主句更像使用解释，不是最短定义句；但对 learner-facing 类别解释更稳。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "暂不换回 0120 的 membership 句；保持当前 explanation primary 更利于理解。",
    },
    "四逆": {
        "audit_label": "boundary_unclear",
        "audit_decision": "adjust_sentence_source",
        "main_risk_reason": "句段角色规则把“四逆者，四肢不温也”误判成 formula_composition_sentence。",
        "fix_action": "tighten_sentence_role_formula_dosage_rule",
        "needs_followup": False,
        "notes": "本轮修正 sentence role 规则，不改对象层定位。",
    },
    "坏病": {
        "audit_label": "context_dependent",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句自足，但自带误治前提语境，因此不升 high。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保留 safe primary；证据链和 term 指向清晰。",
    },
    "奔豚": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "命名句短而独立，风险主要在 source layer 而非句义。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保留 medium safe primary。",
    },
    "小结胸": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "分型句闭合，长段风险已被 sentence-level extraction 隔离。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保留 medium safe primary。",
    },
    "并病": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句可独立成义，但仍属于传经上下文中的概念命名。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 medium；不需要额外 alias 调整。",
    },
    "时行之气": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句完整，风险主要来自原始载体层级。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 safe primary。",
    },
    "水结胸": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "分型说明足够完整，且已把后续方药句留在 support。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 medium safe primary。",
    },
    "消渴": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "命名句附带病机短解释，适合作 learner-facing primary。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 medium safe primary。",
    },
    "湿痹": {
        "audit_label": "editorial_contaminated",
        "audit_decision": "adjust_sentence_source",
        "main_risk_reason": "原句含赵本/一云类 inline variant note，role 判定应基于 strip 后句面。",
        "fix_action": "strip_variant_then_reclassify_sentence_role",
        "needs_followup": False,
        "notes": "本轮不降级，但明确它不是 high。",
    },
    "盗汗": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句极短且 learner alias 清晰，风险主要来自 source layer。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 medium safe primary。",
    },
    "结阴": {
        "audit_label": "boundary_unclear",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "与代阴共用一条带 variant 干扰的脉象段，仍不适合升 high。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 medium safe primary。",
    },
    "肺痿": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "命名句足够自足，长段病机说明已留在 support/review。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 medium safe primary。",
    },
    "胆瘅": {
        "audit_label": "promotion_too_aggressive",
        "audit_decision": "downgrade_to_review_only",
        "main_risk_reason": "当前 primary sentence 直接带《内经》曰 commentarial citation，升格过激。",
        "fix_action": "downgrade_definition_object_and_remove_safe_primary_surfaces",
        "needs_followup": True,
        "notes": "本轮降回 review_only；下一轮若想升格，需要找到不依赖 commentary citation 的自足句段。",
    },
    "虚烦": {
        "audit_label": "clean_enough",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "定义句完整，后续 variant/commentary 已留在 support。",
        "fix_action": "none",
        "needs_followup": False,
        "notes": "保持 medium safe primary。",
    },
    "阳易": {
        "audit_label": "alias_insufficient",
        "audit_decision": "adjust_aliases",
        "main_risk_reason": "与阴易共享 learner alias“阴阳易”，当前 runtime 会强行落到阳易。",
        "fix_action": "remove_shared_ambiguous_alias",
        "needs_followup": True,
        "notes": "保留 safe primary，但去掉共享歧义 alias，避免错误定向。",
    },
    "阴易": {
        "audit_label": "alias_insufficient",
        "audit_decision": "adjust_aliases",
        "main_risk_reason": "与阳易共享 learner alias“阴阳易”，会造成单边误归一。",
        "fix_action": "remove_shared_ambiguous_alias",
        "needs_followup": True,
        "notes": "保留 safe primary，但去掉共享歧义 alias。",
    },
    "风温": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主句来自 safe main passage，句义完整；原 medium 主要是 role heuristics 未把“X为病”识别成定义句。",
        "fix_action": "upgrade_confidence_after_role_reclassify",
        "needs_followup": False,
        "notes": "本轮升到 high。",
    },
}

FORMULA_EXPLICIT_AUDITS: dict[str, dict[str, Any]] = {
    "乌梅丸": {
        "audit_label": "editorial_contaminated",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "当前仅有带异文标记的组成行，缺少独立 usage/decoction span。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "继续保持 medium。",
    },
    "四逆加人参汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主行已内联“馀根据四逆汤法服”，builder 之前未把 inline usage 计入高置信。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "四逆加猪胆汁汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主行内联前法服用与替代说明，足以构成高置信继承型方文。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "旋复代赭石汤": {
        "audit_label": "editorial_contaminated",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "标题与药味中均带赵本异文，且无独立 usage/decoction span。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 medium。",
    },
    "柴胡加芒硝汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主行含加减关系与“服不解，更服”使用信息，builder 低估了 inline usage。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "栀子浓朴汤": {
        "audit_label": "editorial_contaminated",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "药味行异文较多，且仅有组成行。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 medium。",
    },
    "桂枝加浓朴杏子汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "继承型公式稳定，主行已含“馀根据前法”。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "桂枝加芍药汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主行是稳定加减公式，前法继承明确。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "桂枝去桂加茯苓白术汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主行同时含继承关系、煎服方式和“小便利则愈”的使用语义。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "桂枝去芍药加附子汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主行继承关系与加附子边界清晰。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "桂枝去芍药汤": {
        "audit_label": "clean_enough",
        "audit_decision": "upgrade_confidence",
        "main_risk_reason": "主行是纯净的基方去味关系，前法继承清楚。",
        "fix_action": "upgrade_confidence_for_inline_inherited_usage",
        "needs_followup": False,
        "notes": "升到 high。",
    },
    "桂枝甘草龙骨牡蛎汤": {
        "audit_label": "editorial_contaminated",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "仅有药味组成行，且标题/药味异文较多。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 medium。",
    },
    "茵陈蒿汤": {
        "audit_label": "span_uncertain",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "当前只有组成行，缺独立 decoction/usage span。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 medium。",
    },
    "麻黄附子甘草汤": {
        "audit_label": "editorial_contaminated",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "主行含赵本变体，且没有额外 usage/decoction span。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 medium。",
    },
}

REVIEW_ONLY_EXPLICIT_AUDITS: dict[str, dict[str, Any]] = {
    "两阳": {
        "audit_label": "review_only_expected",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "术语定义强依赖后续病机展开，当前不适合 learner-facing 主定义对象。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "继续 review_only；即使 query 可命中主文，也不升为 definition object primary。",
    },
    "将军": {
        "audit_label": "review_only_expected",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "更偏药名训诂/注解层，不是当前 definition family 的安全主对象。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 review_only。",
    },
    "神丹": {
        "audit_label": "review_only_expected",
        "audit_decision": "keep_as_is",
        "main_risk_reason": "证据主要来自注释汇编层，缺独立 canonical 支撑。",
        "fix_action": "none",
        "needs_followup": True,
        "notes": "保持 review_only。",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and refine medium-confidence data-plane objects.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--before-db-path", default=DEFAULT_BEFORE_DB_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_json_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return [str(item) for item in json.loads(str(value)) if item]


def append_note(note_text: str, extra: str) -> str:
    base = (note_text or "").strip()
    extra = extra.strip()
    if not base:
        return extra
    if extra in base:
        return base
    return f"{base} {extra}"


def find_primary_sentence_meta(
    sentence_entries: list[dict[str, Any]],
    passage_id: str,
    source_table: str,
    primary_evidence_text: str,
) -> dict[str, Any] | None:
    normalized_target = compact_text(primary_evidence_text)
    candidates = [
        entry
        for entry in sentence_entries
        if entry["passage_id"] == passage_id and entry["source_table"] == source_table
    ]
    for entry in candidates:
        normalized_sentence = entry["normalized_sentence_text"]
        if normalized_target and (
            normalized_target in normalized_sentence or normalized_sentence in normalized_target
        ):
            return entry
    return candidates[0] if candidates else None


def load_before_confidence_maps(before_db_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    conn = sqlite3.connect(before_db_path)
    conn.row_factory = sqlite3.Row
    try:
        definition_map = {
            row["concept_id"]: row["source_confidence"]
            for row in conn.execute("SELECT concept_id, source_confidence FROM definition_term_registry")
        }
        formula_map = {
            row["formula_id"]: row["source_confidence"]
            for row in conn.execute("SELECT formula_id, source_confidence FROM formula_canonical_registry")
        }
        return definition_map, formula_map
    finally:
        conn.close()


def apply_definition_refinements(definition_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updated = []
    for record in definition_records:
        row = dict(record)
        canonical_term = row["canonical_term"]
        query_aliases = safe_json_list(row["query_aliases_json"])
        learner_surface_forms = safe_json_list(row["learner_surface_forms_json"])

        if canonical_term == "风温":
            row["source_confidence"] = "high"
            row["promotion_reason"] = "audit_v1_clean_main_definition_sentence"
            row["notes"] = append_note(row["notes"], "audit_v1: clean main-passage definition sentence upgraded to high.")

        if canonical_term == "发汗药":
            row["primary_evidence_type"] = "exact_term_explanation"
            row["promotion_reason"] = "gold_fix_v1_explanation_primary_not_strict_definition"
            row["definition_evidence_passage_ids_json"] = json.dumps([], ensure_ascii=False, separators=(",", ":"))
            row["explanation_evidence_passage_ids_json"] = json.dumps(
                ["ZJSHL-CH-006-P-0127"],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            row["membership_evidence_passage_ids_json"] = json.dumps(
                ["ZJSHL-CH-006-P-0120"],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            row["notes"] = append_note(
                row["notes"],
                (
                    "gold_fix_v1: no safer standalone membership/definition sentence was selected; "
                    "keep the current sentence as explanation-primary, not definition-primary. "
                    "ZJSHL-CH-006-P-0120 remains support membership evidence only."
                ),
            )

        if canonical_term == "胆瘅":
            row["source_confidence"] = "review_only"
            row["promotion_state"] = "review_only"
            row["review_only_reason"] = (
                "primary sentence directly depends on commentary citation《内经》曰，当前不宜作为 learner-facing safe primary。"
            )
            row["notes"] = append_note(row["notes"], "audit_v1: downgraded from safe_primary because the primary sentence is commentarial.")
            row["notes"] = append_note(
                row["notes"],
                "gold_fix_v1: removed review-only learner aliases 口苦病/胆瘅病 from query aliases and retrieval text.",
            )
            row["is_safe_primary_candidate"] = 0
            query_aliases = [alias for alias in query_aliases if alias not in {"口苦病", "胆瘅病"}]
            learner_surface_forms = []
            retrieval_lines = [
                line
                for line in str(row["retrieval_text"]).splitlines()
                if compact_text(line) not in {"口苦病", "胆瘅病"}
            ]
            row["retrieval_text"] = "\n".join(retrieval_lines)
            row["normalized_retrieval_text"] = compact_text(row["retrieval_text"])

        if canonical_term in {"阳易", "阴易"}:
            query_aliases = [alias for alias in query_aliases if alias != "阴阳易"]
            learner_surface_forms = [alias for alias in learner_surface_forms if alias != "阴阳易"]
            row["notes"] = append_note(row["notes"], "audit_v1: removed shared ambiguous alias 阴阳易.")

        row["query_aliases_json"] = json.dumps(query_aliases, ensure_ascii=False, separators=(",", ":"))
        row["learner_surface_forms_json"] = json.dumps(
            learner_surface_forms,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        updated.append(row)
    return updated


def apply_formula_refinements(conn: sqlite3.Connection) -> None:
    with conn:
        conn.executemany(
            "UPDATE formula_canonical_registry SET source_confidence = 'high' WHERE canonical_name = ?",
            [(name,) for name in sorted(FORMULA_UPGRADE_SET)],
        )


def fetch_definition_records(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM definition_term_registry ORDER BY canonical_term")]


def fetch_formula_records(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM formula_canonical_registry ORDER BY canonical_name")]


def build_definition_audit_records(
    definition_records: list[dict[str, Any]],
    sentence_entries: list[dict[str, Any]],
    rows_by_table: dict[str, dict[str, dict[str, Any]]],
    before_confidence_map: dict[str, str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in definition_records:
        canonical_term = row["canonical_term"]
        if before_confidence_map.get(row["concept_id"]) != "medium":
            continue
        if canonical_term in REVIEW_ONLY_EXPLICIT_AUDITS and row["promotion_state"] == "review_only":
            continue
        audit_meta = DEFINITION_EXPLICIT_AUDITS[canonical_term]
        sentence_meta = find_primary_sentence_meta(
            sentence_entries,
            row["primary_support_passage_id"],
            row["primary_source_table"],
            row["primary_evidence_text"],
        )
        source_row = rows_by_table[row["primary_source_table"]][row["primary_support_passage_id"]]
        records.append(
            {
                "object_type": "definition_term",
                "object_id": row["concept_id"],
                "canonical_name": canonical_term,
                "current_status": row["promotion_state"],
                "source_confidence_before": before_confidence_map.get(row["concept_id"], row["source_confidence"]),
                "primary_support_passage_id": row["primary_support_passage_id"],
                "promotion_source_layer": row["promotion_source_layer"],
                "main_risk_reason": audit_meta["main_risk_reason"],
                "audit_label": audit_meta["audit_label"],
                "audit_decision": audit_meta["audit_decision"],
                "fix_action": audit_meta["fix_action"],
                "confidence_after": row["source_confidence"],
                "needs_followup": audit_meta["needs_followup"],
                "notes": audit_meta["notes"],
                "primary_source_table": row["primary_source_table"],
                "primary_evidence_type": row["primary_evidence_type"],
                "primary_evidence_text": row["primary_evidence_text"],
                "sentence_primary_role": None if sentence_meta is None else sentence_meta["primary_role"],
                "sentence_role_tags": [] if sentence_meta is None else sentence_meta["role_tags"],
                "sentence_risk_label": None if sentence_meta is None else sentence_meta["risk_label"],
                "source_excerpt": source_row["retrieval_text"],
            }
        )
    return records


def build_review_only_audit_records(
    definition_records: list[dict[str, Any]],
    sentence_entries: list[dict[str, Any]],
    rows_by_table: dict[str, dict[str, dict[str, Any]]],
    before_confidence_map: dict[str, str],
) -> list[dict[str, Any]]:
    by_term = {row["canonical_term"]: row for row in definition_records if row["promotion_state"] == "review_only"}
    records: list[dict[str, Any]] = []
    for canonical_term, audit_meta in REVIEW_ONLY_EXPLICIT_AUDITS.items():
        row = by_term[canonical_term]
        sentence_meta = find_primary_sentence_meta(
            sentence_entries,
            row["primary_support_passage_id"],
            row["primary_source_table"],
            row["primary_evidence_text"],
        )
        source_row = rows_by_table[row["primary_source_table"]][row["primary_support_passage_id"]]
        records.append(
            {
                "object_type": "review_only_term",
                "object_id": row["concept_id"],
                "canonical_name": canonical_term,
                "current_status": row["promotion_state"],
                "source_confidence_before": before_confidence_map.get(row["concept_id"], row["source_confidence"]),
                "primary_support_passage_id": row["primary_support_passage_id"],
                "promotion_source_layer": row["promotion_source_layer"],
                "main_risk_reason": audit_meta["main_risk_reason"],
                "audit_label": audit_meta["audit_label"],
                "audit_decision": audit_meta["audit_decision"],
                "fix_action": audit_meta["fix_action"],
                "confidence_after": row["source_confidence"],
                "needs_followup": audit_meta["needs_followup"],
                "notes": audit_meta["notes"],
                "primary_source_table": row["primary_source_table"],
                "primary_evidence_type": row["primary_evidence_type"],
                "primary_evidence_text": row["primary_evidence_text"],
                "sentence_primary_role": None if sentence_meta is None else sentence_meta["primary_role"],
                "sentence_role_tags": [] if sentence_meta is None else sentence_meta["role_tags"],
                "sentence_risk_label": None if sentence_meta is None else sentence_meta["risk_label"],
                "source_excerpt": source_row["retrieval_text"],
            }
        )
    return records


def build_formula_audit_records(
    conn: sqlite3.Connection,
    formula_records: list[dict[str, Any]],
    before_confidence_map: dict[str, str],
) -> list[dict[str, Any]]:
    main_text_by_passage = {
        row["passage_id"]: dict(row)
        for row in conn.execute(
            """
            SELECT passage_id, text, chapter_id
            FROM records_main_passages
            """
        )
    }
    records: list[dict[str, Any]] = []
    for row in formula_records:
        if before_confidence_map.get(row["formula_id"]) != "medium":
            continue
        audit_meta = FORMULA_EXPLICIT_AUDITS[row["canonical_name"]]
        source_row = main_text_by_passage[row["primary_formula_passage_id"]]
        records.append(
            {
                "object_type": "formula",
                "object_id": row["formula_id"],
                "canonical_name": row["canonical_name"],
                "current_status": "formula_primary",
                "source_confidence_before": before_confidence_map.get(row["formula_id"], row["source_confidence"]),
                "primary_support_passage_id": row["primary_formula_passage_id"],
                "promotion_source_layer": "formula_registry_main_passage",
                "main_risk_reason": audit_meta["main_risk_reason"],
                "audit_label": audit_meta["audit_label"],
                "audit_decision": audit_meta["audit_decision"],
                "fix_action": audit_meta["fix_action"],
                "confidence_after": row["source_confidence"],
                "needs_followup": audit_meta["needs_followup"],
                "notes": audit_meta["notes"],
                "formula_span_start_passage_id": row["formula_span_start_passage_id"],
                "formula_span_end_passage_id": row["formula_span_end_passage_id"],
                "composition_passage_ids": safe_json_list(row["composition_passage_ids_json"]),
                "decoction_passage_ids": safe_json_list(row["decoction_passage_ids_json"]),
                "usage_context_passage_ids": safe_json_list(row["usage_context_passage_ids_json"]),
                "source_excerpt": source_row["text"],
            }
        )
    return records


def build_ledger_payload(
    definition_audits: list[dict[str, Any]],
    formula_audits: list[dict[str, Any]],
    review_only_audits: list[dict[str, Any]],
) -> dict[str, Any]:
    all_records = definition_audits + formula_audits + review_only_audits
    return {
        "generated_at_utc": now_utc(),
        "definition_medium_count": len(definition_audits),
        "formula_medium_count": len(formula_audits),
        "review_only_count": len(review_only_audits),
        "audit_label_counts": dict(sorted(Counter(row["audit_label"] for row in all_records).items())),
        "audit_decision_counts": dict(sorted(Counter(row["audit_decision"] for row in all_records).items())),
        "records": all_records,
    }


def md_table(records: list[dict[str, Any]], *, include_excerpt: bool = False) -> list[str]:
    headers = [
        "canonical_name",
        "audit_label",
        "audit_decision",
        "before",
        "after",
        "primary_support_passage_id",
        "main_risk_reason",
        "fix_action",
    ]
    if include_excerpt:
        headers.append("primary_evidence_text")
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in records:
        values = [
            row["canonical_name"],
            row["audit_label"],
            row["audit_decision"],
            str(row["source_confidence_before"]),
            str(row["confidence_after"]),
            row["primary_support_passage_id"],
            row["main_risk_reason"],
            row["fix_action"],
        ]
        if include_excerpt:
            values.append(str(row.get("primary_evidence_text") or ""))
        safe_values = [value.replace("\n", "<br>") for value in values]
        lines.append("| " + " | ".join(safe_values) + " |")
    return lines


def write_markdown_docs(
    doc_path: Path,
    output_dir: Path,
    definition_audits: list[dict[str, Any]],
    formula_audits: list[dict[str, Any]],
    review_only_audits: list[dict[str, Any]],
    ledger_payload: dict[str, Any],
    summary_before: dict[str, Any],
    summary_after: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    keep_records = [row for row in ledger_payload["records"] if row["audit_decision"] == "keep_as_is"]
    refine_records = [
        row
        for row in ledger_payload["records"]
        if row["audit_decision"] in {"upgrade_confidence", "adjust_sentence_source", "adjust_aliases", "adjust_span"}
    ]
    downgrade_records = [row for row in ledger_payload["records"] if row["audit_decision"] == "downgrade_to_review_only"]

    summary_lines = [
        "# Data Plane Audit And Refine v1",
        "",
        "## Audit Scope",
        "",
        f"- definition medium audited: `{len(definition_audits)}`",
        f"- formula medium audited: `{len(formula_audits)}`",
        f"- review-only audited: `{len(review_only_audits)}`",
        "",
        "## Before / After Snapshot",
        "",
        f"- definition high: `{summary_before['definition_source_confidence'].get('high', 0)} -> {summary_after['definition_source_confidence'].get('high', 0)}`",
        f"- definition medium: `{summary_before['definition_source_confidence'].get('medium', 0)} -> {summary_after['definition_source_confidence'].get('medium', 0)}`",
        f"- definition review_only: `{summary_before['definition_source_confidence'].get('review_only', 0)} -> {summary_after['definition_source_confidence'].get('review_only', 0)}`",
        f"- formula high: `{summary_before['formula_source_confidence'].get('high', 0)} -> {summary_after['formula_source_confidence'].get('high', 0)}`",
        f"- formula medium: `{summary_before['formula_source_confidence'].get('medium', 0)} -> {summary_after['formula_source_confidence'].get('medium', 0)}`",
        f"- term_alias_registry: `{summary_before['term_alias_count']} -> {summary_after['term_alias_count']}`",
        f"- learner_query_normalization_lexicon: `{summary_before['learner_lexicon_count']} -> {summary_after['learner_lexicon_count']}`",
        "",
        "## Keep List",
        "",
        *md_table(keep_records[:], include_excerpt=False),
        "",
        "## Refine List",
        "",
        *md_table(refine_records[:], include_excerpt=False),
        "",
        "## Downgrade List",
        "",
        *md_table(downgrade_records[:], include_excerpt=False),
        "",
    ]
    doc_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    ledger_md_path = output_dir / "object_audit_ledger_v1.md"
    ledger_lines = [
        "# Object Audit Ledger v1",
        "",
        f"- generated_at_utc: `{ledger_payload['generated_at_utc']}`",
        f"- audit_label_counts: `{json.dumps(ledger_payload['audit_label_counts'], ensure_ascii=False)}`",
        f"- audit_decision_counts: `{json.dumps(ledger_payload['audit_decision_counts'], ensure_ascii=False)}`",
        "",
        *md_table(ledger_payload["records"], include_excerpt=True),
        "",
    ]
    ledger_md_path.write_text("\n".join(ledger_lines) + "\n", encoding="utf-8")

    definition_md_path = output_dir / "definition_medium_confidence_audit_v1.md"
    definition_lines = [
        "# Definition Medium Confidence Audit v1",
        "",
        *md_table(definition_audits, include_excerpt=True),
        "",
    ]
    definition_md_path.write_text("\n".join(definition_lines) + "\n", encoding="utf-8")

    formula_md_path = output_dir / "formula_medium_confidence_audit_v1.md"
    formula_lines = [
        "# Formula Medium Confidence Audit v1",
        "",
        *md_table(formula_audits, include_excerpt=False),
        "",
    ]
    formula_md_path.write_text("\n".join(formula_lines) + "\n", encoding="utf-8")

    review_md_path = output_dir / "review_only_boundary_audit_v1.md"
    review_lines = [
        "# Review Only Boundary Audit v1",
        "",
        *md_table(review_only_audits, include_excerpt=True),
        "",
    ]
    review_md_path.write_text("\n".join(review_lines) + "\n", encoding="utf-8")


def build_snapshot_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    definition_counts = Counter(
        row["source_confidence"] for row in conn.execute("SELECT source_confidence FROM definition_term_registry")
    )
    formula_counts = Counter(
        row["source_confidence"] for row in conn.execute("SELECT source_confidence FROM formula_canonical_registry")
    )
    term_alias_count = conn.execute("SELECT COUNT(*) FROM term_alias_registry").fetchone()[0]
    learner_lexicon_count = conn.execute("SELECT COUNT(*) FROM learner_query_normalization_lexicon").fetchone()[0]
    return {
        "definition_source_confidence": dict(sorted(definition_counts.items())),
        "formula_source_confidence": dict(sorted(formula_counts.items())),
        "term_alias_count": term_alias_count,
        "learner_lexicon_count": learner_lexicon_count,
    }


def write_registry_artifacts(
    output_dir: Path,
    definition_records: list[dict[str, Any]],
    term_alias_records: list[dict[str, Any]],
    learner_records: list[dict[str, Any]],
    sentence_entries: list[dict[str, Any]],
    formula_records: list[dict[str, Any]],
) -> None:
    write_json(
        output_dir / "definition_term_registry_audited_v1.json",
        {
            "generated_at_utc": now_utc(),
            "definition_term_count": len(definition_records),
            "records": definition_records,
        },
    )
    write_json(
        output_dir / "term_alias_registry_audited_v1.json",
        {
            "generated_at_utc": now_utc(),
            "term_alias_count": len(term_alias_records),
            "records": term_alias_records,
        },
    )
    write_json(
        output_dir / "learner_query_normalization_lexicon_audited_v1.json",
        {
            "generated_at_utc": now_utc(),
            "learner_lexicon_count": len(learner_records),
            "records": learner_records,
        },
    )
    write_json(
        output_dir / "sentence_role_registry_audited_v1.json",
        {
            "generated_at_utc": now_utc(),
            "sentence_count": len(sentence_entries),
            "records": sentence_entries,
        },
    )
    write_json(
        output_dir / "formula_canonical_registry_audited_v1.json",
        {
            "generated_at_utc": now_utc(),
            "formula_count": len(formula_records),
            "records": formula_records,
        },
    )


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    before_db_path = resolve_project_path(args.before_db_path)
    output_dir = resolve_project_path(args.output_dir)
    doc_path = resolve_project_path(args.doc_path)

    definition_before_confidence, formula_before_confidence = load_before_confidence_maps(before_db_path)

    before_conn = sqlite3.connect(before_db_path)
    before_conn.row_factory = sqlite3.Row
    try:
        summary_before = build_snapshot_summary(before_conn)
    finally:
        before_conn.close()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows_by_table = load_source_rows(conn)
        sentence_entries, sentence_summary = build_sentence_role_registry(rows_by_table)
        definition_records = build_definition_records(rows_by_table, sentence_entries)
        definition_records = apply_definition_refinements(definition_records)
        term_alias_records = build_term_alias_records(definition_records)
        learner_records = build_learner_lexicon_records(definition_records, term_alias_records)

        create_schema(conn)
        insert_records(conn, definition_records, term_alias_records, learner_records, sentence_entries)
        apply_formula_refinements(conn)

        summary_after = build_snapshot_summary(conn)
        formula_summary = build_formula_risk_summary(conn)

        definition_records = fetch_definition_records(conn)
        formula_records = fetch_formula_records(conn)
        summary_payload = build_summary_payload(
            definition_records,
            term_alias_records,
            learner_records,
            sentence_summary,
            formula_summary,
        )

        definition_audits = build_definition_audit_records(
            definition_records,
            sentence_entries,
            rows_by_table,
            definition_before_confidence,
        )
        review_only_audits = build_review_only_audit_records(
            definition_records,
            sentence_entries,
            rows_by_table,
            definition_before_confidence,
        )
        formula_audits = build_formula_audit_records(conn, formula_records, formula_before_confidence)
        ledger_payload = build_ledger_payload(definition_audits, formula_audits, review_only_audits)

        output_dir.mkdir(parents=True, exist_ok=True)
        write_json(output_dir / "object_audit_ledger_v1.json", ledger_payload)
        write_json(output_dir / "definition_term_registry_v2_audit_summary.json", summary_payload)
        write_registry_artifacts(
            output_dir,
            definition_records,
            term_alias_records,
            learner_records,
            sentence_entries,
            formula_records,
        )
        write_markdown_docs(
            doc_path,
            output_dir,
            definition_audits,
            formula_audits,
            review_only_audits,
            ledger_payload,
            summary_before,
            summary_after,
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
