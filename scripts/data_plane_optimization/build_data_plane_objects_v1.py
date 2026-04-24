#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_optimization"
DEFAULT_DEFINITION_JSON = "artifacts/data_plane_optimization/definition_term_registry_v2.json"
DEFAULT_TERM_ALIAS_JSON = "artifacts/data_plane_optimization/term_alias_registry_v1.json"
DEFAULT_LEARNER_JSON = "artifacts/data_plane_optimization/learner_query_normalization_lexicon_v1.json"
DEFAULT_SENTENCE_ROLE_JSON = "artifacts/data_plane_optimization/sentence_role_registry_v1.json"

DOSAGE_PATTERN = re.compile(r"[一二三四五六七八九十百半]+(?:两|枚|升|合|铢|分|斤|丸|匕|个|片)")
FORMULA_TITLE_PATTERN = re.compile(r"[一-龥]+(?:汤|散|丸|饮)方[：:]")
VARIANT_NOTE_PATTERN = re.compile(r"(?:赵本|医统本|汪本|千金|成本|玉函|校记|注：|注「|一云|作「|无「|有「)")
EDITORIAL_NOTE_PATTERN = re.compile(r"(?:按：|按曰|详见|见卷|详于|详在|见前|见后)")
COMMENTARY_CITATION_PATTERN = re.compile(r"《[^》]{1,16}》曰")
DEFINITION_PATTERN = re.compile(r"(?:名曰|谓之|此名|之为病|何谓)")
TERM_BY_DISEASE_PATTERN = re.compile(r"^[一-龥]{1,8}为病(?:，|,)")
MEMBERSHIP_PATTERN = re.compile(r"者，[^。；]{0,20}?(?:药|病|证|脉|气|痹|结|烦|汗|逆|痿|温|冷|痛)也")
FORMULA_USAGE_PATTERN = re.compile(r"(?:主之|汤主之|可与|宜与|与[^。；]{0,24}(?:汤|散|丸|饮)|不可与)")
FORMULA_DECOCTION_PATTERN = re.compile(r"(?:^上|^右|以水|煮取|煑取|去滓|温服|分温|方寸匕)")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？；])")
PUNCTUATION_STRIP = "，。；：:、 “”\"'「」"


@dataclass(frozen=True)
class ConceptSeed:
    canonical_term: str
    concept_type: str
    primary_passage_id: str
    primary_source_table: str
    primary_sentence_hint: str
    primary_evidence_type: str
    definition_passage_ids: tuple[str, ...] = ()
    explanation_passage_ids: tuple[str, ...] = ()
    membership_passage_ids: tuple[str, ...] = ()
    query_aliases: tuple[str, ...] = ()
    notes: str = ""
    promotion_state: str = "safe_primary"
    source_confidence_override: str | None = None
    review_only_reason: str | None = None


def concept_seed(
    canonical_term: str,
    concept_type: str,
    primary_passage_id: str,
    primary_source_table: str,
    primary_sentence_hint: str,
    primary_evidence_type: str,
    *,
    definition_passage_ids: Iterable[str] = (),
    explanation_passage_ids: Iterable[str] = (),
    membership_passage_ids: Iterable[str] = (),
    query_aliases: Iterable[str] = (),
    notes: str,
    promotion_state: str = "safe_primary",
    source_confidence_override: str | None = None,
    review_only_reason: str | None = None,
) -> ConceptSeed:
    return ConceptSeed(
        canonical_term=canonical_term,
        concept_type=concept_type,
        primary_passage_id=primary_passage_id,
        primary_source_table=primary_source_table,
        primary_sentence_hint=primary_sentence_hint,
        primary_evidence_type=primary_evidence_type,
        definition_passage_ids=tuple(definition_passage_ids),
        explanation_passage_ids=tuple(explanation_passage_ids),
        membership_passage_ids=tuple(membership_passage_ids),
        query_aliases=tuple(query_aliases),
        notes=notes,
        promotion_state=promotion_state,
        source_confidence_override=source_confidence_override,
        review_only_reason=review_only_reason,
    )


