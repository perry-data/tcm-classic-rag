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

from backend.answers.assembler import (  # noqa: E402
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    AnswerAssembler,
    resolve_project_path,
)


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_plane_gold_audit"
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs/data_plane_gold_audit/small_gold_audit_set_v1.md"

FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
REVIEW_ONLY_OR_NOT_READY_VERDICTS = {"gold_review_only", "gold_not_ready_for_promotion"}
SAFE_VERDICTS = {"gold_safe_primary", "gold_safe_primary_but_medium"}


DEFINITION_GOLD_AUDITS: dict[str, dict[str, Any]] = {
    "下药": {
        "audit_focus": "short therapeutic-category term promoted from mixed full passage",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "“承气汤者，下药也”是自足类属句，足以支撑短问法；但原 passage 同段混有汗下风险与《金匮玉函》材料，不能升 high。",
        "gold_followup_action": "保留 safe primary + medium；后续只需防止把整段 full passage 抬入 primary。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "短词二字且来源层为 promoted_from_full_risk_layer。",
        "notes": "这是可信任但必须维持 medium 的对象，不应用 strong 数量倒推 high。",
    },
    "两感": {
        "audit_focus": "compact disease-state definition from risk-layer passage",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "“表里俱病者，谓之两感”语义闭合，canonical identity 稳定；medium 的根因只是来源层不是干净 main-only。",
        "gold_followup_action": "保持当前对象，不需要改 alias。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "来源层仍是 records_passages/full object。",
        "notes": "learner 表面词“表里两感”合理，但不应扩成更宽泛的表里病机对象。",
    },
    "代阴": {
        "audit_focus": "pulse-pattern term with inline variant note in source row",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "primary evidence text 已抽出核心定义，术语身份成立；但 source sentence 带赵本异文，作为金标准只能保留 medium。",
        "gold_followup_action": "下一轮若能保留 stripped sentence provenance，可考虑单独标注 variant-stripped primary。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "variant note 污染源句，且与结阴共段。",
        "notes": "当前不需要降级，但也不能升 high。",
    },
    "伏气": {
        "audit_focus": "support-only concept promoted from full passage",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "“冬时感寒，伏藏于经中，不即发者，谓之伏气”定义完整；medium 仅因来源来自 full/risk 层。",
        "gold_followup_action": "保持当前 safe primary；不扩大到整段伏寒解释。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "promotion source layer 不是 safe main passage。",
        "notes": "canonical term 稳定，learner alias“伏寒”需维持为辅助入口而非主对象替代。",
    },
    "内烦": {
        "audit_focus": "context-dependent symptom naming sentence",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "句子能解释“内烦”在当前条文中的含义，但强依赖“太阳病吐之”语境，因此只可作为 medium safe primary。",
        "gold_followup_action": "保留 current primary；回答层应继续携带上下文，不应泛化为独立病名。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "依赖误治/吐后上下文。",
        "notes": "不是 high；但不属于越界升格。",
    },
    "发汗药": {
        "audit_focus": "therapeutic category where current primary is explanatory rather than definitional",
        "gold_audit_verdict": "gold_needs_sentence_reselection",
        "gold_reason": "“发汗药，须温暖服者，易为发散也”说明服法与药势，不是严格回答“发汗药是什么”的类属定义。",
        "gold_followup_action": "下一轮应寻找更直接的 membership/definition sentence，或把当前对象标为 explanation-primary 而非 definition-primary。",
        "should_change_now": True,
        "recommended_change_type": "sentence_reselection",
        "main_risk_reason": "primary sentence 看起来像定义，实质是 explanation sentence。",
        "notes": "本轮只提出裁决，不直接改 registry。",
    },
    "四逆": {
        "audit_focus": "learner high-frequency symptom/syndrome term",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "“四逆者，四肢不温也”短而闭合，alias“四肢不温/手足不温”合理；medium 仅因原句来自 full/risk 层。",
        "gold_followup_action": "保持当前对象；持续防止被 formula composition 规则误伤。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "短词与方名语境相邻，容易被 formula heuristic 污染。",
        "notes": "上一轮角色修正后，该对象可作为 gold-safe-medium。",
    },
    "坏病": {
        "audit_focus": "context-heavy disease-state definition promoted from full passage",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "定义句自足且包含“为医所坏病”解释，但它的成立依赖误治上下文，因此不应升 high。",
        "gold_followup_action": "保持 medium；不要把后续“随所逆而救之”整体并入 primary。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "上下文依赖强。",
        "notes": "适合 answer primary，但不是可脱离上下文的术语词典项。",
    },
    "时行之气": {
        "audit_focus": "learner alias 时气 mapped to canonical term",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "“四时气候不正为病，谓之时行之气”定义闭合，alias“时气”有学习者价值；medium 源于原载体层。",
        "gold_followup_action": "保持当前 alias，但不要继续扩成广义疫病/时病解释对象。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "alias 较短，容易被 broad disease queries 误召回。",
        "notes": "当前 learner normalization 是合理的。",
    },
    "水结胸": {
        "audit_focus": "compound disease-state term with formula context nearby",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "主句明确把“水饮结于胸胁”命名为水结胸，定义充分；medium 是因为同段还有大柴胡汤/大陷胸汤用法语境。",
        "gold_followup_action": "保持当前 primary；formula usage 句继续留在 support/review。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "相邻方药使用句较多。",
        "notes": "不需要降级。",
    },
    "湿痹": {
        "audit_focus": "definition sentence with inline variant contamination",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "stripped primary text 可以独立解释湿痹，但原句含赵本注和一云材料，金标准上只能承认为 medium。",
        "gold_followup_action": "后续可以把 stripped sentence provenance 显式写入 registry notes。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "variant/editorial contamination in source sentence。",
        "notes": "当前不越界，但不能升 high。",
    },
    "盗汗": {
        "audit_focus": "high-frequency learner symptom term",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "“睡而汗出者，谓之盗汗”是非常干净的定义句，learner alias“睡着出汗”也合理；medium 只因来源层不是 high-safe main。",
        "gold_followup_action": "保持当前对象；可作为 learner_short 稳定样本。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "source layer medium。",
        "notes": "这是本轮金标准集中最稳的 medium 定义对象之一。",
    },
    "结阴": {
        "audit_focus": "pulse-pattern term paired with 代阴",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "命名句可独立成义，但与代阴同段且上下句是结代脉族解释，不能给 high。",
        "gold_followup_action": "保留 medium；后续如拆脉象子段，可再评估 high。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "同段多术语共现，边界不宜放宽。",
        "notes": "当前 alias“结阴脉”可保留。",
    },
    "虚烦": {
        "audit_focus": "longer explanatory definition sentence from full layer",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "句子虽长，但核心因果和命名关系完整；source layer 与病机解释混合，故维持 medium。",
        "gold_followup_action": "保持当前对象；后续可考虑拆出更短 primary + explanation support。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "definition sentence 偏长，解释与定义混合。",
        "notes": "不是降级对象，但存在后续 sentence compaction 空间。",
    },
    "阳易": {
        "audit_focus": "paired concept after ambiguous alias cleanup",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "阳易对象身份稳定，当前没有再把“阴阳易”强行归到阳易；medium 是因为同段同时定义易/阳易/阴易。",
        "gold_followup_action": "继续禁止共享 alias“阴阳易”；若要支持该问法，应建 umbrella concept 而不是映射到阳易。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "同段 pair concept 和 umbrella term 共存。",
        "notes": "当前 canonical alias 可保留。",
    },
    "阴易": {
        "audit_focus": "paired concept after ambiguous alias cleanup",
        "gold_audit_verdict": "gold_safe_primary_but_medium",
        "gold_reason": "阴易对象身份稳定，已避免与阳易共享“阴阳易”alias；medium 合理。",
        "gold_followup_action": "继续禁止共享 alias；如需恢复“阴阳易”，必须先单建 umbrella concept。",
        "should_change_now": False,
        "recommended_change_type": "none",
        "main_risk_reason": "同段 pair concept 和 umbrella term 共存。",
        "notes": "当前不需要再改。",
    },
}


