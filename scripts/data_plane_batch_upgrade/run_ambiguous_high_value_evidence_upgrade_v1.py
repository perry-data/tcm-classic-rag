#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_ambiguous_high_value_evidence_upgrade_v1.db"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_batch_upgrade"
DEFAULT_DOC_DIR = "docs/data_plane_batch_upgrade"
RUN_ID = "ambiguous_high_value_evidence_upgrade_v1"
SOURCE = RUN_ID
PUNCTUATION_STRIP = "，。；：:、 “”\"'「」"
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？；])")


@dataclass(frozen=True)
class EvidenceCandidate:
    candidate_id: str
    category: str
    canonical_term: str
    concept_type: str
    source_table: str
    passage_id: str
    sentence_hint: str
    evidence_type: str
    candidate_priority: str
    classification_reason: str
    query: str
    aliases: tuple[str, ...] = ()
    risky_aliases: tuple[str, ...] = ()
    ambiguous_aliases: tuple[str, ...] = ()
    definition_passage_ids: tuple[str, ...] = ()
    explanation_passage_ids: tuple[str, ...] = ()
    membership_passage_ids: tuple[str, ...] = ()
    source_confidence: str = "medium"
    promotion_state: str = "safe_primary"
    promotion_reason: str = "clean sentence promoted from ambiguous/full-risk/B layer"
    review_only_reason: str = ""
    sentence_role: str = "definition_sentence"
    notes: str = ""
    rejection_reason: str = ""
    future_condition: str = ""
    risk_source: str = ""
    concept_id: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", stable_id("AHV", compact_text(self.canonical_term)))


def stable_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def compact_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def strip_inline_notes(text: str | None) -> str:
    if not text:
        return ""
    cleaned = compact_whitespace(text)
    cleaned = re.sub(r"(?:赵本|医统本|汪本|成本|千金|玉函)+(?:有|无|作)「[^」]+」字?", "", cleaned)
    cleaned = re.sub(r"(?:赵本|医统本|汪本|成本)+(?:并)?有「[^」]+」字?", "", cleaned)
    cleaned = re.sub(r"(?:赵本|医统本|汪本|成本)注：?「[^」]+」", "", cleaned)
    cleaned = re.sub(r"《[^》]{1,16}》曰：?", "", cleaned)
    return compact_whitespace(cleaned).strip(PUNCTUATION_STRIP)


def split_sentences(text: str) -> list[str]:
    normalized = compact_whitespace(text)
    if not normalized:
        return []
    pieces = SENTENCE_SPLIT_PATTERN.split(normalized)
    return [piece.strip() for piece in pieces if piece.strip()] or [normalized]


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def candidate(
    category: str,
    canonical_term: str,
    concept_type: str,
    source_table: str,
    passage_id: str,
    sentence_hint: str,
    evidence_type: str,
    candidate_priority: str,
    classification_reason: str,
    query: str,
    *,
    aliases: Iterable[str] = (),
    risky_aliases: Iterable[str] = (),
    ambiguous_aliases: Iterable[str] = (),
    definition_passage_ids: Iterable[str] = (),
    explanation_passage_ids: Iterable[str] = (),
    membership_passage_ids: Iterable[str] = (),
    source_confidence: str = "medium",
    promotion_state: str = "safe_primary",
    promotion_reason: str = "clean sentence promoted from ambiguous/full-risk/B layer",
    review_only_reason: str = "",
    sentence_role: str = "definition_sentence",
    notes: str = "",
    rejection_reason: str = "",
    future_condition: str = "",
    risk_source: str = "",
) -> EvidenceCandidate:
    prefix = {"A": "AHV-A", "B": "AHV-B", "C": "AHV-C"}[category]
    return EvidenceCandidate(
        candidate_id=stable_id(prefix, f"{category}|{canonical_term}|{source_table}|{passage_id}"),
        category=category,
        canonical_term=canonical_term,
        concept_type=concept_type,
        source_table=source_table,
        passage_id=passage_id,
        sentence_hint=sentence_hint,
        evidence_type=evidence_type,
        candidate_priority=candidate_priority,
        classification_reason=classification_reason,
        query=query,
        aliases=tuple(aliases),
        risky_aliases=tuple(risky_aliases),
        ambiguous_aliases=tuple(ambiguous_aliases),
        definition_passage_ids=tuple(definition_passage_ids),
        explanation_passage_ids=tuple(explanation_passage_ids),
        membership_passage_ids=tuple(membership_passage_ids),
        source_confidence=source_confidence,
        promotion_state=promotion_state,
        promotion_reason=promotion_reason,
        review_only_reason=review_only_reason,
        sentence_role=sentence_role,
        notes=notes,
        rejection_reason=rejection_reason,
        future_condition=future_condition,
        risk_source=risk_source,
    )


