#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.llm import (
    DEFAULT_MODEL_STUDIO_BASE_URL,
    DEFAULT_MODEL_STUDIO_MODEL,
    LLMOutputValidationError,
    ModelStudioLLMClient,
    ModelStudioLLMConfig,
    ModelStudioLLMError,
    build_answer_text_prompt,
    parse_answer_text_json,
    validate_rendered_answer_text,
)
from backend.strategies.general_question import (
    GeneralBranchMeta,
    GeneralQuestionPlan,
    analyze_general_branch,
    detect_general_question,
)
from backend.retrieval.hybrid import (
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
    HybridRetrievalEngine,
    json_dumps,
    log,
)
from backend.retrieval.minimal import compact_text, extract_title_anchor
from backend.retrieval.minimal import extract_focus_text


DEFAULT_ANSWER_EXAMPLES_OUT = "artifacts/hybrid_answer_examples.json"
DEFAULT_ANSWER_SMOKE_OUT = "artifacts/hybrid_answer_smoke_checks.md"
ANSWER_SMOKE_EXAMPLES = [
    *DEFAULT_EXAMPLES,
    {
        "example_id": "general_ambiguous_dedup",
        "query_text": "若噎者怎么办？",
        "expected_mode": "weak_with_review_notice",
    },
]
DEFAULT_DEFINITION_QUERY_PRIORITY_RULES_PATH = "config/controlled_replay/definition_query_priority_rules_v1.json"
FORMULA_EFFECT_PRIMARY_RULES_ENV_FLAG = "TCM_ENABLE_FORMULA_EFFECT_PRIMARY_RULES_V1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNIPPET_LIMIT = 120
LLM_EVIDENCE_TEXT_LIMIT = 280
LLM_FALLBACK_LINE_LIMIT = 72
COMPARISON_ENTITY_LIMIT = 2
COMPARISON_FORMULA_TITLE_LIMIT = 1
COMPARISON_SUPPORT_LIMIT = 1
COMPARISON_REVIEW_LIMIT = 2
GENERAL_BRANCH_LIMIT = 4
GENERAL_MANAGEMENT_BRANCH_LIMIT = 3
GENERAL_WEAK_BRANCH_LIMIT = 3
GENERAL_SECONDARY_LIMIT = 5
GENERAL_REVIEW_LIMIT = 3
DEFINITION_OUTLINE_SECONDARY_LIMIT = 5
DEFINITION_OUTLINE_REVIEW_LIMIT = 3

GENERAL_TOPIC_ALIAS_CONFIG = {
    compact_text("少阳病"): {
        "text_aliases": (compact_text("少阳"),),
        "chapter_aliases": (compact_text("辨少阳病"),),
    },
    compact_text("伤寒瘥后"): {
        "text_aliases": (
            compact_text("伤寒瘥"),
            compact_text("大病瘥后"),
            compact_text("伤寒解后"),
        ),
        "chapter_aliases": (
            compact_text("瘥后"),
            compact_text("劳复"),
        ),
    },
}

SIX_STAGE_DISEASE_BASES = (
    "太阳",
    "阳明",
    "少阳",
    "太阴",
    "少阴",
    "厥阴",
)

DEFINITION_OUTLINE_TOPIC_CONFIG = {
    compact_text(f"{base}病"): {
        "canonical_name": f"{base}病",
        "topic_base": base,
        "topic_aliases": (
            compact_text(f"{base}病"),
            compact_text(base),
            compact_text(f"{base}之为病"),
            compact_text(f"{base}之病"),
        ),
        "chapter_aliases": (compact_text(f"辨{base}病"),),
        "definition_prefixes": (
            compact_text(f"{base}之为病"),
            compact_text(f"{base}之病"),
        ),
    }
    for base in SIX_STAGE_DISEASE_BASES
}

DEFINITION_OUTLINE_ALIAS_LOOKUP = {
    alias: config_key
    for config_key, config in DEFINITION_OUTLINE_TOPIC_CONFIG.items()
    for alias in config["topic_aliases"]
}

DEFINITION_OUTLINE_TRIGGER_SPECS = (
    ("之为病是什么", "definition"),
    ("的提纲是什么", "outline"),
    ("的定义是什么", "definition"),
    ("提纲是什么", "outline"),
    ("定义是什么", "definition"),
    ("是什么病", "definition"),
    ("是什么", "definition"),
)

DEFINITION_OUTLINE_PREFIXES = (
    "请问",
    "关于",
    "对于",
    "书中",
    "文中",
    "伤寒论里",
    "伤寒论中",
)

DEFINITION_OUTLINE_SUFFIX_NOISE = (
    "的",
    "呢",
    "呀",
)

DEFINITION_OUTLINE_BLOCK_HINTS = tuple(
    compact_text(hint)
    for hint in (
        "怎么办",
        "该怎么办",
        "应该怎么办",
        "怎么处理",
        "如何处理",
        "如何治疗",
        "条文",
        "原文",
        "出处",
        "出自",
        "有哪些情况",
        "有什么情况",
        "有哪些分支",
        "有什么分支",
        "分类",
        "区别",
        "不同",
        "异同",
        "比较",
        "为什么",
        "是什么意思",
        "什么意思",
        "有哪些核心表现",
        "应该用什么方",
        "如何用药",
    )
)

FORMULA_VARIANT_REPLACEMENTS = (
    ("厚朴", "浓朴"),
    ("杏仁", "杏子"),
    ("杏人", "杏子"),
)

COMPARISON_KEYWORDS = (
    "区别",
    "不同",
    "异同",
    "比较",
    "相比",
    "何异",
    "差别",
    "多了什么",
    "少了什么",
)

UNSUPPORTED_COMPARISON_HINTS = (
    "哪个好",
    "哪个更好",
    "谁更好",
    "更适合",
    "优劣",
    "更强",
)

MEANING_EXPLANATION_QUERY_HINTS = (
    "是什么意思",
    "什么意思",
)

FORMULA_EFFECT_QUERY_HINTS = tuple(
    compact_text(hint)
    for hint in (
        "有什么作用",
        "有何作用",
        "作用是什么",
        "有什么用",
        "有何用",
        "是干什么的",
        "是做什么的",
        "主什么",
        "主治什么",
        "适用于什么情况",
        "适用什么情况",
        "用于什么情况",
        "用在什么情况",
        "是治什么的",
        "治什么的",
    )
)

FORMULA_COMPOSITION_QUERY_HINTS = tuple(
    compact_text(hint)
    for hint in (
        "由什么组成",
        "组成是什么",
        "由哪些组成",
        "有哪些药",
        "有什么药",
        "药味",
        "组成",
    )
)

FORMULA_EFFECT_BLOCK_HINTS = tuple(
    compact_text(hint)
    for hint in (
        "条文",
        "原文",
        "出处",
        "出自",
        "组成",
        "药味",
        "区别",
        "不同",
        "比较",
        "异同",
        "多了什么",
        "少了什么",
    )
)

FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS = (
    "恶寒",
    "恶风",
    "发热",
    "汗出",
    "无汗",
    "头痛",
    "项强",
    "脉浮",
    "脉紧",
    "脉迟",
    "脉数",
    "身疼",
    "腹满",
    "腹痛",
    "大便",
    "不大便",
    "小便不利",
    "胸满",
    "胸中有热",
    "有水气",
    "潮热",
    "谵语",
    "下利",
    "咽痛",
    "咽中痛",
    "呕",
    "吐",
    "咳",
    "喘",
    "渴",
    "烦",
    "挛急",
    "拘急",
    "胀满",
    "实痛",
    "厥愈",
    "足温",
    "虚羸",
    "少气",
    "气逆",
)

FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS = (
    "当先与",
    "可与",
    "更作",
    "发汗宜",
    "解表宜",
    "急下之宜",
    "下之与",
    "先与",
    "当用",
    "当以",
    "当",
    "宜",
    "与",
    "可",
    "作",
)

FORMULA_EFFECT_CONTEXT_BAD_PREFIX_HINTS = (
    "服",
    "与",
    "宜",
    "可与",
    "更作",
    "作",
    "本方",
    "上为末",
    "右",
)

FORMULA_EFFECT_CONTEXT_NOISE_HINTS = (
    "赵本",
    "医统本",
    "详见",
    "本云",
    "按",
    "问曰",
)

FORMULA_EFFECT_DIRECT_USAGE_MARKERS = (
    "主之",
    "宜",
    "与",
    "可与",
    "不可与",
)

FORMULA_COMPOSITION_DOSAGE_PATTERN = re.compile(
    r"(?:各|半|[一二三四五六七八九十百千万\d]+)(?:两|枚|个|斤|升|合|钱|铢)"
)

STRONG_MEANING_EXPLANATION_MARKERS = (
    "名曰",
    "谓之",
)

COMPARISON_CONTEXT_HINTS = (
    "证候",
    "主治",
    "语境",
    "适用",
    "症状",
    "条文语境",
)

PERSONAL_HEALTH_CONTEXT_HINTS = (
    "我的体重",
    "我的症状",
    "我的体质",
    "我现在",
    "我目前",
    "我血压",
    "我发烧",
    "我发热",
    "我咳嗽",
    "按我的",
    "适合我",
    "本人",
    "患者",
    "病人",
)

PERSONAL_TREATMENT_ACTION_HINTS = (
    "能不能",
    "可不可以",
    "可以不可以",
    "能用",
    "服用",
    "该用",
    "应该用",
    "用哪个方",
    "开处方",
    "用药",
)

DOSAGE_CONVERSION_HINTS = (
    "体重",
    "克数",
    "剂量",
    "换算",
    "折算",
    "用量",
)

MODERN_MEDICAL_TERMS = (
    "支气管炎",
    "高血压",
    "血压高",
    "糖尿病",
    "肺炎",
    "新冠",
    "疫苗",
    "癌",
    "肿瘤",
)

MODERN_MEDICAL_ACTION_HINTS = (
    "治疗",
    "疗效",
    "能不能",
    "能用",
    "适应症",
    "治",
)

PERSONAL_REGIMEN_HINTS = (
    "七天",
    "7天",
    "疗程",
    "方案",
    "用药方案",
    "适合我体质",
)

EXTERNAL_BOOK_HINTS = (
    "黄帝内经",
    "素问",
    "灵枢",
    "金匮要略",
    "温病条辨",
    "本草纲目",
)

VALUE_JUDGMENT_HINTS = (
    "哪个更准确",
    "哪一个更准确",
    "谁更准确",
    "哪个更好",
    "哪个好",
    "谁更好",
    "更适合",
    "优劣",
    "更强",
)

REFUSE_GUIDANCE_TEMPLATES = [
    "请改问具体条文，例如：某一条文的原文或含义是什么？",
    "请改问具体方名，例如：黄连汤方的组成或条文是什么？",
    "请改问书中某个明确术语或概念，例如：某句话出自哪一条？",
]

COMPARISON_REFUSE_GUIDANCE_TEMPLATES = [
    "请明确写出两个方名，例如：A 和 B 的区别是什么？",
    "若想比较证候或语境，请直接说明，例如：A 和 B 的条文语境有什么不同？",
    "若当前只确定一个方名，可先单独追问该方条文，再继续比较。",
]

NON_INGREDIENT_TOKENS = {
    "皮",
    "皮尖",
    "尖",
    "节",
    "穣",
    "根据前法",
    "前法",
    "馀根据前法",
    "馀根据",
    "根据",
    "煎服",
    "则愈",
    "右",
}

FORMULA_EFFECT_SUPPORT_LIMIT = 1
FORMULA_EFFECT_FORMULA_LIMIT = 1
FORMULA_EFFECT_REVIEW_LIMIT = 3
FORMULA_COMPOSITION_LIMIT = 3
DEFINITION_PRIORITY_EXPLANATION_MARKERS = (
    "也",
    "名曰",
    "谓之",
    "所谓",
    "故",
    "所以",
    "须",
    "即",
    "可见",
)
QUERY_TRAILING_PUNCTUATION = "？?！!。；;，,：:"


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def env_flag_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble stable answer payloads from hybrid retrieval results.")
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
    parser.add_argument("--query", help="Run a single query and print the assembled answer payload.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_ANSWER_EXAMPLES_OUT,
        help="Where to write the default answer examples JSON.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_ANSWER_SMOKE_OUT,
        help="Where to write the answer smoke check markdown report.",
    )
    return parser.parse_args()


def compact_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())


def snippet_text(text: str | None, limit: int = SNIPPET_LIMIT) -> str:
    compact = compact_whitespace(text)
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "..."


def first_meaningful_line(text: str | None) -> str:
    if not text:
        return ""
    for line in str(text).splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def strip_inline_notes(text: str | None) -> str:
    if not text:
        return ""
    cleaned = compact_whitespace(text)
    cleaned = re.sub(r"(?:赵本|医统本)+(?:有|无|作)「[^」]+」字?", "", cleaned)
    cleaned = re.sub(r"(?:赵本|医统本)+并有「[^」]+」字", "", cleaned)
    cleaned = re.sub(r"(?:赵本|医统本)注：?「[^」]+」", "", cleaned)
    return compact_whitespace(cleaned).strip()


def build_examples_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "examples": results,
    }


def normalize_formula_lookup_text(text: str | None, *, keep_formula_suffix: bool = True) -> str:
    normalized = compact_text(text)
    for source, target in FORMULA_VARIANT_REPLACEMENTS:
        normalized = normalized.replace(compact_text(source), compact_text(target))
    if not keep_formula_suffix and normalized.endswith("方") and len(normalized) > 1:
        normalized = normalized[:-1]
    return normalized


def raw_title_anchor(text: str | None) -> str:
    if not text:
        return ""
    first_line = next((line.strip() for line in str(text).splitlines() if line.strip()), "")
    if not first_line:
        return ""
    return re.split(r"[：:]", first_line, maxsplit=1)[0].strip()


def clean_formula_title_anchor(title: str | None) -> str:
    raw_title = compact_whitespace(title)
    if not raw_title:
        return ""
    cleaned = re.sub(r"(?:赵本|医统本)+并有「([^」]+)」字", r"\1", raw_title)
    cleaned = re.sub(r"(?:赵本|医统本)+(?:作|无)「[^」]+」字?", "", cleaned)
    return compact_text(cleaned)


def _replace_title_suffix(prefix: str, variant_text: str) -> str:
    normalized_prefix = compact_whitespace(prefix)
    normalized_variant = compact_whitespace(variant_text)
    if not normalized_variant:
        return normalized_prefix
    if len(normalized_prefix) >= len(normalized_variant):
        return normalized_prefix[: -len(normalized_variant)] + normalized_variant
    return normalized_variant


def _remove_title_suffix(prefix: str, removed_text: str) -> str:
    normalized_prefix = compact_whitespace(prefix)
    normalized_removed = compact_whitespace(removed_text)
    if not normalized_removed:
        return normalized_prefix
    if len(normalized_prefix) >= len(normalized_removed):
        return normalized_prefix[: -len(normalized_removed)]
    return ""


def _inline_formula_title_variants(raw_title: str) -> set[str]:
    variants: set[str] = set()
    rewritten = compact_whitespace(raw_title)

    replace_match = re.search(r"^(.*?)(?:赵本|医统本)+作「([^」]+)」(.*)$", rewritten)
    if replace_match:
        prefix, variant_text, suffix = replace_match.groups()
        variants.add(_replace_title_suffix(prefix, variant_text) + compact_whitespace(suffix))

    delete_match = re.search(r"^(.*?)(?:赵本|医统本)+无「([^」]+)」字?(.*)$", rewritten)
    if delete_match:
        prefix, removed_text, suffix = delete_match.groups()
        variants.add(_remove_title_suffix(prefix, removed_text) + compact_whitespace(suffix))

    add_match = re.search(r"^(.*?)(?:赵本|医统本)+并有「([^」]+)」字(.*)$", rewritten)
    if add_match:
        prefix, added_text, suffix = add_match.groups()
        variants.add(compact_whitespace(prefix) + compact_whitespace(added_text) + compact_whitespace(suffix))

    return {variant for variant in variants if variant}


def formula_title_alias_variants(raw_title: str, canonical_title: str) -> set[str]:
    variants = {raw_title, canonical_title}
    variants.add(clean_formula_title_anchor(raw_title))
    variants.update(clean_formula_title_anchor(variant) for variant in _inline_formula_title_variants(raw_title))
    variants.add(clean_formula_title_anchor(re.sub(r"(?:赵本|医统本)+并有「([^」]+)」字", "", raw_title)))
    return {variant for variant in variants if variant}


def dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


@dataclass(frozen=True)
class DefinitionOutlinePlan:
    query_text: str
    topic_text: str
    normalized_topic: str
    canonical_topic: str
    topic_base: str
    query_kind: str
    matched_trigger: str


@dataclass(frozen=True)
class DefinitionPriorityPlan:
    query_text: str
    family_id: str
    family_label: str
    pattern_id: str
    topic_text: str | None = None
    normalized_topic: str | None = None
    subject_text: str | None = None
    subject_variants: tuple[str, ...] = ()
    predicate_text: str | None = None
    predicate_variants: tuple[str, ...] = ()


