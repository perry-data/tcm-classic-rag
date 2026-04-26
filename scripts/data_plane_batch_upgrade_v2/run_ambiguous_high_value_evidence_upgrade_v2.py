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
DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_ambiguous_high_value_evidence_upgrade_v2.db"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_batch_upgrade_v2"
DEFAULT_DOC_DIR = "docs/data_plane_batch_upgrade_v2"
RUN_ID = "ambiguous_high_value_evidence_upgrade_v2"
SOURCE = RUN_ID
AHV2_SAFE_LAYER = "ambiguous_high_value_evidence_upgrade_v2_safe_primary"
AHV2_SUPPORT_LAYER = "ambiguous_high_value_evidence_upgrade_v2_support_only"
PUNCTUATION_STRIP = "，。；：:、 “”\"'「」"


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
        object.__setattr__(self, "concept_id", stable_id("AHV2", compact_text(self.canonical_term)))


def stable_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", str(text).lower())


def compact_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def strip_inline_notes(text: str | None) -> str:
    cleaned = compact_whitespace(text)
    if not cleaned:
        return ""
    cleaned = re.sub(r"(?:赵本|医统本|汪本|成本|千金|玉函|熊校记)注?：?「[^」]+」", "", cleaned)
    cleaned = re.sub(r"(?:赵本|医统本|汪本|成本|旧钞)+(?:并)?(?:有|无|作|上有|下增)「[^」]+」字?", "", cleaned)
    cleaned = re.sub(r"(?:赵本|医统本|汪本|成本|旧钞)+(?:作|无|有)[^，。；：:]{0,10}", "", cleaned)
    cleaned = re.sub(r"《[^》]{1,16}》曰：?", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(PUNCTUATION_STRIP)


def split_sentences(text: str) -> list[str]:
    normalized = compact_whitespace(text)
    if not normalized:
        return []
    pieces = re.split(r"(?<=[。！？；])", normalized)
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
    prefix = {"A": "AHV2-A", "B": "AHV2-B", "C": "AHV2-C"}[category]
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
        "荣气微",
        "pulse_qi_state_term",
        "records_main_passages",
        "ZJSHL-CH-003-P-0010",
        "其脉沉者，荣气微也",
        "exact_term_definition",
        "P1",
        "B 级 main passage 有闭合判断句，可切为荣气状态对象。",
        "荣气微是什么意思",
        definition_passage_ids=("ZJSHL-CH-003-P-0010",),
        notes="AHV2: 只升格荣气微句段，不扩展到荣血/阴虚长注。",
    ),
    candidate(
        "A",
        "卫气衰",
        "pulse_qi_state_term",
        "records_main_passages",
        "ZJSHL-CH-003-P-0012",
        "其脉浮，而汗出如流珠者，卫气衰也",
        "exact_term_definition",
        "P1",
        "B 级 main passage 以脉象和汗出定义卫气衰，句子可独立成义。",
        "卫气衰是什么意思",
        definition_passage_ids=("ZJSHL-CH-003-P-0012",),
        notes="AHV2: 保留中等置信，不把卫气系统解释整体上浮。",
    ),
    candidate(
        "A",
        "阳气微",
        "pulse_qi_state_term",
        "records_main_passages",
        "ZJSHL-CH-003-P-0021",
        "脉瞥瞥，如羹上肥者，阳气微也",
        "exact_term_definition",
        "P1",
        "B 级 main passage 有稳定的脉象-气状态判断。",
        "阳气微是什么意思",
        definition_passage_ids=("ZJSHL-CH-003-P-0021",),
        notes="AHV2: 与 v1 内虚/行尸不同，限定为脉象所见阳气微。",
    ),
    candidate(
        "A",
        "亡血",
        "qi_blood_state_term",
        "records_main_passages",
        "ZJSHL-CH-003-P-0026",
        "脉绵绵，如泻漆之绝者，亡其血也",
        "exact_term_definition",
        "P1",
        "B 级 main passage 用脉象闭合判断亡血，学习者短问高价值。",
        "亡血是什么意思",
        aliases=("亡其血",),
        definition_passage_ids=("ZJSHL-CH-003-P-0026",),
        notes="AHV2: active alias 只保留原文短语“亡其血”，exact match。",
    ),
    candidate(
        "A",
        "平脉",
        "pulse_pattern_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-003-P-0029",
        "脉一息四至曰平",
        "exact_term_definition",
        "P0",
        "risk 层有明确“曰平”脉数定义，适合对象化承接。",
        "平脉是什么",
        ambiguous_aliases=("平",),
        definition_passage_ids=("ZJSHL-CH-003-P-0029",),
        notes="AHV2: 单字“平”仅作 inactive ambiguous alias，不进入 learner normalization。",
    ),
    candidate(
        "A",
        "数脉",
        "pulse_pattern_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-003-P-0029",
        "一息六至曰数",
        "exact_term_definition",
        "P0",
        "同一 passage 中有可独立切出的数脉定义。",
        "数脉是什么意思",
        ambiguous_aliases=("数",),
        definition_passage_ids=("ZJSHL-CH-003-P-0029",),
        notes="AHV2: 不启用单字“数”，避免与数量/次数问法混淆。",
    ),
    candidate(
        "A",
        "毛脉",
        "pulse_pattern_term",
        "records_passages",
        "ZJSHL-CH-004-P-0192",
        "轻虚浮曰毛，肺之平脉也",
        "exact_term_definition",
        "P1",
        "full 层有“曰毛”短定义，可对象化为毛脉。",
        "毛脉是什么",
        ambiguous_aliases=("毛",),
        definition_passage_ids=("ZJSHL-CH-004-P-0192",),
        notes="AHV2: canonical 使用“毛脉”，单字毛不进入 active alias。",
    ),
    candidate(
        "A",
        "纯弦脉",
        "pulse_pattern_term",
        "records_passages",
        "ZJSHL-CH-004-P-0185",
        "纯弦者，为如弦直而不软",
        "exact_term_definition",
        "P1",
        "full 层有“X者，为……”解释，可为学习者说明纯弦脉。",
        "纯弦脉是什么意思",
        risky_aliases=("纯弦",),
        definition_passage_ids=("ZJSHL-CH-004-P-0185",),
        notes="AHV2: “纯弦”只登记 inactive risky alias，避免短语泛化。",
    ),
    candidate(
        "A",
        "残贼",
        "pulse_pathology_term",
        "records_main_passages",
        "ZJSHL-CH-004-P-0178",
        "脉有弦、紧、浮、滑、沉、涩，此六者名曰残贼",
        "exact_term_definition",
        "P0",
        "main passage 明确命名“残贼”，且后文解释其为诸脉作病。",
        "残贼是什么意思",
        definition_passage_ids=("ZJSHL-CH-004-P-0178",),
        explanation_passage_ids=("ZJSHL-CH-004-P-0179",),
        notes="AHV2: 清理校记后只保留命名句，后文八邪解释仅作 supporting evidence。",
    ),
    candidate(
        "A",
        "八邪",
        "pathogen_category_term",
        "records_passages",
        "ZJSHL-CH-004-P-0179",
        "为人病者，名曰八邪，风寒暑湿伤于外也，饥、饱、劳、逸伤于内也",
        "exact_term_definition",
        "P0",
        "full 层有明确命名及枚举，句段自足。",
        "八邪是什么",
        definition_passage_ids=("ZJSHL-CH-004-P-0179",),
        notes="AHV2: 只抽八邪枚举句，不把残贼长解释整体放进 primary。",
    ),
    candidate(
        "A",
        "湿家",
        "disease_person_state_term",
        "records_passages",
        "ZJSHL-CH-007-P-0172",
        "湿家之为病，一身尽疼，发热，身色如似熏黄",
        "exact_term_definition",
        "P0",
        "“X之为病”结构明确，当前没有 safe definition object。",
        "湿家是什么",
        definition_passage_ids=("ZJSHL-CH-007-P-0172",),
        notes="AHV2: 来自 full 层，按 medium safe object 处理。",
    ),
    candidate(
        "A",
        "风湿",
        "disease_state_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-007-P-0182",
        "病者一身尽疼，发热，日晡所剧者，此名风湿",
        "exact_term_definition",
        "P0",
        "risk 层有“此名风湿”结构，短句可独立成义。",
        "风湿是什么",
        risky_aliases=("风湿病",),
        definition_passage_ids=("ZJSHL-CH-007-P-0182",),
        notes="AHV2: 不启用现代“风湿病”别名，避免现代病名误触发。",
    ),
    candidate(
        "A",
        "水逆",
        "disease_state_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-009-P-0148",
        "水入则吐者，名曰水逆",
        "exact_term_definition",
        "P0",
        "risk 层命名句干净，普通学习者可能直接问水逆。",
        "水逆是什么意思",
        definition_passage_ids=("ZJSHL-CH-009-P-0148",),
        notes="AHV2: 不把五苓散处置句纳入 primary。",
    ),
    candidate(
        "A",
        "半表半里证",
        "disease_location_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-009-P-0210",
        "此邪气在表里之间，谓之半表半里证",
        "exact_term_definition",
        "P0",
        "“谓之”结构清楚，且是学习者高频概念。",
        "半表半里证是什么",
        aliases=("半表半里",),
        definition_passage_ids=("ZJSHL-CH-009-P-0210",),
        explanation_passage_ids=("ZJSHL-CH-009-P-0210",),
        notes="AHV2: active alias“半表半里”仅 exact，不让比较/治疗问法被抢占。",
    ),
    candidate(
        "A",
        "过经",
        "disease_course_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-009-P-0257",
        "伤寒十三日再传经尽，谓之过经",
        "exact_term_definition",
        "P0",
        "risk 层有可切分的“谓之过经”定义句。",
        "过经是什么意思",
        definition_passage_ids=("ZJSHL-CH-009-P-0257",),
        notes="AHV2: 只定义过经，不把谵语/承气汤后续治疗语境上浮。",
    ),
    candidate(
        "A",
        "结胸",
        "disease_state_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-010-P-0003",
        "结胸者，邪结在胸",
        "exact_term_definition",
        "P0",
        "risk 层首句“X者……”独立成义，且与已有小结胸/水结胸不同。",
        "结胸是什么",
        aliases=("结胸证",),
        definition_passage_ids=("ZJSHL-CH-010-P-0003",),
        explanation_passage_ids=("ZJSHL-CH-010-P-0002",),
        notes="AHV2: 与脏结、水结胸保持对象边界，exact normalization。",
    ),
    candidate(
        "A",
        "阳明病",
        "six_channel_disease_term",
        "records_main_passages",
        "ZJSHL-CH-011-P-0008",
        "阳明之为病，胃家实也",
        "exact_term_definition",
        "P0",
        "B 级 main passage 是六经提纲定义，可句段化为 safe object。",
        "阳明病是什么",
        aliases=("阳明之为病",),
        definition_passage_ids=("ZJSHL-CH-011-P-0008",),
        notes="AHV2: 只升格提纲句，不把阳明篇证治整体归入 primary。",
    ),
    candidate(
        "A",
        "太阴病",
        "six_channel_disease_term",
        "records_passages",
        "ZJSHL-CH-013-P-0002",
        "太阴之为病，腹满而吐，食不下，自利益甚，时腹自痛",
        "exact_term_definition",
        "P0",
        "full 层有六经提纲句，未单独对象化。",
        "太阴病是什么",
        aliases=("太阴之为病",),
        definition_passage_ids=("ZJSHL-CH-013-P-0002",),
        notes="AHV2: 从 full 层抽句，source_confidence 保持 medium。",
    ),
    candidate(
        "A",
        "少阴病",
        "six_channel_disease_term",
        "records_main_passages",
        "ZJSHL-CH-014-P-0021",
        "少阴之为病，脉微细，但欲寐也",
        "exact_term_definition",
        "P0",
        "B 级 main passage 是六经提纲句，术语锚点稳定。",
        "少阴病是什么",
        aliases=("少阴之为病",),
        definition_passage_ids=("ZJSHL-CH-014-P-0021",),
        notes="AHV2: 只覆盖少阴病提纲定义，不触碰少阴篇方证主线。",
    ),
    candidate(
        "A",
        "厥阴病",
        "six_channel_disease_term",
        "records_passages",
        "ZJSHL-CH-015-P-0193",
        "厥阴之为病，消渴，气上撞心，心中疼热，饥而不欲食，食则吐蛔，下之利不止",
        "exact_term_definition",
        "P0",
        "full 层六经提纲句完整，可作为 learner-facing object。",
        "厥阴病是什么",
        aliases=("厥阴之为病",),
        definition_passage_ids=("ZJSHL-CH-015-P-0193",),
        notes="AHV2: 来自 full 层，仅提纲句进入 object primary。",
    ),
    candidate(
        "B",
        "三菽重",
        "pulse_weight_term",
        "records_passages",
        "ZJSHL-CH-004-P-0172",
        "如三菽之重者，肺气也",
        "exact_term_definition",
        "P1",
        "有学习价值，但属于脉按重量体系的一部分，单独进入 primary 容易脱离枚举语境。",
        "三菽重是什么意思",
        promotion_state="review_only",
        review_only_reason="依赖三菽、六菽、九菽、十二菽、至骨的完整枚举体系，暂作 support/review。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 不写 active normalization。",
    ),
    candidate(
        "B",
        "六菽重",
        "pulse_weight_term",
        "records_passages",
        "ZJSHL-CH-004-P-0172",
        "如六菽之重者，心气也",
        "exact_term_definition",
        "P1",
        "同属脉按重量枚举，必须与前后项共同理解。",
        "六菽重是什么意思",
        promotion_state="review_only",
        review_only_reason="依赖完整脉重枚举体系，不能作为独立 safe primary。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 不写 active normalization。",
    ),
    candidate(
        "B",
        "九菽重",
        "pulse_weight_term",
        "records_passages",
        "ZJSHL-CH-004-P-0172",
        "如九菽之重者，脾气也",
        "exact_term_definition",
        "P1",
        "有术语价值，但上下文枚举依赖强。",
        "九菽重是什么意思",
        promotion_state="review_only",
        review_only_reason="依赖完整脉重枚举体系，暂不进入 primary。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 不写 active normalization。",
    ),
    candidate(
        "B",
        "十二菽重",
        "pulse_weight_term",
        "records_passages",
        "ZJSHL-CH-004-P-0172",
        "如十二菽之重者，肝气也",
        "exact_term_definition",
        "P1",
        "句段可解释，但不能脱离同段枚举体系。",
        "十二菽重是什么意思",
        promotion_state="review_only",
        review_only_reason="依赖完整脉重枚举体系，暂不进入 primary。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 不写 active normalization。",
    ),
    candidate(
        "B",
        "纵",
        "five_phase_relation_term",
        "records_passages",
        "ZJSHL-CH-004-P-0176",
        "水行乘火，金行乘木，名曰纵",
        "exact_term_definition",
        "P0",
        "命名句明确但 canonical 是单字，普通语义和五行术语冲突大。",
        "纵是什么意思",
        promotion_state="review_only",
        review_only_reason="单字术语，离开五行相乘语境后误触发风险高。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 单字 term_alias 保持 inactive。",
    ),
    candidate(
        "B",
        "横",
        "five_phase_relation_term",
        "records_passages",
        "ZJSHL-CH-004-P-0176",
        "火行乘水，木行乘金，名曰横",
        "exact_term_definition",
        "P0",
        "命名句明确但单字歧义大。",
        "横是什么意思",
        promotion_state="review_only",
        review_only_reason="单字术语，必须依赖五行相乘上下文。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 单字 term_alias 保持 inactive。",
    ),
    candidate(
        "B",
        "逆",
        "five_phase_relation_term",
        "records_passages",
        "ZJSHL-CH-004-P-0176",
        "水行乘金，火行乘木，名曰逆",
        "exact_term_definition",
        "P0",
        "命名句明确但单字泛义强。",
        "逆是什么意思",
        promotion_state="review_only",
        review_only_reason="单字术语，普通语义和病机语义重叠，不能 learner-safe。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 单字 term_alias 保持 inactive。",
    ),
    candidate(
        "B",
        "顺",
        "five_phase_relation_term",
        "records_passages",
        "ZJSHL-CH-004-P-0176",
        "金行乘水，木行乘火，名曰顺也",
        "exact_term_definition",
        "P0",
        "命名句明确但单字普通义极强。",
        "顺是什么意思",
        promotion_state="review_only",
        review_only_reason="单字术语，不能脱离五行相乘语境独立 primary。",
        sentence_role="context_dependent_sentence",
        source_confidence="review_only",
        notes="AHV2 support-only: 单字 term_alias 保持 inactive。",
    ),
    candidate(
        "C",
        "反",
        "pulse_direction_term",
        "records_passages",
        "ZJSHL-CH-004-P-0188",
        "假令脉来微去大，故名反，病在里也",
        "exact_term_definition",
        "P0",
        "有命名结构，但 canonical 是单字且与“复”成对依赖。",
        "反是什么意思",
        rejection_reason="单字普通义强，且必须与“复”及来去脉势成对解释，不能进入 runtime normalization。",
        future_condition="需要先构建成对脉势关系对象，再证明不会误触发普通“反/复”问法。",
        risk_source="single_character_pair_dependency",
    ),
    candidate(
        "C",
        "复",
        "pulse_direction_term",
        "records_passages",
        "ZJSHL-CH-004-P-0188",
        "脉来头小本大者，故名复，病在表也",
        "exact_term_definition",
        "P0",
        "有命名结构，但 canonical 是单字且与“反”成对依赖。",
        "复是什么意思",
        rejection_reason="单字普通义强，不能脱离前后脉势和“反”对照单独升格。",
        future_condition="需要成对对象和严格 query pattern 后再考虑。",
        risk_source="single_character_pair_dependency",
    ),
    candidate(
        "C",
        "肝乘脾",
        "five_phase_pathology_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-009-P-0268",
        "伤寒腹满谵语，寸口脉浮而紧，此肝乘脾也，名曰纵，刺期门",
        "exact_term_explanation",
        "P1",
        "句子有学习价值，但真正命名对象是“纵”，且混入刺期门处置。",
        "肝乘脾是什么意思",
        rejection_reason="术语锚点不稳定，病机说明、命名和刺法处置混在同句，当前不升格。",
        future_condition="需要先拆五行相乘对象和刺期门治疗语境。",
        risk_source="mixed_pathology_treatment_context",
    ),
    candidate(
        "C",
        "火劫发汗",
        "treatment_error_context_term",
        "risk_registry_ambiguous",
        "ZJSHL-CH-009-P-0279",
        "医以火劫发汗，汗出，大出者亡其阳",
        "contextual_explanation",
        "P1",
        "学习者可能会问，但原句校记多、治疗误法和后续方证黏连。",
        "火劫发汗是什么意思",
        rejection_reason="证据句含校记和治疗误法上下文，不能切成干净 definition primary。",
        future_condition="需要专门处理火逆/火劫误治语境后再对象化。",
        risk_source="variant_and_treatment_context_entanglement",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upgrade AHV evidence objects v2.")
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
    return hint.strip(PUNCTUATION_STRIP) if hint else strip_inline_notes(row.get("text") or "")


def source_object_for_table(table: str) -> str:
    if table == "records_main_passages":
        return "main_passages"
    if table == "records_passages":
        return "passages"
    if table == "risk_registry_ambiguous":
        return "ambiguous_passages"
    return table


def evidence_level_for_source(item: EvidenceCandidate, row: dict[str, Any]) -> str:
    if item.source_table == "risk_registry_ambiguous":
        return "C"
    return str(row.get("evidence_level") or "C")


def source_record_id_for_source(item: EvidenceCandidate, row: dict[str, Any]) -> str:
    if item.source_table == "risk_registry_ambiguous":
        return str(row.get("record_id") or f"full:ambiguous_passages:{item.passage_id}")
    return str(row.get("record_id") or "")


def build_definition_record(conn: sqlite3.Connection, item: EvidenceCandidate) -> dict[str, Any]:
    row = fetch_source_row(conn, item.source_table, item.passage_id)
    primary_sentence = sentence_for_candidate(row, item.sentence_hint)
    definition_ids = unique(item.definition_passage_ids or (item.passage_id,))
    explanation_ids = unique(item.explanation_passage_ids)
    membership_ids = unique(item.membership_passage_ids)
    source_ids = unique([item.passage_id] + definition_ids + explanation_ids + membership_ids)
    chapter_ids: list[str] = []
    for pid in source_ids:
        source_row = None
        for table_name in (item.source_table, "records_main_passages", "records_passages", "risk_registry_ambiguous"):
            try:
                source_row = fetch_source_row(conn, table_name, pid)
                break
            except KeyError:
                continue
        if source_row:
            chapter_ids.append(str(source_row.get("chapter_id") or ""))
    safe_aliases = unique(item.aliases)
    retrieval_sentences = unique([primary_sentence, item.canonical_term, *safe_aliases])
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
        "primary_source_object": source_object_for_table(item.source_table),
        "primary_source_record_id": source_record_id_for_source(item, row),
        "primary_source_evidence_level": evidence_level_for_source(item, row),
        "source_passage_ids_json": json_text(source_ids),
        "chapter_ids_json": json_text(unique(chapter_ids)),
        "query_aliases_json": json_text(safe_aliases if item.category == "A" else []),
        "learner_surface_forms_json": json_text(safe_aliases if item.category == "A" else []),
        "primary_evidence_type": item.evidence_type,
        "primary_evidence_text": primary_sentence,
        "retrieval_text": "\n".join(retrieval_sentences),
        "normalized_retrieval_text": compact_text("\n".join(retrieval_sentences)),
        "source_confidence": item.source_confidence,
        "promotion_state": item.promotion_state,
        "promotion_source_layer": AHV2_SAFE_LAYER if item.category == "A" else AHV2_SUPPORT_LAYER,
        "promotion_reason": item.promotion_reason if item.category == "A" else "registered as support/review-only explainable object",
        "review_only_reason": item.review_only_reason,
        "notes": item.notes,
        "is_safe_primary_candidate": 1 if item.category == "A" else 0,
        "is_active": 1,
    }