CANDIDATES: tuple[EvidenceCandidate, ...] = (
    candidate(
        "A",
        "太阳病",
        "six_channel_disease_term",
        "records_main_passages",
        "ZJSHL-CH-008-P-0191",
        "太阳之为病，脉浮，头项强痛而恶寒",
        "exact_term_definition",
        "P0",
        "B 级 main passage 有闭合的“X之为病”定义句，可切成独立 safe concept object。",
        "何谓太阳病",
        aliases=("太阳之为病",),
        definition_passage_ids=("ZJSHL-CH-008-P-0191",),
        source_confidence="medium",
        notes="六经提纲类对象只升格闭合句，不把整章太阳病条文整体放进 primary。",
    ),
    candidate(
        "A",
        "伤寒",
        "disease_state_term",
        "records_passages",
        "ZJSHL-CH-008-P-0195",
        "必恶寒，体痛，呕逆，脉阴阳俱紧者，名曰伤寒",
        "exact_term_definition",
        "P0",
        "full/risk 层中有明确命名句，普通学习者高频会问“伤寒是什么”。",
        "伤寒是什么",
        aliases=("伤寒病",),
        definition_passage_ids=("ZJSHL-CH-008-P-0195", "ZJSHL-CH-006-P-0007"),
        explanation_passage_ids=("ZJSHL-CH-008-P-0196",),
        notes="只抽命名句，避免把伤寒总论长段恢复为 safe main。",
    ),
    candidate(
        "A",
        "温病",
        "seasonal_disease_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-006-P-0017",
        "温者，冬时感寒，至春发者是也",
        "exact_term_definition",
        "P0",
        "ambiguous 层里有“X者……是也”的短定义，句子可独立理解。",
        "温病是什么意思",
        aliases=("春温",),
        definition_passage_ids=("ZJSHL-CH-006-P-0017", "ZJSHL-CH-006-P-0012"),
        source_confidence="medium",
        notes="来自 ambiguous risk registry，升格对象为 medium safe primary，raw ambiguous 不进 primary。",
    ),
    candidate(
        "A",
        "暑病",
        "seasonal_disease_term",
        "records_passages",
        "ZJSHL-CH-006-P-0012",
        "暑病者，热极重于温也",
        "exact_term_definition",
        "P0",
        "full passage 中有短定义句，术语锚点明确。",
        "暑病是什么意思",
        aliases=("暑病者",),
        definition_passage_ids=("ZJSHL-CH-006-P-0012",),
        notes="只取“暑病者”句，不把温暑病长论作为主证据。",
    ),
    candidate(
        "A",
        "冬温",
        "seasonal_disease_term",
        "records_passages",
        "ZJSHL-CH-006-P-0020",
        "其冬有非节之暖者，名曰冬温",
        "exact_term_definition",
        "P0",
        "“名曰冬温”结构明确，适合 learner-facing definition query。",
        "冬温是什么",
        aliases=("冬温病",),
        definition_passage_ids=("ZJSHL-CH-006-P-0020",),
        notes="非节之暖为定义核心，后续证治差异不进入 primary。",
    ),
    candidate(
        "A",
        "时行寒疫",
        "seasonal_disease_term",
        "records_passages",
        "ZJSHL-CH-006-P-0024",
        "从春分以后，至秋分节前，天有暴寒者，皆为时行寒疫也",
        "exact_term_definition",
        "P1",
        "学习者可能追问时行寒疫含义，句子有类属判断且可独立成义。",
        "时行寒疫是什么",
        aliases=("寒疫",),
        definition_passage_ids=("ZJSHL-CH-006-P-0024",),
        notes="保留为中等置信 safe object，不扩展到疫气全段。",
    ),
    candidate(
        "A",
        "刚痓",
        "disease_state_term",
        "records_main_passages",
        "ZJSHL-CH-007-P-0157",
        "太阳病，发热无汗，反恶寒者，名曰刚痓",
        "exact_term_definition",
        "P0",
        "B 级 main passage 的命名句完整，且属于常见学习者术语。",
        "刚痓是什么",
        aliases=("刚痉",),
        ambiguous_aliases=("痉",),
        definition_passage_ids=("ZJSHL-CH-007-P-0157",),
        explanation_passage_ids=("ZJSHL-CH-007-P-0165",),
        notes="保留“痉”作 inactive ambiguous alias，不直接 runtime normalization。",
    ),
    candidate(
        "A",
        "柔痓",
        "disease_state_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-007-P-0160",
        "表虚感湿，故曰柔痓",
        "exact_term_explanation",
        "P1",
        "ambiguous 层中解释句短且术语锚点清楚，可作为刚痓的配套概念。",
        "柔痓是什么意思",
        aliases=("柔痉",),
        ambiguous_aliases=("痉",),
        definition_passage_ids=("ZJSHL-CH-007-P-0160",),
        notes="medium safe object，只抽解释句，保留原 ambiguous passage 的风险边界。",
    ),
    candidate(
        "A",
        "痓病",
        "disease_state_term",
        "records_passages",
        "ZJSHL-CH-007-P-0166",
        "背反张者，痓病也",
        "exact_term_definition",
        "P1",
        "痓病作为 learner 短问法高价值对象，句子给出症状闭合锚点。",
        "痓病是什么",
        aliases=("痉病",),
        ambiguous_aliases=("痓",),
        definition_passage_ids=("ZJSHL-CH-007-P-0166", "ZJSHL-CH-007-P-0161"),
        notes="不启用单字“痓”归一化，只启用痓病/痉病。",
    ),
    candidate(
        "A",
        "结脉",
        "pulse_pattern_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-003-P-0029",
        "时有一止者，阴阳之气不得相续也",
        "exact_term_explanation",
        "P1",
        "结脉的解释句在 ambiguous 层，结合 full 层命名句可形成可审计对象。",
        "结脉是什么",
        aliases=("结脉",),
        ambiguous_aliases=("结",),
        definition_passage_ids=("ZJSHL-CH-003-P-0028",),
        explanation_passage_ids=("ZJSHL-CH-003-P-0029",),
        notes="单字“结”不进入 learner-safe alias，避免泛化到结胸/脏结等对象。",
    ),
    candidate(
        "A",
        "促脉",
        "pulse_pattern_term",
        "records_passages",
        "ZJSHL-CH-003-P-0028",
        "脉来数，时一止复来者，名曰促",
        "exact_term_definition",
        "P0",
        "命名句独立，适合作为促脉短问法对象。",
        "促脉是什么",
        ambiguous_aliases=("促",),
        definition_passage_ids=("ZJSHL-CH-003-P-0028", "ZJSHL-CH-008-P-0239"),
        notes="单字“促”只登记为 inactive ambiguous alias。",
    ),
    candidate(
        "A",
        "弦脉",
        "pulse_pattern_term",
        "records_passages",
        "ZJSHL-CH-003-P-0037",
        "脉浮而紧者，名曰弦也",
        "exact_term_definition",
        "P0",
        "“名曰弦”与后句“状如弓弦”共同构成稳定脉象对象。",
        "弦脉是什么",
        ambiguous_aliases=("弦",),
        definition_passage_ids=("ZJSHL-CH-003-P-0037",),
        explanation_passage_ids=("ZJSHL-CH-003-P-0037",),
        notes="单字“弦”不参与直接 normalization。",
    ),
    candidate(
        "A",
        "滑脉",
        "pulse_pattern_term",
        "records_passages",
        "ZJSHL-CH-004-P-0203",
        "翕奄沉，名曰滑",
        "exact_term_definition",
        "P0",
        "有命名句与后续解释句，适合脉象术语升格。",
        "滑脉是什么意思",
        ambiguous_aliases=("滑",),
        definition_passage_ids=("ZJSHL-CH-004-P-0203",),
        explanation_passage_ids=("ZJSHL-CH-004-P-0205",),
        notes="单字“滑”不直接 runtime normalization。",
    ),
    candidate(
        "A",
        "革脉",
        "pulse_pattern_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-003-P-0040",
        "寒虚相搏，此名为革",
        "exact_term_definition",
        "P0",
        "ambiguous 层里有闭合命名句，术语锚点明确但来源需保持 medium。",
        "革脉是什么",
        ambiguous_aliases=("革",),
        definition_passage_ids=("ZJSHL-CH-003-P-0040",),
        explanation_passage_ids=("ZJSHL-CH-003-P-0041",),
        notes="只升格革脉对象，妇人/男子后续病候不作为 primary 定义。",
    ),
    candidate(
        "A",
        "行尸",
        "disease_state_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-004-P-0200",
        "脉病患不病，名曰行尸",
        "exact_term_definition",
        "P0",
        "“名曰行尸”结构明确，普通学习者可能查询。",
        "行尸是什么意思",
        definition_passage_ids=("ZJSHL-CH-004-P-0200",),
        explanation_passage_ids=("ZJSHL-CH-004-P-0201",),
        notes="来自 risk registry，仅以短命名句升格为 medium safe object。",
    ),
    candidate(
        "A",
        "内虚",
        "disease_state_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-004-P-0200",
        "人病脉不病，名曰内虚",
        "exact_term_definition",
        "P0",
        "与行尸同段但概念不同，可拆成独立对象。",
        "内虚是什么意思",
        definition_passage_ids=("ZJSHL-CH-004-P-0200",),
        explanation_passage_ids=("ZJSHL-CH-004-P-0202",),
        notes="不把同段整体混为一个概念包。",
    ),
    candidate(
        "A",
        "血崩",
        "disease_state_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-004-P-0257",
        "荣盛，则其肤必疏，三焦绝经，名曰血崩",
        "exact_term_definition",
        "P0",
        "risk 层有清晰命名句，适合做可追溯概念对象。",
        "血崩是什么",
        aliases=("崩血",),
        definition_passage_ids=("ZJSHL-CH-004-P-0257",),
        explanation_passage_ids=("ZJSHL-CH-004-P-0259",),
        notes="只抽命名句，避免把三焦/荣卫长注释整体上浮。",
    ),
    candidate(
        "A",
        "霍乱",
        "disease_state_term",
        "records_passages",
        "ZJSHL-CH-016-P-0002",
        "呕吐而利，名曰霍乱",
        "exact_term_definition",
        "P0",
        "“名曰霍乱”句式干净且学习者高频。",
        "霍乱是什么",
        aliases=("吐利霍乱",),
        definition_passage_ids=("ZJSHL-CH-016-P-0002", "ZJSHL-CH-016-P-0004"),
        explanation_passage_ids=("ZJSHL-CH-016-P-0003",),
        notes="霍乱作为病名对象升格，后续证治条文不进入 primary。",
    ),
    candidate(
        "A",
        "劳复",
        "post_recovery_term",
        "records_passages",
        "ZJSHL-CH-017-P-0049",
        "伤寒新瘥，血气未平，馀热未尽，早作劳动病者，名曰劳复",
        "exact_term_definition",
        "P0",
        "有明确“病者，名曰”结构，适合 learner_short query。",
        "劳复是什么意思",
        aliases=("劳动病",),
        definition_passage_ids=("ZJSHL-CH-017-P-0049",),
        notes="只升格劳复概念，不混入食复同句的另一个概念。",
    ),
    candidate(
        "A",
        "食复",
        "post_recovery_term",
        "records_passages",
        "ZJSHL-CH-017-P-0049",
        "病热少愈而强食之，热有所藏，因其谷气留搏，两阳相合而病者，名曰食复",
        "exact_term_definition",
        "P0",
        "同段第二个命名结构可以独立切出。",
        "食复是什么意思",
        aliases=("强食复病",),
        definition_passage_ids=("ZJSHL-CH-017-P-0049",),
        notes="与劳复分开建对象，避免同段多概念互相遮挡。",
    ),
    candidate(
        "B",
        "高",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0208",
        "寸口卫气盛，名曰高",
        "exact_term_definition",
        "P0",
        "命名句清晰但术语为单字，普通问法极易误解。",
        "寸口卫气盛名曰高是什么意思",
        promotion_state="review_only",
        review_only_reason="单字术语，离开寸口/卫气上下文后歧义过大，只能 support/review。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "B",
        "章",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0210",
        "荣气盛，名曰章",
        "exact_term_definition",
        "P0",
        "命名句清晰但单字术语风险高。",
        "荣气盛名曰章是什么意思",
        promotion_state="review_only",
        review_only_reason="单字术语且依赖荣气盛上下文，不能进入 primary normalization。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "B",
        "纲",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0212",
        "高章相搏，名曰纲",
        "exact_term_definition",
        "P0",
        "命名句短，但必须依赖高/章前文。",
        "高章相搏名曰纲是什么意思",
        promotion_state="review_only",
        review_only_reason="依赖高章两个前置术语，语义不自足，暂作 support-only。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "B",
        "惵",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0214",
        "卫气弱，名曰惵",
        "exact_term_definition",
        "P0",
        "命名句干净但字形罕见，学习者短问法容易误召回。",
        "卫气弱名曰惵是什么意思",
        promotion_state="review_only",
        review_only_reason="单字罕见术语，需保留上下文核对，不能 learner-safe 归一。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "B",
        "卑",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0216",
        "荣气弱，名曰卑",
        "exact_term_definition",
        "P0",
        "命名句清楚但单字现代义强。",
        "荣气弱名曰卑是什么意思",
        promotion_state="review_only",
        review_only_reason="单字现代义强，离开荣气弱上下文容易误解。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "B",
        "损",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0218",
        "卑相搏，名曰损",
        "exact_term_definition",
        "P0",
        "有命名结构但依赖卑与后文五脏六腑虚解释。",
        "卑相搏名曰损是什么意思",
        promotion_state="review_only",
        review_only_reason="单字且依赖前后文，不作为 primary。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "B",
        "缓",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0220",
        "卫气和，名曰缓",
        "exact_term_definition",
        "P0",
        "命名句短但与一般脉缓/病缓/语义缓慢混淆。",
        "卫气和名曰缓是什么意思",
        promotion_state="review_only",
        review_only_reason="单字别名冲突多，当前只保留为 support-only。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "B",
        "迟",
        "pulse_named_state",
        "records_main_passages",
        "ZJSHL-CH-004-P-0223",
        "荣气和，名曰迟",
        "exact_term_definition",
        "P0",
        "命名句短但“迟”泛义强。",
        "荣气和名曰迟是什么意思",
        promotion_state="review_only",
        review_only_reason="单字泛义强，不能直接进入 runtime normalization。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="登记 support-only，不给 learner-safe alias。",
    ),
    candidate(
        "C",
        "动",
        "pulse_pattern_term",
        "records_passages",
        "ZJSHL-CH-003-P-0031",
        "阴阳相搏，名曰动",
        "exact_term_definition",
        "P0",
        "句式命名明显，但单字“动”与现代“动脉”及普通动词强冲突。",
        "动是什么意思",
        rejection_reason="单字术语多义风险极高，直接归一会污染现代/普通语义查询。",
        future_condition="需要建立带“动脉/动脉象”限定的专门脉象对象，并证明不会吞掉普通动词查询。",
        risk_source="single_character_alias_conflict",
    ),
    candidate(
        "C",
        "两阳",
        "pathology_term",
        "records_passages",
        "ZJSHL-CH-009-P-0276",
        "风与火气，谓之两阳",
        "exact_term_definition",
        "P0",
        "已有学习价值但强依赖火劫发汗上下文。",
        "两阳是什么意思",
        rejection_reason="概念依赖火气、风邪、发黄/衄/小便难等长链上下文，当前不能作为 learner-safe primary。",
        future_condition="需要先拆出火劫发汗语境与两阳病机层级，再做分层对象。",
        risk_source="context_dependent_pathology_chain",
    ),
    candidate(
        "C",
        "清邪中上",
        "pathology_term",
        "records_passages",
        "ZJSHL-CH-003-P-0098",
        "清邪中上，名曰洁也；浊邪中下，名曰浑也",
        "exact_term_definition",
        "P0",
        "有命名结构但同句多个互相依赖概念。",
        "清邪中上是什么意思",
        rejection_reason="清邪/浊邪/洁/浑在同一长段复合说明中交叉出现，单独抽取会误导。",
        future_condition="需要成对构建清邪/浊邪/洁/浑对象和对照视图后再考虑。",
        risk_source="multi_concept_composite_sentence",
    ),
    candidate(
        "C",
        "寒格",
        "disease_state_term",
        "records_passages",
        "ZJSHL-CH-015-P-0277",
        "食入口即吐，谓之寒格",
        "exact_term_definition",
        "P0",
        "命名句表面明确，但上下文牵涉误吐下和方证。",
        "寒格是什么意思",
        rejection_reason="该句与“更复吐下”“乾姜黄连黄芩人参汤”处置语境黏连，当前证据粒度不够干净。",
        future_condition="需要先拆治疗语境和病名定义，确认不会被方证问法误召回。",
        risk_source="formula_treatment_context_entanglement",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upgrade high-value ambiguous/full-risk definition evidence v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--before-db", default=DEFAULT_BEFORE_DB)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-dir", default=DEFAULT_DOC_DIR)
    parser.add_argument("--refresh-before", action="store_true")
    return parser.parse_args()


def fetch_source_row(conn: sqlite3.Connection, source_table: str, passage_id: str) -> dict[str, Any]:
    row = conn.execute(f"SELECT * FROM {source_table} WHERE passage_id = ?", (passage_id,)).fetchone()
    if row is None and source_table == "risk_registry_ambiguous":
        row = conn.execute("SELECT * FROM records_passages WHERE passage_id = ?", (passage_id,)).fetchone()
    if row is None:
        raise KeyError(f"missing source row {source_table}:{passage_id}")
    payload = dict(row)
    payload["source_table"] = source_table
    return payload


def sentence_for_candidate(row: dict[str, Any], hint: str) -> str:
    normalized_hint = compact_text(hint)
    for sentence in split_sentences(row.get("text") or row.get("retrieval_text") or ""):
        stripped = strip_inline_notes(sentence) or compact_whitespace(sentence)
        if normalized_hint and normalized_hint in compact_text(stripped):
            return stripped
    text = strip_inline_notes(row.get("text") or row.get("retrieval_text") or "")
    if normalized_hint and normalized_hint in compact_text(text):
        return hint
    return hint or text


def source_object_for_table(table: str, row: dict[str, Any]) -> str:
    if table == "records_main_passages":
        return "main_passages"
    if table == "records_passages":
        return "passages"
    if table == "records_annotations":
        return "annotations"
    if table == "risk_registry_ambiguous":
        return "ambiguous_passages"
    return str(row.get("source_object") or "")


def evidence_level_for_source(candidate: EvidenceCandidate, row: dict[str, Any]) -> str:
    if candidate.source_table == "risk_registry_ambiguous":
        return "C"
    return str(row.get("evidence_level") or "C")


def source_record_id_for_source(candidate: EvidenceCandidate, row: dict[str, Any]) -> str:
    if candidate.source_table == "risk_registry_ambiguous":
        return str(row.get("record_id") or f"full:ambiguous_passages:{candidate.passage_id}")
    return str(row.get("record_id") or "")


def build_definition_record(
    conn: sqlite3.Connection,
    item: EvidenceCandidate,
) -> dict[str, Any]:
    row = fetch_source_row(conn, item.source_table, item.passage_id)
    primary_sentence = sentence_for_candidate(row, item.sentence_hint)
    definition_ids = unique(item.definition_passage_ids or (item.passage_id,))
    explanation_ids = unique(item.explanation_passage_ids)
    membership_ids = unique(item.membership_passage_ids)
    source_ids = unique([item.passage_id] + definition_ids + explanation_ids + membership_ids)
    chapter_ids = unique(
        str(fetch_source_row(conn, item.source_table if pid == item.passage_id else "records_passages", pid).get("chapter_id") or "")
        if pid != item.passage_id
        else str(row.get("chapter_id") or "")
        for pid in source_ids
    )
    safe_aliases = unique(item.aliases)
    retrieval_sentences = [primary_sentence, item.canonical_term, *safe_aliases]
    for passage_id in unique(definition_ids + explanation_ids + membership_ids):
        source_row = None
        for table_name in (item.source_table, "records_main_passages", "records_passages", "risk_registry_ambiguous"):
            try:
                source_row = fetch_source_row(conn, table_name, passage_id)
                break
            except KeyError:
                continue
        if source_row is not None:
            retrieval_sentences.append(sentence_for_candidate(source_row, item.canonical_term))
    source_object = source_object_for_table(item.source_table, row)
    is_safe = 1 if item.category == "A" else 0
    return {
        "concept_id": item.concept_id,
        "canonical_term": item.canonical_term,
        "normalized_term": compact_text(item.canonical_term),
        "concept_type": item.concept_type,
        "definition_evidence_passage_ids_json": json_text(definition_ids),
        "explanation_evidence_passage_ids_json": json_text(explanation_ids),
        "membership_evidence_passage_ids_json": json_text(membership_ids),
        "primary_support_passage_id": item.passage_id,
        "primary_source_table": item.source_table,
        "primary_source_object": source_object,
        "primary_source_record_id": source_record_id_for_source(item, row),
        "primary_source_evidence_level": evidence_level_for_source(item, row),
        "source_passage_ids_json": json_text(source_ids),
        "chapter_ids_json": json_text(chapter_ids),
        "query_aliases_json": json_text(safe_aliases),
        "learner_surface_forms_json": json_text(safe_aliases if item.category == "A" else []),
        "primary_evidence_type": item.evidence_type,
        "primary_evidence_text": primary_sentence,
        "retrieval_text": "\n".join(unique(retrieval_sentences)),
        "normalized_retrieval_text": compact_text("\n".join(unique(retrieval_sentences))),
        "source_confidence": item.source_confidence,
        "promotion_state": item.promotion_state,
        "promotion_source_layer": "ambiguous_high_value_batch_safe_primary"
        if item.category == "A"
        else "ambiguous_high_value_batch_support_only",
        "promotion_reason": item.promotion_reason if item.category == "A" else "registered as support/review-only explainable object",
        "review_only_reason": item.review_only_reason,
        "notes": item.notes,
        "is_safe_primary_candidate": is_safe,
        "is_active": 1,
    }


def build_alias_records(item: EvidenceCandidate) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "alias_id": stable_id("AHV-TAL", f"{item.concept_id}|canonical|{item.canonical_term}"),
            "alias": item.canonical_term,
            "normalized_alias": compact_text(item.canonical_term),
            "concept_id": item.concept_id,
            "canonical_term": item.canonical_term,
            "alias_type": "canonical" if item.category == "A" else "review_only_support",
            "confidence": 1.0,
            "source": SOURCE,
            "notes": "canonical term alias",
            "is_active": 1,
        }
    )
    if item.category == "A":
        for alias in unique(item.aliases):
            rows.append(
                {
                    "alias_id": stable_id("AHV-TAL", f"{item.concept_id}|learner_safe|{alias}"),
                    "alias": alias,
                    "normalized_alias": compact_text(alias),
                    "concept_id": item.concept_id,
                    "canonical_term": item.canonical_term,
                    "alias_type": "learner_safe",
                    "confidence": 0.9,
                    "source": SOURCE,
                    "notes": "batch learner-safe alias",
                    "is_active": 1,
                }
            )
    for alias in unique(item.risky_aliases):
        rows.append(
            {
                "alias_id": stable_id("AHV-TAL", f"{item.concept_id}|learner_risky|{alias}"),
                "alias": alias,
                "normalized_alias": compact_text(alias),
                "concept_id": item.concept_id,
                "canonical_term": item.canonical_term,
                "alias_type": "learner_risky",
                "confidence": 0.42,
                "source": SOURCE,
                "notes": "inactive risky alias; not used for runtime normalization",
                "is_active": 0,
            }
        )
    for alias in unique(item.ambiguous_aliases):
        rows.append(
            {
                "alias_id": stable_id("AHV-TAL", f"{item.concept_id}|ambiguous|{alias}"),
                "alias": alias,
                "normalized_alias": compact_text(alias),
                "concept_id": item.concept_id,
                "canonical_term": item.canonical_term,
                "alias_type": "ambiguous",
                "confidence": 0.3,
                "source": SOURCE,
                "notes": "inactive ambiguous alias; not used for runtime normalization",
                "is_active": 0,
            }
        )
    return [row for row in rows if row["normalized_alias"]]