FORMULA_GOLD_AUDITS: dict[str, dict[str, Any]] = {
    "乌梅丸": {
        "gold_audit_verdict": "gold_needs_span_fix",
        "gold_reason": "当前 passage 只覆盖组成开头，且带赵本“枚/个”异文；不能判为完整高置信方文。",
        "gold_followup_action": "下一轮补完整 composition span，再决定是否升 high。",
        "main_risk_reason": "composition span incomplete and editorial variant contamination。",
    },
    "旋复代赭石汤": {
        "gold_audit_verdict": "gold_needs_span_fix",
        "gold_reason": "标题和药味均含赵本无“石”字，且缺 decoction/usage span；medium 合理。",
        "gold_followup_action": "清理 canonical title display 与 composition span 后再复核。",
        "main_risk_reason": "heading and composition contain inline variant notes。",
    },
    "栀子浓朴汤": {
        "gold_audit_verdict": "gold_needs_span_fix",
        "gold_reason": "当前只有药味组成行，且多处赵本异文；可检索但不可升 high。",
        "gold_followup_action": "补煎服/用法 span 或明确 composition-only formula policy。",
        "main_risk_reason": "variant-heavy composition-only object。",
    },
    "桂枝甘草龙骨牡蛎汤": {
        "gold_audit_verdict": "gold_needs_span_fix",
        "gold_reason": "对象身份成立，但当前行只有组成且含去皮/炙异文；缺少完整方文边界证据。",
        "gold_followup_action": "补齐 span 与 variant-stripped composition display。",
        "main_risk_reason": "composition-only with editorial variants。",
    },
    "茵陈蒿汤": {
        "gold_audit_verdict": "gold_needs_span_fix",
        "gold_reason": "组成行干净度尚可，但缺少煎服/用法 span；继续 medium 更稳。",
        "gold_followup_action": "查找相邻煎服句并补 span。",
        "main_risk_reason": "missing decoction and usage span。",
    },
    "麻黄附子甘草汤": {
        "gold_audit_verdict": "gold_needs_span_fix",
        "gold_reason": "方名和组成稳定，但附子炮制处含赵本异文，且缺少后续用法边界。",
        "gold_followup_action": "补 span 并记录 variant-stripped 药味。",
        "main_risk_reason": "composition variant note and missing usage/decoction span。",
    },
}