def build_alias_records(item: EvidenceCandidate) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if item.category == "A":
        rows.append(
            {
                "alias_id": stable_id("AHV2-TAL", f"{item.concept_id}|canonical|{item.canonical_term}"),
                "alias": item.canonical_term,
                "normalized_alias": compact_text(item.canonical_term),
                "concept_id": item.concept_id,
                "canonical_term": item.canonical_term,
                "alias_type": "canonical",
                "confidence": 1.0,
                "source": SOURCE,
                "notes": "AHV2 canonical exact-match alias",
                "is_active": 1,
            }
        )
        for alias in unique(item.aliases):
            rows.append(
                {
                    "alias_id": stable_id("AHV2-TAL", f"{item.concept_id}|learner_safe|{alias}"),
                    "alias": alias,
                    "normalized_alias": compact_text(alias),
                    "concept_id": item.concept_id,
                    "canonical_term": item.canonical_term,
                    "alias_type": "learner_safe",
                    "confidence": 0.9,
                    "source": SOURCE,
                    "notes": "AHV2 learner-safe exact-match alias",
                    "is_active": 1,
                }
            )
    else:
        rows.append(
            {
                "alias_id": stable_id("AHV2-TAL", f"{item.concept_id}|review_only|{item.canonical_term}"),
                "alias": item.canonical_term,
                "normalized_alias": compact_text(item.canonical_term),
                "concept_id": item.concept_id,
                "canonical_term": item.canonical_term,
                "alias_type": "review_only_support",
                "confidence": 0.25,
                "source": SOURCE,
                "notes": "AHV2 support/review-only alias is inactive and not used for runtime normalization",
                "is_active": 0,
            }
        )
    for alias in unique(item.risky_aliases):
        rows.append(
            {
                "alias_id": stable_id("AHV2-TAL", f"{item.concept_id}|learner_risky|{alias}"),
                "alias": alias,
                "normalized_alias": compact_text(alias),
                "concept_id": item.concept_id,
                "canonical_term": item.canonical_term,
                "alias_type": "learner_risky",
                "confidence": 0.42,
                "source": SOURCE,
                "notes": "AHV2 inactive risky alias; not used for runtime normalization",
                "is_active": 0,
            }
        )
    for alias in unique(item.ambiguous_aliases):
        rows.append(
            {
                "alias_id": stable_id("AHV2-TAL", f"{item.concept_id}|ambiguous|{alias}"),
                "alias": alias,
                "normalized_alias": compact_text(alias),
                "concept_id": item.concept_id,
                "canonical_term": item.canonical_term,
                "alias_type": "ambiguous",
                "confidence": 0.3,
                "source": SOURCE,
                "notes": "AHV2 inactive ambiguous alias; not used for runtime normalization",
                "is_active": 0,
            }
        )
    return [row for row in rows if row["normalized_alias"]]