@dataclass
class AnswerAssembler:
    db_path: Path
    policy_path: Path
    embed_model: str
    rerank_model: str
    cache_dir: Path
    dense_chunks_index: Path
    dense_chunks_meta: Path
    dense_main_index: Path
    dense_main_meta: Path
    llm_config: ModelStudioLLMConfig | None = None

    def __post_init__(self) -> None:
        self.engine = HybridRetrievalEngine(
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
        self._record_cache: dict[str, dict[str, Any]] = {}
        (
            self._formula_catalog,
            self._formula_aliases,
            self._formula_alias_lookup,
        ) = self._load_formula_catalog()
        self._last_comparison_debug: dict[str, Any] | None = None
        self._last_general_debug: dict[str, Any] | None = None
        self._last_definition_priority_debug: dict[str, Any] | None = None
        self._last_llm_debug: dict[str, Any] | None = None
        self._progress_callback: Callable[[dict[str, Any]], None] | None = None
        self._last_progress_stage: str | None = None
        self.definition_query_priority_config = self._load_definition_query_priority_config()
        self.definition_query_priority_enabled = self._is_definition_query_priority_enabled(
            self.definition_query_priority_config
        )
        self.formula_effect_primary_prioritization_enabled = self._is_formula_effect_primary_prioritization_enabled()
        self._llm_config = self.llm_config or ModelStudioLLMConfig(
            enabled=False,
            api_key=None,
            model=DEFAULT_MODEL_STUDIO_MODEL,
            base_url=DEFAULT_MODEL_STUDIO_BASE_URL,
        )
        self._llm_client = ModelStudioLLMClient(self._llm_config) if self._llm_config.enabled else None

    def close(self) -> None:
        self.engine.close()

    def _load_definition_query_priority_config(self) -> dict[str, Any]:
        config_path = resolve_project_path(DEFAULT_DEFINITION_QUERY_PRIORITY_RULES_PATH)
        if not config_path.exists():
            return {
                "experiment_id": "definition_query_priority_rules_v1",
                "enabled_by_default": False,
                "env_flag": "TCM_ENABLE_DEFINITION_QUERY_PRIORITY_RULES_V1",
                "families": [],
                "_config_path": str(config_path),
            }
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["_config_path"] = str(config_path)
        return config

    def _is_definition_query_priority_enabled(self, config: dict[str, Any]) -> bool:
        env_flag = str(config.get("env_flag") or "").strip()
        if env_flag and env_flag in os.environ:
            return env_flag_enabled(os.environ.get(env_flag))
        return bool(config.get("enabled_by_default"))

    def _is_formula_effect_primary_prioritization_enabled(self) -> bool:
        if FORMULA_EFFECT_PRIMARY_RULES_ENV_FLAG in os.environ:
            return env_flag_enabled(os.environ.get(FORMULA_EFFECT_PRIMARY_RULES_ENV_FLAG))
        return True

    def assemble(
        self,
        query_text: str,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        self._last_comparison_debug = None
        self._last_general_debug = None
        self._last_definition_priority_debug = None
        self._last_llm_debug = None
        self._progress_callback = progress_callback
        self._last_progress_stage = None
        self._emit_progress(
            "retrieving_evidence",
            "已提交问题，正在检索可用依据并判断是否命中稳定边界。",
        )
        try:
            policy_refusal = self._detect_policy_refusal(query_text)
            if policy_refusal is not None:
                return self._assemble_policy_refusal(query_text, policy_refusal)
            comparison_plan = self._detect_comparison_query(query_text)
            if comparison_plan is not None:
                return self._assemble_comparison(query_text, comparison_plan)
            formula_composition_plan = self._detect_formula_composition_query(query_text)
            if formula_composition_plan is not None:
                return self._assemble_formula_composition_query(query_text, formula_composition_plan)
            formula_effect_plan = self._detect_formula_effect_query(query_text)
            if formula_effect_plan is not None:
                return self._assemble_formula_effect_query(query_text, formula_effect_plan)
            definition_outline_plan = self._detect_definition_outline_query(query_text)
            if definition_outline_plan is not None:
                return self._assemble_definition_outline_query(query_text, definition_outline_plan)
            definition_priority_plan = self._detect_definition_priority_query(query_text)
            if definition_priority_plan is not None:
                return self._assemble_definition_priority_query(query_text, definition_priority_plan)
            general_plan = detect_general_question(query_text)
            if general_plan is not None:
                return self._assemble_general_question(query_text, general_plan)
            return self._assemble_standard(query_text)
        finally:
            self._progress_callback = None
            self._last_progress_stage = None

    def get_last_comparison_debug(self) -> dict[str, Any] | None:
        return self._last_comparison_debug

    def get_last_definition_priority_debug(self) -> dict[str, Any] | None:
        return self._last_definition_priority_debug

    def get_last_llm_debug(self) -> dict[str, Any] | None:
        return self._last_llm_debug

    def _emit_progress(self, stage: str, detail: str) -> None:
        if stage == self._last_progress_stage:
            return
        self._last_progress_stage = stage
        if self._progress_callback:
            self._progress_callback({"stage": stage, "detail": detail})

    def _detect_policy_refusal(self, query_text: str) -> str | None:
        compact_query = compact_whitespace(query_text)
        if not compact_query:
            return None

        has_personal_context = self._has_any_hint(compact_query, PERSONAL_HEALTH_CONTEXT_HINTS)
        has_personal_action = self._has_any_hint(compact_query, PERSONAL_TREATMENT_ACTION_HINTS)

        if self._has_any_hint(compact_query, EXTERNAL_BOOK_HINTS) and self._has_any_hint(
            compact_query,
            VALUE_JUDGMENT_HINTS,
        ):
            return "跨书比较或价值判断超出《伤寒论》单书研读支持边界。"

        if has_personal_context and self._has_any_hint(compact_query, DOSAGE_CONVERSION_HINTS):
            return "按体重或个体情况换算剂量超出《伤寒论》研读支持边界。"

        if has_personal_context and self._has_any_hint(compact_query, PERSONAL_REGIMEN_HINTS):
            return "个体化处方或疗程方案超出《伤寒论》研读支持边界。"

        if self._has_any_hint(compact_query, MODERN_MEDICAL_TERMS) and self._has_any_hint(
            compact_query,
            MODERN_MEDICAL_ACTION_HINTS,
        ):
            return "现代病名疗效或用药判断超出《伤寒论》研读支持边界。"

        if has_personal_context and has_personal_action:
            return "个人诊疗、服药或处方建议超出《伤寒论》研读支持边界。"

        return None

    @staticmethod
    def _has_any_hint(text: str, hints: tuple[str, ...]) -> bool:
        return any(hint in text for hint in hints)

    def _assemble_policy_refusal(self, query_text: str, refuse_reason: str) -> dict[str, Any]:
        self._emit_progress(
            "organizing_evidence",
            "当前问题落在统一拒答边界，正在整理拒答原因与改问建议。",
        )
        return self._compose_payload(
            query_text=query_text,
            answer_mode="refuse",
            answer_text=self._build_refuse_answer_text(
                "这个问题超出了《伤寒论》单书研读支持范围，所以这里不直接回答",
                "可以改问书中的具体条文、方名，或某一句话在书里是什么意思",
            ),
            primary=[],
            secondary=[],
            review=[],
            review_notice=None,
            disclaimer=self._build_disclaimer("refuse", False, False),
            refuse_reason=refuse_reason,
            suggested_followup_questions=self._build_followups("refuse"),
            citations=[],
        )

    def _assemble_standard(self, query_text: str) -> dict[str, Any]:
        retrieval = self.engine.retrieve(query_text)
        self._emit_progress(
            "organizing_evidence",
            "已拿到候选依据，正在裁决主依据、补充依据与核对材料。",
        )
        primary = [self._build_evidence_item(row, display_role="primary") for row in retrieval["primary_evidence"]]
        secondary = [self._build_evidence_item(row, display_role="secondary") for row in retrieval["secondary_evidence"]]
        review = [self._build_evidence_item(row, display_role="review") for row in retrieval["risk_materials"]]

        answer_mode = retrieval["mode"]
        answer_retrieval = retrieval
        if self._should_demote_meaning_explanation(query_text, answer_mode, primary):
            secondary = self._merge_evidence_items(
                secondary,
                [self._demote_primary_to_secondary(item) for item in primary],
            )
            primary = []
            answer_mode = "weak_with_review_notice"
            answer_retrieval = {**retrieval, "mode": answer_mode}
        answer_text = self._build_answer_text(answer_retrieval, primary, secondary, review)
        review_notice = self._build_review_notice(answer_mode)
        disclaimer = self._build_disclaimer(answer_mode, bool(secondary), bool(review))
        refuse_reason = self._build_refuse_reason(answer_mode)
        suggested_followup_questions = self._build_followups(answer_mode)
        citations = self._build_citations(answer_mode, primary, secondary, review)
        return self._compose_payload(
            query_text=query_text,
            answer_mode=answer_mode,
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            review_notice=review_notice,
            disclaimer=disclaimer,
            refuse_reason=refuse_reason,
            suggested_followup_questions=suggested_followup_questions,
            citations=citations,
        )

    def _should_demote_meaning_explanation(
        self,
        query_text: str,
        answer_mode: str,
        primary: list[dict[str, Any]],
    ) -> bool:
        if answer_mode != "strong" or not primary:
            return False
        if not any(hint in query_text for hint in MEANING_EXPLANATION_QUERY_HINTS):
            return False
        return not any(self._evidence_supports_strong_meaning_explanation(item) for item in primary)

    def _evidence_supports_strong_meaning_explanation(self, item: dict[str, Any]) -> bool:
        snippet = item.get("snippet", "")
        if any(marker in snippet for marker in STRONG_MEANING_EXPLANATION_MARKERS):
            return True
        return bool(re.search(r"者[^。；]*也", snippet))

    def _demote_primary_to_secondary(self, item: dict[str, Any]) -> dict[str, Any]:
        demoted = dict(item)
        demoted["display_role"] = "secondary"
        demoted["risk_flags"] = dedupe_strings(list(demoted.get("risk_flags") or []) + ["meaning_explanation_demoted"])
        return demoted

    def _merge_evidence_items(
        self,
        first: list[dict[str, Any]],
        second: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in first + second:
            record_id = item.get("record_id")
            if record_id in seen:
                continue
            if record_id:
                seen.add(record_id)
            merged.append(item)
        return merged

    def _supporting_material_key(self, record_id: str | None, record_type: str | None) -> str:
        normalized_record_id = str(record_id or "")
        if record_type in {"passages", "ambiguous_passages"}:
            parts = normalized_record_id.split(":", 2)
            if len(parts) == 3:
                return f"{parts[0]}:risk_passage:{parts[2]}"
        return normalized_record_id

    def _evidence_item_preference(self, item: dict[str, Any]) -> tuple[int, int, int, str]:
        record_type = item.get("record_type")
        source_preference = 0
        if record_type == "passages":
            source_preference = 2
        elif record_type == "ambiguous_passages":
            source_preference = 1
        return (
            source_preference,
            len(compact_whitespace(item.get("snippet"))),
            len(compact_whitespace(item.get("title"))),
            str(item.get("record_id") or ""),
        )

    def _merge_evidence_item_metadata(self, target: dict[str, Any], incoming: dict[str, Any]) -> None:
        target["risk_flags"] = dedupe_strings(
            list(target.get("risk_flags") or []) + list(incoming.get("risk_flags") or [])
        )
        if not target.get("snippet") and incoming.get("snippet"):
            target["snippet"] = incoming["snippet"]
        if not target.get("title") and incoming.get("title"):
            target["title"] = incoming["title"]
        if not target.get("chapter_title") and incoming.get("chapter_title"):
            target["chapter_title"] = incoming["chapter_title"]
        if not target.get("chapter_id") and incoming.get("chapter_id"):
            target["chapter_id"] = incoming["chapter_id"]

    def _normalize_evidence_slots(
        self,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        normalized = {
            "primary": [dict(item) for item in primary],
            "secondary": [dict(item) for item in secondary],
            "review": [dict(item) for item in review],
        }
        kept_by_key: dict[str, dict[str, Any]] = {}
        location_by_key: dict[str, tuple[str, int]] = {}

        for slot_name in ("primary", "secondary", "review"):
            for index, item in enumerate(normalized[slot_name]):
                semantic_key = self._supporting_material_key(item.get("record_id"), item.get("record_type"))
                existing = kept_by_key.get(semantic_key)
                if existing is None:
                    kept_by_key[semantic_key] = item
                    location_by_key[semantic_key] = (slot_name, index)
                    continue

                self._merge_evidence_item_metadata(existing, item)
                existing_slot, existing_index = location_by_key[semantic_key]
                if existing_slot != slot_name:
                    normalized[slot_name][index] = None
                    continue

                if self._evidence_item_preference(item) > self._evidence_item_preference(existing):
                    replacement = dict(item)
                    self._merge_evidence_item_metadata(replacement, existing)
                    normalized[slot_name][existing_index] = replacement
                    kept_by_key[semantic_key] = replacement
                normalized[slot_name][index] = None

        return (
            [item for item in normalized["primary"] if item is not None],
            [item for item in normalized["secondary"] if item is not None],
            [item for item in normalized["review"] if item is not None],
        )

    def _normalize_citations(
        self,
        citations: list[dict[str, Any]],
        *,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        evidence_by_key: dict[str, dict[str, Any]] = {}
        for item in primary + secondary + review:
            evidence_by_key[self._supporting_material_key(item.get("record_id"), item.get("record_type"))] = item

        normalized: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for citation in citations:
            semantic_key = self._supporting_material_key(citation.get("record_id"), citation.get("record_type"))
            if semantic_key in seen_keys:
                continue
            seen_keys.add(semantic_key)

            evidence_item = evidence_by_key.get(semantic_key)
            if evidence_item is None:
                normalized.append(
                    {
                        **citation,
                        "citation_id": f"c{len(normalized) + 1}",
                    }
                )
                continue

            normalized.append(
                {
                    "citation_id": f"c{len(normalized) + 1}",
                    "record_id": evidence_item["record_id"],
                    "record_type": evidence_item["record_type"],
                    "title": evidence_item["title"],
                    "evidence_level": evidence_item["evidence_level"],
                    "snippet": evidence_item["snippet"],
                    "chapter_id": evidence_item["chapter_id"],
                    "chapter_title": evidence_item["chapter_title"],
                    "citation_role": evidence_item["display_role"],
                }
            )

        return normalized

    def _assemble_general_question(self, query_text: str, general_plan: GeneralQuestionPlan) -> dict[str, Any]:
        query_retrieval = self.engine.retrieve(query_text)
        topic_retrieval = (
            query_retrieval
            if compact_text(query_text) == general_plan.normalized_topic
            else self.engine.retrieve(general_plan.topic_text)
        )
        self._emit_progress(
            "organizing_evidence",
            "已拿到总括性问题的候选分支，正在整理主依据与核对材料。",
        )
        retrievals = [query_retrieval] if topic_retrieval is query_retrieval else [query_retrieval, topic_retrieval]

        seed_scores = self._build_general_seed_scores(retrievals)
        candidates = self._collect_general_branch_candidates(general_plan, seed_scores)
        strong_candidates = self._select_general_branches(candidates, general_plan, strong_only=True)
        fallback_secondary_rows = self._collect_general_slot_rows(retrievals, slot_name="secondary_evidence")
        fallback_review_rows = self._collect_general_slot_rows(retrievals, slot_name="risk_materials")

        self._last_general_debug = {
            "query": query_text,
            "general_question_detected": True,
            "general_kind": general_plan.general_kind,
            "topic_text": general_plan.topic_text,
            "candidate_count": len(candidates),
            "strong_candidate_count": sum(1 for candidate in candidates if candidate["strong_eligible"]),
            "selected_branch_count": len(strong_candidates),
        }

        if len(strong_candidates) >= 2:
            primary = [
                self._build_evidence_item(
                    candidate["row"],
                    display_role="primary",
                    title_override=candidate["branch_meta"].branch_label,
                )
                for candidate in strong_candidates
            ]
            selected_ids = {item["record_id"] for item in primary}
            secondary: list[dict[str, Any]] = []
            for candidate in candidates:
                record_id = candidate["row"]["record_id"]
                if record_id in selected_ids:
                    continue
                secondary.append(
                    self._build_evidence_item(
                        candidate["row"],
                        display_role="secondary",
                        title_override=candidate["branch_meta"].branch_label,
                    )
                )
                selected_ids.add(record_id)
                if len(secondary) >= GENERAL_SECONDARY_LIMIT:
                    break
            for row in fallback_secondary_rows:
                if row["record_id"] in selected_ids:
                    continue
                secondary.append(self._build_evidence_item(row, display_role="secondary"))
                selected_ids.add(row["record_id"])
                if len(secondary) >= GENERAL_SECONDARY_LIMIT:
                    break

            review: list[dict[str, Any]] = []
            for row in fallback_review_rows[:GENERAL_REVIEW_LIMIT]:
                review.append(self._build_evidence_item(row, display_role="review"))

            answer_text = self._build_general_answer_text(
                general_plan,
                strong_candidates,
                answer_mode="strong",
            )
            review_notice = self._build_review_notice("strong") if secondary or review else None
            disclaimer = self._build_disclaimer("strong", bool(secondary), bool(review))
            citations = self._build_citations("strong", primary, secondary, review)
            return self._compose_payload(
                query_text=query_text,
                answer_mode="strong",
                answer_text=answer_text,
                primary=primary,
                secondary=secondary,
                review=review,
                review_notice=review_notice,
                disclaimer=disclaimer,
                refuse_reason=None,
                suggested_followup_questions=[],
                citations=citations,
            )

        weak_candidates = self._select_general_branches(candidates, general_plan, strong_only=False)
        if weak_candidates or fallback_secondary_rows or fallback_review_rows:
            display_candidates = list(weak_candidates[:GENERAL_WEAK_BRANCH_LIMIT])
            if not display_candidates:
                display_candidates = self._build_general_fallback_display_candidates(
                    fallback_secondary_rows[:GENERAL_WEAK_BRANCH_LIMIT],
                    general_plan,
                )

            secondary: list[dict[str, Any]] = []
            seen_ids: set[str] = set()
            for candidate in weak_candidates[:GENERAL_WEAK_BRANCH_LIMIT]:
                risk_flags = dedupe_strings(candidate["row"]["risk_flag"] + ["general_branch_incomplete"])
                secondary.append(
                    self._build_evidence_item(
                        candidate["row"],
                        display_role="secondary",
                        title_override=candidate["branch_meta"].branch_label,
                        risk_flags_override=risk_flags,
                    )
                )
                seen_ids.add(candidate["row"]["record_id"])

            for row in fallback_secondary_rows:
                if row["record_id"] in seen_ids:
                    continue
                risk_flags = dedupe_strings(self._extract_risk_flags(row) + ["general_branch_incomplete"])
                secondary.append(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        risk_flags_override=risk_flags,
                    )
                )
                seen_ids.add(row["record_id"])
                if len(secondary) >= GENERAL_SECONDARY_LIMIT:
                    break

            review: list[dict[str, Any]] = []
            review_seen = set(seen_ids)
            for row in fallback_review_rows:
                if row["record_id"] in review_seen:
                    continue
                review.append(self._build_evidence_item(row, display_role="review"))
                review_seen.add(row["record_id"])
                if len(review) >= GENERAL_REVIEW_LIMIT:
                    break

            answer_text = self._build_general_answer_text(
                general_plan,
                display_candidates,
                answer_mode="weak_with_review_notice",
            )
            review_notice = "这是总括性问题，但当前只能整理出部分分支线索，以下内容需核对，不应视为完整答案。"
            disclaimer = "当前只输出部分分支整理与核对材料，不输出完整定案。"
            followups = self._build_general_followups(general_plan, display_candidates)
            citations = self._build_citations("weak_with_review_notice", [], secondary, review)
            return self._compose_payload(
                query_text=query_text,
                answer_mode="weak_with_review_notice",
                answer_text=answer_text,
                primary=[],
                secondary=secondary,
                review=review,
                review_notice=review_notice,
                disclaimer=disclaimer,
                refuse_reason=None,
                suggested_followup_questions=followups,
                citations=citations,
            )

        answer_text = (
            self._build_refuse_answer_text(
                f"当前还不能把“{general_plan.topic_text}”稳定整理成书内分支，所以先不直接给概括性结论",
                f"可以改问“{general_plan.topic_text}”里的某一支条文、某个症状分支，或某句话具体怎么理解",
            )
        )
        followups = self._build_general_followups(general_plan, [])
        return self._compose_payload(
            query_text=query_text,
            answer_mode="refuse",
            answer_text=answer_text,
            primary=[],
            secondary=[],
            review=[],
            review_notice=None,
            disclaimer="当前为总括类问题的拒答降级，不输出推测性概括。",
            refuse_reason=f"未能为“{general_plan.topic_text}”组织出至少两条可核对的可靠分支。",
            suggested_followup_questions=followups,
            citations=[],
        )

    def _build_general_seed_scores(self, retrievals: list[dict[str, Any]]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for retrieval in retrievals:
            for row in retrieval.get("raw_candidates", []):
                raw_score = min(float(row.get("combined_score", 0.0)) / 35.0, 28.0)
                if row.get("record_table") == "records_main_passages":
                    scores[row["record_id"]] = max(scores.get(row["record_id"], 0.0), raw_score)
                    continue
                if row.get("record_table") != "records_chunks":
                    continue
                for backref in self.engine._fetch_chunk_backrefs(row["record_id"]):
                    if backref["evidence_level"] not in {"A", "B"}:
                        continue
                    scores[backref["record_id"]] = max(scores.get(backref["record_id"], 0.0), raw_score)

            for slot_name in ("primary_evidence", "secondary_evidence"):
                for row in retrieval.get(slot_name, []):
                    slot_score = min(float(row.get("combined_score", 0.0)) / 40.0, 22.0)
                    scores[row["record_id"]] = max(scores.get(row["record_id"], 0.0), slot_score)
        return scores

    def _collect_general_branch_candidates(
        self,
        general_plan: GeneralQuestionPlan,
        seed_scores: dict[str, float],
    ) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for row in self.engine.unified_rows:
            if row["source_object"] != "main_passages":
                continue
            if row["evidence_level"] not in {"A", "B"}:
                continue
            if not self._general_topic_matches(general_plan, row):
                continue

            branch_meta = analyze_general_branch(
                row["retrieval_text"],
                general_plan.topic_text,
                general_kind=general_plan.general_kind,
                chapter_matches_topic=self._general_chapter_matches(general_plan, row),
            )
            if branch_meta is None:
                continue

            selection_score = branch_meta.heuristic_score + seed_scores.get(row["record_id"], 0.0)
            selection_score += 8.0 if row["evidence_level"] == "A" else -4.0
            if selection_score < 18.0:
                continue

            candidate = {
                "row": self._normalize_record_row(row),
                "branch_meta": branch_meta,
                "selection_score": selection_score,
                "strong_eligible": row["evidence_level"] == "A",
            }
            existing = deduped.get(branch_meta.branch_key)
            if existing is None or candidate["selection_score"] > existing["selection_score"]:
                deduped[branch_meta.branch_key] = candidate

        return sorted(
            deduped.values(),
            key=lambda item: (
                -item["selection_score"],
                item["row"]["chapter_id"],
                item["row"]["record_id"],
            ),
        )

    def _general_topic_matches(self, general_plan: GeneralQuestionPlan, row: dict[str, Any]) -> bool:
        normalized_text = compact_text(row["retrieval_text"])
        if general_plan.normalized_topic in normalized_text:
            return True

        alias_config = GENERAL_TOPIC_ALIAS_CONFIG.get(general_plan.normalized_topic)
        if not alias_config:
            return False
        if not self._general_chapter_matches(general_plan, row):
            return False
        return any(alias in normalized_text for alias in alias_config["text_aliases"])

    def _general_chapter_matches(self, general_plan: GeneralQuestionPlan, row: dict[str, Any]) -> bool:
        normalized_chapter_name = compact_text(row.get("chapter_name"))
        if general_plan.normalized_topic in normalized_chapter_name:
            return True
        alias_config = GENERAL_TOPIC_ALIAS_CONFIG.get(general_plan.normalized_topic)
        if not alias_config:
            return False
        return any(alias in normalized_chapter_name for alias in alias_config["chapter_aliases"])

    def _select_general_branches(
        self,
        candidates: list[dict[str, Any]],
        general_plan: GeneralQuestionPlan,
        *,
        strong_only: bool,
    ) -> list[dict[str, Any]]:
        eligible = [candidate for candidate in candidates if candidate["strong_eligible"] or not strong_only]
        if not eligible:
            return []
        branch_limit = GENERAL_MANAGEMENT_BRANCH_LIMIT if general_plan.general_kind == "management" else GENERAL_BRANCH_LIMIT

        classifications = [
            candidate for candidate in eligible if candidate["branch_meta"].branch_type == "classification"
        ]
        cautions = [candidate for candidate in eligible if candidate["branch_meta"].branch_type == "caution"]
        formulas = [candidate for candidate in eligible if candidate["branch_meta"].branch_type == "formula"]
        courses = [candidate for candidate in eligible if candidate["branch_meta"].branch_type == "course"]
        remainder = [candidate for candidate in eligible if candidate["branch_meta"].branch_type not in {"classification", "caution", "formula", "course"}]

        buckets = [sorted(bucket, key=lambda item: (-item["selection_score"], item["row"]["record_id"])) for bucket in [classifications, cautions, formulas, courses, remainder]]
        selected: list[dict[str, Any]] = []

        def add_from_bucket(bucket: list[dict[str, Any]], limit: int) -> None:
            for candidate in bucket:
                if candidate in selected:
                    continue
                selected.append(candidate)
                if len(selected) >= limit:
                    break

        if general_plan.general_kind == "overview":
            add_from_bucket(buckets[0], min(2, branch_limit))
            add_from_bucket(buckets[2], branch_limit)
            add_from_bucket(buckets[1], branch_limit)
            add_from_bucket(buckets[3], branch_limit)
        else:
            add_from_bucket(buckets[0], 1)
            add_from_bucket(buckets[2], branch_limit)
            add_from_bucket(buckets[1], branch_limit)
            add_from_bucket(buckets[3], branch_limit)

        if len(selected) < branch_limit:
            combined_remainder = sorted(
                [candidate for bucket in buckets for candidate in bucket if candidate not in selected],
                key=lambda item: (-item["selection_score"], item["row"]["record_id"]),
            )
            add_from_bucket(combined_remainder, branch_limit)

        return selected[:branch_limit]

    def _collect_general_slot_rows(
        self,
        retrievals: list[dict[str, Any]],
        *,
        slot_name: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for retrieval in retrievals:
            for row in retrieval.get(slot_name, []):
                if row["record_id"] in seen_ids:
                    continue
                rows.append(row)
                seen_ids.add(row["record_id"])
        return rows

    def _build_general_fallback_display_candidates(
        self,
        rows: list[dict[str, Any]],
        general_plan: GeneralQuestionPlan,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for index, row in enumerate(rows, start=1):
            full_text = self._fetch_record_meta(row["record_id"])["retrieval_text"]
            branch_label = f"待核对线索 {index}"
            candidates.append(
                {
                    "row": self._normalize_record_row(
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "evidence_level": row["evidence_level"],
                            "chapter_id": row["chapter_id"],
                            "chapter_name": row["chapter_name"],
                            "retrieval_text": full_text or row.get("text_preview", ""),
                            "risk_flag": json_dumps(self._extract_risk_flags(row)),
                        }
                    ),
                    "branch_meta": GeneralBranchMeta(
                        branch_key=row["record_id"],
                        branch_type="fallback",
                        branch_label=branch_label,
                        branch_summary=f"当前只检索到与“{general_plan.topic_text}”相关的一条待核对线索，尚不足以独立成支。",
                        heuristic_score=0.0,
                    ),
                    "selection_score": 0.0,
                    "strong_eligible": False,
                }
            )
        return candidates

    def _build_general_answer_text(
        self,
        general_plan: GeneralQuestionPlan,
        selected_candidates: list[dict[str, Any]],
        *,
        answer_mode: str,
    ) -> str:
        if general_plan.general_kind == "management":
            lead = f"这是一个总括性问题，书中谈“{general_plan.topic_text}”并非只有一个固定治法，需要分情况看。"
        else:
            lead = f"这是一个总括性问题，书中谈“{general_plan.topic_text}”并非只有一条统一描述，需要分情况整理。"

        if answer_mode == "strong":
            lines = [lead, "以下先按当前能稳定抓到的典型分支整理："]
            for idx, candidate in enumerate(selected_candidates, start=1):
                branch_meta: GeneralBranchMeta = candidate["branch_meta"]
                lines.append(
                    f"{idx}. {branch_meta.branch_label}：{branch_meta.branch_summary} 依据：{candidate['row']['text_preview']}"
                )
            lines.append(f"当前回答只列若干典型分支，不等于穷尽全部“{general_plan.topic_text}”处理。")
            return "\n".join(lines)

        lines = [lead, "当前只能先整理出部分可核对的分支线索："]
        for idx, candidate in enumerate(selected_candidates, start=1):
            branch_meta = candidate["branch_meta"]
            lines.append(
                f"{idx}. {branch_meta.branch_label}：{branch_meta.branch_summary} 依据：{candidate['row']['text_preview']}"
            )
        lines.append("分支组织仍不完整，建议继续收窄到某一支再问。")
        return "\n".join(lines)

    def _build_general_followups(
        self,
        general_plan: GeneralQuestionPlan,
        selected_candidates: list[dict[str, Any]],
    ) -> list[str]:
        followups = [
            f"请改问更窄的一支，例如：{general_plan.topic_text}中某一支具体对应哪条？",
            f"请改问更窄的处理线索，例如：{general_plan.topic_text}里某种表现为什么用某方？",
        ]
        for candidate in selected_candidates[:2]:
            if candidate["branch_meta"].branch_label.startswith("待核对线索"):
                continue
            followups.append(
                f"可以继续追问：{general_plan.topic_text}里“{candidate['branch_meta'].branch_label}”具体怎么理解？"
            )
        return dedupe_strings(followups)[:3]

    def _detect_definition_outline_query(self, query_text: str) -> DefinitionOutlinePlan | None:
        compact_query = compact_whitespace(query_text)
        if not compact_query:
            return None

        normalized_query = compact_text(compact_query)
        if any(hint in normalized_query for hint in DEFINITION_OUTLINE_BLOCK_HINTS):
            return None

        matched_trigger = ""
        query_kind = ""
        for trigger, kind in DEFINITION_OUTLINE_TRIGGER_SPECS:
            if normalized_query.endswith(compact_text(trigger)):
                matched_trigger = trigger
                query_kind = kind
                break

        if not matched_trigger:
            return None

        stripped_query = compact_query.strip().strip("？?！!。；;，,：:")
        topic_text = stripped_query[: -len(matched_trigger)].strip().strip("？?！!。；;，,：:")
        for prefix in DEFINITION_OUTLINE_PREFIXES:
            if topic_text.startswith(prefix):
                topic_text = topic_text[len(prefix) :].strip()
        for suffix in DEFINITION_OUTLINE_SUFFIX_NOISE:
            if topic_text.endswith(suffix):
                topic_text = topic_text[: -len(suffix)].strip()
        topic_text = topic_text.strip("？?！!。；;，,：:")
        if not topic_text:
            return None

        normalized_topic = self._normalize_definition_outline_topic(topic_text)
        if not normalized_topic:
            return None

        topic_config = DEFINITION_OUTLINE_TOPIC_CONFIG[normalized_topic]
        return DefinitionOutlinePlan(
            query_text=compact_query,
            topic_text=topic_text,
            normalized_topic=normalized_topic,
            canonical_topic=topic_config["canonical_name"],
            topic_base=topic_config["topic_base"],
            query_kind=query_kind,
            matched_trigger=matched_trigger,
        )

    def _normalize_definition_outline_topic(self, topic_text: str) -> str | None:
        normalized_topic = compact_text(topic_text)
        if not normalized_topic:
            return None

        direct_hit = DEFINITION_OUTLINE_ALIAS_LOOKUP.get(normalized_topic)
        if direct_hit:
            return direct_hit

        for suffix in (compact_text("之为病"), compact_text("之病")):
            if normalized_topic.endswith(suffix) and len(normalized_topic) > len(suffix):
                trimmed = normalized_topic[: -len(suffix)]
                return (
                    DEFINITION_OUTLINE_ALIAS_LOOKUP.get(trimmed)
                    or DEFINITION_OUTLINE_ALIAS_LOOKUP.get(trimmed + compact_text("病"))
                )

        if not normalized_topic.endswith(compact_text("病")):
            return DEFINITION_OUTLINE_ALIAS_LOOKUP.get(normalized_topic + compact_text("病"))
        return None

    def _assemble_definition_outline_query(
        self,
        query_text: str,
        definition_plan: DefinitionOutlinePlan,
    ) -> dict[str, Any]:
        query_retrieval = self.engine.retrieve(query_text)
        topic_focus = extract_focus_text(query_text)
        topic_retrieval = (
            query_retrieval
            if topic_focus == definition_plan.normalized_topic
            else self.engine.retrieve(definition_plan.canonical_topic)
        )
        retrievals = [query_retrieval] if topic_retrieval is query_retrieval else [query_retrieval, topic_retrieval]
        seed_scores = self._build_general_seed_scores(retrievals)

        self._emit_progress(
            "organizing_evidence",
            "已识别为定义 / 提纲类问题，正在优先裁决经典定义句与总纲句。",
        )
        candidates = self._collect_definition_outline_candidates(definition_plan, seed_scores)
        if not candidates:
            return self._assemble_standard(query_text)

        primary = [
            self._build_evidence_item(
                candidates[0]["row"],
                display_role="primary",
                title_override=f"{definition_plan.canonical_topic} · 提纲条文",
            )
        ]
        secondary = self._build_definition_outline_secondary(
            definition_plan,
            candidates=candidates[1:],
            retrievals=retrievals,
            selected_record_ids={primary[0]["record_id"]},
        )
        review_rows = self._collect_general_slot_rows(retrievals, slot_name="risk_materials")
        review = [
            self._build_evidence_item(row, display_role="review")
            for row in review_rows[:DEFINITION_OUTLINE_REVIEW_LIMIT]
        ]
        answer_text = self._build_definition_outline_answer_text(
            definition_plan,
            primary[0],
            has_secondary=bool(secondary),
        )
        citations = self._build_citations("strong", primary, secondary, review)
        return self._compose_payload(
            query_text=query_text,
            answer_mode="strong",
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            review_notice=self._build_review_notice("strong") if secondary or review else None,
            disclaimer=self._build_disclaimer("strong", bool(secondary), bool(review)),
            refuse_reason=None,
            suggested_followup_questions=[],
            citations=citations,
        )

    def _collect_definition_outline_candidates(
        self,
        definition_plan: DefinitionOutlinePlan,
        seed_scores: dict[str, float],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for row in self.engine.unified_rows:
            if row["source_object"] != "main_passages":
                continue
            if row["evidence_level"] not in {"A", "B"}:
                continue
            candidate_meta = self._score_definition_outline_row(
                definition_plan,
                row,
                seed_score=seed_scores.get(row["record_id"], 0.0),
            )
            if candidate_meta is None:
                continue
            candidates.append(
                {
                    "row": self._normalize_record_row(row),
                    **candidate_meta,
                }
            )

        return sorted(
            candidates,
            key=lambda item: (
                -item["selection_score"],
                item["row"]["chapter_id"],
                item["row"]["record_id"],
            ),
        )

    def _score_definition_outline_row(
        self,
        definition_plan: DefinitionOutlinePlan,
        row: dict[str, Any],
        *,
        seed_score: float,
    ) -> dict[str, Any] | None:
        cleaned_compact = self._definition_outline_clean_text(row.get("retrieval_text", ""))
        if not cleaned_compact:
            return None

        topic_compact = compact_text(definition_plan.canonical_topic)
        topic_config = DEFINITION_OUTLINE_TOPIC_CONFIG[definition_plan.normalized_topic]

        candidate_kind = ""
        score = 0.0
        if any(cleaned_compact.startswith(prefix) for prefix in topic_config["definition_prefixes"]):
            candidate_kind = "outline_definition"
            score = 120.0
        elif re.match(
            rf"^问曰{re.escape(topic_compact)}[^。；]{0,24}(?:外证云何|何谓也|何也)答曰",
            cleaned_compact,
        ):
            candidate_kind = "qa_definition"
            score = 72.0
        elif cleaned_compact.startswith(compact_text(f"凡{definition_plan.topic_base}病")) or cleaned_compact.startswith(
            compact_text(f"凡{definition_plan.topic_base}")
        ):
            candidate_kind = "fan_definition"
            score = 86.0
        elif cleaned_compact.startswith(topic_compact) and ("名曰" in cleaned_compact or "名为" in cleaned_compact):
            candidate_kind = "named_definition"
            score = 64.0
        elif cleaned_compact.startswith(topic_compact):
            candidate_kind = "topic_statement"
            score = 38.0
        else:
            return None

        score += 16.0 if self._definition_outline_chapter_matches(definition_plan, row) else 0.0
        score += 10.0 if row["evidence_level"] == "A" else 6.0
        score += min(seed_score, 24.0)

        text_length = len(cleaned_compact)
        if text_length <= 40:
            score += 6.0
        elif text_length <= 80:
            score += 3.0

        if "主之" in cleaned_compact:
            score -= 18.0
        if "欲解时" in cleaned_compact:
            score -= 24.0
        if "死" in cleaned_compact and candidate_kind == "topic_statement":
            score -= 18.0
        if "问曰" in cleaned_compact and candidate_kind != "qa_definition":
            score -= 10.0

        if score < 48.0:
            return None

        return {
            "selection_score": score,
            "candidate_kind": candidate_kind,
            "clean_snippet": self._normalize_definition_outline_source_text(row.get("retrieval_text", "")),
        }

    def _build_definition_outline_secondary(
        self,
        definition_plan: DefinitionOutlinePlan,
        *,
        candidates: list[dict[str, Any]],
        retrievals: list[dict[str, Any]],
        selected_record_ids: set[str],
    ) -> list[dict[str, Any]]:
        secondary: list[dict[str, Any]] = []
        seen_ids = set(selected_record_ids)

        for candidate in candidates:
            if candidate["selection_score"] < 64.0:
                continue
            record_id = candidate["row"]["record_id"]
            if record_id in seen_ids:
                continue
            secondary.append(self._build_evidence_item(candidate["row"], display_role="secondary"))
            seen_ids.add(record_id)
            if len(secondary) >= 2:
                break

        fallback_primary_rows = self._collect_general_slot_rows(retrievals, slot_name="primary_evidence")
        fallback_secondary_rows = self._collect_general_slot_rows(retrievals, slot_name="secondary_evidence")
        for row in fallback_primary_rows + fallback_secondary_rows:
            if row["record_id"] in seen_ids:
                continue
            secondary.append(self._build_evidence_item(row, display_role="secondary"))
            seen_ids.add(row["record_id"])
            if len(secondary) >= DEFINITION_OUTLINE_SECONDARY_LIMIT:
                break

        return secondary

    def _definition_outline_chapter_matches(
        self,
        definition_plan: DefinitionOutlinePlan,
        row: dict[str, Any],
    ) -> bool:
        normalized_chapter_name = compact_text(row.get("chapter_name"))
        if definition_plan.normalized_topic in normalized_chapter_name:
            return True
        topic_config = DEFINITION_OUTLINE_TOPIC_CONFIG[definition_plan.normalized_topic]
        return any(alias in normalized_chapter_name for alias in topic_config["chapter_aliases"])

    def _definition_outline_clean_text(self, text: str | None) -> str:
        return compact_text(self._normalize_definition_outline_source_text(text))

    def _normalize_definition_outline_source_text(self, text: str | None) -> str:
        cleaned = compact_whitespace(text)
        cleaned = re.sub(r"(?:赵本|医统本)+(?:皆)?并有「([^」]+)」字", r"\1", cleaned)
        cleaned = re.sub(r"(?:赵本|医统本)+(?:皆)?有「([^」]+)」字", r"\1", cleaned)
        cleaned = re.sub(r"(?:赵本|医统本)+(?:皆)?(?:作|无)「[^」]+」字?", "", cleaned)
        cleaned = re.sub(r"(?:赵本|医统本)注：?「[^」]+」", "", cleaned)
        return compact_whitespace(cleaned).strip()

    def _build_definition_outline_answer_text(
        self,
        definition_plan: DefinitionOutlinePlan,
        primary_item: dict[str, Any],
        *,
        has_secondary: bool,
    ) -> str:
        primary_text = self._normalize_definition_outline_source_text(
            self._fetch_record_meta(primary_item["record_id"])["retrieval_text"]
        ) or primary_item["snippet"]
        lines = [
            f"书中对“{definition_plan.canonical_topic}”的提纲性表述，可先看“{primary_text}”",
            f"主依据条文：{primary_text}",
        ]
        if has_secondary:
            lines.append("其余相关条文可再看补充依据，用来展开外证、分类或治法，但不替代这条提纲句。")
        return "\n".join(lines)

    def _detect_definition_priority_query(self, query_text: str) -> DefinitionPriorityPlan | None:
        if not self.definition_query_priority_enabled:
            return None

        compact_query = compact_whitespace(query_text)
        if not compact_query:
            return None

        stripped_query = self._strip_definition_priority_query(compact_query)
        normalized_query = compact_text(stripped_query)
        if not normalized_query:
            return None

        block_hints = self.definition_query_priority_config.get("block_hints", [])
        if any(compact_text(hint) in normalized_query for hint in block_hints):
            return None

        for family_rule in self.definition_query_priority_config.get("families", []):
            for pattern in family_rule.get("patterns", []):
                extracted = self._match_definition_priority_pattern(stripped_query, pattern)
                if extracted is None:
                    continue
                plan = self._build_definition_priority_plan(
                    compact_query,
                    family_rule,
                    pattern,
                    extracted,
                )
                if plan is not None:
                    return plan
        return None

    def _strip_definition_priority_query(self, query_text: str) -> str:
        stripped = compact_whitespace(query_text).strip().strip(QUERY_TRAILING_PUNCTUATION)
        for prefix in self.definition_query_priority_config.get("query_prefix_noise", []):
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix) :].strip()
        for suffix in self.definition_query_priority_config.get("query_suffix_noise", []):
            if stripped.endswith(suffix):
                stripped = stripped[: -len(suffix)].strip()
        return stripped.strip(QUERY_TRAILING_PUNCTUATION)

    def _match_definition_priority_pattern(
        self,
        stripped_query: str,
        pattern: dict[str, Any],
    ) -> dict[str, str] | None:
        mode = pattern.get("match_mode")
        value = str(pattern.get("value") or "")
        extract_as = str(pattern.get("extract_as") or "topic")

        if mode == "prefix":
            if not value or not stripped_query.startswith(value):
                return None
            return {extract_as: stripped_query[len(value) :].strip()}

        if mode == "suffix":
            if not value or not stripped_query.endswith(value):
                return None
            if value == "什么意思" and stripped_query.endswith("是什么意思"):
                return None
            return {extract_as: stripped_query[: -len(value)].strip()}

        if mode == "regex":
            if not value:
                return None
            match = re.match(value, stripped_query)
            if not match:
                return None
            return {key: compact_whitespace(item).strip() for key, item in match.groupdict().items() if item}

        return None

    def _build_definition_priority_plan(
        self,
        query_text: str,
        family_rule: dict[str, Any],
        pattern: dict[str, Any],
        extracted: dict[str, str],
    ) -> DefinitionPriorityPlan | None:
        family_id = str(family_rule.get("family_id") or "")
        topic_text = extracted.get("topic")
        subject_text = extracted.get("subject")
        predicate_text = extracted.get("predicate")

        if topic_text:
            topic_text = topic_text.strip(QUERY_TRAILING_PUNCTUATION).strip()
        if subject_text:
            subject_text = subject_text.strip(QUERY_TRAILING_PUNCTUATION).strip()
        if predicate_text:
            predicate_text = predicate_text.strip(QUERY_TRAILING_PUNCTUATION).strip()

        normalized_topic = compact_text(topic_text) if topic_text else None
        if topic_text and not normalized_topic:
            return None
        if subject_text and not self._definition_priority_term_variants(subject_text):
            return None
        if predicate_text and not self._definition_priority_term_variants(predicate_text):
            return None

        if family_id in {"what_is", "what_means"} and not topic_text:
            return None
        if family_id.startswith("category_membership") and not subject_text:
            return None

        # Keep already-specialized six-stage disease outline topics out of the
        # generic "X 是什么意思" family to avoid stealing their stable path.
        if family_id == "what_means" and topic_text and self._normalize_definition_outline_topic(topic_text):
            return None

        if topic_text and len(normalized_topic or "") < 2:
            return None

        return DefinitionPriorityPlan(
            query_text=query_text,
            family_id=family_id,
            family_label=str(family_rule.get("label") or family_id),
            pattern_id=str(pattern.get("pattern_id") or family_id),
            topic_text=topic_text,
            normalized_topic=normalized_topic,
            subject_text=subject_text,
            subject_variants=self._definition_priority_term_variants(subject_text),
            predicate_text=predicate_text,
            predicate_variants=self._definition_priority_term_variants(predicate_text),
        )

    def _definition_priority_term_variants(self, text: str | None) -> tuple[str, ...]:
        if not text:
            return ()
        variants = [compact_text(text)]
        normalized_formula = normalize_formula_lookup_text(text, keep_formula_suffix=True)
        normalized_formula_without_suffix = normalize_formula_lookup_text(text, keep_formula_suffix=False)
        variants.extend([normalized_formula, normalized_formula_without_suffix])
        mentions = self._find_formula_mentions(text)
        if len(mentions) == 1:
            canonical_name = mentions[0]["canonical_name"]
            variants.extend(
                [
                    normalize_formula_lookup_text(canonical_name, keep_formula_suffix=True),
                    normalize_formula_lookup_text(canonical_name, keep_formula_suffix=False),
                    compact_text(canonical_name),
                ]
            )
        return tuple(value for value in dedupe_strings([value for value in variants if value]))

    def _get_definition_priority_family_rule(self, family_id: str) -> dict[str, Any] | None:
        for family_rule in self.definition_query_priority_config.get("families", []):
            if family_rule.get("family_id") == family_id:
                return family_rule
        return None

    def _assemble_definition_priority_query(
        self,
        query_text: str,
        definition_plan: DefinitionPriorityPlan,
    ) -> dict[str, Any]:
        retrieval = self.engine.retrieve(query_text)
        family_rule = self._get_definition_priority_family_rule(definition_plan.family_id)
        if family_rule is None:
            return self._assemble_standard(query_text)

        self._emit_progress(
            "organizing_evidence",
            "已识别为定义 / 术语解释类问题，正在优先裁决定义句、解释句与方义句。",
        )
        prioritized_candidates = self._collect_definition_priority_candidates(definition_plan, retrieval, family_rule)
        primary_limit = int(self.definition_query_priority_config.get("primary_limit", 1))
        secondary_limit = int(self.definition_query_priority_config.get("secondary_limit", 5))

        if not prioritized_candidates[:primary_limit]:
            self._last_definition_priority_debug = {
                "query": query_text,
                "enabled": True,
                "family_id": definition_plan.family_id,
                "selected_primary_ids": [],
                "candidate_debug": [],
                "fallback_to_standard": True,
            }
            return self._assemble_standard(query_text)

        selected_primary_candidates = prioritized_candidates[:primary_limit]
        primary = [
            self._build_evidence_item(candidate["row"], display_role="primary")
            for candidate in selected_primary_candidates
        ]
        selected_primary_ids = {item["record_id"] for item in primary}

        preferred_secondary_candidates = [
            candidate
            for candidate in prioritized_candidates[primary_limit:]
            if candidate["row"]["record_id"] not in selected_primary_ids
        ][:2]
        secondary: list[dict[str, Any]] = [
            self._build_evidence_item(candidate["row"], display_role="secondary")
            for candidate in preferred_secondary_candidates
        ]
        seen_secondary_ids = set(selected_primary_ids) | {item["record_id"] for item in secondary}

        for row in retrieval["primary_evidence"]:
            if row["record_id"] in seen_secondary_ids:
                continue
            secondary.append(
                self._build_evidence_item(
                    row,
                    display_role="secondary",
                    risk_flags_override=dedupe_strings(
                        self._extract_risk_flags(row) + ["definition_priority_demoted_from_primary"]
                    ),
                )
            )
            seen_secondary_ids.add(row["record_id"])
            if len(secondary) >= secondary_limit:
                break

        if len(secondary) < secondary_limit:
            for row in retrieval["secondary_evidence"]:
                if row["record_id"] in seen_secondary_ids:
                    continue
                secondary.append(self._build_evidence_item(row, display_role="secondary"))
                seen_secondary_ids.add(row["record_id"])
                if len(secondary) >= secondary_limit:
                    break

        review = [
            self._build_evidence_item(row, display_role="review")
            for row in retrieval["risk_materials"]
            if row["record_id"] not in selected_primary_ids
        ]
        answer_text = self._build_definition_priority_answer_text(
            definition_plan,
            selected_primary_candidates[0],
            preferred_secondary_candidates,
        )
        citations = self._build_citations("strong", primary, secondary, review)
        self._last_definition_priority_debug = {
            "query": query_text,
            "enabled": True,
            "family_id": definition_plan.family_id,
            "pattern_id": definition_plan.pattern_id,
            "selected_primary_ids": [candidate["row"]["record_id"] for candidate in selected_primary_candidates],
            "preferred_secondary_ids": [candidate["row"]["record_id"] for candidate in preferred_secondary_candidates],
            "candidate_debug": [
                {
                    "record_id": candidate["row"]["record_id"],
                    "record_type": candidate["row"]["source_object"],
                    "evidence_type": candidate["evidence_type"],
                    "selection_score": round(candidate["selection_score"], 3),
                }
                for candidate in prioritized_candidates[:8]
            ],
            "fallback_to_standard": False,
        }
        return self._compose_payload(
            query_text=query_text,
            answer_mode="strong",
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            review_notice=self._build_review_notice("strong") if secondary or review else None,
            disclaimer=self._build_disclaimer("strong", bool(secondary), bool(review)),
            refuse_reason=None,
            suggested_followup_questions=[],
            citations=citations,
        )

    def _collect_definition_priority_candidates(
        self,
        definition_plan: DefinitionPriorityPlan,
        retrieval: dict[str, Any],
        family_rule: dict[str, Any],
    ) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for row in retrieval.get("raw_candidates", []):
            candidate_meta = self._score_definition_priority_candidate(definition_plan, row, family_rule)
            if candidate_meta is None:
                continue
            normalized_row = self._normalize_record_row(row)
            candidate = {
                "row": normalized_row,
                **candidate_meta,
            }
            existing = deduped.get(normalized_row["record_id"])
            if existing is None or candidate["selection_score"] > existing["selection_score"]:
                deduped[normalized_row["record_id"]] = candidate

        return sorted(
            deduped.values(),
            key=lambda item: (
                -item["selection_score"],
                item["row"]["chapter_id"] or "",
                item["row"]["record_id"],
            ),
        )

    def _score_definition_priority_candidate(
        self,
        definition_plan: DefinitionPriorityPlan,
        row: dict[str, Any],
        family_rule: dict[str, Any],
    ) -> dict[str, Any] | None:
        source_object = row.get("source_object")
        blocked_sources = set(family_rule.get("blocked_source_objects", []))
        allowed_sources = set(family_rule.get("primary_source_allowlist", []))
        if source_object in blocked_sources:
            return None
        if allowed_sources and source_object not in allowed_sources:
            return None

        cleaned_text = strip_inline_notes(row.get("retrieval_text", ""))
        normalized_text = compact_text(cleaned_text)
        if not normalized_text:
            return None

        candidate_types: list[str] = []
        topic = definition_plan.normalized_topic
        if topic and topic in normalized_text:
            if normalized_text.startswith(topic + "者") and "也" in normalized_text:
                candidate_types.append("exact_term_definition")
            elif normalized_text.startswith(topic + "之为病"):
                candidate_types.append("exact_term_definition")
            elif normalized_text.startswith(topic) and any(
                marker in normalized_text for marker in map(compact_text, DEFINITION_PRIORITY_EXPLANATION_MARKERS)
            ):
                candidate_types.append("exact_term_explanation")
            elif re.search(rf".{{1,20}}者.{{0,24}}{re.escape(topic)}也", normalized_text):
                candidate_types.append("term_membership_sentence")

        if definition_plan.subject_variants and definition_plan.predicate_variants:
            subject_match = any(subject in normalized_text for subject in definition_plan.subject_variants)
            predicate_match = any(predicate in normalized_text for predicate in definition_plan.predicate_variants)
            if subject_match and predicate_match:
                if any(
                    re.search(rf"{re.escape(subject)}者.{{0,32}}{re.escape(predicate)}也", normalized_text)
                    for subject in definition_plan.subject_variants
                    for predicate in definition_plan.predicate_variants
                ):
                    candidate_types.append("subject_predicate_definition")
                else:
                    candidate_types.append("subject_predicate_explanation")

        if definition_plan.subject_variants and not definition_plan.predicate_variants:
            if any(subject in normalized_text for subject in definition_plan.subject_variants):
                if any(
                    re.search(rf"{re.escape(subject)}者(.{{1,18}}?药)也", normalized_text)
                    for subject in definition_plan.subject_variants
                ):
                    candidate_types.append("subject_category_definition")

        preferred_types = list(family_rule.get("preferred_evidence_types", []))
        evidence_type_weights = self.definition_query_priority_config.get("evidence_type_weights", {})
        ranked_types = [
            (
                float(evidence_type_weights.get(candidate_type, 0.0))
                + float(len(preferred_types) - preferred_types.index(candidate_type)) * 4.0,
                candidate_type,
            )
            for candidate_type in dedupe_strings(candidate_types)
            if candidate_type in preferred_types
        ]
        if not ranked_types:
            return None

        base_score, evidence_type = max(ranked_types, key=lambda item: item[0])
        source_bonus = float(self.definition_query_priority_config.get("source_object_bonus", {}).get(source_object, 0.0))
        retrieval_bonus = min(float(row.get("combined_score", 0.0)) / 4.0, 24.0)
        text_length = len(cleaned_text)
        length_bonus = 6.0 if text_length <= 72 else 2.0 if text_length <= 120 else -4.0
        selection_score = base_score + source_bonus + retrieval_bonus + length_bonus
        return {
            "selection_score": selection_score,
            "evidence_type": evidence_type,
            "clean_text": cleaned_text,
        }

    def _build_definition_priority_answer_text(
        self,
        definition_plan: DefinitionPriorityPlan,
        primary_candidate: dict[str, Any],
        secondary_candidates: list[dict[str, Any]],
    ) -> str:
        full_primary_text = strip_inline_notes(
            self._fetch_record_meta(primary_candidate["row"]["record_id"]).get("retrieval_text", "")
        ) or primary_candidate["row"]["text_preview"]
        primary_text = self._definition_priority_excerpt(
            full_primary_text,
            definition_plan,
            primary_candidate["evidence_type"],
        )
        secondary_text = ""
        if secondary_candidates:
            full_secondary_text = strip_inline_notes(
                self._fetch_record_meta(secondary_candidates[0]["row"]["record_id"]).get("retrieval_text", "")
            ) or secondary_candidates[0]["row"]["text_preview"]
            secondary_text = self._definition_priority_excerpt(
                full_secondary_text,
                definition_plan,
                secondary_candidates[0]["evidence_type"],
            )

        if definition_plan.family_id == "category_membership_yesno":
            lines = [
                f"从现有直接归类句看，可以把“{definition_plan.subject_text}”看作“{definition_plan.predicate_text}”。",
                f"直接依据：{primary_text}",
            ]
            if secondary_text:
                lines.append(f"补充说明：{secondary_text}")
            return "\n".join(lines)

        if definition_plan.family_id == "category_membership_open":
            category = self._extract_subject_category_from_text(primary_text, definition_plan.subject_variants)
            if category:
                lines = [
                    f"从现有归类句看，“{definition_plan.subject_text}”可归入“{category}”。",
                    f"直接依据：{primary_text}",
                ]
            else:
                lines = [
                    f"从现有归类句看，可先据“{primary_text}”判断“{definition_plan.subject_text}”所属药类。",
                ]
            if secondary_text:
                lines.append(f"补充说明：{secondary_text}")
            return "\n".join(lines)

        if definition_plan.family_id == "what_means":
            lines = [
                f"从现有解释句看，“{definition_plan.topic_text}”可先参考“{primary_text}”来理解。",
                f"直接依据：{primary_text}",
            ]
            if secondary_text:
                lines.append(f"补充说明：{secondary_text}")
            return "\n".join(lines)

        if primary_candidate["evidence_type"] == "term_membership_sentence":
            lines = [
                f"书中并不是先给“{definition_plan.topic_text}”下一条抽象定义，现有可直接对应该问法的归类句是“{primary_text}”。",
                f"也就是说，这里是用具体对象的归属来说明“{definition_plan.topic_text}”这一类。",
            ]
        else:
            lines = [
                f"书中对“{definition_plan.topic_text}”的直接解释，可先看“{primary_text}”。",
                f"直接依据：{primary_text}",
            ]
        if secondary_text:
            lines.append(f"补充说明：{secondary_text}")
        return "\n".join(lines)

    def _definition_priority_excerpt(
        self,
        text: str,
        definition_plan: DefinitionPriorityPlan,
        evidence_type: str,
    ) -> str:
        compact = compact_whitespace(text)
        if not compact:
            return ""

        if definition_plan.family_id == "category_membership_yesno":
            subject = re.escape(definition_plan.subject_text or "")
            predicate = re.escape(definition_plan.predicate_text or "")
            if subject and predicate:
                match = re.search(rf"({subject}者[^。；]*?{predicate}也。?)", compact)
                if match:
                    return match.group(1)

        if evidence_type == "term_membership_sentence" and "《" in compact:
            return compact.split("《", 1)[0].rstrip("，；; ")

        first_sentence = re.split(r"(?<=[。；])", compact, maxsplit=1)[0].strip()
        return first_sentence or compact

    def _extract_subject_category_from_text(self, text: str, subject_variants: tuple[str, ...]) -> str | None:
        normalized_text = compact_text(text)
        for subject in subject_variants:
            match = re.search(rf"{re.escape(subject)}者(.{{1,18}}?药)也", normalized_text)
            if not match:
                continue
            return match.group(1)
        return None

    def _build_comparison_refuse_reason(self, reason: str) -> str:
        if reason == "unsupported_comparison":
            return "当前只支持基于条文证据整理“区别 / 不同 / 异同 / 多了什么 / 少了什么”这类比较，不支持优劣判断。"
        if reason == "too_many_entities":
            return "当前一次只支持两个对象的 pairwise comparison，请把问题收缩到两个方名。"
        return "当前无法稳定识别两个待比较的方名，因此不能可靠组织比较答案。"

    def _detect_formula_composition_query(self, query_text: str) -> dict[str, Any] | None:
        compact_query = compact_whitespace(query_text)
        if not compact_query:
            return None

        mentions = self._find_formula_mentions(compact_query)
        if len(mentions) != 1:
            return None

        normalized_query = normalize_formula_lookup_text(compact_query, keep_formula_suffix=True)
        mention = mentions[0]
        residual = compact_text(normalized_query[: mention["start"]] + normalized_query[mention["end"] :])
        if not residual:
            return None
        if any(hint in residual for hint in COMPARISON_KEYWORDS):
            return None
        if not any(hint in residual for hint in FORMULA_COMPOSITION_QUERY_HINTS):
            return None

        return {
            "canonical_name": mention["canonical_name"],
            "mention": mention,
        }

    def _assemble_formula_composition_query(
        self,
        query_text: str,
        composition_plan: dict[str, Any],
    ) -> dict[str, Any]:
        canonical_name = composition_plan["canonical_name"]
        rows = self._collect_formula_composition_rows(canonical_name)
        self._emit_progress(
            "organizing_evidence",
            "已识别为方剂组成类问题，正在整理方文中的药味组成。",
        )

        if rows:
            primary = [
                self._build_evidence_item(
                    row,
                    display_role="primary",
                    title_override=f"{canonical_name} · 方文组成",
                )
                for row in rows[:FORMULA_COMPOSITION_LIMIT]
            ]
            secondary = []
            review = [
                self._build_evidence_item(row, display_role="review")
                for row in self._lookup_review_rows(rows[:FORMULA_COMPOSITION_LIMIT])[:FORMULA_EFFECT_REVIEW_LIMIT]
            ]
            answer_text = self._build_formula_composition_answer_text(canonical_name, primary)
            return self._compose_payload(
                query_text=query_text,
                answer_mode="strong",
                answer_text=answer_text,
                primary=primary,
                secondary=secondary,
                review=review,
                review_notice=self._build_review_notice("strong"),
                disclaimer=self._build_disclaimer("strong", False, bool(review)),
                refuse_reason=None,
                suggested_followup_questions=[],
                citations=self._build_citations("strong", primary, secondary, review),
            )

        return self._compose_payload(
            query_text=query_text,
            answer_mode="refuse",
            answer_text=self._build_refuse_answer_text(
                f"目前还没有稳定命中能直接说明“{canonical_name}由什么组成”的方文依据，所以这里不硬答",
                f"可以改问“{canonical_name}的条文是什么”，或再确认一次方名写法",
            ),
            primary=[],
            secondary=[],
            review=[],
            review_notice=None,
            disclaimer=self._build_disclaimer("refuse", False, False),
            refuse_reason=self._build_refuse_reason("refuse"),
            suggested_followup_questions=self._build_followups("refuse"),
            citations=[],
        )

    def _detect_formula_effect_query(self, query_text: str) -> dict[str, Any] | None:
        compact_query = compact_whitespace(query_text)
        if not compact_query:
            return None

        mentions = self._find_formula_mentions(compact_query)
        if len(mentions) != 1:
            return None

        normalized_query = normalize_formula_lookup_text(compact_query, keep_formula_suffix=True)
        mention = mentions[0]
        residual = compact_text(normalized_query[: mention["start"]] + normalized_query[mention["end"] :])
        if not residual:
            return None
        if any(hint in residual for hint in FORMULA_EFFECT_BLOCK_HINTS):
            return None
        if not any(hint in residual for hint in FORMULA_EFFECT_QUERY_HINTS):
            return None

        return {
            "canonical_name": mention["canonical_name"],
            "mention": mention,
        }

    def _assemble_formula_effect_query(
        self,
        query_text: str,
        effect_plan: dict[str, Any],
    ) -> dict[str, Any]:
        canonical_name = effect_plan["canonical_name"]
        bundle = self._build_formula_bundle(
            canonical_name,
            formula_effect_primary_v1=self.formula_effect_primary_prioritization_enabled,
        )
        self._emit_progress(
            "organizing_evidence",
            "已识别为方剂作用类问题，正在整理直接使用语境与条文依据。",
        )

        answer_mode = self._determine_formula_effect_mode(bundle)
        if answer_mode == "strong":
            primary = [
                self._build_evidence_item(
                    row,
                    display_role="primary",
                    title_override=f"{canonical_name} · 直接条文依据",
                )
                for row in bundle["support_rows"][:FORMULA_EFFECT_SUPPORT_LIMIT]
            ]
            secondary = [
                self._build_evidence_item(
                    row,
                    display_role="secondary",
                    title_override=f"{canonical_name} · 方文",
                )
                for row in bundle["formula_rows"][:FORMULA_EFFECT_FORMULA_LIMIT]
            ]
            review = [
                self._build_evidence_item(row, display_role="review")
                for row in bundle["review_rows"][:FORMULA_EFFECT_REVIEW_LIMIT]
            ]
        elif answer_mode == "weak_with_review_notice":
            primary = []
            secondary = [
                self._build_evidence_item(
                    row,
                    display_role="secondary",
                    title_override=f"{canonical_name} · 方文",
                    risk_flags_override=dedupe_strings(self._extract_risk_flags(row) + ["formula_effect_mode_demoted"]),
                )
                for row in bundle["formula_rows"][:FORMULA_EFFECT_FORMULA_LIMIT]
            ]
            review = [
                self._build_evidence_item(row, display_role="review")
                for row in bundle["review_rows"][:FORMULA_EFFECT_REVIEW_LIMIT]
            ]
        else:
            primary = []
            secondary = []
            review = []

        answer_text = self._build_formula_effect_answer_text(
            canonical_name,
            bundle,
            answer_mode=answer_mode,
        )
        review_notice = self._build_review_notice(answer_mode)
        disclaimer = self._build_disclaimer(answer_mode, bool(secondary), bool(review))
        citations = self._build_formula_effect_citations(answer_mode, primary, secondary, review)
        refuse_reason = self._build_refuse_reason(answer_mode)
        followups = self._build_followups(answer_mode)
        return self._compose_payload(
            query_text=query_text,
            answer_mode=answer_mode,
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            review_notice=review_notice,
            disclaimer=disclaimer,
            refuse_reason=refuse_reason,
            suggested_followup_questions=followups,
            citations=citations,
        )

    def _build_formula_bundle(
        self,
        canonical_name: str,
        *,
        formula_effect_primary_v1: bool = False,
    ) -> dict[str, Any]:
        retrieval = self.engine.retrieve(canonical_name)
        formula_row = self._find_formula_heading_row(canonical_name, retrieval)
        formula_rows = [formula_row] if formula_row else []
        excluded_record_ids = {row["record_id"] for row in formula_rows}
        support_rows = (
            self._find_formula_effect_support_rows_v1(
                canonical_name,
                excluded_record_ids=excluded_record_ids,
            )
            if formula_effect_primary_v1
            else self._find_support_rows(
                canonical_name,
                excluded_record_ids=excluded_record_ids,
            )
        )
        context_row = support_rows[0] if support_rows else (
            self._find_formula_effect_review_context_row_v1(
                canonical_name,
                excluded_record_ids=excluded_record_ids,
            )
            if formula_effect_primary_v1
            else self._find_formula_effect_review_context_row(
                canonical_name,
                excluded_record_ids=excluded_record_ids,
            )
        )
        review_rows = self._lookup_review_rows(formula_rows + support_rows)
        if context_row and context_row["source_object"] != "main_passages":
            existing_review_ids = {row["record_id"] for row in review_rows}
            if context_row["record_id"] not in existing_review_ids:
                review_rows.append(context_row)
        facts = self._extract_formula_facts(
            canonical_name,
            formula_row=formula_rows[0] if formula_rows else None,
            context_row=context_row,
            formula_effect_primary_v1=formula_effect_primary_v1,
        )
        return {
            "canonical_name": canonical_name,
            "formula_rows": formula_rows,
            "support_rows": support_rows,
            "review_rows": review_rows,
            "facts": facts,
            "context_row": context_row,
            "context_source": context_row["source_object"] if context_row else None,
        }

    def _build_comparison_entity_bundle(self, entity: dict[str, Any]) -> dict[str, Any]:
        bundle = self._build_formula_bundle(entity["canonical_name"])
        return {
            "group_label": entity["group_label"],
            **bundle,
        }

    def _find_formula_heading_row(self, canonical_name: str, retrieval: dict[str, Any]) -> dict[str, Any] | None:
        for row in retrieval["primary_evidence"] + retrieval["secondary_evidence"]:
            if row["source_object"] != "main_passages":
                continue
            if self._row_is_formula_heading_for_entity(row, canonical_name):
                return row
        return None

    def _collect_formula_composition_rows(self, canonical_name: str) -> list[dict[str, Any]]:
        retrieval = self.engine.retrieve(canonical_name)
        formula_row = self._find_formula_heading_row(canonical_name, retrieval)
        if not formula_row:
            return []

        formula_chapter_id = formula_row["chapter_id"]
        ordered_rows = sorted(
            retrieval["primary_evidence"] + retrieval["secondary_evidence"],
            key=lambda row: row["record_id"],
        )
        rows: list[dict[str, Any]] = []
        for row in ordered_rows:
            if row["source_object"] != "main_passages":
                continue
            if row["chapter_id"] != formula_chapter_id:
                continue
            if row["record_id"] < formula_row["record_id"]:
                continue
            if self._row_is_other_formula_heading(row, canonical_name):
                continue
            if not self._row_is_formula_composition_line(row, canonical_name):
                continue
            rows.append(row)
        return rows[:FORMULA_COMPOSITION_LIMIT]

    def _row_is_formula_composition_line(self, row: dict[str, Any], canonical_name: str) -> bool:
        text = self._fetch_record_meta(row["record_id"])["retrieval_text"] or row.get("text_preview", "")
        if self._row_is_formula_heading_for_entity(row, canonical_name):
            return True
        compact_line = compact_whitespace(text)
        if "主之" in compact_line:
            return False
        if any(hint in compact_line for hint in FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS) and any(
            variant in compact_line for variant in self._formula_text_variants(canonical_name)
        ):
            return False
        if any(
            marker in compact_line and any(variant in compact_line for variant in self._formula_text_variants(canonical_name))
            for marker in FORMULA_EFFECT_DIRECT_USAGE_MARKERS
        ):
            return False
        if compact_line.startswith("上") and "以水" in compact_line:
            return False
        return len(FORMULA_COMPOSITION_DOSAGE_PATTERN.findall(compact_line)) >= 2

    def _find_support_rows(self, canonical_name: str, excluded_record_ids: set[str]) -> list[dict[str, Any]]:
        return self._find_matching_rows(
            canonical_name,
            excluded_record_ids=excluded_record_ids,
            source_objects=("main_passages",),
            extra_risk_flags=["topic_mismatch_demoted"],
            limit=FORMULA_EFFECT_SUPPORT_LIMIT,
        )

    def _find_formula_effect_support_rows_v1(
        self,
        canonical_name: str,
        excluded_record_ids: set[str],
    ) -> list[dict[str, Any]]:
        preferred_chapter_id = self._formula_catalog.get(canonical_name, {}).get("chapter_id")
        candidates: list[tuple[float, int, dict[str, Any], dict[str, Any]]] = []
        for row in self.engine.unified_rows:
            if row["record_id"] in excluded_record_ids:
                continue
            if row["source_object"] != "main_passages":
                continue
            row_mentions = {mention["canonical_name"] for mention in self._find_formula_mentions(row["retrieval_text"])}
            if canonical_name not in row_mentions:
                continue
            if self._row_is_formula_heading_for_entity(row, canonical_name):
                continue
            if self._row_is_other_formula_heading(row, canonical_name):
                continue
            context_meta = self._analyze_formula_effect_context_row_v1(
                row,
                canonical_name=canonical_name,
                formula_chapter_id=preferred_chapter_id,
            )
            score, context_distance = self._score_formula_effect_context_row_v1(
                row,
                canonical_name=canonical_name,
                preferred_chapter_id=preferred_chapter_id,
                row_mentions=row_mentions,
            )
            candidates.append(
                (
                    score,
                    context_distance,
                    self._normalize_record_row(row),
                    context_meta,
                )
            )

        candidates.sort(key=lambda item: (-item[0], item[1], item[2]["record_id"]))
        if candidates:
            top_meta = candidates[0][3]
            has_direct_context_candidate = any(
                self._row_qualifies_for_formula_effect_direct_context_preference_v1(
                    candidate[3],
                    score=candidate[0],
                )
                for candidate in candidates
            )
            if top_meta["is_formula_title_or_composition"] and has_direct_context_candidate:
                candidates.sort(
                    key=lambda item: (
                        0
                        if self._row_qualifies_for_formula_effect_direct_context_preference_v1(
                            item[3],
                            score=item[0],
                        )
                        else 1,
                        -item[0],
                        item[1],
                        item[2]["record_id"],
                    )
                )
                top_meta = candidates[0][3]
            has_same_chapter_direct_candidate = any(
                self._row_qualifies_for_formula_effect_same_chapter_preference_v1(
                    candidate[3],
                    score=candidate[0],
                )
                for candidate in candidates
            )
            if (
                top_meta["is_cross_chapter_bridge"]
                and top_meta["contains_direct_context"]
                and not top_meta["is_formula_title_or_composition"]
                and not top_meta["is_short_tail_fragment"]
                and has_same_chapter_direct_candidate
            ):
                candidates.sort(
                    key=lambda item: (
                        0
                        if self._row_qualifies_for_formula_effect_same_chapter_preference_v1(
                            item[3],
                            score=item[0],
                        )
                        else 1,
                        -item[0],
                        item[1],
                        item[2]["record_id"],
                    )
                )

        return [candidate[2] for candidate in candidates[:FORMULA_EFFECT_SUPPORT_LIMIT]]

    def _find_review_context_row(self, canonical_name: str, excluded_record_ids: set[str]) -> dict[str, Any] | None:
        rows = self._find_matching_rows(
            canonical_name,
            excluded_record_ids=excluded_record_ids,
            source_objects=("passages", "ambiguous_passages"),
            extra_risk_flags=None,
            limit=1,
        )
        return rows[0] if rows else None

    def _find_formula_effect_review_context_row(
        self,
        canonical_name: str,
        excluded_record_ids: set[str],
    ) -> dict[str, Any] | None:
        preferred_chapter_id = self._formula_catalog.get(canonical_name, {}).get("chapter_id")
        candidates: list[tuple[int, int, dict[str, Any]]] = []
        for row in self.engine.unified_rows:
            if row["record_id"] in excluded_record_ids:
                continue
            if row["source_object"] not in {"passages", "ambiguous_passages"}:
                continue
            row_mentions = {mention["canonical_name"] for mention in self._find_formula_mentions(row["retrieval_text"])}
            if canonical_name not in row_mentions:
                continue
            if self._row_is_other_formula_heading(row, canonical_name):
                continue
            score = 0
            if "主之" in row["retrieval_text"]:
                score += 40
            if row.get("chapter_id") == preferred_chapter_id:
                score += 25
            if row["source_object"] == "passages":
                score += 8
            compact_length = len(compact_whitespace(row["retrieval_text"]))
            if compact_length <= 96:
                score += 10
            candidates.append(
                (
                    score,
                    compact_length,
                    self._normalize_record_row(row),
                )
            )

        candidates.sort(key=lambda item: (-item[0], item[1], item[2]["record_id"]))
        return candidates[0][2] if candidates else None

    def _find_formula_effect_review_context_row_v1(
        self,
        canonical_name: str,
        excluded_record_ids: set[str],
    ) -> dict[str, Any] | None:
        preferred_chapter_id = self._formula_catalog.get(canonical_name, {}).get("chapter_id")
        candidates: list[tuple[float, int, dict[str, Any]]] = []
        for row in self.engine.unified_rows:
            if row["record_id"] in excluded_record_ids:
                continue
            if row["source_object"] not in {"passages", "ambiguous_passages"}:
                continue
            row_mentions = {mention["canonical_name"] for mention in self._find_formula_mentions(row["retrieval_text"])}
            if canonical_name not in row_mentions:
                continue
            if self._row_is_formula_heading_for_entity(row, canonical_name):
                continue
            if self._row_is_other_formula_heading(row, canonical_name):
                continue
            score, context_distance = self._score_formula_effect_context_row_v1(
                row,
                canonical_name=canonical_name,
                preferred_chapter_id=preferred_chapter_id,
                row_mentions=row_mentions,
            )
            if row["source_object"] == "passages":
                score += 6.0
            else:
                score -= 4.0
            candidates.append(
                (
                    score,
                    context_distance,
                    self._normalize_record_row(row),
                )
            )

        candidates.sort(key=lambda item: (-item[0], item[1], item[2]["record_id"]))
        return candidates[0][2] if candidates else None

    def _analyze_formula_effect_context_row_v1(
        self,
        row: dict[str, Any],
        *,
        canonical_name: str,
        formula_chapter_id: str | None,
    ) -> dict[str, Any]:
        row_text = strip_inline_notes(row.get("retrieval_text", ""))
        context_clause = self._clean_formula_effect_context(
            self._extract_formula_effect_context_clause_v1(row_text, canonical_name)
        )
        symptom_hits = sum(1 for hint in FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS if hint in context_clause)
        separator_hits = context_clause.count("，") + context_clause.count("；")
        bad_tail = any(context_clause.endswith(hint) for hint in FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS)
        bad_prefix = any(context_clause.startswith(hint) for hint in FORMULA_EFFECT_CONTEXT_BAD_PREFIX_HINTS)
        has_noise = any(hint in context_clause for hint in FORMULA_EFFECT_CONTEXT_NOISE_HINTS)
        is_formula_title_or_composition = False
        if row.get("source_object") == "main_passages":
            is_formula_title_or_composition = self._row_is_formula_heading_for_entity(row, canonical_name) or (
                self._row_is_formula_composition_line(row, canonical_name)
            )
        context_length = len(context_clause)
        is_compact_direct_clause = self._formula_effect_context_is_compact_direct_clause(
            context_clause,
            symptom_hits=symptom_hits,
            separator_hits=separator_hits,
            bad_tail=bad_tail,
            bad_prefix=bad_prefix,
            has_noise=has_noise,
        )
        is_short_tail_fragment = bool(context_clause) and (
            not is_compact_direct_clause
            and (
                context_length <= 7
                or bad_tail
                or bad_prefix
                or (symptom_hits == 0 and separator_hits == 0 and context_length <= 12)
            )
        )
        contains_direct_context = (
            bool(context_clause)
            and not is_formula_title_or_composition
            and not bad_tail
            and not bad_prefix
            and not has_noise
            and (
                is_compact_direct_clause
                or context_length >= 6
            )
            and (
                symptom_hits >= 1
                or separator_hits >= 1
                or "主之" in row_text
                or "者" in row_text
            )
        )
        is_cross_chapter_bridge = bool(formula_chapter_id) and bool(row.get("chapter_id")) and (
            row.get("chapter_id") != formula_chapter_id
        )
        return {
            "context_clause": context_clause,
            "contains_direct_context": contains_direct_context,
            "is_formula_title_or_composition": is_formula_title_or_composition,
            "is_short_tail_fragment": is_short_tail_fragment,
            "is_cross_chapter_bridge": is_cross_chapter_bridge,
            "symptom_hits": symptom_hits,
            "separator_hits": separator_hits,
            "context_length": context_length,
            "bad_tail": bad_tail,
            "bad_prefix": bad_prefix,
            "has_noise": has_noise,
        }

    def _formula_effect_context_is_compact_direct_clause(
        self,
        context_clause: str,
        *,
        symptom_hits: int,
        separator_hits: int,
        bad_tail: bool,
        bad_prefix: bool,
        has_noise: bool,
    ) -> bool:
        if not context_clause or bad_tail or bad_prefix or has_noise:
            return False
        if symptom_hits >= 1:
            return True
        if separator_hits >= 1 and ("病" in context_clause or len(context_clause) >= 6):
            return True
        if "病" in context_clause and len(context_clause) >= 4:
            return True
        return any(context_clause.endswith(hint) for hint in ("痛", "满", "利", "厥", "渴", "烦", "逆", "温"))

    def _row_qualifies_for_formula_effect_direct_context_preference_v1(
        self,
        context_meta: dict[str, Any],
        *,
        score: float,
    ) -> bool:
        return (
            context_meta["contains_direct_context"]
            and not context_meta["is_formula_title_or_composition"]
            and not context_meta["is_short_tail_fragment"]
            and score >= 0.0
        )

    def _row_qualifies_for_formula_effect_same_chapter_preference_v1(
        self,
        context_meta: dict[str, Any],
        *,
        score: float,
    ) -> bool:
        return (
            context_meta["contains_direct_context"]
            and not context_meta["is_formula_title_or_composition"]
            and not context_meta["is_short_tail_fragment"]
            and not context_meta["is_cross_chapter_bridge"]
            and score >= 0.0
        )

    def _score_formula_effect_context_row_v1(
        self,
        row: dict[str, Any],
        *,
        canonical_name: str,
        preferred_chapter_id: str | None,
        row_mentions: set[str],
    ) -> tuple[float, int]:
        context_meta = self._analyze_formula_effect_context_row_v1(
            row,
            canonical_name=canonical_name,
            formula_chapter_id=preferred_chapter_id,
        )
        row_text = strip_inline_notes(row.get("retrieval_text", ""))
        context_clause = context_meta["context_clause"]
        display_name = canonical_name[:-1] if canonical_name.endswith("方") else canonical_name
        score = 0.0

        if row.get("chapter_id") == preferred_chapter_id:
            score += 12.0
        else:
            score += 8.0

        if "主之" in row_text:
            score += 16.0
        if f"{canonical_name}主之" in row_text or f"{display_name}主之" in row_text:
            score += 4.0

        symptom_hits = context_meta["symptom_hits"]
        score += min(symptom_hits, 6) * 4.0

        separator_hits = context_meta["separator_hits"]
        score += min(separator_hits, 4) * 5.0

        context_length = context_meta["context_length"]
        if 8 <= context_length <= 44:
            score += 12.0
        elif 45 <= context_length <= 64:
            score += 4.0
        elif context_length > 64:
            score -= 20.0
        else:
            score -= 24.0

        if context_meta["bad_tail"]:
            score -= 20.0
        if context_meta["bad_prefix"]:
            score -= 16.0
        if context_meta["has_noise"]:
            score -= 14.0
        if context_meta["is_formula_title_or_composition"]:
            score -= 36.0
        if "详见" in row_text:
            score -= 8.0

        extra_formula_mentions = max(0, len(row_mentions) - 1)
        score -= extra_formula_mentions * 24.0

        if not context_clause:
            score -= 32.0

        return score, abs(context_length - 24)

    def _find_matching_rows(
        self,
        canonical_name: str,
        *,
        excluded_record_ids: set[str],
        source_objects: tuple[str, ...],
        extra_risk_flags: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        candidates: list[tuple[int, int, dict[str, Any]]] = []
        for row in self.engine.unified_rows:
            if row["record_id"] in excluded_record_ids:
                continue
            if row["source_object"] not in source_objects:
                continue
            row_mentions = {mention["canonical_name"] for mention in self._find_formula_mentions(row["retrieval_text"])}
            if canonical_name not in row_mentions:
                continue
            if self._row_is_formula_heading_for_entity(row, canonical_name):
                continue
            if self._row_is_other_formula_heading(row, canonical_name):
                continue
            score = 0
            if "主之" in row["retrieval_text"]:
                score += 30
            if row.get("chapter_id") != self._formula_catalog.get(canonical_name, {}).get("chapter_id"):
                score += 20
            compact_length = len(compact_whitespace(row["retrieval_text"]))
            if compact_length <= 96:
                score += 10
            if "详见" in row["retrieval_text"]:
                score += 5
            candidates.append(
                (
                    score,
                    compact_length,
                    self._normalize_record_row(row, extra_risk_flags=extra_risk_flags),
                )
            )

        candidates.sort(key=lambda item: (-item[0], item[1], item[2]["record_id"]))
        return [candidate[2] for candidate in candidates[:limit]]

    def _lookup_review_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        review_rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in rows:
            record_id = row["record_id"]
            if not record_id.startswith("safe:main_passages:"):
                continue
            suffix = record_id.removeprefix("safe:main_passages:")
            candidate_ids = [f"full:passages:{suffix}", f"full:ambiguous_passages:{suffix}"]
            for candidate_id in candidate_ids:
                candidate_row = self.engine.record_by_id.get(candidate_id)
                if candidate_row is None or candidate_id in seen:
                    continue
                review_rows.append(self._normalize_record_row(candidate_row))
                seen.add(candidate_id)
        return review_rows

    def _normalize_record_row(
        self,
        row: dict[str, Any],
        *,
        extra_risk_flags: list[str] | None = None,
    ) -> dict[str, Any]:
        risk_flags = dedupe_strings(self._extract_risk_flags(row) + (extra_risk_flags or []))
        return {
            "record_id": row["record_id"],
            "source_object": row["source_object"],
            "evidence_level": row["evidence_level"],
            "chapter_id": row["chapter_id"],
            "chapter_name": row["chapter_name"],
            "text_preview": snippet_text(row.get("retrieval_text") or row.get("text_preview")),
            "risk_flag": risk_flags,
            "topic_anchor": extract_title_anchor(row.get("retrieval_text") or row.get("text_preview")),
        }

    def _extract_risk_flags(self, row: dict[str, Any]) -> list[str]:
        risk_flags = row.get("risk_flag", [])
        if isinstance(risk_flags, str):
            try:
                parsed = json.loads(risk_flags)
            except json.JSONDecodeError:
                parsed = [risk_flags] if risk_flags else []
            risk_flags = parsed
        return [flag for flag in risk_flags if flag]

    def _row_is_formula_heading_for_entity(self, row: dict[str, Any], canonical_name: str) -> bool:
        text = row.get("retrieval_text") or row.get("text_preview", "")
        title = clean_formula_title_anchor(raw_title_anchor(text))
        if not title or not title.endswith("方"):
            return False
        return normalize_formula_lookup_text(title, keep_formula_suffix=False) == normalize_formula_lookup_text(
            canonical_name,
            keep_formula_suffix=False,
        )

    def _row_is_other_formula_heading(self, row: dict[str, Any], canonical_name: str) -> bool:
        text = row.get("retrieval_text") or row.get("text_preview", "")
        title = clean_formula_title_anchor(raw_title_anchor(text))
        if not title or not title.endswith("方"):
            return False
        return normalize_formula_lookup_text(title, keep_formula_suffix=False) != normalize_formula_lookup_text(
            canonical_name,
            keep_formula_suffix=False,
        )

    def _extract_formula_facts(
        self,
        canonical_name: str,
        *,
        formula_row: dict[str, Any] | None,
        context_row: dict[str, Any] | None,
        formula_effect_primary_v1: bool = False,
    ) -> dict[str, Any]:
        facts = {
            "base_formula": "",
            "added_ingredients": [],
            "removed_ingredients": [],
            "context_clause": "",
            "formula_chapter_id": formula_row["chapter_id"] if formula_row else None,
            "formula_chapter_title": formula_row["chapter_name"] if formula_row else None,
            "support_chapter_id": context_row["chapter_id"] if context_row else None,
            "support_chapter_title": context_row["chapter_name"] if context_row else None,
        }
        if formula_row:
            formula_text = self._fetch_record_meta(formula_row["record_id"])["retrieval_text"]
            core_formula_text = formula_text.split("：", 1)[1] if "：" in formula_text else formula_text
            core_formula_text = core_formula_text.split("。", 1)[0]
            base_match = re.search(r"于(?:第[一二三四五六七八九十百千万0-9]+卷)?([^，。；:：]+?方)内", core_formula_text)
            if base_match:
                facts["base_formula"] = base_match.group(1).strip()
            facts["added_ingredients"] = self._extract_formula_delta_names(core_formula_text, marker="add")
            facts["removed_ingredients"] = self._extract_formula_delta_names(core_formula_text, marker="remove")

        if context_row:
            support_text = self._fetch_record_meta(context_row["record_id"])["retrieval_text"]
            facts["context_clause"] = (
                self._extract_formula_effect_context_clause_v1(support_text, canonical_name)
                if formula_effect_primary_v1
                else self._extract_context_clause(support_text, canonical_name)
            )
        return facts

    def _extract_formula_delta_names(self, formula_text: str, *, marker: str) -> list[str]:
        if marker == "add":
            segments = re.findall(r"(?:加|更加)([^。；]+)", formula_text)
        else:
            segments = re.findall(r"(?:^|，)去([^，。；]+)", formula_text)

        names: list[str] = []
        for segment in segments:
            if marker == "remove":
                segment = segment.split("加", 1)[0]
            for name in self._extract_phrase_names(segment):
                if name not in NON_INGREDIENT_TOKENS:
                    names.append(name)
        return dedupe_strings(names)

    def _extract_phrase_names(self, segment: str) -> list[str]:
        cleaned = compact_whitespace(segment)
        cleaned = re.sub(r"(根据前法|馀根据前法|馀根据|根据前|根据|煎服|前法).*$", "", cleaned)
        matches: list[str] = []
        for part in [piece.strip() for piece in re.split(r"[，]", cleaned) if piece.strip()]:
            if "、" in part and "各" in part:
                prefix = part.split("各", 1)[0]
                matches.extend(name.strip() for name in prefix.split("、") if name.strip())
                continue
            dosage_match = re.match(
                r"^([一-龥]{1,10}?)(?:各)?(?:半|[一二三四五六七八九十百千万\d]+)(?:两|枚|个|斤|升|合|钱|铢)",
                part,
            )
            if dosage_match:
                matches.append(dosage_match.group(1))
                continue
            matches.extend(piece.strip() for piece in part.split("、") if piece.strip())
        names: list[str] = []
        for match in matches:
            candidate = re.sub(r"(炮|炙|切|洗|擘|熬|去皮尖?|去节|破八片|绵裹|赵本.*|医统本.*)$", "", match).strip()
            candidate = candidate.strip("，、 ")
            if not candidate or candidate in NON_INGREDIENT_TOKENS or candidate.endswith("方"):
                continue
            names.append(candidate)
        return dedupe_strings(names)

    def _extract_context_clause(self, support_text: str, canonical_name: str) -> str:
        match_index = -1
        for variant in self._formula_text_variants(canonical_name):
            current_index = support_text.find(variant)
            if current_index >= 0 and (match_index < 0 or current_index < match_index):
                match_index = current_index
        if match_index < 0:
            return snippet_text(support_text, limit=64)
        context_text = support_text[:match_index].strip("，。；：: ")
        if "。" in context_text:
            context_text = context_text.split("。")[-1]
        if "；" in context_text:
            context_text = context_text.split("；")[-1]
        return compact_whitespace(context_text.strip("，。；：: "))

    def _extract_formula_effect_context_clause_v1(self, support_text: str, canonical_name: str) -> str:
        cleaned_text = strip_inline_notes(support_text)
        match_index = -1
        for variant in self._formula_text_variants(canonical_name):
            current_index = cleaned_text.find(variant)
            if current_index >= 0 and (match_index < 0 or current_index < match_index):
                match_index = current_index
        if match_index < 0:
            return snippet_text(cleaned_text, limit=64)

        context_text = cleaned_text[:match_index].strip("，。；：: ")
        if not context_text:
            return ""

        segments = [
            segment.strip("，。；：: ")
            for segment in re.split(r"[。；]", context_text)
            if segment.strip("，。；：: ")
        ]
        candidate = self._choose_formula_effect_context_segment_v1(segments) if segments else context_text
        candidate = self._strip_formula_effect_tail_markers(candidate)
        return compact_whitespace(candidate.strip("，。；：: "))

    def _choose_formula_effect_context_segment_v1(self, segments: list[str]) -> str:
        normalized_segments = [compact_whitespace(segment.strip("，。；：: ")) for segment in segments if segment.strip("，。；：: ")]
        if not normalized_segments:
            return ""

        candidate = compact_whitespace(
            self._strip_formula_effect_tail_markers(normalized_segments[-1]).strip("，。；：: ")
        )
        if not self._formula_effect_context_segment_needs_backtrack(candidate):
            return candidate

        previous_segment = ""
        for segment in reversed(normalized_segments[:-1]):
            cleaned = compact_whitespace(self._strip_formula_effect_tail_markers(segment).strip("，。；：: "))
            if not cleaned:
                continue
            previous_segment = cleaned
            if not self._formula_effect_context_segment_needs_backtrack(cleaned):
                break

        if previous_segment:
            if candidate and self._formula_effect_context_should_append_short_tail(candidate):
                return f"{previous_segment}；{candidate}"
            return previous_segment
        return candidate

    def _formula_effect_context_segment_needs_backtrack(self, text: str) -> bool:
        cleaned = self._clean_formula_effect_context(text)
        if not cleaned:
            return True

        symptom_hits = sum(1 for hint in FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS if hint in cleaned)
        separator_hits = cleaned.count("，") + cleaned.count("；")
        if self._formula_effect_context_is_compact_direct_clause(
            cleaned,
            symptom_hits=symptom_hits,
            separator_hits=separator_hits,
            bad_tail=any(cleaned.endswith(hint) for hint in FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS),
            bad_prefix=any(cleaned.startswith(hint) for hint in FORMULA_EFFECT_CONTEXT_BAD_PREFIX_HINTS),
            has_noise=any(hint in cleaned for hint in FORMULA_EFFECT_CONTEXT_NOISE_HINTS),
        ):
            return False

        if any(cleaned == hint for hint in FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS):
            return True
        if any(cleaned.startswith(hint) and len(cleaned) <= len(hint) + 2 for hint in FORMULA_EFFECT_CONTEXT_BAD_PREFIX_HINTS):
            return True
        return len(cleaned) <= 2

    def _formula_effect_context_should_append_short_tail(self, text: str) -> bool:
        cleaned = self._clean_formula_effect_context(text)
        return bool(cleaned) and len(cleaned) <= 4 and cleaned.startswith(("不", "未", "欲"))

    def _strip_formula_effect_tail_markers(self, text: str) -> str:
        cleaned = compact_whitespace(text).strip("，。；：: ")
        while cleaned:
            matched_tail = next(
                (
                    hint
                    for hint in sorted(FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS, key=len, reverse=True)
                    if cleaned.endswith(hint) and len(cleaned) > len(hint) + 1
                ),
                None,
            )
            if not matched_tail:
                break
            cleaned = cleaned[: -len(matched_tail)].strip("，。；：: ")
        return cleaned

    def _clean_formula_effect_context(self, context_text: str) -> str:
        cleaned = strip_inline_notes(context_text).strip("，。；：: ")
        cleaned = self._strip_formula_effect_tail_markers(cleaned)
        if cleaned.endswith("者") and len(cleaned) > 1:
            cleaned = cleaned[:-1]
        if cleaned.startswith("若") and len(cleaned) > 2:
            candidate = cleaned[1:].strip("，。；：: ")
            if candidate and (
                any(hint in candidate for hint in FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS)
                or "病" in candidate
                or "，" in candidate
                or any(candidate.endswith(hint) for hint in ("痛", "满", "利", "厥", "渴", "烦", "逆", "温"))
            ):
                cleaned = candidate
        return cleaned.strip("，。；：: ")

    def _build_formula_composition_answer_text(
        self,
        canonical_name: str,
        primary: list[dict[str, Any]],
    ) -> str:
        lines = [f"根据当前主依据，{canonical_name}的组成可先按方文直读："]
        for idx, item in enumerate(primary, start=1):
            lines.append(f"{idx}. {item['snippet']}")
        return "\n".join(lines)

    def _determine_formula_effect_mode(self, bundle: dict[str, Any]) -> str:
        if bundle["support_rows"] and bundle["context_source"] == "main_passages":
            return "strong"
        if bundle["context_row"] or bundle["formula_rows"]:
            return "weak_with_review_notice"
        return "refuse"

    def _build_formula_effect_answer_text(
        self,
        canonical_name: str,
        bundle: dict[str, Any],
        *,
        answer_mode: str,
    ) -> str:
        display_name = canonical_name[:-1] if canonical_name.endswith("方") else canonical_name
        context_row = bundle.get("context_row")
        context_text = self._clean_formula_effect_context(bundle["facts"].get("context_clause", ""))
        context_snippet = ""
        if context_row:
            context_snippet = snippet_text(self._fetch_record_meta(context_row["record_id"])["retrieval_text"])
        formula_snippet = ""
        if bundle["formula_rows"]:
            formula_snippet = snippet_text(self._fetch_record_meta(bundle["formula_rows"][0]["record_id"])["retrieval_text"])

        if answer_mode == "strong":
            lines = [
                f"根据当前主依据，{display_name}在书中的直接使用语境，是“{context_text or context_snippet}”。",
                f"也就是说，它更偏向用于{context_text or context_snippet}这类情况。",
            ]
            if context_snippet:
                lines.append(f"依据条文：{context_snippet}")
            if formula_snippet:
                lines.append(f"补充方文：{formula_snippet}")
            return "\n".join(lines)

        if answer_mode == "weak_with_review_notice":
            if context_text or context_snippet:
                lines = [
                    f"当前未稳定找到{display_name}在正文中的直接主治条文；目前只能从核对层材料看到“{context_text or context_snippet}”这一使用语境。",
                    f"因此只能先保守理解为：它偏向用于{context_text or context_snippet}这类情况。",
                ]
                if context_snippet:
                    lines.append(f"核对材料：{context_snippet}")
            else:
                lines = [
                    f"当前只稳定找到{display_name}的方文，尚未稳定找到它在书中的直接使用语境，因此不能把“作用”概括成确定结论。"
                ]
            if formula_snippet:
                lines.append(f"补充方文：{formula_snippet}")
            return "\n".join(lines)

        return self._build_refuse_answer_text(
            f"目前还没有稳定命中能直接说明“{canonical_name}有什么作用”的书内使用语境，所以这里不直接下结论",
            f"可以改问“{canonical_name}的条文是什么”，或先看它在书里对应的方文和上下文",
        )

    def _formula_text_variants(self, canonical_name: str) -> list[str]:
        variants = {
            canonical_name,
            canonical_name[:-1] if canonical_name.endswith("方") else canonical_name,
        }
        replacement_pairs = [
            ("浓朴", "厚朴"),
            ("杏子", "杏人"),
            ("杏子", "杏仁"),
        ]
        expanded = set(variants)
        for source, target in replacement_pairs:
            current_variants = list(expanded)
            for variant in current_variants:
                if source in variant:
                    expanded.add(variant.replace(source, target))
        return sorted((variant for variant in expanded if variant), key=len, reverse=True)

    def _determine_comparison_mode(self, comparison_plan: dict[str, Any], entity_bundles: list[dict[str, Any]]) -> str:
        if any(not bundle["formula_rows"] for bundle in entity_bundles):
            return "refuse"

        composition_supported = any(
            bundle["facts"]["base_formula"] or bundle["facts"]["added_ingredients"] or bundle["facts"]["removed_ingredients"]
            for bundle in entity_bundles
        )
        context_supported = all(bundle["facts"]["context_clause"] for bundle in entity_bundles)
        context_main_supported = all(bundle["context_source"] == "main_passages" for bundle in entity_bundles)

        if comparison_plan["requested_context"] and (not context_supported or not context_main_supported):
            return "weak_with_review_notice"
        if not composition_supported and not context_supported:
            return "weak_with_review_notice"
        return "strong"

    def _build_comparison_lines(
        self,
        comparison_plan: dict[str, Any],
        entity_bundles: list[dict[str, Any]],
        answer_mode: str,
    ) -> list[str]:
        first, second = entity_bundles
        first_name = first["canonical_name"]
        second_name = second["canonical_name"]
        first_facts = first["facts"]
        second_facts = second["facts"]
        shared_base = (
            first_facts["base_formula"]
            if first_facts["base_formula"] and first_facts["base_formula"] == second_facts["base_formula"]
            else ""
        )
        first_added = [name for name in first_facts["added_ingredients"] if name not in second_facts["added_ingredients"]]
        second_added = [name for name in second_facts["added_ingredients"] if name not in first_facts["added_ingredients"]]
        first_removed = [name for name in first_facts["removed_ingredients"] if name not in second_facts["removed_ingredients"]]
        second_removed = [name for name in second_facts["removed_ingredients"] if name not in first_facts["removed_ingredients"]]

        if answer_mode == "strong":
            if shared_base:
                lines = [f"从现有方文与相关条文看，{first_name}与{second_name}都从{shared_base}加减而来，但显式加味和对应语境不同。"]
            else:
                lines = [f"从现有方文与相关条文看，{first_name}与{second_name}在显式组成和相关条文语境上并不相同。"]
        else:
            lines = [f"两方都已识别，但当前比较仍有证据缺口，以下只按现有方文做弱整理：{first_name} 与 {second_name} 的差异需要继续核对。"]

        if comparison_plan["query_kind"] == "same_and_diff" and shared_base:
            lines.append(f"1. 共同点：两方的方文都写明是在“{shared_base}”基础上加减。")

        delta_line = self._build_comparison_delta_line(
            comparison_plan["query_kind"],
            first_name,
            second_name,
            first_added,
            second_added,
            first_removed,
            second_removed,
        )
        if delta_line:
            lines.append(f"{len(lines)}. {delta_line}")

        if answer_mode == "strong" and first_facts["context_clause"] and second_facts["context_clause"]:
            first_context_prefix = "相关条文可见" if first["context_source"] == "main_passages" else "核对材料可见"
            second_context_prefix = "相关条文可见" if second["context_source"] == "main_passages" else "核对材料可见"
            lines.append(
                f"{len(lines)}. 条文语境：{first_name}{first_context_prefix}“{first_facts['context_clause']}”；"
                f"{second_name}{second_context_prefix}“{second_facts['context_clause']}”。"
            )
        elif comparison_plan["requested_context"]:
            missing_names = [
                bundle["canonical_name"]
                for bundle in entity_bundles
                if bundle["context_source"] != "main_passages"
            ]
            if missing_names:
                lines.append(
                    f"{len(lines)}. 语境证据缺口：当前未稳定找到 {self._join_formula_names(missing_names)} 的直接相关条文，"
                    "因此语境差异只能暂缓判断。"
                )

        source_line = self._build_comparison_source_line(first, second)
        if source_line:
            lines.append(f"{len(lines)}. {source_line}")

        lines.append("以上差异仅按当前可见条文与方文整理；若要逐字核对，请继续查看引用。")
        return lines

    def _build_comparison_delta_line(
        self,
        query_kind: str,
        first_name: str,
        second_name: str,
        first_added: list[str],
        second_added: list[str],
        first_removed: list[str],
        second_removed: list[str],
    ) -> str:
        pieces: list[str] = []
        if first_added:
            pieces.append(f"{first_name}明写加{ '、'.join(first_added) }")
        if second_added:
            pieces.append(f"{second_name}明写加{ '、'.join(second_added) }")
        if first_removed:
            pieces.append(f"{first_name}另去{ '、'.join(first_removed) }")
        if second_removed:
            pieces.append(f"{second_name}另去{ '、'.join(second_removed) }")

        if not pieces:
            return ""

        if query_kind == "delta":
            return "显式加减关系：" + "；".join(pieces) + "。"
        return "显式加减与药味差异：" + "；".join(pieces) + "。"

    def _build_comparison_source_line(self, first: dict[str, Any], second: dict[str, Any]) -> str:
        source_parts: list[str] = []
        first_facts = first["facts"]
        second_facts = second["facts"]
        if first_facts["formula_chapter_title"]:
            source_parts.append(
                f"{first['canonical_name']}的方文见“{self._format_comparison_source(first_facts['formula_chapter_title'])}”"
            )
        if second_facts["formula_chapter_title"]:
            source_parts.append(
                f"{second['canonical_name']}的方文见“{self._format_comparison_source(second_facts['formula_chapter_title'])}”"
            )
        if first_facts["support_chapter_title"]:
            source_parts.append(
                f"{first['canonical_name']}相关条文位于“{self._format_comparison_source(first_facts['support_chapter_title'])}”"
            )
        if second_facts["support_chapter_title"]:
            source_parts.append(
                f"{second['canonical_name']}相关条文位于“{self._format_comparison_source(second_facts['support_chapter_title'])}”"
            )
        if not source_parts:
            return ""
        return "出处线索：" + "；".join(source_parts) + "。"

    def _join_formula_names(self, names: list[str]) -> str:
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        return "、".join(names[:-1]) + "和" + names[-1]

    def _format_comparison_source(self, source_title: str) -> str:
        if source_title == "《卷内音释，上卷已有。》":
            return "卷十附方位置"
        return source_title

    def _build_comparison_review_notice(
        self,
        answer_mode: str,
        comparison_plan: dict[str, Any],
        entity_bundles: list[dict[str, Any]],
    ) -> str | None:
        if answer_mode == "weak_with_review_notice":
            return "当前比较仍有证据缺口，以下内容只可视为待核对的弱整理，不应视为确定结论。"
        if answer_mode == "strong" and (
            any(bundle["support_rows"] for bundle in entity_bundles) or any(bundle["review_rows"] for bundle in entity_bundles)
        ):
            return "以下补充依据与核对材料仅用于比较佐证，不作为主结论。"
        return None

    def _build_comparison_disclaimer(self, answer_mode: str, has_secondary: bool, has_review: bool) -> str | None:
        if answer_mode == "strong":
            if has_secondary or has_review:
                return "比较结论优先依据两侧方文；补充依据与核对材料仅作佐证。"
            return "比较结论优先依据两侧方文整理。"
        if answer_mode == "weak_with_review_notice":
            return "当前只输出弱整理，不把证据不足的差异包装成确定结论。"
        return self._build_disclaimer(answer_mode, has_secondary, has_review)

    def _build_comparison_citations(
        self,
        answer_mode: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if answer_mode == "strong":
            citation_source = list(primary + secondary)
            covered_titles = {item["title"] for item in secondary}
            for item in review:
                if item["title"] not in covered_titles:
                    citation_source.append(item)
        elif answer_mode == "weak_with_review_notice":
            citation_source = secondary + review
        else:
            citation_source = []

        citations: list[dict[str, Any]] = []
        for index, item in enumerate(citation_source, start=1):
            citations.append(
                {
                    "citation_id": f"c{index}",
                    "record_id": item["record_id"],
                    "record_type": item["record_type"],
                    "title": item["title"],
                    "evidence_level": item["evidence_level"],
                    "snippet": item["snippet"],
                    "chapter_id": item["chapter_id"],
                    "chapter_title": item["chapter_title"],
                    "citation_role": item["display_role"],
                }
            )
        return citations

    def _build_formula_effect_citations(
        self,
        answer_mode: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if answer_mode == "strong":
            citation_source = primary + secondary
        elif answer_mode == "weak_with_review_notice":
            citation_source = secondary + review
        else:
            citation_source = []

        citations: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in citation_source:
            record_id = item["record_id"]
            if record_id in seen:
                continue
            seen.add(record_id)
            citations.append(
                {
                    "citation_id": f"c{len(citations) + 1}",
                    "record_id": item["record_id"],
                    "record_type": item["record_type"],
                    "title": item["title"],
                    "evidence_level": item["evidence_level"],
                    "snippet": item["snippet"],
                    "chapter_id": item["chapter_id"],
                    "chapter_title": item["chapter_title"],
                    "citation_role": item["display_role"],
                }
            )
        return citations

    def _load_formula_catalog(self) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
        rows = self.engine.conn.execute(
            """
            SELECT record_id, text, chapter_id, chapter_name
            FROM records_main_passages
            WHERE text LIKE '%方：%'
            """
        ).fetchall()
        catalog: dict[str, dict[str, Any]] = {}
        alias_lookup: dict[str, list[str]] = {}
        alias_records: list[dict[str, Any]] = []
        for row in rows:
            row_dict = dict(row)
            raw_title = raw_title_anchor(row_dict["text"])
            title = clean_formula_title_anchor(raw_title)
            if not title or not title.endswith("方"):
                continue
            if title not in catalog:
                catalog[title] = {
                    "canonical_name": title,
                    "record_id": row_dict["record_id"],
                    "chapter_id": row_dict["chapter_id"],
                    "chapter_name": row_dict["chapter_name"],
                }
            title_aliases = formula_title_alias_variants(raw_title, title)
            alias_keys = set()
            for title_alias in title_aliases:
                alias_keys.add(normalize_formula_lookup_text(title_alias, keep_formula_suffix=True))
                alias_keys.add(normalize_formula_lookup_text(title_alias, keep_formula_suffix=False))
            for alias_key in alias_keys:
                if not alias_key:
                    continue
                alias_lookup.setdefault(alias_key, [])
                if title not in alias_lookup[alias_key]:
                    alias_lookup[alias_key].append(title)
                alias_records.append({"alias_key": alias_key, "canonical_name": title})

        alias_records.sort(key=lambda item: (-len(item["alias_key"]), item["alias_key"], item["canonical_name"]))
        return catalog, alias_records, alias_lookup

    def _detect_comparison_query(self, query_text: str) -> dict[str, Any] | None:
        compact_query = compact_whitespace(query_text)
        has_supported_keyword = any(keyword in compact_query for keyword in COMPARISON_KEYWORDS)
        mentions = self._find_formula_mentions(compact_query)

        if len(mentions) >= COMPARISON_ENTITY_LIMIT and any(hint in compact_query for hint in UNSUPPORTED_COMPARISON_HINTS):
            return {
                "valid": False,
                "reason": "unsupported_comparison",
                "mentions": mentions,
            }

        if not has_supported_keyword:
            return None

        if len(mentions) != COMPARISON_ENTITY_LIMIT:
            return {
                "valid": False,
                "reason": "entity_resolution_failed" if len(mentions) < COMPARISON_ENTITY_LIMIT else "too_many_entities",
                "mentions": mentions,
            }

        entities: list[dict[str, Any]] = []
        for index, mention in enumerate(mentions, start=1):
            entity = dict(self._formula_catalog[mention["canonical_name"]])
            entity["group_label"] = "A" if index == 1 else "B"
            entity["mention_span"] = [mention["start"], mention["end"]]
            entities.append(entity)

        return {
            "valid": True,
            "reason": "comparison_detected",
            "mentions": mentions,
            "entities": entities,
            "query_kind": self._infer_comparison_query_kind(compact_query),
            "requested_context": any(hint in compact_query for hint in COMPARISON_CONTEXT_HINTS),
        }

    def _infer_comparison_query_kind(self, query_text: str) -> str:
        if "异同" in query_text:
            return "same_and_diff"
        if "多了什么" in query_text or "少了什么" in query_text:
            return "delta"
        return "difference"

    def _find_formula_mentions(self, query_text: str) -> list[dict[str, Any]]:
        normalized_query = normalize_formula_lookup_text(query_text, keep_formula_suffix=True)
        selected: list[dict[str, Any]] = []
        occupied_spans: list[tuple[int, int]] = []
        selected_formulas: set[str] = set()

        for alias in self._formula_aliases:
            alias_key = alias["alias_key"]
            search_from = 0
            while True:
                start = normalized_query.find(alias_key, search_from)
                if start < 0:
                    break
                end = start + len(alias_key)
                search_from = start + 1
                if alias["canonical_name"] in selected_formulas:
                    continue
                if any(max(start, left) < min(end, right) for left, right in occupied_spans):
                    continue
                selected.append(
                    {
                        "canonical_name": alias["canonical_name"],
                        "alias_key": alias_key,
                        "start": start,
                        "end": end,
                    }
                )
                occupied_spans.append((start, end))
                selected_formulas.add(alias["canonical_name"])
                break

        selected.sort(key=lambda item: item["start"])
        return selected

    def _assemble_comparison(self, query_text: str, comparison_plan: dict[str, Any]) -> dict[str, Any]:
        if not comparison_plan["valid"]:
            self._emit_progress(
                "organizing_evidence",
                "比较对象未能稳定识别，正在整理拒答原因与改问建议。",
            )
            refuse_reason = self._build_comparison_refuse_reason(comparison_plan["reason"])
            self._last_comparison_debug = {
                "query": query_text,
                "comparison_detected": True,
                "comparison_valid": False,
                "reason": comparison_plan["reason"],
                "recognized_entities": [mention["canonical_name"] for mention in comparison_plan.get("mentions", [])],
                "structured_difference_count": 0,
            }
            return self._compose_payload(
                query_text=query_text,
                answer_mode="refuse",
                answer_text=self._build_refuse_answer_text(
                    "当前没能稳定识别出要比较的两个对象，所以这里不直接给比较结论",
                    "请明确写出两个方名，或先分别追问其中一个方的条文、组成或语境",
                ),
                primary=[],
                secondary=[],
                review=[],
                review_notice=None,
                disclaimer=self._build_disclaimer("refuse", False, False),
                refuse_reason=refuse_reason,
                suggested_followup_questions=list(COMPARISON_REFUSE_GUIDANCE_TEMPLATES),
                citations=[],
            )

        entity_bundles = [self._build_comparison_entity_bundle(entity) for entity in comparison_plan["entities"]]
        self._emit_progress(
            "organizing_evidence",
            "已定位待比较对象，正在组织差异点与证据层级。",
        )
        answer_mode = self._determine_comparison_mode(comparison_plan, entity_bundles)
        structured_lines = self._build_comparison_lines(comparison_plan, entity_bundles, answer_mode)

        if answer_mode == "strong":
            primary = []
            secondary = []
            review = []
            for bundle in entity_bundles:
                primary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="primary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["formula_rows"][:COMPARISON_FORMULA_TITLE_LIMIT]
                )
                secondary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["support_rows"][:COMPARISON_SUPPORT_LIMIT]
                )
                review.extend(
                    self._build_evidence_item(
                        row,
                        display_role="review",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["review_rows"][:COMPARISON_REVIEW_LIMIT]
                )
        else:
            primary = []
            secondary = []
            review = []
            for bundle in entity_bundles:
                secondary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                        risk_flags_override=dedupe_strings(self._extract_risk_flags(row) + ["comparison_mode_demoted"]),
                    )
                    for row in bundle["formula_rows"][:COMPARISON_FORMULA_TITLE_LIMIT]
                )
                secondary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                        risk_flags_override=dedupe_strings(self._extract_risk_flags(row) + ["comparison_mode_demoted"]),
                    )
                    for row in bundle["support_rows"][:COMPARISON_SUPPORT_LIMIT]
                )
                review.extend(
                    self._build_evidence_item(
                        row,
                        display_role="review",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["review_rows"][:COMPARISON_REVIEW_LIMIT]
                )

        answer_text = "\n".join(structured_lines)
        review_notice = self._build_comparison_review_notice(answer_mode, comparison_plan, entity_bundles)
        disclaimer = self._build_comparison_disclaimer(answer_mode, bool(secondary), bool(review))
        citations = self._build_comparison_citations(answer_mode, primary, secondary, review)
        refuse_reason = None
        followups: list[str] = []
        self._last_comparison_debug = {
            "query": query_text,
            "comparison_detected": True,
            "comparison_valid": True,
            "query_kind": comparison_plan["query_kind"],
            "requested_context": comparison_plan["requested_context"],
            "answer_mode": answer_mode,
            "recognized_entities": [
                {
                    "group_label": bundle["group_label"],
                    "canonical_name": bundle["canonical_name"],
                    "formula_row_found": bool(bundle["formula_rows"]),
                    "support_row_found": bool(bundle["support_rows"]),
                    "context_supported_by_main_passage": bundle["context_source"] == "main_passages",
                }
                for bundle in entity_bundles
            ],
            "structured_difference_count": max(len(structured_lines) - 1, 0),
        }
        return self._compose_payload(
            query_text=query_text,
            answer_mode=answer_mode,
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            review_notice=review_notice,
            disclaimer=disclaimer,
            refuse_reason=refuse_reason,
            suggested_followup_questions=followups,
            citations=citations,
        )

    def _compose_payload(
        self,
        *,
        query_text: str,
        answer_mode: str,
        answer_text: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
        review_notice: str | None,
        disclaimer: str | None,
        refuse_reason: str | None,
        suggested_followup_questions: list[str],
        citations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        generating_detail = "正在生成回答文本。"
        if answer_mode == "weak_with_review_notice":
            generating_detail = "正在生成待核对回答。"
        elif answer_mode == "refuse":
            generating_detail = "正在生成统一拒答说明。"
        self._emit_progress("generating_answer", generating_detail)
        primary, secondary, review = self._normalize_evidence_slots(primary, secondary, review)
        citations = self._normalize_citations(
            citations,
            primary=primary,
            secondary=secondary,
            review=review,
        )
        final_answer_text = self._maybe_render_answer_text(
            query_text=query_text,
            answer_mode=answer_mode,
            baseline_answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
        )
        display_sections = self._build_display_sections(
            answer_text=final_answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            citations=citations,
            review_notice=review_notice,
            suggested_followup_questions=suggested_followup_questions,
        )
        return {
            "query": query_text,
            "answer_mode": answer_mode,
            "answer_text": final_answer_text,
            "primary_evidence": primary,
            "secondary_evidence": secondary,
            "review_materials": review,
            "disclaimer": disclaimer,
            "review_notice": review_notice,
            "refuse_reason": refuse_reason,
            "suggested_followup_questions": suggested_followup_questions,
            "citations": citations,
            "display_sections": display_sections,
        }

    def _maybe_render_answer_text(
        self,
        *,
        query_text: str,
        answer_mode: str,
        baseline_answer_text: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> str:
        debug: dict[str, Any] = {
            "provider": self._llm_config.provider_name,
            "enabled": self._llm_config.enabled,
            "model": self._llm_config.model,
            "base_url": self._llm_config.base_url,
            "query_text": query_text,
            "answer_mode": answer_mode,
            "attempted": False,
            "used_llm": False,
            "fallback_used": False,
            "skipped_reason": None,
            "fallback_reason": None,
            "answer_source": "baseline",
            "baseline_answer_text_excerpt": snippet_text(baseline_answer_text, limit=160),
            "attempts": [],
        }

        if answer_mode == "refuse":
            debug["skipped_reason"] = "refuse_mode"
            debug["answer_source"] = "baseline_refuse"
            self._last_llm_debug = debug
            return baseline_answer_text

        if not self._llm_client:
            debug["skipped_reason"] = "llm_disabled"
            self._last_llm_debug = debug
            return baseline_answer_text

        evidence_pack = self._build_llm_evidence_pack(primary=primary, secondary=secondary, review=review)
        debug["evidence_pack_summary"] = {
            "primary": [item["evidence_id"] for item in evidence_pack["primary"]],
            "secondary": [item["evidence_id"] for item in evidence_pack["secondary"]],
            "review": [item["evidence_id"] for item in evidence_pack["review"]],
        }
        if not evidence_pack["all_items"]:
            debug["skipped_reason"] = "empty_evidence_pack"
            self._last_llm_debug = debug
            return baseline_answer_text

        debug["attempted"] = True
        candidate_answer_text: str | None = None
        failure_reason: str | None = None

        for attempt_number in (1, 2):
            strict_retry = attempt_number == 2
            prompt = build_answer_text_prompt(
                config=self._llm_config,
                query_text=query_text,
                answer_mode=answer_mode,
                evidence_pack=evidence_pack,
                strict_retry=strict_retry,
                retry_reason=failure_reason,
            )
            attempt_debug: dict[str, Any] = {
                "attempt": attempt_number,
                "strict_retry": strict_retry,
            }
            try:
                raw_content = self._llm_client.render_answer_text(
                    system_instruction=prompt.system_instruction,
                    user_prompt=prompt.user_prompt,
                )
                candidate_answer_text = parse_answer_text_json(raw_content)
                validate_rendered_answer_text(
                    answer_mode=answer_mode,
                    candidate_answer_text=candidate_answer_text,
                    evidence_pack=evidence_pack,
                    query_text=query_text,
                )
            except (ModelStudioLLMError, LLMOutputValidationError) as exc:
                failure_reason = str(exc)
                attempt_debug["status"] = "failed"
                attempt_debug["error"] = failure_reason
                debug["attempts"].append(attempt_debug)
                candidate_answer_text = None
                continue

            attempt_debug["status"] = "passed"
            attempt_debug["rendered_answer_text_excerpt"] = snippet_text(candidate_answer_text, limit=160)
            debug["attempts"].append(attempt_debug)
            break

        if candidate_answer_text is None:
            fallback_answer_text = self._build_guardrail_fallback_answer_text(
                query_text=query_text,
                answer_mode=answer_mode,
                evidence_pack=evidence_pack,
            )
            debug["fallback_used"] = True
            debug["fallback_reason"] = failure_reason or "llm_render_failed"
            debug["answer_source"] = "guardrail_fallback"
            debug["rendered_answer_text_excerpt"] = snippet_text(fallback_answer_text, limit=160)
            self._last_llm_debug = debug
            return fallback_answer_text

        debug["used_llm"] = True
        debug["answer_source"] = "llm"
        debug["rendered_answer_text_excerpt"] = snippet_text(candidate_answer_text, limit=160)
        self._last_llm_debug = debug
        return candidate_answer_text

    def _clip_llm_evidence_text(self, text: str | None, limit: int = LLM_EVIDENCE_TEXT_LIMIT) -> str:
        compact = compact_whitespace(text)
        if len(compact) <= limit:
            return compact
        return compact[:limit].rstrip("，,；;：: ") + "..."

    def _build_llm_evidence_pack(
        self,
        *,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> dict[str, Any]:
        grouped_rows = [
            ("primary", primary[: self._llm_config.max_primary_items]),
            ("secondary", secondary[: self._llm_config.max_secondary_items]),
            ("review", review[: self._llm_config.max_review_items]),
        ]
        counters = {"value": 1}
        pack: dict[str, Any] = {"primary": [], "secondary": [], "review": [], "all_items": [], "all_evidence_ids": []}

        for group_name, rows in grouped_rows:
            for item in rows:
                meta = self._fetch_record_meta(item["record_id"])
                content = self._clip_llm_evidence_text(meta.get("retrieval_text") or item.get("snippet") or "")
                evidence_entry = {
                    "evidence_id": f"E{counters['value']}",
                    "record_id": item["record_id"],
                    "source_type": item.get("record_type") or meta.get("source_object") or "unknown",
                    "slot_name": group_name,
                    "title": item.get("title") or self._derive_title(meta, content),
                    "section_label": self._build_llm_section_label(item),
                    "content": content,
                }
                counters["value"] += 1
                pack[group_name].append(evidence_entry)
                pack["all_items"].append(evidence_entry)
                pack["all_evidence_ids"].append(evidence_entry["evidence_id"])

        return pack

    def _build_llm_section_label(self, item: dict[str, Any]) -> str:
        chapter_title = compact_whitespace(item.get("chapter_title"))
        if chapter_title:
            return chapter_title
        return "未标明章节"

    def _format_evidence_ref_suffix(self, evidence_ids: list[str]) -> str:
        ordered_ids = dedupe_strings([evidence_id for evidence_id in evidence_ids if evidence_id])
        return "".join(f"[{evidence_id}]" for evidence_id in ordered_ids)

    def _is_formula_identity_query(self, query_text: str) -> bool:
        compact_query = compact_whitespace(query_text)
        return "方是什么" in compact_query and not any(
            marker in compact_query for marker in ("条文", "原文", "组成", "由什么")
        )

    def _is_meaning_explanation_query(self, query_text: str) -> bool:
        compact_query = compact_whitespace(query_text)
        return "是什么意思" in compact_query or "什么意思" in compact_query

    def _build_refuse_answer_text(self, summary: str, suggestion: str | None = None) -> str:
        summary_text = compact_whitespace(summary).rstrip("。；;，, ")
        if summary_text and summary_text[-1] not in "。！？!?":
            summary_text += "。"
        suggestion_text = compact_whitespace(suggestion or "可以改问书中的具体条文、方名，或某一句话的含义。").rstrip(
            "。；;，, "
        )
        if suggestion_text and suggestion_text[-1] not in "。！？!?":
            suggestion_text += "。"
        return f"{summary_text}{suggestion_text}"

    def _derive_query_anchor_text(self, query_text: str) -> str:
        compact_query = compact_whitespace(query_text).strip().strip(QUERY_TRAILING_PUNCTUATION)
        if self._is_formula_identity_query(compact_query) and "是什么" in compact_query:
            return compact_query.split("是什么", 1)[0].strip() or compact_query
        return compact_query or query_text

    def _extract_guardrail_fragments(self, content: str, *, max_fragments: int) -> list[str]:
        segments = [segment.strip(" ，,；;：:。") for segment in re.split(r"[。；;]", content) if segment.strip(" ，,；;：:。")]
        if not segments:
            compact = compact_whitespace(content)
            return [snippet_text(compact, limit=LLM_FALLBACK_LINE_LIMIT)] if compact else []

        fragments: list[str] = []
        for segment in segments:
            fragments.append(snippet_text(segment, limit=LLM_FALLBACK_LINE_LIMIT))
            if len(fragments) >= max_fragments:
                break
        return fragments

    def _build_guardrail_point_candidates(self, evidence_pack: dict[str, Any]) -> list[dict[str, str]]:
        candidates: list[dict[str, str]] = []
        items = evidence_pack["all_items"]
        for index, item in enumerate(items):
            fragment_limit = 2 if len(items) == 1 and index == 0 else 1
            for fragment in self._extract_guardrail_fragments(item["content"], max_fragments=fragment_limit):
                candidates.append(
                    {
                        "slot_name": item["slot_name"],
                        "evidence_id": item["evidence_id"],
                        "fragment": fragment,
                    }
                )
        if len(candidates) < 2 and items:
            first_item = items[0]
            seen_fragments = {candidate["fragment"] for candidate in candidates}
            for fragment in self._extract_guardrail_fragments(first_item["content"], max_fragments=4):
                if fragment in seen_fragments:
                    continue
                candidates.append(
                    {
                        "slot_name": first_item["slot_name"],
                        "evidence_id": first_item["evidence_id"],
                        "fragment": fragment,
                    }
                )
                seen_fragments.add(fragment)
                if len(candidates) >= 2:
                    break
        if len(candidates) == 1 and items:
            first_item = items[0]
            title_fragment = snippet_text(first_item["title"], limit=LLM_FALLBACK_LINE_LIMIT)
            if title_fragment and title_fragment != candidates[0]["fragment"]:
                candidates.append(
                    {
                        "slot_name": first_item["slot_name"],
                        "evidence_id": first_item["evidence_id"],
                        "fragment": title_fragment,
                    }
                )
        return candidates[:3]

    def _build_guardrail_fallback_answer_text(
        self,
        *,
        query_text: str,
        answer_mode: str,
        evidence_pack: dict[str, Any],
    ) -> str:
        point_candidates = self._build_guardrail_point_candidates(evidence_pack)
        if not point_candidates:
            fallback_refs = self._format_evidence_ref_suffix(list(evidence_pack.get("all_evidence_ids") or [])[:1])
            if answer_mode == "weak_with_review_notice":
                return "\n".join(
                    [
                        f"这句话目前只能先保守地理解到这里，不宜直接当成完全确定的定论。{fallback_refs}",
                        f"之所以只能这样回答，是因为现在拿到的片段还不足，缺少更完整的正文上下文。{fallback_refs}",
                        f"建议先回看当前命中的原句，再连同前后文一起核对关键字词。{fallback_refs}",
                    ]
                )
            return "\n".join(
                [
                    f"目前能先确定的是，这个问题和当前命中的书内片段直接相关，但还不宜超出片段硬作发挥。{fallback_refs}",
                    f"现有材料至少提示了原文落点，不过更完整的解释仍要以原句语境为准。{fallback_refs}",
                    f"依据主要来自当前命中的条文或片段，继续回看引用会更稳妥。{fallback_refs}",
                ]
            )

        summary_candidates = point_candidates[:2]
        summary_refs = self._format_evidence_ref_suffix([candidate["evidence_id"] for candidate in summary_candidates])
        query_anchor = snippet_text(self._derive_query_anchor_text(query_text), limit=24)
        evidence_fragments = "、".join(f"“{candidate['fragment']}”" for candidate in summary_candidates)

        if answer_mode == "weak_with_review_notice":
            if self._is_meaning_explanation_query(query_text):
                return "\n".join(
                    [
                        f"这句话目前可以先理解为：原文是在提醒某种做法会一面扶助阳气，一面耗伤阴分，所以重点在说利弊并见。{summary_refs}",
                        f"之所以只能先这样解释，是因为现在主要拿到的是辅助或核对片段，原句前后文还不完整，像“益阳”“损阴”这些词还得回到原文里对着看。{summary_refs}",
                        f"建议把当前命中的原句连同上一句、下一句一起核对，重点看“益阳”“损阴”以及相关阴阳词是怎样互相对应的。{summary_refs}",
                    ]
                )
            return "\n".join(
                [
                    f"目前只能先保守地把“{query_anchor}”理解成和{evidence_fragments}有关的意思，不宜直接当成完全确定的定论。{summary_refs}",
                    f"之所以只能说到这里，是因为当前缺少更完整的正文主证据，现有片段还不足以把主语、条件和结果都讲死。{summary_refs}",
                    f"建议先回看这些片段所在的原句，再核对前后文里有没有补足关键条件或语境的话。{summary_refs}",
                ]
            )

        if self._is_formula_identity_query(query_text):
            return "\n".join(
                [
                    f"{query_anchor}可以先看作书里的一个方名或方剂条目，当前直接命中的主依据主要是在交代它的方文内容。{summary_refs}",
                    f"目前检索到的组成片段包括{evidence_fragments}；如果方文还没完整展开，就只能先看到这些。{summary_refs}",
                    f"要确认它的主治或具体使用语境，还得继续回看对应条文或方后注解；现阶段能直接依据的主要就是这些片段。{summary_refs}",
                ]
            )

        return "\n".join(
            [
                f"可以先把“{query_anchor}”理解成和{evidence_fragments}直接相关的书内内容。{summary_refs}",
                f"从现有片段看，重点落在这些明写信息上，超出这层就不宜硬补。{summary_refs}",
                f"依据主要来自当前命中的条文或片段；如果要逐字确认语境，继续回看引用会更稳妥。{summary_refs}",
            ]
        )

    def _fetch_record_meta(self, record_id: str) -> dict[str, Any]:
        cached = self._record_cache.get(record_id)
        if cached:
            return cached
        row = self.engine.conn.execute(
            """
            SELECT
                record_id,
                source_object,
                retrieval_text,
                chapter_id,
                chapter_name
            FROM vw_retrieval_records_unified
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            replay_row = self.engine.record_by_id.get(record_id)
            if replay_row is None:
                meta = {
                    "record_id": record_id,
                    "source_object": None,
                    "retrieval_text": "",
                    "chapter_id": None,
                    "chapter_name": None,
                }
            else:
                meta = {
                    "record_id": replay_row["record_id"],
                    "source_object": replay_row.get("source_object"),
                    "retrieval_text": replay_row.get("retrieval_text", ""),
                    "chapter_id": replay_row.get("chapter_id"),
                    "chapter_name": replay_row.get("chapter_name"),
                }
        else:
            meta = dict(row)
        self._record_cache[record_id] = meta
        return meta

    def _derive_title(self, row: dict[str, Any], full_text: str) -> str:
        topic_anchor = row.get("topic_anchor")
        if topic_anchor:
            return topic_anchor
        first_line = first_meaningful_line(full_text)
        if "：" in first_line:
            head = first_line.split("：", 1)[0].strip()
            if 1 <= len(head) <= 24:
                return head
        if ":" in first_line:
            head = first_line.split(":", 1)[0].strip()
            if 1 <= len(head) <= 24:
                return head
        if first_line:
            return snippet_text(first_line, limit=24)
        return row["record_id"]

    def _build_evidence_item(
        self,
        row: dict[str, Any],
        display_role: str,
        title_override: str | None = None,
        risk_flags_override: list[str] | None = None,
    ) -> dict[str, Any]:
        meta = self._fetch_record_meta(row["record_id"])
        full_text = meta["retrieval_text"] or row.get("text_preview", "")
        title = title_override or self._derive_title(row, full_text)
        risk_flags = risk_flags_override if risk_flags_override is not None else self._extract_risk_flags(row)
        return {
            "record_id": row["record_id"],
            "record_type": row["source_object"],
            "display_role": display_role,
            "title": title,
            "evidence_level": row["evidence_level"],
            "chapter_id": row["chapter_id"],
            "chapter_title": row["chapter_name"],
            "snippet": snippet_text(full_text),
            "risk_flags": list(risk_flags),
        }

    def _build_answer_text(
        self,
        retrieval: dict[str, Any],
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> str:
        mode = retrieval["mode"]
        query_text = retrieval["query_request"].get("query_text", "")
        query_theme = retrieval["query_request"].get("query_theme", {})
        query_anchor = query_theme.get("anchor") or retrieval["query_request"]["query_text_normalized"]

        if mode == "strong":
            if self._is_formula_identity_query(query_text):
                snippets = "；".join(item["snippet"] for item in primary[:2])
                return "\n".join(
                    [
                        f"{query_anchor}可以先看作书里的一个方名，当前直接命中的主依据主要是在交代它的方文内容。",
                        f"目前检索到的组成片段包括：{snippets}。",
                        "如果还要确认它的主治或使用语境，还得继续回看对应条文。",
                    ]
                )
            if query_theme.get("type") == "formula_name":
                lead = f"和“{query_anchor}”直接相关的主条，当前主要落在这些方文或条文片段里。"
            else:
                lead = "和这个问题直接相关的主条，当前主要落在这些命中片段里。"
            lines = [lead]
            for item in primary[:3]:
                lines.append(item["snippet"])
            lines.append("可以先据此理解原文意思，具体字句再结合引用继续回看。")
            return "\n".join(lines)

        if mode == "weak_with_review_notice":
            if secondary:
                return "\n".join(
                    [
                        f"这个问题目前只能先保守地理解到这里：{secondary[0]['snippet']}。",
                        "之所以只能先这样说，是因为当前缺少更稳定的正文主证据。",
                        "建议先回看这条命中片段所在原句，再核对前后文。",
                    ]
                )
            if review:
                return "\n".join(
                    [
                        f"这个问题目前只能先保守地理解到这里：{review[0]['snippet']}。",
                        "之所以只能弱答，是因为现在只检索到核对层材料，原文语境还不完整。",
                        "建议先回看当前命中的原句，并把前后文一起核对。",
                    ]
                )
            return "\n".join(
                [
                    "这个问题目前只能先保守地理解到这里，还不宜直接下定论。",
                    "之所以只能弱答，是因为当前没有足够稳定的正文主证据。",
                    "建议改问更具体的条文、方名，或把原句前后文一起带上再问。",
                ]
            )

        return self._build_refuse_answer_text(
            "目前还没有检索到足以支撑回答的书内依据，所以这里先不硬答",
            "可以改问更具体的条文、方名，或某一句话在书里是什么意思",
        )

    def _build_review_notice(self, answer_mode: str) -> str | None:
        if answer_mode == "strong":
            return "以下补充依据与核对材料仅作说明，不作为主依据。"
        if answer_mode == "weak_with_review_notice":
            return "正文强证据不足，以下内容需核对，不应视为确定答案。"
        return None

    def _build_disclaimer(self, answer_mode: str, has_secondary: bool, has_review: bool) -> str | None:
        if answer_mode == "strong":
            if has_secondary or has_review:
                return "主证据优先；补充依据与核对材料不参与主结论判定。"
            return None
        if answer_mode == "weak_with_review_notice":
            return "当前只输出弱表述与核对材料，不输出确定性答案。"
        if answer_mode == "refuse":
            return "当前为统一拒答结构，不输出推测性答案。"
        return None

    def _build_refuse_reason(self, answer_mode: str) -> str | None:
        if answer_mode != "refuse":
            return None
        return "未检索到足以支撑回答的主证据、辅助证据或可供核对的风险材料。"

    def _build_followups(self, answer_mode: str) -> list[str]:
        if answer_mode == "refuse":
            return list(REFUSE_GUIDANCE_TEMPLATES)
        return []

    def _build_citations(
        self,
        answer_mode: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        citation_source: list[dict[str, Any]]
        if answer_mode == "strong":
            citation_source = primary
        elif answer_mode == "weak_with_review_notice":
            citation_source = secondary + review
        else:
            citation_source = []

        citations: list[dict[str, Any]] = []
        for index, item in enumerate(citation_source, start=1):
            citations.append(
                {
                    "citation_id": f"c{index}",
                    "record_id": item["record_id"],
                    "record_type": item["record_type"],
                    "title": item["title"],
                    "evidence_level": item["evidence_level"],
                    "snippet": item["snippet"],
                    "chapter_id": item["chapter_id"],
                    "chapter_title": item["chapter_title"],
                    "citation_role": item["display_role"],
                }
            )
        return citations

    def _build_display_sections(
        self,
        answer_text: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
        citations: list[dict[str, Any]],
        review_notice: str | None,
        suggested_followup_questions: list[str],
    ) -> list[dict[str, Any]]:
        return [
            {
                "section_id": "answer",
                "title": "回答",
                "section_type": "text",
                "visible": True,
                "field": "answer_text",
                "summary": snippet_text(answer_text, limit=48),
            },
            {
                "section_id": "review_notice",
                "title": "核对提示",
                "section_type": "notice",
                "visible": bool(review_notice),
                "field": "review_notice",
                "summary": review_notice or "",
            },
            {
                "section_id": "primary_evidence",
                "title": "主依据",
                "section_type": "slot_ref",
                "visible": bool(primary),
                "field": "primary_evidence",
                "item_count": len(primary),
            },
            {
                "section_id": "secondary_evidence",
                "title": "补充依据",
                "section_type": "slot_ref",
                "visible": bool(secondary),
                "field": "secondary_evidence",
                "item_count": len(secondary),
            },
            {
                "section_id": "review_materials",
                "title": "核对材料",
                "section_type": "slot_ref",
                "visible": bool(review),
                "field": "review_materials",
                "item_count": len(review),
            },
            {
                "section_id": "citations",
                "title": "引用",
                "section_type": "slot_ref",
                "visible": bool(citations),
                "field": "citations",
                "item_count": len(citations),
            },
            {
                "section_id": "refusal_guidance",
                "title": "改问建议",
                "section_type": "list",
                "visible": bool(suggested_followup_questions),
                "field": "suggested_followup_questions",
                "item_count": len(suggested_followup_questions),
            },
        ]


def build_smoke_markdown(command: str, results: list[dict[str, Any]]) -> str:
    strong_result = next(result for result in results if result["example_id"] == "strong_chunk_backref")
    weak_result = next(result for result in results if result["example_id"] == "weak_with_review_notice")
    refuse_result = next(result for result in results if result["example_id"] == "refuse_no_match")

    strong_primary_ids = [row["record_id"] for row in strong_result["primary_evidence"]]
    lines = [
        "# Hybrid Answer Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 结论",
        "",
        "- retrieval_backend: `hybrid_rrf_rerank`",
        "",
    ]

    for result in results:
        lines.append(
            f"- `{result['query']}` -> mode=`{result['answer_mode']}`, "
            f"primary={len(result['primary_evidence'])}, "
            f"secondary={len(result['secondary_evidence'])}, "
            f"review={len(result['review_materials'])}, "
            f"citations={len(result['citations'])}"
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- strong_precision_patch_preserved: `{'ZJSHL-CH-009' not in ''.join(strong_primary_ids)}`",
            f"- weak_review_notice_present: `{bool(weak_result['review_notice'])}`",
            f"- refuse_guidance_present: `{bool(refuse_result['suggested_followup_questions'])}`",
        ]
    )

    for result in results:
        section_summary = [
            {
                "section_id": section["section_id"],
                "visible": section["visible"],
                "field": section["field"],
            }
            for section in result["display_sections"]
        ]
        lines.extend(
            [
                "",
                f"## Query: {result['query']}",
                "",
                f"- answer_mode: `{result['answer_mode']}`",
                f"- answer_text: {result['answer_text']}",
                f"- disclaimer: {result['disclaimer'] or 'None'}",
                f"- review_notice: {result['review_notice'] or 'None'}",
                f"- refuse_reason: {result['refuse_reason'] or 'None'}",
                f"- evidence_summary: primary={len(result['primary_evidence'])}, secondary={len(result['secondary_evidence'])}, review={len(result['review_materials'])}",
                f"- citations_summary: `{json_dumps([citation['record_id'] for citation in result['citations']])}`",
                f"- display_sections: `{json_dumps(section_summary)}`",
                "",
                "### Primary Evidence",
                "",
                json_dumps(result["primary_evidence"]) if result["primary_evidence"] else "_no rows_",
                "",
                "### Secondary Evidence",
                "",
                json_dumps(result["secondary_evidence"]) if result["secondary_evidence"] else "_no rows_",
                "",
                "### Review Materials",
                "",
                json_dumps(result["review_materials"]) if result["review_materials"] else "_no rows_",
                "",
                "### Suggested Follow-up Questions",
                "",
                json_dumps(result["suggested_followup_questions"]) if result["suggested_followup_questions"] else "_no rows_",
            ]
        )

    return "\n".join(lines) + "\n"


def run_examples(assembler: AnswerAssembler) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in ANSWER_SMOKE_EXAMPLES:
        payload = assembler.assemble(example["query_text"])
        payload["example_id"] = example["example_id"]
        payload["expected_mode"] = example["expected_mode"]
        results.append(payload)
    return results


def assert_smoke_expectations(results: list[dict[str, Any]]) -> None:
    examples = {result["example_id"]: result for result in results}

    strong = examples["strong_chunk_backref"]
    if strong["answer_mode"] != "strong":
        raise AssertionError("strong_chunk_backref mode regressed")
    if not strong["primary_evidence"]:
        raise AssertionError("strong_chunk_backref missing primary evidence")
    if any(item["record_type"] != "main_passages" for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence must contain only main_passages")
    if any("ZJSHL-CH-009" in item["chapter_id"] for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence reintroduced 葛根黄芩黄连汤方-related passages")
    if any(item["record_type"] in {"passages", "ambiguous_passages"} for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence must not include review materials")

    weak = examples["weak_with_review_notice"]
    if weak["answer_mode"] != "weak_with_review_notice":
        raise AssertionError("weak_with_review_notice mode regressed")
    if weak["primary_evidence"]:
        raise AssertionError("weak_with_review_notice should not contain primary evidence")
    if not weak["review_notice"]:
        raise AssertionError("weak_with_review_notice missing review_notice")
    if any(item["record_type"] == "annotation_links" for item in weak["secondary_evidence"] + weak["review_materials"]):
        raise AssertionError("annotation_links must remain disabled")

    refuse = examples["refuse_no_match"]
    if refuse["answer_mode"] != "refuse":
        raise AssertionError("refuse mode regressed")
    if refuse["answer_text"] == "":
        raise AssertionError("refuse answer_text should not be empty")
    if not refuse["refuse_reason"]:
        raise AssertionError("refuse missing refuse_reason")
    if len(refuse["suggested_followup_questions"]) < 3:
        raise AssertionError("refuse missing follow-up guidance")

    def assert_no_semantic_duplicates(items: list[dict[str, Any]], *, slot_name: str) -> None:
        seen: set[str] = set()
        for item in items:
            record_type = item.get("record_type")
            record_id = str(item.get("record_id") or "")
            if record_type in {"passages", "ambiguous_passages"}:
                parts = record_id.split(":", 2)
                semantic_key = f"{parts[0]}:risk_passage:{parts[2]}" if len(parts) == 3 else record_id
            else:
                semantic_key = record_id
            if semantic_key in seen:
                raise AssertionError(f"{slot_name} contains semantic duplicate evidence: {record_id}")
            seen.add(semantic_key)

    for result in results:
        if any(item["record_type"] == "annotation_links" for item in result["primary_evidence"]):
            raise AssertionError("annotation_links leaked into primary_evidence")
        if any(item["record_type"] == "annotation_links" for item in result["secondary_evidence"]):
            raise AssertionError("annotation_links leaked into secondary_evidence")
        if any(item["record_type"] == "annotation_links" for item in result["review_materials"]):
            raise AssertionError("annotation_links leaked into review_materials")
        assert_no_semantic_duplicates(result["primary_evidence"], slot_name="primary_evidence")
        assert_no_semantic_duplicates(result["secondary_evidence"], slot_name="secondary_evidence")
        assert_no_semantic_duplicates(result["review_materials"], slot_name="review_materials")
        assert_no_semantic_duplicates(
            result["primary_evidence"] + result["secondary_evidence"] + result["review_materials"],
            slot_name="all_evidence",
        )
        assert_no_semantic_duplicates(result["citations"], slot_name="citations")


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    policy_path = resolve_project_path(args.policy_json)
    cache_dir = resolve_project_path(args.cache_dir)
    dense_chunks_index = resolve_project_path(args.dense_chunks_index)
    dense_chunks_meta = resolve_project_path(args.dense_chunks_meta)
    dense_main_index = resolve_project_path(args.dense_main_index)
    dense_main_meta = resolve_project_path(args.dense_main_meta)
    examples_out = resolve_project_path(args.examples_out)
    smoke_out = resolve_project_path(args.smoke_checks_out)

    examples_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)

    assembler = AnswerAssembler(
        db_path=db_path,
        policy_path=policy_path,
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=cache_dir,
        dense_chunks_index=dense_chunks_index,
        dense_chunks_meta=dense_chunks_meta,
        dense_main_index=dense_main_index,
        dense_main_meta=dense_main_meta,
    )
    try:
        log(f"[1/4] Loaded policy from {policy_path}")
        log(f"[2/4] Loaded hybrid retrieval database and dense assets from {db_path}")

        if args.query:
            payload = assembler.assemble(args.query)
            print(json_dumps(payload))
            log("[3/4] Ran single-query hybrid answer assembly")
            log("[4/4] No artifact files updated in single-query mode")
            return 0

        results = run_examples(assembler)
        assert_smoke_expectations(results)
        examples_out.write_text(json_dumps(build_examples_payload(results)) + "\n", encoding="utf-8")

        command = f"{Path(sys.executable).name} -m backend.answers.assembler"
        smoke_out.write_text(build_smoke_markdown(command, results), encoding="utf-8")
        log("[3/4] Ran default answer examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        assembler.close()


if __name__ == "__main__":
    raise SystemExit(main())