REVIEW_ONLY_GOLD_AUDITS: dict[str, dict[str, Any]] = {
    "神丹": {
        "gold_audit_verdict": "gold_review_only",
        "gold_reason": "“神丹者，发汗之药也”有类属信息，但对象更像注释汇编中的药名训诂，缺少独立 canonical 支撑。",
        "gold_followup_action": "若后续要升格，必须找到非注释汇编层的稳定药名证据。",
        "main_risk_reason": "not learner-facing canonical primary definition。",
        "recommended_change_type": "defer",
    },
    "将军": {
        "gold_audit_verdict": "gold_review_only",
        "gold_reason": "“大黄谓之将军”偏药名别称/训诂，不应作为当前 definition family 的 safe primary。",
        "gold_followup_action": "若要支持，应先建立药名别称对象层，而不是放入 general definition safe primary。",
        "main_risk_reason": "drug nickname rather than primary concept definition。",
        "recommended_change_type": "defer",
    },
    "两阳": {
        "gold_audit_verdict": "gold_not_ready_for_promotion",
        "gold_reason": "“风与火气，谓之两阳”必须依赖后续病机展开；单句对普通学习者不够自足。",
        "gold_followup_action": "下一轮需要一组病机解释 support object，而不是只升格命名句。",
        "main_risk_reason": "context-dependent pathology phrase。",
        "recommended_change_type": "defer",
    },
    "胆瘅": {
        "gold_audit_verdict": "gold_review_only",
        "gold_reason": "核心句来自《内经》曰式 commentarial citation；当前降级正确，不能恢复 safe primary。",
        "gold_followup_action": "建议清理 review-only 对象上的 learner aliases“口苦病/胆瘅病”，防止未来 runtime 误启用。",
        "main_risk_reason": "commentary-dependent definition sentence。",
        "recommended_change_type": "alias_cleanup",
    },
}