CONCEPT_SEEDS: tuple[ConceptSeed, ...] = (
    concept_seed(
        "发汗药",
        "therapeutic_category",
        "ZJSHL-CH-006-P-0127",
        "records_passages",
        "发汗药，须温暖服者",
        "exact_term_explanation",
        explanation_passage_ids=("ZJSHL-CH-006-P-0127",),
        membership_passage_ids=("ZJSHL-CH-006-P-0120",),
        query_aliases=("发汗的药", "发汗类药"),
        notes="从 risk_only full passage 中抽出解释句与类属句，避免整段混入《金匮玉函》警示材料。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "下药",
        "therapeutic_category",
        "ZJSHL-CH-006-P-0120",
        "records_passages",
        "承气汤者，下药也",
        "term_membership_sentence",
        membership_passage_ids=("ZJSHL-CH-006-P-0120",),
        query_aliases=("泻下药", "通下药", "下法用药"),
        notes="优先提升直接类属句，解决二字短术语 definition query 缺少稳定锚点的问题。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "坏病",
        "disease_state_term",
        "ZJSHL-CH-008-P-0227",
        "records_passages",
        "谓之坏病",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-008-P-0226", "ZJSHL-CH-008-P-0227"),
        explanation_passage_ids=("ZJSHL-CH-008-P-0227",),
        query_aliases=("误治坏病",),
        notes="保留“为医所坏病”的解释语义，但不再让整段误治语境直接越权为 primary。",
    ),
    concept_seed(
        "阳结",
        "pulse_pattern_term",
        "ZJSHL-CH-003-P-0004",
        "records_main_passages",
        "名曰阳结",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-003-P-0004", "ZJSHL-CH-003-P-0017"),
        explanation_passage_ids=("ZJSHL-CH-003-P-0018",),
        query_aliases=("阳结证",),
        notes="作为已有 safe main 的脉象概念对象，补足解释句与别名。 ",
    ),
    concept_seed(
        "阴结",
        "pulse_pattern_term",
        "ZJSHL-CH-003-P-0004",
        "records_main_passages",
        "名曰阴结",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-003-P-0004", "ZJSHL-CH-003-P-0019"),
        explanation_passage_ids=("ZJSHL-CH-003-P-0020",),
        query_aliases=("阴结证",),
        notes="与阳结成对纳入脉象对象层，避免 pairwise 脉象问法只靠长段 recall。",
    ),
    concept_seed(
        "阳不足",
        "pulse_pattern_term",
        "ZJSHL-CH-003-P-0006",
        "records_main_passages",
        "名曰阳不足",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-003-P-0006",),
        explanation_passage_ids=("ZJSHL-CH-006-P-0117",),
        notes="保留“阴气上入阳中”的解释句，支撑术语解释与病机补充。",
    ),
    concept_seed(
        "阴不足",
        "pulse_pattern_term",
        "ZJSHL-CH-003-P-0006",
        "records_main_passages",
        "名曰阴不足",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-003-P-0006",),
        explanation_passage_ids=("ZJSHL-CH-006-P-0117",),
        notes="与阳不足成对纳入对象层，保留对“阳气下陷入阴中”的解释。",
    ),
    concept_seed(
        "关格",
        "disease_state_term",
        "ZJSHL-CH-004-P-0233",
        "records_main_passages",
        "名曰关格",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-004-P-0233",),
        explanation_passage_ids=("ZJSHL-CH-004-P-0188",),
        query_aliases=("关格不通",),
        notes="直接定义句较短，适合作为 safe primary；解释仍保留在 support 语境中。",
    ),
    concept_seed(
        "并病",
        "disease_state_term",
        "ZJSHL-CH-009-P-0064",
        "records_main_passages",
        "名曰并病",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-009-P-0008", "ZJSHL-CH-009-P-0064"),
        query_aliases=("并病证", "两经并病"),
        notes="把“合病 / 并病”里明确指向并病的句子对象化，避免 broad chapter long-form 直接压上来。",
    ),
    concept_seed(
        "消渴",
        "disease_state_term",
        "ZJSHL-CH-009-P-0137",
        "records_passages",
        "谓之消渴",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-009-P-0137",),
        explanation_passage_ids=("ZJSHL-CH-006-P-0129",),
        query_aliases=("多饮少尿", "消渴证"),
        notes="从 mixed-role full passage 中拆出精确命名句，保留“上焦燥 / 里热甚实”的解释补充。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "四逆",
        "syndrome_term",
        "ZJSHL-CH-015-P-0203",
        "records_main_passages",
        "四逆者，四肢不温也",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-015-P-0203",),
        query_aliases=("四肢不温", "手足不温"),
        notes="补齐普通学习者常见口语入口，解决‘四肢不温是什么’这类问法的归一化缺口。",
    ),
    concept_seed(
        "两感",
        "disease_state_term",
        "ZJSHL-CH-006-P-0057",
        "records_passages",
        "谓之两感",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-006-P-0057",),
        explanation_passage_ids=("ZJSHL-CH-006-P-0074",),
        query_aliases=("表里两感",),
        notes="full passage 句子极短且定义完整，可安全升格为概念对象。",
    ),
    concept_seed(
        "伏气",
        "disease_state_term",
        "ZJSHL-CH-004-P-0164",
        "records_passages",
        "谓之伏气",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-004-P-0164",),
        explanation_passage_ids=("ZJSHL-CH-004-P-0163", "ZJSHL-CH-004-P-0165"),
        query_aliases=("伏寒",),
        notes="通过 definition object 承接‘伏气 / 伏寒’这种短术语问法，而不再依赖整段脉法上下文。",
    ),
    concept_seed(
        "盗汗",
        "symptom_term",
        "ZJSHL-CH-010-P-0018",
        "records_passages",
        "谓之盗汗",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-010-P-0018",),
        query_aliases=("睡着出汗", "睡中出汗"),
        notes="将睡眠中出汗的口语问法数据化映射到 canonical term。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "奔豚",
        "disease_state_term",
        "ZJSHL-CH-009-P-0109",
        "records_passages",
        "名曰奔豚",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-009-P-0109",),
        explanation_passage_ids=("ZJSHL-CH-009-P-0108", "ZJSHL-CH-009-P-0295"),
        query_aliases=("肾气上冲", "气从少腹上冲"),
        notes="把‘欲作奔豚’和‘奔豚’的病机解释拆开，避免 query focus 被整段汤证语境稀释。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "小结胸",
        "disease_state_term",
        "ZJSHL-CH-010-P-0030",
        "records_passages",
        "谓之小结胸",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-010-P-0029", "ZJSHL-CH-010-P-0030"),
        query_aliases=("小结胸病",),
        notes="从结胸长段里抽出‘热气犹浅’对应的小结胸命名句，避免长段抢答。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "肺痿",
        "disease_state_term",
        "ZJSHL-CH-008-P-0235",
        "records_passages",
        "谓之肺痿",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-008-P-0235",),
        explanation_passage_ids=("ZJSHL-CH-015-P-0269",),
        notes="升格的是命名句，不是整段吐脓血病机长论。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "虚烦",
        "disease_state_term",
        "ZJSHL-CH-009-P-0157",
        "records_main_passages",
        "谓之虚烦",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-009-P-0156", "ZJSHL-CH-009-P-0157"),
        query_aliases=("烦而不得眠",),
        notes="优先抽取‘邪热乘虚客于胸中’对应的定义句，保留不得眠的解释补充。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "内烦",
        "disease_state_term",
        "ZJSHL-CH-009-P-0306",
        "records_passages",
        "谓之内烦",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-009-P-0306",),
        explanation_passage_ids=("ZJSHL-CH-009-P-0307",),
        query_aliases=("吐后内烦",),
        notes="full passage 的定义句短而完整，适合安全升格；解释句仍作为 support。",
    ),
    concept_seed(
        "时行之气",
        "pathology_term",
        "ZJSHL-CH-006-P-0015",
        "records_passages",
        "谓之时行之气",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-006-P-0015",),
        explanation_passage_ids=("ZJSHL-CH-006-P-0014", "ZJSHL-CH-006-P-0017"),
        query_aliases=("时气", "时行病气"),
        notes="为普通学习者的‘时气是什么意思’保留可直接命中的术语对象。",
    ),
    concept_seed(
        "胆瘅",
        "disease_state_term",
        "ZJSHL-CH-012-P-0214",
        "records_passages",
        "名曰胆瘅",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-012-P-0214",),
        query_aliases=("口苦病",),
        notes="从 full passage 中抽出明确命名句，避免整段经络解释压成 support-only。",
    ),
    concept_seed(
        "湿痹",
        "disease_state_term",
        "ZJSHL-CH-007-P-0170",
        "records_main_passages",
        "此名湿痹",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-007-P-0170",),
        explanation_passage_ids=("ZJSHL-CH-007-P-0171",),
        query_aliases=("湿邪痹痛",),
        notes="兼顾 canonical short definition 与 explanation sentence。",
    ),
    concept_seed(
        "脏结",
        "disease_state_term",
        "ZJSHL-CH-010-P-0002",
        "records_main_passages",
        "名曰脏结",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-010-P-0002",),
        explanation_passage_ids=("ZJSHL-CH-010-P-0003",),
        query_aliases=("藏结",),
        notes="把结胸 / 脏结边界对象化，降低‘结胸长段 + 邪结阴分’混杂对主证据的污染。",
    ),
    concept_seed(
        "水结胸",
        "disease_state_term",
        "ZJSHL-CH-010-P-0026",
        "records_main_passages",
        "谓之水结胸",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-010-P-0026",),
        query_aliases=("水饮结胸",),
        notes="明确标记为水饮结胸，而不是把整段结胸分型一并上浮。",
    ),
    concept_seed(
        "阳易",
        "disease_state_term",
        "ZJSHL-CH-017-P-0046",
        "records_passages",
        "名曰阳易",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-017-P-0046",),
        explanation_passage_ids=("ZJSHL-CH-017-P-0045",),
        query_aliases=("阴阳易",),
        notes="从 full passage 中拆出男女交感后各自的命名句，避免阴阳易整段混成一个主题包。",
    ),
    concept_seed(
        "阴易",
        "disease_state_term",
        "ZJSHL-CH-017-P-0046",
        "records_passages",
        "名曰阴易",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-017-P-0046",),
        query_aliases=("阴阳易",),
        notes="与阳易分成独立对象，避免同一长段里两个概念互相遮挡。",
    ),
    concept_seed(
        "风温",
        "disease_state_term",
        "ZJSHL-CH-008-P-0203",
        "records_main_passages",
        "风温为病",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-008-P-0203",),
        explanation_passage_ids=("ZJSHL-CH-008-P-0204",),
        query_aliases=("风温病",),
        notes="面向短问法‘风温是什么意思’，主对象只承接病名定义句，不承接逆治长论。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "结阴",
        "pulse_pattern_term",
        "ZJSHL-CH-010-P-0174",
        "records_main_passages",
        "名曰结阴",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-010-P-0174", "ZJSHL-CH-010-P-0175"),
        query_aliases=("结阴脉",),
        notes="补齐结代脉族中的短术语对象，避免只靠长段脉象解释命中。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "代阴",
        "pulse_pattern_term",
        "ZJSHL-CH-010-P-0174",
        "records_main_passages",
        "名曰代阴",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-010-P-0174", "ZJSHL-CH-010-P-0175"),
        query_aliases=("代阴脉",),
        notes="与结阴成对进入对象层，补足代脉相关短问法。",
        source_confidence_override="medium",
    ),
    concept_seed(
        "神丹",
        "drug_name_term",
        "ZJSHL-CH-006-P-0118",
        "records_passages",
        "神丹者，发汗之药也",
        "term_membership_sentence",
        membership_passage_ids=("ZJSHL-CH-006-P-0118",),
        notes="句子有一定类属信息，但上下文仍偏注释汇编，继续登记为 review-only。",
        promotion_state="review_only",
        source_confidence_override="review_only",
        review_only_reason="当前证据主要来自 full/annotation 汇编层，缺少足够独立的 canonical 支撑。",
    ),
    concept_seed(
        "两阳",
        "pathology_term",
        "ZJSHL-CH-009-P-0276",
        "records_passages",
        "谓之两阳",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-009-P-0276",),
        notes="命名句明确，但后文强依赖长段病机解释；本轮只登记不升格。",
        promotion_state="review_only",
        source_confidence_override="review_only",
        review_only_reason="单句命名可以抽出，但对普通学习者仍高度依赖后续病机展开，暂不作为 safe primary。",
    ),
    concept_seed(
        "将军",
        "drug_name_term",
        "ZJSHL-CH-010-P-0021",
        "records_passages",
        "谓之将军",
        "exact_term_definition",
        definition_passage_ids=("ZJSHL-CH-010-P-0021",),
        notes="更偏药名注解 / 训诂，不适合当前 learner-facing safe primary 闭环。",
        promotion_state="review_only",
        source_confidence_override="review_only",
        review_only_reason="属于药名解释层，不是当前 definition family 的高优先安全对象。",
    ),
)