def build_learner_records(item: EvidenceCandidate) -> list[dict[str, Any]]:
    if item.category != "A":
        return []
    safe_surfaces = unique([item.canonical_term, *item.aliases])
    rows: list[dict[str, Any]] = []
    for surface in safe_surfaces:
        normalized = compact_text(surface)
        if len(normalized) < 2:
            continue
        rows.append(
            {
                "lexicon_id": stable_id("AHV-LQN", f"{item.concept_id}|{normalized}"),
                "entry_type": "term_surface",
                "match_mode": "contains",
                "surface_form": surface,
                "normalized_surface_form": normalized,
                "target_type": "concept_term",
                "target_id": item.concept_id,
                "target_term": item.canonical_term,
                "intent_hint": "what_is",
                "canonical_query_template": f"什么是{item.canonical_term}",
                "confidence": 1.0 if surface == item.canonical_term else 0.9,
                "source": SOURCE,
                "notes": "batch learner_safe normalization",
                "is_active": 1,
            }
        )
    return rows


def ensure_before_db(db_path: Path, before_db: Path, refresh: bool) -> None:
    before_db.parent.mkdir(parents=True, exist_ok=True)
    if refresh or not before_db.exists():
        shutil.copy2(db_path, before_db)


def insert_definition_records(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns = list(rows[0].keys())
    placeholders = ", ".join(f":{column}" for column in columns)
    assignments = ", ".join(f"{column}=excluded.{column}" for column in columns if column != "concept_id")
    sql = f"""
        INSERT INTO definition_term_registry ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(concept_id) DO UPDATE SET {assignments}
    """
    conn.executemany(sql, rows)


def insert_alias_records(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT INTO term_alias_registry (
            alias_id, alias, normalized_alias, concept_id, canonical_term, alias_type,
            confidence, source, notes, is_active
        ) VALUES (
            :alias_id, :alias, :normalized_alias, :concept_id, :canonical_term, :alias_type,
            :confidence, :source, :notes, :is_active
        )
        ON CONFLICT(alias_id) DO UPDATE SET
            alias=excluded.alias,
            normalized_alias=excluded.normalized_alias,
            concept_id=excluded.concept_id,
            canonical_term=excluded.canonical_term,
            alias_type=excluded.alias_type,
            confidence=excluded.confidence,
            source=excluded.source,
            notes=excluded.notes,
            is_active=excluded.is_active
        """,
        rows,
    )


def insert_learner_records(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT INTO learner_query_normalization_lexicon (
            lexicon_id, entry_type, match_mode, surface_form, normalized_surface_form,
            target_type, target_id, target_term, intent_hint, canonical_query_template,
            confidence, source, notes, is_active
        ) VALUES (
            :lexicon_id, :entry_type, :match_mode, :surface_form, :normalized_surface_form,
            :target_type, :target_id, :target_term, :intent_hint, :canonical_query_template,
            :confidence, :source, :notes, :is_active
        )
        ON CONFLICT(lexicon_id) DO UPDATE SET
            entry_type=excluded.entry_type,
            match_mode=excluded.match_mode,
            surface_form=excluded.surface_form,
            normalized_surface_form=excluded.normalized_surface_form,
            target_type=excluded.target_type,
            target_id=excluded.target_id,
            target_term=excluded.target_term,
            intent_hint=excluded.intent_hint,
            canonical_query_template=excluded.canonical_query_template,
            confidence=excluded.confidence,
            source=excluded.source,
            notes=excluded.notes,
            is_active=excluded.is_active
        """,
        rows,
    )


def update_sentence_role_registry(conn: sqlite3.Connection, candidates: list[EvidenceCandidate]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for item in candidates:
        row = fetch_source_row(conn, item.source_table, item.passage_id)
        sentence_text = sentence_for_candidate(row, item.sentence_hint)
        normalized_hint = compact_text(sentence_text)
        matches = [
            dict(match)
            for match in conn.execute(
                """
                SELECT *
                FROM sentence_role_registry
                WHERE source_table = ?
                  AND passage_id = ?
                ORDER BY sentence_index
                """,
                (item.source_table, item.passage_id),
            )
        ]
        selected = None
        for match in matches:
            if normalized_hint and normalized_hint in compact_text(match["sentence_text"]):
                selected = match
                break
        if selected is None and matches:
            selected = matches[0]
        if selected is None:
            continue
        tags = json.loads(selected["role_tags_json"])
        tags = unique([*tags, item.sentence_role, SOURCE])
        if item.category == "B":
            tags = unique([*tags, "review_only_support"])
        primary_role = selected["primary_role"]
        if primary_role in {"risk_sentence", "explanation_sentence"} and item.sentence_role in {
            "definition_sentence",
            "membership_sentence",
            "context_dependent_sentence",
        }:
            primary_role = item.sentence_role
        risk_label = selected["risk_label"]
        if item.category == "B":
            risk_label = "review_only"
        conn.execute(
            """
            UPDATE sentence_role_registry
            SET primary_role = ?,
                role_tags_json = ?,
                risk_label = ?
            WHERE sentence_id = ?
            """,
            (primary_role, json_text(tags), risk_label, selected["sentence_id"]),
        )
        updates.append(
            {
                "candidate_id": item.candidate_id,
                "canonical_term": item.canonical_term,
                "sentence_id": selected["sentence_id"],
                "primary_role": primary_role,
                "role_tags": tags,
                "risk_label": risk_label,
            }
        )
    return updates


def table_rows(conn: sqlite3.Connection, table_or_view: str, order_by: str) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(f"SELECT * FROM {table_or_view} ORDER BY {order_by}")]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def candidate_payload(item: EvidenceCandidate, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    source_text = ""
    primary_evidence_text = item.sentence_hint
    source_evidence_level = ""
    source_object = ""
    source_record_id = ""
    if conn is not None and item.category in {"A", "B"}:
        row = fetch_source_row(conn, item.source_table, item.passage_id)
        source_text = str(row.get("text") or "")
        primary_evidence_text = sentence_for_candidate(row, item.sentence_hint)
        source_evidence_level = evidence_level_for_source(item, row)
        source_object = source_object_for_table(item.source_table, row)
        source_record_id = source_record_id_for_source(item, row)
    return {
        "candidate_id": item.candidate_id,
        "category": item.category,
        "candidate_priority": item.candidate_priority,
        "concept_id": item.concept_id if item.category in {"A", "B"} else None,
        "canonical_term": item.canonical_term,
        "normalized_term": compact_text(item.canonical_term),
        "concept_type": item.concept_type,
        "source_table": item.source_table,
        "source_object": source_object,
        "source_record_id": source_record_id,
        "source_evidence_level": source_evidence_level,
        "passage_id": item.passage_id,
        "primary_evidence_type": item.evidence_type,
        "primary_evidence_text": primary_evidence_text,
        "source_text": source_text,
        "query": item.query,
        "aliases": list(item.aliases),
        "risky_aliases": list(item.risky_aliases),
        "ambiguous_aliases": list(item.ambiguous_aliases),
        "classification_reason": item.classification_reason,
        "promotion_state": item.promotion_state if item.category in {"A", "B"} else "rejected",
        "review_only_reason": item.review_only_reason,
        "rejection_reason": item.rejection_reason,
        "future_condition": item.future_condition,
        "risk_source": item.risk_source,
        "notes": item.notes,
    }


def write_candidate_pool(output_dir: Path, conn: sqlite3.Connection) -> None:
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "candidate_count": len(CANDIDATES),
        "category_counts": {
            category: sum(1 for item in CANDIDATES if item.category == category)
            for category in ("A", "B", "C")
        },
        "source_scope": [
            "ambiguous_passages/risk_registry_ambiguous",
            "records_passages",
            "B/non-primary records_main_passages",
            "support-only or weak definition/concept materials",
        ],
        "candidates": [candidate_payload(item, conn) for item in CANDIDATES],
    }
    write_json(output_dir / "ambiguous_high_value_candidate_pool_v1.json", payload)
    lines = [
        "# Ambiguous High Value Candidate Pool v1",
        "",
        f"- run_id: `{RUN_ID}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- category_counts: `{json.dumps(payload['category_counts'], ensure_ascii=False)}`",
        "",
        "| category | priority | term | source | query | decision |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["candidates"]:
        decision = (
            "promote safe primary"
            if item["category"] == "A"
            else "support/review-only"
            if item["category"] == "B"
            else "reject promotion"
        )
        lines.append(
            f"| {item['category']} | {item['candidate_priority']} | {item['canonical_term']} | "
            f"{item['source_table']}:{item['passage_id']} | {item['query']} | {decision} |"
        )
    write_md(output_dir / "ambiguous_high_value_candidate_pool_v1.md", lines)


def write_snapshots(conn: sqlite3.Connection, output_dir: Path) -> None:
    write_json(
        output_dir / "definition_term_registry_batch_upgrade_v1_snapshot.json",
        table_rows(conn, "definition_term_registry", "canonical_term, concept_id"),
    )
    write_json(
        output_dir / "term_alias_registry_batch_upgrade_v1_snapshot.json",
        table_rows(conn, "term_alias_registry", "canonical_term, alias, alias_id"),
    )
    write_json(
        output_dir / "learner_query_normalization_batch_upgrade_v1_snapshot.json",
        table_rows(conn, "learner_query_normalization_lexicon", "entry_type, surface_form, target_term"),
    )
    write_json(
        output_dir / "sentence_role_registry_batch_upgrade_v1_snapshot.json",
        table_rows(conn, "sentence_role_registry", "source_table, passage_id, sentence_index"),
    )


def registry_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "definition_term_registry": conn.execute("SELECT COUNT(*) FROM definition_term_registry").fetchone()[0],
        "retrieval_ready_definition_view": conn.execute("SELECT COUNT(*) FROM retrieval_ready_definition_view").fetchone()[0],
        "term_alias_registry": conn.execute("SELECT COUNT(*) FROM term_alias_registry").fetchone()[0],
        "learner_query_normalization_lexicon": conn.execute(
            "SELECT COUNT(*) FROM learner_query_normalization_lexicon"
        ).fetchone()[0],
        "sentence_role_registry": conn.execute("SELECT COUNT(*) FROM sentence_role_registry").fetchone()[0],
    }


def write_ledger(
    conn: sqlite3.Connection,
    output_dir: Path,
    before_counts: dict[str, int],
    after_counts: dict[str, int],
    sentence_updates: list[dict[str, Any]],
) -> None:
    a_items = [item for item in CANDIDATES if item.category == "A"]
    b_items = [item for item in CANDIDATES if item.category == "B"]
    c_items = [item for item in CANDIDATES if item.category == "C"]
    promoted_ids = [item.concept_id for item in a_items]
    support_ids = [item.concept_id for item in b_items]
    forbidden_primary_projection = conn.execute(
        """
        SELECT COUNT(*)
        FROM retrieval_ready_definition_view
        WHERE primary_source_object IN ('passages', 'ambiguous_passages', 'annotations', 'annotation_links')
          AND concept_id NOT IN ({})
        """.format(",".join("?" for _ in promoted_ids) or "''"),
        promoted_ids,
    ).fetchone()[0]
    batch_safe_from_risk = conn.execute(
        """
        SELECT COUNT(*)
        FROM retrieval_ready_definition_view
        WHERE concept_id IN ({})
          AND primary_source_object IN ('passages', 'ambiguous_passages', 'main_passages')
        """.format(",".join("?" for _ in promoted_ids) or "''"),
        promoted_ids,
    ).fetchone()[0]
    review_lexicon_conflicts = conn.execute(
        """
        SELECT COUNT(*)
        FROM learner_query_normalization_lexicon
        WHERE target_id IN ({})
          AND is_active = 1
        """.format(",".join("?" for _ in support_ids) or "''"),
        support_ids,
    ).fetchone()[0]
    alias_risk_conflicts = conn.execute(
        """
        SELECT COUNT(*)
        FROM term_alias_registry
        WHERE source = ?
          AND alias_type IN ('learner_risky', 'ambiguous')
          AND is_active = 1
        """,
        (SOURCE,),
    ).fetchone()[0]
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "summary": {
            "candidate_count": len(CANDIDATES),
            "promoted_safe_primary_count": len(a_items),
            "support_only_registered_count": len(b_items),
            "rejected_count": len(c_items),
            "batch_safe_from_risk_or_b_count": batch_safe_from_risk,
            "review_only_learner_lexicon_conflict_count": review_lexicon_conflicts,
            "alias_risk_conflict_count": alias_risk_conflicts,
            "existing_forbidden_primary_projection_count": forbidden_primary_projection,
        },
        "registry_counts_before": before_counts,
        "registry_counts_after": after_counts,
        "promoted_safe_primary": [candidate_payload(item, conn) for item in a_items],
        "support_only_registered": [candidate_payload(item, conn) for item in b_items],
        "rejected": [candidate_payload(item, conn) for item in c_items],
        "sentence_role_updates": sentence_updates,
    }
    write_json(output_dir / "batch_upgrade_ledger_v1.json", payload)
    lines = [
        "# Batch Upgrade Ledger v1",
        "",
        f"- run_id: `{RUN_ID}`",
        f"- candidate_count: `{payload['summary']['candidate_count']}`",
        f"- promoted_safe_primary_count: `{payload['summary']['promoted_safe_primary_count']}`",
        f"- support_only_registered_count: `{payload['summary']['support_only_registered_count']}`",
        f"- rejected_count: `{payload['summary']['rejected_count']}`",
        f"- alias_risk_conflict_count: `{payload['summary']['alias_risk_conflict_count']}`",
        "",
        "## A Promoted",
        "",
    ]
    for item in a_items:
        lines.append(f"- `{item.canonical_term}` -> `{item.concept_id}` from `{item.source_table}:{item.passage_id}`")
    lines.extend(["", "## B Support Only", ""])
    for item in b_items:
        lines.append(f"- `{item.canonical_term}` -> `{item.review_only_reason}`")
    lines.extend(["", "## C Rejected", ""])
    for item in c_items:
        lines.append(f"- `{item.canonical_term}` -> {item.rejection_reason}")
    write_md(output_dir / "batch_upgrade_ledger_v1.md", lines)