REGRESSION_QUERIES: tuple[dict[str, Any], ...] = (
    {"category": "formula", "query": "乌梅丸方的条文是什么？"},
    {"category": "formula", "query": "旋复代赭石汤方的条文是什么？"},
    {"category": "formula", "query": "栀子浓朴汤方的条文是什么？"},
    {"category": "formula", "query": "桂枝甘草龙骨牡蛎汤方的条文是什么？"},
    {"category": "formula", "query": "茵陈蒿汤方的条文是什么？"},
    {"category": "formula", "query": "麻黄附子甘草汤方的条文是什么？"},
    {"category": "formula", "query": "桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？"},
    {"category": "formula", "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？"},
    {"category": "definition", "query": "什么是下药", "target_concept": "下药"},
    {"category": "definition", "query": "什么是两感", "target_concept": "两感"},
    {"category": "definition", "query": "什么是四逆", "target_concept": "四逆"},
    {"category": "definition", "query": "什么是发汗药", "target_concept": "发汗药"},
    {"category": "definition", "query": "什么是湿痹", "target_concept": "湿痹"},
    {"category": "definition", "query": "什么是结阴", "target_concept": "结阴"},
    {"category": "definition", "query": "什么是阳易", "target_concept": "阳易"},
    {"category": "definition", "query": "什么是内烦", "target_concept": "内烦"},
    {"category": "learner_short", "query": "泻下药是什么意思", "target_concept": "下药"},
    {"category": "learner_short", "query": "表里两感是什么意思", "target_concept": "两感"},
    {"category": "learner_short", "query": "四肢不温是什么", "target_concept": "四逆"},
    {"category": "learner_short", "query": "睡着出汗是什么意思", "target_concept": "盗汗"},
    {"category": "learner_short", "query": "时气是什么意思", "target_concept": "时行之气"},
    {"category": "learner_short", "query": "水饮结胸是什么意思", "target_concept": "水结胸"},
    {"category": "learner_short", "query": "阴阳易是什么意思"},
    {"category": "learner_short", "query": "口苦病是什么意思", "target_concept": "胆瘅"},
    {"category": "review_only_boundary", "query": "神丹是什么意思", "target_concept": "神丹"},
    {"category": "review_only_boundary", "query": "将军是什么意思", "target_concept": "将军"},
    {"category": "review_only_boundary", "query": "两阳是什么意思", "target_concept": "两阳"},
    {"category": "review_only_boundary", "query": "什么是胆瘅", "target_concept": "胆瘅"},
    {"category": "review_only_boundary", "query": "口苦病是什么意思", "target_concept": "胆瘅"},
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build small gold audit set v1.")
    parser.add_argument("--db", default=str(resolve_project_path(DEFAULT_DB_PATH)))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--doc-path", default=str(DEFAULT_DOC_PATH))
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json_array(value: str | None) -> list[Any]:
    if not value:
        return []
    return json.loads(value)


def compact(value: str) -> str:
    return "".join(ch for ch in value if not ch.isspace() and ch not in "。，；：、,.；;:「」\"“”")


def fetch_one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def fetch_source_text(conn: sqlite3.Connection, passage_id: str) -> tuple[str, str]:
    for table in ("records_main_passages", "records_passages", "records_annotations"):
        row = fetch_one(conn, f"select text from {table} where passage_id = ? limit 1", (passage_id,))
        if row:
            return table, str(row["text"])
    return "", ""


def find_sentence_role(conn: sqlite3.Connection, passage_id: str, evidence_text: str) -> str:
    rows = conn.execute(
        """
        select sentence_text, primary_role
        from sentence_role_registry
        where passage_id = ?
        order by case source_table when 'records_main_passages' then 0 when 'records_passages' then 1 else 2 end,
                 sentence_index
        """,
        (passage_id,),
    ).fetchall()
    needle = compact(evidence_text)
    for row in rows:
        if needle and needle in compact(str(row["sentence_text"])):
            return str(row["primary_role"])
    return str(rows[0]["primary_role"]) if rows else ""


def build_definition_record(conn: sqlite3.Connection, canonical_name: str, audit: dict[str, Any]) -> dict[str, Any]:
    row = fetch_one(
        conn,
        "select * from definition_term_registry where canonical_term = ?",
        (canonical_name,),
    )
    if row is None:
        raise RuntimeError(f"Missing definition object: {canonical_name}")
    sentence_role = find_sentence_role(conn, row["primary_support_passage_id"], row["primary_evidence_text"])
    return {
        "object_type": "definition_term",
        "object_id": row["concept_id"],
        "canonical_name": canonical_name,
        "current_status": row["promotion_state"],
        "source_confidence_before": row["source_confidence"],
        "promotion_state_before": row["promotion_state"],
        "primary_support_passage_id": row["primary_support_passage_id"],
        "primary_source_table": row["primary_source_table"],
        "promotion_source_layer": row["promotion_source_layer"],
        "primary_evidence_text": row["primary_evidence_text"],
        "sentence_primary_role": sentence_role,
        "main_risk_reason": audit["main_risk_reason"],
        "audit_focus": audit["audit_focus"],
        "gold_audit_verdict": audit["gold_audit_verdict"],
        "gold_reason": audit["gold_reason"],
        "gold_followup_action": audit["gold_followup_action"],
        "should_change_now": audit["should_change_now"],
        "recommended_change_type": audit["recommended_change_type"],
        "notes": audit["notes"],
    }


def build_formula_record(conn: sqlite3.Connection, canonical_name: str, audit: dict[str, Any]) -> dict[str, Any]:
    row = fetch_one(
        conn,
        "select * from formula_canonical_registry where canonical_name = ?",
        (canonical_name,),
    )
    if row is None:
        raise RuntimeError(f"Missing formula object: {canonical_name}")
    source_table, text = fetch_source_text(conn, row["primary_formula_passage_id"])
    sentence_role = find_sentence_role(conn, row["primary_formula_passage_id"], text)
    return {
        "object_type": "formula",
        "object_id": row["formula_id"],
        "canonical_name": canonical_name,
        "current_status": row["source_confidence"],
        "source_confidence_before": row["source_confidence"],
        "promotion_state_before": "retrieval_ready_formula",
        "primary_support_passage_id": row["primary_formula_passage_id"],
        "primary_source_table": source_table,
        "promotion_source_layer": "retrieval_ready_formula_view",
        "primary_evidence_text": text,
        "sentence_primary_role": sentence_role or "formula_composition_sentence",
        "main_risk_reason": audit["main_risk_reason"],
        "audit_focus": "remaining formula medium object",
        "gold_audit_verdict": audit["gold_audit_verdict"],
        "gold_reason": audit["gold_reason"],
        "gold_followup_action": audit["gold_followup_action"],
        "should_change_now": False,
        "recommended_change_type": "span_fix",
        "notes": "本轮仅裁决，不直接补 formula span。",
    }


def build_review_only_record(conn: sqlite3.Connection, canonical_name: str, audit: dict[str, Any]) -> dict[str, Any]:
    row = fetch_one(
        conn,
        "select * from definition_term_registry where canonical_term = ?",
        (canonical_name,),
    )
    if row is None:
        raise RuntimeError(f"Missing review-only object: {canonical_name}")
    sentence_role = find_sentence_role(conn, row["primary_support_passage_id"], row["primary_evidence_text"])
    recommended = audit.get("recommended_change_type", "defer")
    return {
        "object_type": "review_only_term",
        "object_id": row["concept_id"],
        "canonical_name": canonical_name,
        "current_status": row["promotion_state"],
        "source_confidence_before": row["source_confidence"],
        "promotion_state_before": row["promotion_state"],
        "primary_support_passage_id": row["primary_support_passage_id"],
        "primary_source_table": row["primary_source_table"],
        "promotion_source_layer": row["promotion_source_layer"],
        "primary_evidence_text": row["primary_evidence_text"],
        "sentence_primary_role": sentence_role,
        "main_risk_reason": audit["main_risk_reason"],
        "audit_focus": "review-only boundary object",
        "gold_audit_verdict": audit["gold_audit_verdict"],
        "gold_reason": audit["gold_reason"],
        "gold_followup_action": audit["gold_followup_action"],
        "should_change_now": recommended != "defer",
        "recommended_change_type": recommended,
        "notes": row["review_only_reason"] or row["notes"],
    }


def make_assembler(db_path: Path) -> AnswerAssembler:
    return AnswerAssembler(
        db_path=db_path,
        policy_path=resolve_project_path(DEFAULT_POLICY_PATH),
        embed_model=DEFAULT_EMBED_MODEL,
        rerank_model=DEFAULT_RERANK_MODEL,
        cache_dir=resolve_project_path(DEFAULT_CACHE_DIR),
        dense_chunks_index=resolve_project_path(DEFAULT_DENSE_CHUNKS_INDEX),
        dense_chunks_meta=resolve_project_path(DEFAULT_DENSE_CHUNKS_META),
        dense_main_index=resolve_project_path(DEFAULT_DENSE_MAIN_INDEX),
        dense_main_meta=resolve_project_path(DEFAULT_DENSE_MAIN_META),
    )


def primary_forbidden_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for item in payload.get("primary_evidence") or []:
        record_id = str(item.get("record_id") or "")
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES or record_id.startswith("full:passages:"):
            out.append({"record_id": item.get("record_id"), "record_type": item.get("record_type")})
    return out


def concept_ids_by_name(ledger: list[dict[str, Any]]) -> dict[str, str]:
    return {row["canonical_name"]: row["object_id"] for row in ledger if row["object_type"] != "formula"}


def run_regression(db_path: Path, ledger: list[dict[str, Any]]) -> dict[str, Any]:
    verdict_by_id = {row["object_id"]: row["gold_audit_verdict"] for row in ledger}
    ids_by_name = concept_ids_by_name(ledger)
    assembler = make_assembler(db_path)
    rows: list[dict[str, Any]] = []
    try:
        for item in REGRESSION_QUERIES:
            query = item["query"]
            retrieval = assembler.engine.retrieve(query)
            payload = assembler.assemble(query)
            raw_top = retrieval.get("raw_candidates") or []
            primary_ids = [str(row.get("record_id") or "") for row in payload.get("primary_evidence") or []]
            primary_concept_ids = [
                record_id.rsplit(":", 1)[-1] for record_id in primary_ids if record_id.startswith("safe:definition_terms:")
            ]
            target_name = item.get("target_concept")
            target_id = ids_by_name.get(target_name or "")
            target_verdict = verdict_by_id.get(target_id or "")
            target_hit = bool(target_id and target_id in primary_concept_ids)
            review_only_conflicts = [
                cid
                for cid in primary_concept_ids
                if verdict_by_id.get(cid) in REVIEW_ONLY_OR_NOT_READY_VERDICTS
            ]
            rows.append(
                {
                    "category": item["category"],
                    "query": query,
                    "answer_mode": payload.get("answer_mode"),
                    "primary_ids": primary_ids,
                    "primary_record_types": [
                        row.get("record_type") for row in payload.get("primary_evidence") or []
                    ],
                    "primary_forbidden_items": primary_forbidden_items(payload),
                    "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
                    "term_normalization": retrieval.get("query_request", {}).get("term_normalization") or {},
                    "formula_bad_anchor_top5_count": sum(
                        1 for row in raw_top[:5] if row.get("topic_consistency") in BAD_FORMULA_TOPICS
                    ),
                    "target_concept": target_name,
                    "target_concept_id": target_id,
                    "target_gold_verdict": target_verdict,
                    "target_definition_primary_hit": target_hit,
                    "review_only_or_not_ready_definition_primary_conflicts": review_only_conflicts,
                    "gold_safe_primary_expected_hit": target_verdict in SAFE_VERDICTS,
                    "gold_safe_primary_missed": target_verdict in SAFE_VERDICTS and not target_hit,
                }
            )
    finally:
        assembler.close()

    category_counts: dict[str, dict[str, int]] = {}
    for category in sorted({row["category"] for row in rows}):
        category_counts[category] = dict(
            sorted(Counter(row["answer_mode"] for row in rows if row["category"] == category).items())
        )
    return {
        "rows": rows,
        "summary": {
            "query_count": len(rows),
            "mode_counts": dict(sorted(Counter(row["answer_mode"] for row in rows).items())),
            "category_mode_counts": category_counts,
            "forbidden_primary_total": sum(len(row["primary_forbidden_items"]) for row in rows),
            "formula_query_count": sum(1 for row in rows if row["category"] == "formula"),
            "formula_strong_count": sum(
                1 for row in rows if row["category"] == "formula" and row["answer_mode"] == "strong"
            ),
            "formula_bad_anchor_top5_total": sum(
                row["formula_bad_anchor_top5_count"] for row in rows if row["category"] == "formula"
            ),
            "review_only_or_not_ready_definition_primary_conflict_total": sum(
                len(row["review_only_or_not_ready_definition_primary_conflicts"]) for row in rows
            ),
            "gold_safe_primary_expected_count": sum(
                1 for row in rows if row["gold_safe_primary_expected_hit"]
            ),
            "gold_safe_primary_hit_count": sum(
                1
                for row in rows
                if row["gold_safe_primary_expected_hit"] and row["target_definition_primary_hit"]
            ),
            "gold_safe_primary_missed_count": sum(
                1 for row in rows if row["gold_safe_primary_missed"]
            ),
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_ledger_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Small Gold Audit Ledger v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- object_count: `{payload['summary']['object_count']}`",
        f"- verdict_counts: `{json.dumps(payload['summary']['verdict_counts'], ensure_ascii=False)}`",
        f"- recommended_change_counts: `{json.dumps(payload['summary']['recommended_change_counts'], ensure_ascii=False)}`",
        "",
        "| object_type | canonical_name | source_confidence | verdict | should_change_now | recommended_change_type | primary_support_passage_id | gold_reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["records"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["object_type"],
                    row["canonical_name"],
                    row["source_confidence_before"],
                    row["gold_audit_verdict"],
                    str(row["should_change_now"]).lower(),
                    row["recommended_change_type"],
                    row["primary_support_passage_id"],
                    row["gold_reason"].replace("|", "／"),
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_set_doc(path: Path, audit_set: dict[str, Any], ledger: dict[str, Any], regression: dict[str, Any]) -> None:
    trust = [row for row in ledger["records"] if row["gold_audit_verdict"] in SAFE_VERDICTS]
    fixable = [
        row
        for row in ledger["records"]
        if row["recommended_change_type"] in {"confidence_adjustment", "promotion_state_adjustment", "alias_cleanup", "sentence_reselection", "span_fix"}
    ]
    conservative = [
        row
        for row in ledger["records"]
        if row["gold_audit_verdict"] in REVIEW_ONLY_OR_NOT_READY_VERDICTS
    ]
    lines = [
        "# Small Gold Audit Set v1",
        "",
        "## Scope",
        "",
        f"- generated_at_utc: `{audit_set['generated_at_utc']}`",
        f"- total objects: `{audit_set['summary']['object_count']}`",
        f"- definition medium objects: `{audit_set['summary']['definition_medium_count']}`",
        f"- formula medium objects: `{audit_set['summary']['formula_medium_count']}`",
        f"- review-only boundary objects: `{audit_set['summary']['review_only_count']}`",
        "",
        "## Verdict Counts",
        "",
        f"- `{json.dumps(ledger['summary']['verdict_counts'], ensure_ascii=False)}`",
        "",
        "## Table 1: 当前可直接信任的对象",
        "",
        "| canonical_name | object_type | verdict | reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in trust:
        lines.append(
            f"| {row['canonical_name']} | {row['object_type']} | {row['gold_audit_verdict']} | {row['gold_reason'].replace('|', '／')} |"
        )
    lines.extend(
        [
            "",
            "## Table 2: 当前不能直接信任但可修的对象",
            "",
            "| canonical_name | object_type | recommended_change_type | followup |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in fixable:
        lines.append(
            f"| {row['canonical_name']} | {row['object_type']} | {row['recommended_change_type']} | {row['gold_followup_action'].replace('|', '／')} |"
        )
    lines.extend(
        [
            "",
            "## Table 3: 当前应明确保守的对象",
            "",
            "| canonical_name | verdict | reason | followup |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in conservative:
        lines.append(
            f"| {row['canonical_name']} | {row['gold_audit_verdict']} | {row['gold_reason'].replace('|', '／')} | {row['gold_followup_action'].replace('|', '／')} |"
        )
    lines.extend(
        [
            "",
            "## Regression Summary",
            "",
            f"- forbidden primary total: `{regression['summary']['forbidden_primary_total']}`",
            f"- formula strong: `{regression['summary']['formula_strong_count']} / {regression['summary']['formula_query_count']}`",
            f"- formula bad anchors top5 total: `{regression['summary']['formula_bad_anchor_top5_total']}`",
            f"- review-only / not-ready definition primary conflicts: `{regression['summary']['review_only_or_not_ready_definition_primary_conflict_total']}`",
            f"- gold safe primary hits: `{regression['summary']['gold_safe_primary_hit_count']} / {regression['summary']['gold_safe_primary_expected_count']}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_regression_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Small Gold Audit Regression v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- mode_counts: `{json.dumps(payload['summary']['mode_counts'], ensure_ascii=False)}`",
        f"- category_mode_counts: `{json.dumps(payload['summary']['category_mode_counts'], ensure_ascii=False)}`",
        f"- forbidden primary total: `{payload['summary']['forbidden_primary_total']}`",
        f"- formula strong: `{payload['summary']['formula_strong_count']} / {payload['summary']['formula_query_count']}`",
        f"- formula bad anchors top5 total: `{payload['summary']['formula_bad_anchor_top5_total']}`",
        f"- review-only / not-ready definition primary conflicts: `{payload['summary']['review_only_or_not_ready_definition_primary_conflict_total']}`",
        f"- gold safe primary hits: `{payload['summary']['gold_safe_primary_hit_count']} / {payload['summary']['gold_safe_primary_expected_count']}`",
        "",
        "| category | query | answer_mode | focus | target | verdict | target_hit | primary_ids |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        primary = "<br>".join(row["primary_ids"]) or "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["category"],
                    row["query"],
                    str(row["answer_mode"]),
                    str(row["query_focus_source"]),
                    str(row.get("target_concept") or ""),
                    str(row.get("target_gold_verdict") or ""),
                    str(row["target_definition_primary_hit"]).lower(),
                    primary,
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fix_recommendations(path: Path, ledger: list[dict[str, Any]]) -> None:
    rows = [row for row in ledger if row["recommended_change_type"] != "none"]
    lines = [
        "# Gold Audit Minimal Fix Recommendations v1",
        "",
        "本文件只记录 small gold audit v1 的最小修正建议；本轮未直接批量修改 registry。",
        "",
        "| canonical_name | recommended_change_type | should_change_now | recommendation |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['canonical_name']} | {row['recommended_change_type']} | {str(row['should_change_now']).lower()} | {row['gold_followup_action'].replace('|', '／')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    db_path = Path(args.db).resolve()
    output_dir = Path(args.output_dir).resolve()
    doc_path = Path(args.doc_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        records: list[dict[str, Any]] = []
        for name, audit in DEFINITION_GOLD_AUDITS.items():
            records.append(build_definition_record(conn, name, audit))
        for name, audit in FORMULA_GOLD_AUDITS.items():
            records.append(build_formula_record(conn, name, audit))
        for name, audit in REVIEW_ONLY_GOLD_AUDITS.items():
            records.append(build_review_only_record(conn, name, audit))
    finally:
        conn.close()

    generated = now_utc()
    set_payload = {
        "generated_at_utc": generated,
        "name": "small_gold_audit_set_v1",
        "selection_policy": {
            "definition_medium": "关键 learner 高频、support-only 升格、risk-layer promotion、上下文/编校/alias 边界争议对象。",
            "formula_medium": "当前 formula_canonical_registry 中 source_confidence=medium 的全部剩余对象。",
            "review_only": "当前 definition_term_registry 中 source_confidence=review_only 的全部边界对象。",
        },
        "summary": {
            "object_count": len(records),
            "definition_medium_count": sum(1 for row in records if row["object_type"] == "definition_term"),
            "formula_medium_count": sum(1 for row in records if row["object_type"] == "formula"),
            "review_only_count": sum(1 for row in records if row["object_type"] == "review_only_term"),
        },
        "objects": [
            {
                "object_type": row["object_type"],
                "object_id": row["object_id"],
                "canonical_name": row["canonical_name"],
                "audit_focus": row["audit_focus"],
            }
            for row in records
        ],
    }
    ledger_payload = {
        "generated_at_utc": generated,
        "summary": {
            "object_count": len(records),
            "verdict_counts": dict(sorted(Counter(row["gold_audit_verdict"] for row in records).items())),
            "recommended_change_counts": dict(
                sorted(Counter(row["recommended_change_type"] for row in records).items())
            ),
            "should_change_now_count": sum(1 for row in records if row["should_change_now"]),
        },
        "records": records,
    }
    regression_payload = run_regression(db_path, records)
    regression_payload["generated_at_utc"] = generated
    regression_payload["db_path"] = str(db_path)

    write_json(output_dir / "small_gold_audit_set_v1.json", set_payload)
    write_json(output_dir / "small_gold_audit_ledger_v1.json", ledger_payload)
    write_ledger_md(output_dir / "small_gold_audit_ledger_v1.md", ledger_payload)
    write_json(output_dir / "small_gold_audit_regression_v1.json", regression_payload)
    write_regression_md(output_dir / "small_gold_audit_regression_v1.md", regression_payload)
    write_fix_recommendations(output_dir / "gold_audit_minimal_fix_recommendations_v1.md", records)
    write_set_doc(doc_path, set_payload, ledger_payload, regression_payload)


if __name__ == "__main__":
    main()