QUERY_FAMILY_ENTRIES: tuple[dict[str, Any], ...] = (
    {
        "entry_type": "query_family",
        "match_mode": "prefix",
        "surface_form": "什么是",
        "intent_hint": "what_is",
        "canonical_query_template": "什么是{topic}",
        "confidence": 1.0,
        "notes": "普通定义问法前缀",
    },
    {
        "entry_type": "query_family",
        "match_mode": "prefix",
        "surface_form": "什么叫",
        "intent_hint": "what_is",
        "canonical_query_template": "什么是{topic}",
        "confidence": 0.96,
        "notes": "口语定义问法前缀",
    },
    {
        "entry_type": "query_family",
        "match_mode": "prefix",
        "surface_form": "何谓",
        "intent_hint": "what_is",
        "canonical_query_template": "什么是{topic}",
        "confidence": 0.95,
        "notes": "文言定义问法前缀",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "是什么",
        "intent_hint": "what_is",
        "canonical_query_template": "{topic}是什么",
        "confidence": 1.0,
        "notes": "普通定义问法后缀",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "是什么东西",
        "intent_hint": "what_is",
        "canonical_query_template": "{topic}是什么",
        "confidence": 0.86,
        "notes": "口语泛指问法后缀",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "是什么意思",
        "intent_hint": "what_means",
        "canonical_query_template": "{topic}是什么意思",
        "confidence": 1.0,
        "notes": "解释问法长后缀",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "什么意思",
        "intent_hint": "what_means",
        "canonical_query_template": "{topic}是什么意思",
        "confidence": 0.98,
        "notes": "解释问法短后缀",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "怎么理解",
        "intent_hint": "what_means",
        "canonical_query_template": "{topic}是什么意思",
        "confidence": 0.92,
        "notes": "学习者理解问法",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "是干什么的",
        "intent_hint": "what_means",
        "canonical_query_template": "{topic}是什么意思",
        "confidence": 0.95,
        "notes": "口语用途问法，优先回收到术语解释 family。",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "是做什么的",
        "intent_hint": "what_means",
        "canonical_query_template": "{topic}是什么意思",
        "confidence": 0.93,
        "notes": "口语用途问法变体",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "有什么用",
        "intent_hint": "what_means",
        "canonical_query_template": "{topic}是什么意思",
        "confidence": 0.9,
        "notes": "学习者口语用途问法",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "有啥用",
        "intent_hint": "what_means",
        "canonical_query_template": "{topic}是什么意思",
        "confidence": 0.84,
        "notes": "学习者口语用途问法缩略变体",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "是什么药",
        "intent_hint": "category_membership_open",
        "canonical_query_template": "{topic}是什么药",
        "confidence": 0.97,
        "notes": "药类归属问法",
    },
    {
        "entry_type": "query_family",
        "match_mode": "suffix",
        "surface_form": "属于什么药",
        "intent_hint": "category_membership_open",
        "canonical_query_template": "{topic}是什么药",
        "confidence": 0.95,
        "notes": "药类归属问法变体",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build data-plane optimization objects v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--definition-json", default=DEFAULT_DEFINITION_JSON)
    parser.add_argument("--term-alias-json", default=DEFAULT_TERM_ALIAS_JSON)
    parser.add_argument("--learner-json", default=DEFAULT_LEARNER_JSON)
    parser.add_argument("--sentence-role-json", default=DEFAULT_SENTENCE_ROLE_JSON)
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def stable_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def split_sentences(text: str) -> list[str]:
    normalized = compact_whitespace(text)
    if not normalized:
        return []
    pieces = SENTENCE_SPLIT_PATTERN.split(normalized)
    sentences = [piece.strip() for piece in pieces if piece.strip()]
    return sentences or [normalized]


def primary_role_for_sentence(sentence: str, source_object: str) -> tuple[str, list[str], str]:
    tags: list[str] = []
    normalized = compact_text(sentence)
    stripped = strip_inline_notes(sentence)
    analysis_sentence = stripped or compact_whitespace(sentence)

    if FORMULA_TITLE_PATTERN.search(analysis_sentence):
        tags.append("formula_name_sentence")
    if FORMULA_DECOCTION_PATTERN.search(analysis_sentence):
        tags.append("formula_decoction_sentence")
    if len(DOSAGE_PATTERN.findall(analysis_sentence)) >= 2 and "主之" not in analysis_sentence:
        tags.append("formula_composition_sentence")
    if FORMULA_USAGE_PATTERN.search(analysis_sentence):
        tags.append("formula_usage_sentence")
    if DEFINITION_PATTERN.search(analysis_sentence) or TERM_BY_DISEASE_PATTERN.search(analysis_sentence):
        tags.append("definition_sentence")
    if MEMBERSHIP_PATTERN.search(analysis_sentence):
        tags.append("membership_sentence")
    if stripped and stripped != compact_whitespace(sentence):
        tags.append("explanation_sentence")
    if COMMENTARY_CITATION_PATTERN.search(sentence):
        tags.append("commentary_like_sentence")
    if VARIANT_NOTE_PATTERN.search(sentence):
        tags.append("variant_note_sentence")
    if EDITORIAL_NOTE_PATTERN.search(sentence):
        tags.append("editorial_note_sentence")
    if source_object in {"passages", "annotations", "ambiguous_passages"}:
        tags.append("risk_sentence")
    if (
        "definition_sentence" not in tags
        and "membership_sentence" not in tags
        and "formula_name_sentence" not in tags
        and len(normalized) >= 6
        and any(marker in normalized for marker in map(compact_text, ("故", "所以", "则", "言", "是以", "可见")))
    ):
        tags.append("explanation_sentence")
    if not tags:
        tags.append("explanation_sentence" if len(normalized) >= 8 else "risk_sentence")

    primary_order = [
        "formula_name_sentence",
        "formula_composition_sentence",
        "formula_decoction_sentence",
        "formula_usage_sentence",
        "membership_sentence",
        "definition_sentence",
        "explanation_sentence",
        "commentary_like_sentence",
        "variant_note_sentence",
        "editorial_note_sentence",
        "risk_sentence",
    ]
    for role in primary_order:
        if role in tags:
            primary_role = role
            break
    else:
        primary_role = "risk_sentence"

    confidence = "high"
    if primary_role in {"explanation_sentence", "commentary_like_sentence"}:
        confidence = "medium"
    if primary_role in {"variant_note_sentence", "editorial_note_sentence", "risk_sentence"}:
        confidence = "low"
    return primary_role, unique(tags), confidence


def load_source_rows(conn: sqlite3.Connection) -> dict[str, dict[str, dict[str, Any]]]:
    table_map = {
        "records_main_passages": "main_passages",
        "records_passages": "passages",
        "records_annotations": "annotations",
        "risk_registry_ambiguous": "ambiguous_passages",
    }
    rows_by_table: dict[str, dict[str, dict[str, Any]]] = {}
    for table_name, source_object in table_map.items():
        rows = {}
        chapter_name_expr = "chapter_name" if table_name != "risk_registry_ambiguous" else "'' AS chapter_name"
        for row in conn.execute(
            f"""
            SELECT
                record_id,
                passage_id,
                chapter_id,
                {chapter_name_expr},
                source_object,
                evidence_level,
                display_allowed,
                risk_flag,
                text AS retrieval_text
            FROM {table_name}
            """
        ):
            payload = dict(row)
            payload["source_object"] = source_object
            payload["source_table"] = table_name
            rows[payload["passage_id"]] = payload
        rows_by_table[table_name] = rows
    return rows_by_table


def build_sentence_role_registry(rows_by_table: dict[str, dict[str, dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    by_passage: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    role_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()

    for table_name, table_rows in rows_by_table.items():
        for row in table_rows.values():
            sentences = split_sentences(row["retrieval_text"])
            for sentence_index, sentence in enumerate(sentences, start=1):
                primary_role, role_tags, role_confidence = primary_role_for_sentence(sentence, row["source_object"])
                sentence_id = stable_id(
                    "SROLE",
                    f"{table_name}|{row['passage_id']}|{sentence_index}|{compact_text(sentence)}",
                )
                risk_label = (
                    "review_only"
                    if primary_role in {"variant_note_sentence", "editorial_note_sentence", "commentary_like_sentence"}
                    or row["source_object"] in {"passages", "annotations", "ambiguous_passages"}
                    else "primary_candidate"
                )
                entry = {
                    "sentence_id": sentence_id,
                    "passage_id": row["passage_id"],
                    "record_id": row["record_id"],
                    "source_table": table_name,
                    "source_object": row["source_object"],
                    "chapter_id": row["chapter_id"],
                    "chapter_name": row["chapter_name"],
                    "sentence_index": sentence_index,
                    "sentence_text": sentence,
                    "normalized_sentence_text": compact_text(sentence),
                    "primary_role": primary_role,
                    "role_tags": role_tags,
                    "role_confidence": role_confidence,
                    "risk_label": risk_label,
                }
                entries.append(entry)
                by_passage[(table_name, row["passage_id"])].append(entry)
                role_counts[primary_role] += 1
                source_counts[row["source_object"]] += 1

    mixed_role_passages: list[dict[str, Any]] = []
    editorial_contaminated_passages: list[dict[str, Any]] = []
    commentary_contaminated_passages: list[dict[str, Any]] = []
    for (table_name, passage_id), sentence_entries in by_passage.items():
        distinct_roles = unique(
            role
            for entry in sentence_entries
            for role in entry["role_tags"]
            if role != "risk_sentence"
        )
        row = sentence_entries[0]
        if len(distinct_roles) >= 2:
            mixed_role_passages.append(
                {
                    "source_table": table_name,
                    "source_object": row["source_object"],
                    "passage_id": passage_id,
                    "chapter_id": row["chapter_id"],
                    "chapter_name": row["chapter_name"],
                    "role_tags": distinct_roles,
                    "sentence_count": len(sentence_entries),
                }
            )
        if {"variant_note_sentence", "editorial_note_sentence"} & set(distinct_roles):
            editorial_contaminated_passages.append(
                {
                    "source_table": table_name,
                    "source_object": row["source_object"],
                    "passage_id": passage_id,
                    "chapter_id": row["chapter_id"],
                    "chapter_name": row["chapter_name"],
                    "role_tags": distinct_roles,
                }
            )
        if "commentary_like_sentence" in distinct_roles:
            commentary_contaminated_passages.append(
                {
                    "source_table": table_name,
                    "source_object": row["source_object"],
                    "passage_id": passage_id,
                    "chapter_id": row["chapter_id"],
                    "chapter_name": row["chapter_name"],
                    "role_tags": distinct_roles,
                }
            )

    summary = {
        "generated_at_utc": now_utc(),
        "sentence_count": len(entries),
        "role_counts": dict(sorted(role_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "mixed_role_passage_count": len(mixed_role_passages),
        "mixed_role_passage_counts_by_source": dict(
            sorted(Counter(item["source_table"] for item in mixed_role_passages).items())
        ),
        "editorial_contaminated_passage_count": len(editorial_contaminated_passages),
        "editorial_contaminated_counts_by_source": dict(
            sorted(Counter(item["source_table"] for item in editorial_contaminated_passages).items())
        ),
        "commentary_contaminated_passage_count": len(commentary_contaminated_passages),
        "commentary_contaminated_counts_by_source": dict(
            sorted(Counter(item["source_table"] for item in commentary_contaminated_passages).items())
        ),
        "mixed_role_passage_examples": mixed_role_passages[:20],
        "editorial_contaminated_examples": editorial_contaminated_passages[:20],
        "commentary_contaminated_examples": commentary_contaminated_passages[:20],
    }
    return entries, summary


def resolve_passage_row(
    rows_by_table: dict[str, dict[str, dict[str, Any]]],
    preferred_table: str,
    passage_id: str,
) -> tuple[str, dict[str, Any]]:
    search_order = [preferred_table]
    search_order.extend(
        table_name
        for table_name in ("records_main_passages", "records_passages", "records_annotations", "risk_registry_ambiguous")
        if table_name not in search_order
    )
    for table_name in search_order:
        row = rows_by_table.get(table_name, {}).get(passage_id)
        if row is not None:
            return table_name, row
    raise KeyError(f"missing {preferred_table}:{passage_id}")


def sentence_for_passage(
    sentence_entries: list[dict[str, Any]],
    passage_id: str,
    source_table: str,
    sentence_hint: str,
) -> str:
    normalized_hint = compact_text(sentence_hint)
    candidates = [
        entry
        for entry in sentence_entries
        if entry["passage_id"] == passage_id and entry["source_table"] == source_table
    ]
    for entry in candidates:
        if normalized_hint and normalized_hint in entry["normalized_sentence_text"]:
            return strip_inline_notes(entry["sentence_text"]) or compact_whitespace(entry["sentence_text"])
    for entry in candidates:
        if normalized_hint and compact_text(entry["sentence_text"]).startswith(normalized_hint):
            return strip_inline_notes(entry["sentence_text"]) or compact_whitespace(entry["sentence_text"])
    if candidates:
        return strip_inline_notes(candidates[0]["sentence_text"]) or compact_whitespace(candidates[0]["sentence_text"])
    raise KeyError(f"missing sentence for {source_table}:{passage_id}")


def infer_source_confidence(seed: ConceptSeed, primary_sentence: str, primary_row: dict[str, Any]) -> str:
    if seed.source_confidence_override:
        return seed.source_confidence_override
    if seed.promotion_state != "safe_primary":
        return "review_only"
    if primary_row["source_table"] == "records_main_passages" and len(primary_sentence) <= 64:
        return "high"
    if primary_row["source_table"] == "records_passages" and len(primary_sentence) <= 64:
        return "medium"
    return "medium"


def build_definition_records(
    rows_by_table: dict[str, dict[str, dict[str, Any]]],
    sentence_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed in CONCEPT_SEEDS:
        actual_primary_table, primary_row = resolve_passage_row(
            rows_by_table,
            seed.primary_source_table,
            seed.primary_passage_id,
        )
        primary_sentence = sentence_for_passage(
            sentence_entries,
            seed.primary_passage_id,
            actual_primary_table,
            seed.primary_sentence_hint,
        )
        concept_id = stable_id("DPO", compact_text(seed.canonical_term))
        evidence_ids = unique(
            [seed.primary_passage_id]
            + list(seed.definition_passage_ids)
            + list(seed.explanation_passage_ids)
            + list(seed.membership_passage_ids)
        )
        chapter_ids = unique(
            primary_row["chapter_id"]
            for _ in [0]
        )
        for source_table in rows_by_table.values():
            for passage_id, row in source_table.items():
                if passage_id in evidence_ids and row["chapter_id"] not in chapter_ids:
                    chapter_ids.append(row["chapter_id"])

        query_aliases = unique([seed.canonical_term] + list(seed.query_aliases))
        retrieval_sentences = [primary_sentence]
        for passage_id in unique(list(seed.definition_passage_ids) + list(seed.explanation_passage_ids) + list(seed.membership_passage_ids)):
            for table_name in rows_by_table:
                row = rows_by_table[table_name].get(passage_id)
                if row is None:
                    continue
                sentence = sentence_for_passage(sentence_entries, passage_id, table_name, seed.canonical_term)
                if sentence:
                    retrieval_sentences.append(sentence)
                    break
        retrieval_sentences.extend(query_aliases)
        retrieval_text = "\n".join(unique(retrieval_sentences))
        source_confidence = infer_source_confidence(seed, primary_sentence, primary_row)
        records.append(
            {
                "concept_id": concept_id,
                "canonical_term": seed.canonical_term,
                "normalized_term": compact_text(seed.canonical_term),
                "concept_type": seed.concept_type,
                "definition_evidence_passage_ids_json": json_text(unique(seed.definition_passage_ids)),
                "explanation_evidence_passage_ids_json": json_text(unique(seed.explanation_passage_ids)),
                "membership_evidence_passage_ids_json": json_text(unique(seed.membership_passage_ids)),
                "primary_support_passage_id": seed.primary_passage_id,
                "primary_source_table": actual_primary_table,
                "primary_source_object": primary_row["source_object"],
                "primary_source_record_id": primary_row["record_id"],
                "primary_source_evidence_level": primary_row["evidence_level"],
                "source_passage_ids_json": json_text(evidence_ids),
                "chapter_ids_json": json_text(chapter_ids),
                "query_aliases_json": json_text(unique(seed.query_aliases)),
                "learner_surface_forms_json": json_text(unique(seed.query_aliases)),
                "primary_evidence_type": seed.primary_evidence_type,
                "primary_evidence_text": primary_sentence,
                "retrieval_text": retrieval_text,
                "normalized_retrieval_text": compact_text(retrieval_text),
                "source_confidence": source_confidence,
                "promotion_state": seed.promotion_state,
                "promotion_source_layer": "promoted_from_full_risk_layer"
                if actual_primary_table == "records_passages"
                else "safe_main_passage",
                "promotion_reason": (
                    "exact sentence promoted out of mixed full passage"
                    if actual_primary_table == "records_passages"
                    else "stable main passage concept sentence"
                ),
                "review_only_reason": seed.review_only_reason or "",
                "notes": seed.notes,
                "is_safe_primary_candidate": 1 if seed.promotion_state == "safe_primary" else 0,
                "is_active": 1,
            }
        )
    records.sort(key=lambda row: (0 if row["is_safe_primary_candidate"] else 1, row["canonical_term"]))
    return records


def build_term_alias_records(definition_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alias_records: list[dict[str, Any]] = []
    for record in definition_records:
        concept_id = record["concept_id"]
        canonical_term = record["canonical_term"]
        aliases = [canonical_term]
        aliases.extend(json.loads(record["query_aliases_json"]))
        block_review_only_learner_alias = (
            canonical_term == "胆瘅" and not bool(int(record.get("is_safe_primary_candidate") or 0))
        )
        if (
            record["concept_type"] in {"disease_state_term", "syndrome_term"}
            and not canonical_term.endswith("病")
            and not block_review_only_learner_alias
        ):
            aliases.append(canonical_term + "病")
        if record["concept_type"] == "pulse_pattern_term" and not canonical_term.endswith("脉"):
            aliases.append(canonical_term + "脉")
        if canonical_term == "脏结":
            aliases.append("藏结")

        for alias in unique(aliases):
            alias_type = "canonical" if alias == canonical_term else "learner_surface"
            confidence = 1.0 if alias == canonical_term else 0.9
            alias_records.append(
                {
                    "alias_id": stable_id("TAL", f"{concept_id}|{alias}"),
                    "alias": alias,
                    "normalized_alias": compact_text(alias),
                    "concept_id": concept_id,
                    "canonical_term": canonical_term,
                    "alias_type": alias_type,
                    "confidence": confidence,
                    "source": "data_plane_optimization_v1",
                    "notes": "canonical term alias" if alias == canonical_term else "learner-facing term surface",
                    "is_active": 1,
                }
            )
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in alias_records:
        key = (row["concept_id"], row["normalized_alias"])
        existing = deduped.get(key)
        if existing is None or float(row["confidence"]) > float(existing["confidence"]):
            deduped[key] = row
    return sorted(deduped.values(), key=lambda row: (row["canonical_term"], -row["confidence"], row["alias"]))


def build_learner_lexicon_records(
    definition_records: list[dict[str, Any]],
    term_alias_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    concept_by_id = {row["concept_id"]: row for row in definition_records}
    records: list[dict[str, Any]] = []
    for entry in QUERY_FAMILY_ENTRIES:
        records.append(
            {
                "lexicon_id": stable_id("LQN", f"{entry['entry_type']}|{entry['match_mode']}|{entry['surface_form']}"),
                "entry_type": entry["entry_type"],
                "match_mode": entry["match_mode"],
                "surface_form": entry["surface_form"],
                "normalized_surface_form": compact_text(entry["surface_form"]),
                "target_type": "query_family",
                "target_id": entry["intent_hint"],
                "target_term": "",
                "intent_hint": entry["intent_hint"],
                "canonical_query_template": entry["canonical_query_template"],
                "confidence": entry["confidence"],
                "source": "data_plane_optimization_v1",
                "notes": entry["notes"],
                "is_active": 1,
            }
        )

    for alias in term_alias_records:
        concept = concept_by_id[alias["concept_id"]]
        if not concept["is_safe_primary_candidate"]:
            continue
        records.append(
            {
                "lexicon_id": stable_id("LQN", f"term_surface|{alias['concept_id']}|{alias['normalized_alias']}"),
                "entry_type": "term_surface",
                "match_mode": "contains",
                "surface_form": alias["alias"],
                "normalized_surface_form": alias["normalized_alias"],
                "target_type": "concept_term",
                "target_id": alias["concept_id"],
                "target_term": alias["canonical_term"],
                "intent_hint": "what_is",
                "canonical_query_template": f"什么是{alias['canonical_term']}",
                "confidence": alias["confidence"],
                "source": "term_alias_registry_v1",
                "notes": alias["notes"],
                "is_active": 1,
            }
        )
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in records:
        key = (row["entry_type"], row["normalized_surface_form"], row["target_id"])
        existing = deduped.get(key)
        if existing is None or float(row["confidence"]) > float(existing["confidence"]):
            deduped[key] = row
    return sorted(deduped.values(), key=lambda row: (row["entry_type"], row["surface_form"], row["target_term"]))


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS retrieval_ready_definition_view;
        DROP TABLE IF EXISTS learner_query_normalization_lexicon;
        DROP TABLE IF EXISTS term_alias_registry;
        DROP TABLE IF EXISTS sentence_role_registry;
        DROP TABLE IF EXISTS definition_term_registry;

        CREATE TABLE definition_term_registry (
            concept_id TEXT PRIMARY KEY,
            canonical_term TEXT NOT NULL,
            normalized_term TEXT NOT NULL UNIQUE,
            concept_type TEXT NOT NULL,
            definition_evidence_passage_ids_json TEXT NOT NULL,
            explanation_evidence_passage_ids_json TEXT NOT NULL,
            membership_evidence_passage_ids_json TEXT NOT NULL,
            primary_support_passage_id TEXT NOT NULL,
            primary_source_table TEXT NOT NULL,
            primary_source_object TEXT NOT NULL,
            primary_source_record_id TEXT NOT NULL,
            primary_source_evidence_level TEXT NOT NULL,
            source_passage_ids_json TEXT NOT NULL,
            chapter_ids_json TEXT NOT NULL,
            query_aliases_json TEXT NOT NULL,
            learner_surface_forms_json TEXT NOT NULL,
            primary_evidence_type TEXT NOT NULL,
            primary_evidence_text TEXT NOT NULL,
            retrieval_text TEXT NOT NULL,
            normalized_retrieval_text TEXT NOT NULL,
            source_confidence TEXT NOT NULL,
            promotion_state TEXT NOT NULL,
            promotion_source_layer TEXT NOT NULL,
            promotion_reason TEXT NOT NULL,
            review_only_reason TEXT NOT NULL,
            notes TEXT NOT NULL,
            is_safe_primary_candidate INTEGER NOT NULL,
            is_active INTEGER NOT NULL
        );

        CREATE INDEX idx_definition_term_registry_normalized_term
            ON definition_term_registry(normalized_term);

        CREATE TABLE term_alias_registry (
            alias_id TEXT PRIMARY KEY,
            alias TEXT NOT NULL,
            normalized_alias TEXT NOT NULL,
            concept_id TEXT NOT NULL,
            canonical_term TEXT NOT NULL,
            alias_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            source TEXT NOT NULL,
            notes TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            FOREIGN KEY (concept_id) REFERENCES definition_term_registry(concept_id)
        );

        CREATE INDEX idx_term_alias_registry_normalized
            ON term_alias_registry(normalized_alias);

        CREATE TABLE learner_query_normalization_lexicon (
            lexicon_id TEXT PRIMARY KEY,
            entry_type TEXT NOT NULL,
            match_mode TEXT NOT NULL,
            surface_form TEXT NOT NULL,
            normalized_surface_form TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            target_term TEXT NOT NULL,
            intent_hint TEXT NOT NULL,
            canonical_query_template TEXT NOT NULL,
            confidence REAL NOT NULL,
            source TEXT NOT NULL,
            notes TEXT NOT NULL,
            is_active INTEGER NOT NULL
        );

        CREATE INDEX idx_learner_query_normalization_surface
            ON learner_query_normalization_lexicon(normalized_surface_form, entry_type, target_type);

        CREATE TABLE sentence_role_registry (
            sentence_id TEXT PRIMARY KEY,
            passage_id TEXT NOT NULL,
            record_id TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_object TEXT NOT NULL,
            chapter_id TEXT,
            chapter_name TEXT,
            sentence_index INTEGER NOT NULL,
            sentence_text TEXT NOT NULL,
            normalized_sentence_text TEXT NOT NULL,
            primary_role TEXT NOT NULL,
            role_tags_json TEXT NOT NULL,
            role_confidence TEXT NOT NULL,
            risk_label TEXT NOT NULL
        );

        CREATE INDEX idx_sentence_role_registry_passage
            ON sentence_role_registry(source_table, passage_id, sentence_index);

        CREATE VIEW retrieval_ready_definition_view AS
        SELECT
            concept_id,
            canonical_term,
            normalized_term,
            concept_type,
            definition_evidence_passage_ids_json,
            explanation_evidence_passage_ids_json,
            membership_evidence_passage_ids_json,
            primary_support_passage_id,
            primary_source_table,
            primary_source_object,
            primary_source_record_id,
            primary_source_evidence_level,
            source_passage_ids_json,
            chapter_ids_json,
            query_aliases_json,
            learner_surface_forms_json,
            primary_evidence_type,
            primary_evidence_text,
            retrieval_text,
            normalized_retrieval_text,
            source_confidence,
            promotion_state,
            promotion_source_layer,
            promotion_reason,
            review_only_reason,
            notes,
            'A' AS allowed_evidence_level
        FROM definition_term_registry
        WHERE is_active = 1
          AND is_safe_primary_candidate = 1;
        """
    )


def insert_records(
    conn: sqlite3.Connection,
    definition_records: list[dict[str, Any]],
    term_alias_records: list[dict[str, Any]],
    learner_records: list[dict[str, Any]],
    sentence_entries: list[dict[str, Any]],
) -> None:
    with conn:
        conn.executemany(
            """
            INSERT INTO definition_term_registry (
                concept_id,
                canonical_term,
                normalized_term,
                concept_type,
                definition_evidence_passage_ids_json,
                explanation_evidence_passage_ids_json,
                membership_evidence_passage_ids_json,
                primary_support_passage_id,
                primary_source_table,
                primary_source_object,
                primary_source_record_id,
                primary_source_evidence_level,
                source_passage_ids_json,
                chapter_ids_json,
                query_aliases_json,
                learner_surface_forms_json,
                primary_evidence_type,
                primary_evidence_text,
                retrieval_text,
                normalized_retrieval_text,
                source_confidence,
                promotion_state,
                promotion_source_layer,
                promotion_reason,
                review_only_reason,
                notes,
                is_safe_primary_candidate,
                is_active
            ) VALUES (
                :concept_id,
                :canonical_term,
                :normalized_term,
                :concept_type,
                :definition_evidence_passage_ids_json,
                :explanation_evidence_passage_ids_json,
                :membership_evidence_passage_ids_json,
                :primary_support_passage_id,
                :primary_source_table,
                :primary_source_object,
                :primary_source_record_id,
                :primary_source_evidence_level,
                :source_passage_ids_json,
                :chapter_ids_json,
                :query_aliases_json,
                :learner_surface_forms_json,
                :primary_evidence_type,
                :primary_evidence_text,
                :retrieval_text,
                :normalized_retrieval_text,
                :source_confidence,
                :promotion_state,
                :promotion_source_layer,
                :promotion_reason,
                :review_only_reason,
                :notes,
                :is_safe_primary_candidate,
                :is_active
            )
            """,
            definition_records,
        )
        conn.executemany(
            """
            INSERT INTO term_alias_registry (
                alias_id,
                alias,
                normalized_alias,
                concept_id,
                canonical_term,
                alias_type,
                confidence,
                source,
                notes,
                is_active
            ) VALUES (
                :alias_id,
                :alias,
                :normalized_alias,
                :concept_id,
                :canonical_term,
                :alias_type,
                :confidence,
                :source,
                :notes,
                :is_active
            )
            """,
            term_alias_records,
        )
        conn.executemany(
            """
            INSERT INTO learner_query_normalization_lexicon (
                lexicon_id,
                entry_type,
                match_mode,
                surface_form,
                normalized_surface_form,
                target_type,
                target_id,
                target_term,
                intent_hint,
                canonical_query_template,
                confidence,
                source,
                notes,
                is_active
            ) VALUES (
                :lexicon_id,
                :entry_type,
                :match_mode,
                :surface_form,
                :normalized_surface_form,
                :target_type,
                :target_id,
                :target_term,
                :intent_hint,
                :canonical_query_template,
                :confidence,
                :source,
                :notes,
                :is_active
            )
            """,
            learner_records,
        )
        conn.executemany(
            """
            INSERT INTO sentence_role_registry (
                sentence_id,
                passage_id,
                record_id,
                source_table,
                source_object,
                chapter_id,
                chapter_name,
                sentence_index,
                sentence_text,
                normalized_sentence_text,
                primary_role,
                role_tags_json,
                role_confidence,
                risk_label
            ) VALUES (
                :sentence_id,
                :passage_id,
                :record_id,
                :source_table,
                :source_object,
                :chapter_id,
                :chapter_name,
                :sentence_index,
                :sentence_text,
                :normalized_sentence_text,
                :primary_role,
                :role_tags_json,
                :role_confidence,
                :risk_label
            )
            """,
            [
                {
                    **entry,
                    "role_tags_json": json_text(entry["role_tags"]),
                }
                for entry in sentence_entries
            ],
        )


def build_formula_risk_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = [dict(row) for row in conn.execute("SELECT * FROM formula_canonical_registry")]
    medium_rows = [row for row in rows if row["source_confidence"] == "medium"]
    return {
        "formula_count": len(rows),
        "formula_medium_confidence_count": len(medium_rows),
        "formula_medium_confidence_examples": [
            {
                "formula_id": row["formula_id"],
                "canonical_name": row["canonical_name"],
                "primary_formula_passage_id": row["primary_formula_passage_id"],
                "formula_span_start_passage_id": row["formula_span_start_passage_id"],
                "formula_span_end_passage_id": row["formula_span_end_passage_id"],
            }
            for row in medium_rows[:20]
        ],
    }


def build_summary_payload(
    definition_records: list[dict[str, Any]],
    term_alias_records: list[dict[str, Any]],
    learner_records: list[dict[str, Any]],
    sentence_summary: dict[str, Any],
    formula_summary: dict[str, Any],
) -> dict[str, Any]:
    source_confidence_counts = Counter(row["source_confidence"] for row in definition_records)
    concept_type_counts = Counter(row["concept_type"] for row in definition_records)
    promotion_state_counts = Counter(row["promotion_state"] for row in definition_records)
    source_layer_counts = Counter(row["promotion_source_layer"] for row in definition_records)
    short_term_terms = [
        row["canonical_term"]
        for row in definition_records
        if row["is_safe_primary_candidate"] and len(row["normalized_term"]) <= 2
    ]
    short_query_terms = [
        row["canonical_term"]
        for row in definition_records
        if row["is_safe_primary_candidate"] and len(row["normalized_term"]) <= 3
    ]
    return {
        "generated_at_utc": now_utc(),
        "definition_term_count": len(definition_records),
        "safe_primary_candidate_count": sum(1 for row in definition_records if row["is_safe_primary_candidate"]),
        "review_only_count": sum(1 for row in definition_records if not row["is_safe_primary_candidate"]),
        "source_confidence_counts": dict(sorted(source_confidence_counts.items())),
        "concept_type_counts": dict(sorted(concept_type_counts.items())),
        "promotion_state_counts": dict(sorted(promotion_state_counts.items())),
        "promotion_source_layer_counts": dict(sorted(source_layer_counts.items())),
        "term_alias_count": len(term_alias_records),
        "learner_lexicon_count": len(learner_records),
        "short_term_safe_primary_count": len(short_term_terms),
        "short_term_safe_primary_terms": short_term_terms,
        "short_query_safe_primary_count": len(short_query_terms),
        "short_query_safe_primary_terms": short_query_terms,
        "sentence_role_summary": sentence_summary,
        "formula_risk_summary": formula_summary,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    definition_json = resolve_project_path(args.definition_json)
    term_alias_json = resolve_project_path(args.term_alias_json)
    learner_json = resolve_project_path(args.learner_json)
    sentence_role_json = resolve_project_path(args.sentence_role_json)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows_by_table = load_source_rows(conn)
        sentence_entries, sentence_summary = build_sentence_role_registry(rows_by_table)
        definition_records = build_definition_records(rows_by_table, sentence_entries)
        term_alias_records = build_term_alias_records(definition_records)
        learner_records = build_learner_lexicon_records(definition_records, term_alias_records)
        create_schema(conn)
        insert_records(conn, definition_records, term_alias_records, learner_records, sentence_entries)
        formula_summary = build_formula_risk_summary(conn)
        summary = build_summary_payload(
            definition_records,
            term_alias_records,
            learner_records,
            sentence_summary,
            formula_summary,
        )
    finally:
        conn.close()

    write_json(
        definition_json,
        {
            **summary,
            "registry_id": "definition_term_registry_v2",
            "concepts": definition_records,
        },
    )
    write_json(
        term_alias_json,
        {
            "generated_at_utc": now_utc(),
            "registry_id": "term_alias_registry_v1",
            "alias_count": len(term_alias_records),
            "aliases": term_alias_records,
        },
    )
    write_json(
        learner_json,
        {
            "generated_at_utc": now_utc(),
            "registry_id": "learner_query_normalization_lexicon_v1",
            "entry_count": len(learner_records),
            "entries": learner_records,
        },
    )
    write_json(
        sentence_role_json,
        {
            "generated_at_utc": now_utc(),
            "registry_id": "sentence_role_registry_v1",
            "summary": sentence_summary,
            "sentences": sentence_entries,
        },
    )

    print(f"updated {db_path}")
    print(f"wrote {definition_json}")
    print(f"wrote {term_alias_json}")
    print(f"wrote {learner_json}")
    print(f"wrote {sentence_role_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