def write_docs(doc_dir: Path) -> None:
    write_md(
        doc_dir / "ambiguous_candidate_selection_policy_v1.md",
        [
            "# Ambiguous Candidate Selection Policy v1",
            "",
            "本轮只处理 ambiguous/full-risk/B 级材料中的 definition/concept/learner-facing evidence。",
            "",
            "## Priority",
            "",
            "- P0: `谓之 X`、`名曰 X`、`X 者……也`、`此为 X`、`X 之为病` 等明确命名或定义结构。",
            "- P1: 普通学习者高频会问的术语，且句子能独立成义。",
            "- P2: 当前 definition/concept query 容易 weak/support-only，或缺 alias/normalization 的对象。",
            "",
            "## Exclusions",
            "",
            "- 不恢复 raw `full:passages:*` / `full:ambiguous_passages:*` 为 primary。",
            "- 不把一整段 ambiguous passage 粗暴恢复为 safe main。",
            "- 单字短词、复合注释、异文/校记、方证治疗语境黏连的对象只登记 support/review 或拒绝升格。",
        ],
    )
    write_md(
        doc_dir / "batch_promotion_policy_v1.md",
        [
            "# Batch Promotion Policy v1",
            "",
            "A 类对象进入 `definition_term_registry`，并在 `is_safe_primary_candidate=1` 时通过 `retrieval_ready_definition_view` 暴露给 runtime。",
            "",
            "## A 类",
            "",
            "- 来源可以是 B 级 main、full passage 或 ambiguous risk registry，但 primary 只指向切出的干净句段。",
            "- 来自 full/risk/ambiguous 的对象默认 `source_confidence=medium`，不硬升 high。",
            "- 只有 canonical/learner_safe alias 进入 active runtime normalization。",
            "",
            "## B 类",
            "",
            "- 写入 registry，`promotion_state=review_only`，`is_safe_primary_candidate=0`。",
            "- 允许 canonical support alias，但不写 learner-safe normalization。",
            "- 句子在 `sentence_role_registry` 标记 `review_only_support`。",
            "",
            "## C 类",
            "",
            "- 不写 runtime normalization。",
            "- 只在候选池和 ledger 中记录拒绝理由、风险来源和未来处理条件。",
        ],
    )
    write_md(
        doc_dir / "ambiguous_high_value_evidence_upgrade_v1.md",
        [
            "# Ambiguous High Value Evidence Upgrade v1",
            "",
            "本轮目标是从 ambiguous/full-risk/B 级材料中处理 30 条左右高价值 definition/concept 候选，并让 A 类对象通过 registry/view/normalization 被 runtime 命中。",
            "",
            "## Scope Frozen",
            "",
            "- 不改 prompt、前端、API payload 顶层 contract、answer_mode、commentarial 主逻辑。",
            "- 不重新放开 raw full passages 或 ambiguous passages 直接进入 primary。",
            "- 不为提升 strong 数量硬抬 review-only 材料。",
            "",
            "## Outputs",
            "",
            "- 候选池: `artifacts/data_plane_batch_upgrade/ambiguous_high_value_candidate_pool_v1.json`",
            "- ledger: `artifacts/data_plane_batch_upgrade/batch_upgrade_ledger_v1.json`",
            "- registry snapshots: `artifacts/data_plane_batch_upgrade/*_snapshot.json`",
            "- regression: `artifacts/data_plane_batch_upgrade/batch_upgrade_regression_v1.json`",
        ],
    )


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    before_db = resolve_project_path(args.before_db)
    output_dir = resolve_project_path(args.output_dir)
    doc_dir = resolve_project_path(args.doc_dir)
    ensure_before_db(db_path, before_db, args.refresh_before)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        before_counts = registry_counts(conn)
        a_b_candidates = [item for item in CANDIDATES if item.category in {"A", "B"}]
        definition_rows = [build_definition_record(conn, item) for item in a_b_candidates]
        alias_rows = [row for item in a_b_candidates for row in build_alias_records(item)]
        learner_rows = [row for item in a_b_candidates for row in build_learner_records(item)]
        with conn:
            insert_definition_records(conn, definition_rows)
            insert_alias_records(conn, alias_rows)
            insert_learner_records(conn, learner_rows)
            sentence_updates = update_sentence_role_registry(conn, a_b_candidates)
        after_counts = registry_counts(conn)
        write_candidate_pool(output_dir, conn)
        write_ledger(conn, output_dir, before_counts, after_counts, sentence_updates)
        write_snapshots(conn, output_dir)
        write_docs(doc_dir)
    finally:
        conn.close()

    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "db_path": str(db_path),
                "before_db": str(before_db),
                "candidate_count": len(CANDIDATES),
                "promoted_safe_primary_count": sum(1 for item in CANDIDATES if item.category == "A"),
                "support_only_registered_count": sum(1 for item in CANDIDATES if item.category == "B"),
                "rejected_count": sum(1 for item in CANDIDATES if item.category == "C"),
                "output_dir": str(output_dir),
                "doc_dir": str(doc_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