def build_learner_records(item: EvidenceCandidate) -> list[dict[str, Any]]:
    if item.category != "A":
        return []
    rows: list[dict[str, Any]] = []
    for surface in unique([item.canonical_term, *item.aliases]):
        normalized = compact_text(surface)
        if len(normalized) < 2:
            continue
        rows.append(
            {
                "lexicon_id": stable_id("AHV2-LQN", f"{item.concept_id}|{normalized}"),
                "entry_type": "term_surface",
                "match_mode": "exact",
                "surface_form": surface,
                "normalized_surface_form": normalized,
                "target_type": "concept_term",
                "target_id": item.concept_id,
                "target_term": item.canonical_term,
                "intent_hint": "what_is",
                "canonical_query_template": f"什么是{item.canonical_term}",
                "confidence": 1.0 if surface == item.canonical_term else 0.9,
                "source": SOURCE,
                "notes": "AHV2 learner-safe normalization; exact match only",
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
    conn.executemany(
        f"""
        INSERT INTO definition_term_registry ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(concept_id) DO UPDATE SET {assignments}
        """,
        rows,
    )


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


def upsert_sentence_roles(conn: sqlite3.Connection, items: list[EvidenceCandidate]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for item in items:
        row = fetch_source_row(conn, item.source_table, item.passage_id)
        sentence_text = sentence_for_candidate(row, item.sentence_hint)
        sentence_id = stable_id("AHV2-SENT", f"{item.source_table}|{item.passage_id}|{item.concept_id}")
        role_tags = unique([item.sentence_role, SOURCE, "safe_primary" if item.category == "A" else "review_only_support"])
        role = item.sentence_role
        risk_label = "safe_definition_candidate" if item.category == "A" else "review_only"
        record_id = source_record_id_for_source(item, row)
        conn.execute(
            """
            INSERT INTO sentence_role_registry (
                sentence_id, passage_id, record_id, source_table, source_object, chapter_id,
                chapter_name, sentence_index, sentence_text, normalized_sentence_text,
                primary_role, role_tags_json, role_confidence, risk_label
            ) VALUES (
                :sentence_id, :passage_id, :record_id, :source_table, :source_object, :chapter_id,
                :chapter_name, :sentence_index, :sentence_text, :normalized_sentence_text,
                :primary_role, :role_tags_json, :role_confidence, :risk_label
            )
            ON CONFLICT(sentence_id) DO UPDATE SET
                sentence_text=excluded.sentence_text,
                normalized_sentence_text=excluded.normalized_sentence_text,
                primary_role=excluded.primary_role,
                role_tags_json=excluded.role_tags_json,
                role_confidence=excluded.role_confidence,
                risk_label=excluded.risk_label
            """,
            {
                "sentence_id": sentence_id,
                "passage_id": item.passage_id,
                "record_id": record_id,
                "source_table": item.source_table,
                "source_object": source_object_for_table(item.source_table),
                "chapter_id": row.get("chapter_id") or "",
                "chapter_name": row.get("chapter_name") or "",
                "sentence_index": 0,
                "sentence_text": sentence_text,
                "normalized_sentence_text": compact_text(sentence_text),
                "primary_role": role,
                "role_tags_json": json_text(role_tags),
                "role_confidence": "medium" if item.category == "A" else "review_only",
                "risk_label": risk_label,
            },
        )
        updates.append(
            {
                "candidate_id": item.candidate_id,
                "concept_id": item.concept_id,
                "canonical_term": item.canonical_term,
                "sentence_id": sentence_id,
                "primary_role": role,
                "role_tags": role_tags,
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
    source_object = source_record_id = source_evidence_level = ""
    if conn is not None:
        row = fetch_source_row(conn, item.source_table, item.passage_id)
        source_text = str(row.get("text") or "")
        primary_evidence_text = sentence_for_candidate(row, item.sentence_hint)
        source_object = source_object_for_table(item.source_table)
        source_record_id = source_record_id_for_source(item, row)
        source_evidence_level = evidence_level_for_source(item, row)
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


def registry_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "definition_term_registry": conn.execute("SELECT COUNT(*) FROM definition_term_registry").fetchone()[0],
        "retrieval_ready_definition_view": conn.execute("SELECT COUNT(*) FROM retrieval_ready_definition_view").fetchone()[0],
        "term_alias_registry": conn.execute("SELECT COUNT(*) FROM term_alias_registry").fetchone()[0],
        "learner_query_normalization_lexicon": conn.execute("SELECT COUNT(*) FROM learner_query_normalization_lexicon").fetchone()[0],
        "sentence_role_registry": conn.execute("SELECT COUNT(*) FROM sentence_role_registry").fetchone()[0],
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
            "previously support-only or weak learner definition materials",
        ],
        "excluded_existing_layers": [
            "AHV v1 promoted safe primary objects",
            "AHV v1 review-only single-character objects",
            "formula medium span objects",
        ],
        "candidates": [candidate_payload(item, conn) for item in CANDIDATES],
    }
    write_json(output_dir / "ahv2_candidate_pool_v1.json", payload)
    lines = [
        "# AHV2 Candidate Pool v1",
        "",
        f"- run_id: `{RUN_ID}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- category_counts: `{json.dumps(payload['category_counts'], ensure_ascii=False)}`",
        "",
        "| category | priority | term | source | query | decision |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["candidates"]:
        decision = "promote safe primary" if item["category"] == "A" else "support/review-only" if item["category"] == "B" else "reject promotion"
        lines.append(
            f"| {item['category']} | {item['candidate_priority']} | {item['canonical_term']} | "
            f"{item['source_table']}:{item['passage_id']} | {item['query']} | {decision} |"
        )
    write_md(output_dir / "ahv2_candidate_pool_v1.md", lines)


def write_snapshots(conn: sqlite3.Connection, output_dir: Path) -> None:
    write_json(
        output_dir / "definition_term_registry_ahv2_snapshot.json",
        table_rows(conn, "definition_term_registry", "canonical_term, concept_id"),
    )
    write_json(
        output_dir / "term_alias_registry_ahv2_snapshot.json",
        table_rows(conn, "term_alias_registry", "canonical_term, alias, alias_id"),
    )
    write_json(
        output_dir / "learner_query_normalization_ahv2_snapshot.json",
        table_rows(conn, "learner_query_normalization_lexicon", "entry_type, surface_form, target_term"),
    )
    write_json(
        output_dir / "sentence_role_registry_ahv2_snapshot.json",
        table_rows(conn, "sentence_role_registry", "source_table, passage_id, sentence_index"),
    )


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
    a_ids = [item.concept_id for item in a_items]
    b_ids = [item.concept_id for item in b_items]
    placeholders_a = ",".join("?" for _ in a_ids)
    placeholders_b = ",".join("?" for _ in b_ids)
    active_contains_count = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM learner_query_normalization_lexicon
        WHERE target_id IN ({placeholders_a})
          AND is_active = 1
          AND match_mode = 'contains'
        """,
        a_ids,
    ).fetchone()[0]
    support_active_lexicon_count = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM learner_query_normalization_lexicon
        WHERE target_id IN ({placeholders_b})
          AND is_active = 1
        """,
        b_ids,
    ).fetchone()[0]
    single_active_alias_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM term_alias_registry
        WHERE source = ?
          AND is_active = 1
          AND LENGTH(normalized_alias) < 2
        """,
        (SOURCE,),
    ).fetchone()[0]
    ambiguous_active_alias_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM term_alias_registry
        WHERE source = ?
          AND alias_type IN ('learner_risky', 'ambiguous', 'review_only_support')
          AND is_active = 1
        """,
        (SOURCE,),
    ).fetchone()[0]
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "summary": {
            "candidate_count": len(CANDIDATES),
            "category_A_count": len(a_items),
            "category_B_count": len(b_items),
            "category_C_count": len(c_items),
            "promoted_safe_primary_count": len(a_items),
            "support_only_registered_count": len(b_items),
            "rejected_count": len(c_items),
            "new_active_contains_learner_surface_count": active_contains_count,
            "support_active_lexicon_conflict_count": support_active_lexicon_count,
            "single_active_alias_count": single_active_alias_count,
            "risky_or_review_active_alias_count": ambiguous_active_alias_count,
        },
        "registry_counts_before": before_counts,
        "registry_counts_after": after_counts,
        "promoted_safe_primary": [candidate_payload(item, conn) for item in a_items],
        "support_only_registered": [candidate_payload(item, conn) for item in b_items],
        "rejected": [candidate_payload(item, conn) for item in c_items],
        "sentence_role_updates": sentence_updates,
    }
    write_json(output_dir / "ahv2_batch_upgrade_ledger_v1.json", payload)
    lines = [
        "# AHV2 Batch Upgrade Ledger v1",
        "",
        f"- run_id: `{RUN_ID}`",
        f"- candidate_count: `{payload['summary']['candidate_count']}`",
        f"- category_A_count: `{payload['summary']['category_A_count']}`",
        f"- category_B_count: `{payload['summary']['category_B_count']}`",
        f"- category_C_count: `{payload['summary']['category_C_count']}`",
        f"- promoted_safe_primary_count: `{payload['summary']['promoted_safe_primary_count']}`",
        f"- support_only_registered_count: `{payload['summary']['support_only_registered_count']}`",
        f"- rejected_count: `{payload['summary']['rejected_count']}`",
        f"- new_active_contains_learner_surface_count: `{payload['summary']['new_active_contains_learner_surface_count']}`",
        "",
        "## A Promoted",
        "",
    ]
    for item in a_items:
        lines.append(f"- `{item.canonical_term}` -> `{item.concept_id}` from `{item.source_table}:{item.passage_id}`")
    lines.extend(["", "## B Support/Review Only", ""])
    for item in b_items:
        lines.append(f"- `{item.canonical_term}` -> {item.review_only_reason}")
    lines.extend(["", "## C Rejected", ""])
    for item in c_items:
        lines.append(f"- `{item.canonical_term}` -> {item.rejection_reason}")
    write_md(output_dir / "ahv2_batch_upgrade_ledger_v1.md", lines)


def write_docs(doc_dir: Path) -> None:
    write_md(
        doc_dir / "ambiguous_high_value_evidence_upgrade_v2.md",
        [
            "# Ambiguous High Value Evidence Upgrade v2",
            "",
            "本轮目标是从 ambiguous/full-risk/B 级材料中新增第二批可审计 definition/concept objects，并把 batch upgrade、quality audit、adversarial regression 和 minimal fix 放在同一闭环内。",
            "",
            "## Frozen Boundaries",
            "",
            "- 不改 prompt、前端、API payload 顶层 contract、answer_mode、commentarial 主逻辑。",
            "- 不重新放开 raw `full:passages:*` 或 `full:ambiguous_passages:*` 直接进入 primary。",
            "- 不处理 formula medium span；formula query 只作为 guard。",
            "- AHV2 learner normalization 默认 `exact`，不得新增 active `contains` learner surface。",
            "",
            "## Runtime Shape",
            "",
            "- A 类写入 `definition_term_registry`，`promotion_source_layer=ambiguous_high_value_evidence_upgrade_v2_safe_primary`。",
            "- B 类写入 support/review-only registry row，`is_safe_primary_candidate=0`，不写 active learner normalization。",
            "- C 类只进入候选池和 ledger，不进入 runtime registry。",
        ],
    )
    write_md(
        doc_dir / "batch_promotion_policy_v2.md",
        [
            "# Batch Promotion Policy v2",
            "",
            "## A 类 safe primary",
            "",
            "- 只允许干净、独立、术语锚点明确的句段进入 object primary。",
            "- full/risk/ambiguous 抽句默认 `source_confidence=medium`。",
            "- `primary_evidence_text` 必须是切出的句段，不能是整段 raw passage。",
            "- canonical alias 和 learner-safe alias 均 exact-match。",
            "",
            "## B 类 support/review-only",
            "",
            "- 登记为 `promotion_state=review_only`，`is_safe_primary_candidate=0`。",
            "- 不写 active learner normalization；support alias 也保持 inactive。",
            "- 适合 weak answer 或 review_materials 参考，不进入 safe primary view。",
            "",
            "## C 类 reject",
            "",
            "- 只记录拒绝理由、风险来源和未来条件。",
            "- 不写 registry/view/normalization。",
        ],
    )
    write_md(
        doc_dir / "ahv2_adversarial_policy_v1.md",
        [
            "# AHV2 Adversarial Policy v1",
            "",
            "## Required Query Families",
            "",
            "- A canonical guard: every new AHV2 safe primary object must have at least one canonical query.",
            "- Similar concept false trigger: related or same-character concepts must not hit the wrong AHV2 object.",
            "- Disabled alias recheck: inactive risky/ambiguous aliases must not produce AHV2 normalization or primary.",
            "- Partial word / single-character tests: partial terms must not trigger AHV2 primary.",
            "- Non-definition intent: treatment, formula, mechanism, and comparison questions must not be hijacked by AHV2 definition primary.",
            "- Negative samples: modern or ordinary words must not hit AHV2 primary.",
            "- Guard blocks: formula, gold-safe definition, AHV v1, and review-only boundary queries must not regress.",
        ],
    )


def validate_candidate_counts() -> None:
    counts = {category: sum(1 for item in CANDIDATES if item.category == category) for category in ("A", "B", "C")}
    if not 28 <= len(CANDIDATES) <= 35:
        raise RuntimeError(f"candidate_count out of range: {len(CANDIDATES)}")
    if not 18 <= counts["A"] <= 22:
        raise RuntimeError(f"category A out of range: {counts['A']}")
    if not 6 <= counts["B"] <= 9:
        raise RuntimeError(f"category B out of range: {counts['B']}")
    if not 3 <= counts["C"] <= 5:
        raise RuntimeError(f"category C out of range: {counts['C']}")


def main() -> None:
    validate_candidate_counts()
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
            sentence_updates = upsert_sentence_roles(conn, a_b_candidates)
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
                "category_A_count": sum(1 for item in CANDIDATES if item.category == "A"),
                "category_B_count": sum(1 for item in CANDIDATES if item.category == "B"),
                "category_C_count": sum(1 for item in CANDIDATES if item.category == "C"),
                "output_dir": str(output_dir),
                "doc_dir": str(doc_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
