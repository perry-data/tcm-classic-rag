from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.retrieval.minimal import build_query_terms, compact_text, extract_focus_text


DEFAULT_COMMENTARIAL_CONFIG_PATH = "config/commentarial_layer.json"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ROUTE_ASSISTIVE = "assistive_view"
ROUTE_NAMED = "named_view"
ROUTE_COMPARISON = "comparison_view"
ROUTE_META = "meta_learning_view"

META_BAND_STRONG = "layer_1_strong_meta"
META_BAND_TOPIC = "layer_2_learning_understanding"

COMMENTATOR_SOURCE_IDS = {
    "刘渡舟": "liu_duzhou_shanghan_lectures_2007",
    "郝万山": "hao_wanshan_shanghan_lectures_2007",
}

COMMENTATOR_QUERY_ALIASES = {
    "刘渡舟": "刘渡舟",
    "刘老": "刘渡舟",
    "刘老师": "刘渡舟",
    "郝万山": "郝万山",
    "郝老": "郝万山",
    "郝老师": "郝万山",
}

PASSAGE_QUERY_RE = re.compile(r"(?:第\s*)?(\d{1,3})([上下AaBb]?)(?:\s*条)")

NOTE_PATTERNS = (
    r"(?:赵本|医统本|成本)(?:赵本|医统本|成本)?并作「[^」]+」",
    r"(?:赵本|医统本|成本)(?:注)?[：:]?\s*(?:一作)?「[^」]+」(?:字)?",
    r"(?:《玉函经》|玉函经|《千金翼方》|千金翼方|《金匮要略》|《内经》|《广雅》)(?:作|曰)?[^。；，,]*「[^」]+」(?:字)?",
    r"(?:赵本|医统本|成本)(?:有|无|作)「[^」]+」(?:字)?",
    r"(?:赵本|医统本|成本)卷[一二三四五六七八九十]+载此方",
    r"(?:赵本|医统本|成本)[^。；，,]*详见本书卷[一二三四五六七八九十]+",
)

META_LEARNING_HINTS = (
    "怎么学",
    "如何学",
    "学习方法",
    "有什么方法",
    "有何方法",
    "怎么读",
    "如何读",
    "怎么研读",
    "如何研读",
    "怎样学",
    "入门",
)

META_TOPIC_HINTS = (
    "怎么把握",
    "如何把握",
    "应该怎么理解",
    "该怎么理解",
    "怎么理解",
    "如何理解",
    "先抓什么",
    "先抓",
    "框架",
    "提纲",
    "理解路径",
    "读法",
    "先背条文",
    "背条文",
)

META_LEARNING_CONTEXT_HINTS = (
    "初学者",
    "入门",
    "学习伤寒论",
    "学习《伤寒论》",
    "读伤寒论",
    "读《伤寒论》",
    "研读伤寒论",
    "研读《伤寒论》",
    "学习",
    "读经典",
)

NAMED_HINTS = (
    "怎么看",
    "怎么讲",
    "怎么说",
    "怎么解释",
    "如何解释",
    "怎么理解",
    "如何理解",
    "看法",
    "观点",
    "认识",
    "名家",
    "解读",
)

COMPARISON_HINTS = (
    "两家",
    "这两家",
    "两位老师",
    "两位名家",
    "比较",
    "区别",
    "不同",
    "异同",
    "相比",
    "分歧",
    "差异",
)

GENERIC_COMMENTARIAL_HINTS = (
    "名家",
    "讲稿",
    "两家",
    "这两家",
    "两位老师",
    "两位名家",
)

DEFINITION_HINTS = (
    "是什么",
    "是什么意思",
    "什么意思",
    "何谓",
    "条文是什么",
    "原文是什么",
)

FRAMEWORK_TOPIC_HINTS = (
    "六经",
    "六经辨证",
    "六经病",
    "传经",
    "传变",
    "变证",
    "坏病",
    "合病",
    "并病",
    "主证",
    "兼证",
    "夹杂证",
    "太阳病",
    "阳明病",
    "少阳病",
    "太阴病",
    "少阴病",
    "厥阴病",
    "太阳",
    "阳明",
    "少阳",
    "太阴",
    "少阴",
    "厥阴",
)

BOOK_META_HINTS = (
    "伤寒论",
    "《伤寒论》",
)

FOCUS_NOISE_PATTERNS = (
    r"老师",
    r"老",
    r"怎么看",
    r"怎么讲",
    r"怎么说",
    r"怎么解释",
    r"如何解释",
    r"怎么理解",
    r"如何理解",
    r"比较",
    r"区别",
    r"不同",
    r"异同",
    r"相比",
    r"分歧",
    r"差异",
    r"怎么学",
    r"如何学",
    r"怎样学",
    r"怎么读",
    r"如何读",
    r"怎么研读",
    r"如何研读",
    r"学习方法",
    r"有什么方法",
    r"有何方法",
    r"怎么把握",
    r"如何把握",
    r"先抓什么",
    r"先抓",
    r"框架",
    r"提纲",
    r"读法",
    r"理解路径",
    r"先背条文",
    r"背条文",
    r"名家",
    r"两家",
    r"两位老师",
    r"两位名家",
    r"这两家",
    r"看法",
    r"观点",
    r"认识",
    r"是什么",
    r"是什么意思",
    r"什么意思",
    r"何谓",
    r"这里",
    r"这块",
    r"这一块",
    r"应该",
    r"对",
    r"是",
)

FORMULA_QUERY_RE = re.compile(r"[\u4e00-\u9fff]{1,12}(?:汤方|散方|丸方|饮方|汤|散|丸|饮|方)")
DISEASE_TOPIC_RE = re.compile(r"[\u4e00-\u9fff]{1,12}(?:病|证)")


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


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


def snippet_text(text: str | None, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def normalize_commentarial_anchor_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = str(text)
    normalized = normalized.replace("（", "(").replace("）", ")").replace("［", "[").replace("］", "]")
    normalized = normalized.replace("杏人", "杏仁").replace("小盒饭", "小便当")
    for pattern in NOTE_PATTERNS:
        normalized = re.sub(pattern, "", normalized)
    normalized = re.sub(r"\[[0-9]+\]", "", normalized)
    normalized = re.sub(r"\([0-9]{1,3}[上下ABab]?\)", "", normalized)
    normalized = re.sub(r"「[^」]{0,12}」", "", normalized)
    normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", normalized)
    return normalized


def make_passage_anchor_key(number_text: str, suffix: str) -> str:
    number = str(int(number_text))
    suffix = (suffix or "").strip().upper()
    if suffix == "上":
        suffix = "A"
    elif suffix == "下":
        suffix = "B"
    return f"PASSAGE_NO:{number}{suffix}"


def extract_requested_anchor_keys(query_text: str) -> tuple[str, ...]:
    keys = []
    for match in PASSAGE_QUERY_RE.finditer(query_text):
        keys.append(make_passage_anchor_key(match.group(1), match.group(2)))
    deduped: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return tuple(deduped)


def extract_original_text(unit: dict[str, Any]) -> str:
    quoted = str(unit.get("quoted_original_text") or "").strip()
    if quoted:
        return quoted
    text = str(unit.get("text") or "")
    match = re.search(r"【原文】\s*(.+?)(?:\n\n【|\n【|$)", text, re.S)
    if match:
        return match.group(1).strip()
    return ""


def anchor_marker(anchor_key: str) -> str | None:
    raw = anchor_key.split(":", 1)[-1]
    match = re.fullmatch(r"(\d+)([A-Za-z]?)", raw)
    if not match:
        return None
    number, suffix = match.groups()
    number = str(int(number))
    if suffix.upper() == "A":
        return f"({number}上)"
    if suffix.upper() == "B":
        return f"({number}下)"
    return f"({number})"


def extract_anchor_segment(anchor_key: str, quote: str) -> str:
    normalized_quote = quote.replace("（", "(").replace("）", ")")
    marker = anchor_marker(anchor_key)
    if not marker or marker not in normalized_quote:
        return quote

    marker_index = normalized_quote.index(marker)
    surrounding_markers = list(
        re.finditer(r"\((?:\d{1,3}[上下]?|\d{1,3}[ABab]?)\)", normalized_quote[:marker_index])
    )
    start = surrounding_markers[-1].end() if surrounding_markers else 0
    next_markers = list(
        re.finditer(r"\((?:\d{1,3}[上下]?|\d{1,3}[ABab]?)\)", normalized_quote[marker_index + len(marker) :])
    )
    end = (
        marker_index + len(marker) + next_markers[0].start()
        if next_markers
        else len(normalized_quote)
    )
    return normalized_quote[start : marker_index + len(marker)].strip()


def detect_commentators(query_text: str) -> tuple[str, ...]:
    normalized_query = compact_text(query_text)
    commentators: list[str] = []
    seen: set[str] = set()
    alias_items = sorted(COMMENTATOR_QUERY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True)
    for alias, canonical_name in alias_items:
        normalized_alias = compact_text(alias)
        if alias not in query_text and normalized_alias not in normalized_query:
            continue
        if canonical_name in seen:
            continue
        seen.add(canonical_name)
        commentators.append(canonical_name)
    return tuple(commentators)


def query_has_any_hint(query_text: str, normalized_query: str, hints: tuple[str, ...]) -> bool:
    return any(hint in query_text or compact_text(hint) in normalized_query for hint in hints)


def match_query_hints(query_text: str, normalized_query: str, hints: tuple[str, ...]) -> tuple[str, ...]:
    matched: list[str] = []
    seen: set[str] = set()
    for hint in hints:
        normalized_hint = compact_text(hint)
        if hint not in query_text and normalized_hint not in normalized_query:
            continue
        if hint in seen:
            continue
        seen.add(hint)
        matched.append(hint)
    return tuple(matched)


@dataclass(frozen=True)
class CommentarialRoutePlan:
    route: str
    commentators: tuple[str, ...]
    requested_anchor_keys: tuple[str, ...]
    focus_text: str
    explicit: bool
    meta_band: str | None = None
    debug: dict[str, Any] | None = None


class CommentarialLayer:
    def __init__(self, config_path: str = DEFAULT_COMMENTARIAL_CONFIG_PATH) -> None:
        self.config_path = resolve_project_path(config_path)
        self.enabled = False
        self.load_error: str | None = None
        self.config: dict[str, Any] = {}
        self.bundle_dir: Path | None = None
        self.sources: list[dict[str, Any]] = []
        self.units: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []
        self.resolution: dict[str, Any] = {}
        self.resolved_links: list[dict[str, Any]] = []
        self.support_files: dict[str, Any] = {}
        self.source_meta: dict[str, dict[str, Any]] = {}
        self.units_by_id: dict[str, dict[str, Any]] = {}
        self.resolved_links_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._last_route_debug: dict[str, Any] | None = None
        if not self.config_path.exists():
            self.load_error = f"Missing commentarial config: {self.config_path}"
            return
        self._load()

    def _load(self) -> None:
        try:
            self.config = load_json(self.config_path)
            if not self.config.get("enabled", True):
                self.load_error = "Commentarial layer disabled by config."
                return
            self.bundle_dir = resolve_project_path(str(self.config["bundle_dir"]))
            if not self.bundle_dir.exists():
                self.load_error = f"Missing commentarial bundle directory: {self.bundle_dir}"
                return

            self.sources = load_json(self.bundle_dir / "commentarial_sources.json")
            self.links = load_jsonl(self.bundle_dir / "commentarial_anchor_links.jsonl")
            self.resolution = (
                load_json(resolve_project_path(str(self.config["resolution_file"])))
                if self.config.get("resolution_file")
                and resolve_project_path(str(self.config["resolution_file"])).exists()
                else {}
            )
            self.resolved_links = (
                load_jsonl(resolve_project_path(str(self.config["resolved_links_file"])))
                if self.config.get("resolved_links_file")
                and resolve_project_path(str(self.config["resolved_links_file"])).exists()
                else []
            )
            self.support_files = self._load_support_files(self.bundle_dir)
            self.source_meta = {row["source_id"]: row for row in self.sources}
            for link in self.resolved_links:
                self.resolved_links_by_unit[str(link["unit_id"])].append(link)

            raw_units = load_jsonl(self.bundle_dir / "commentarial_units.jsonl")
            self.units = [self._hydrate_unit(row) for row in raw_units]
            self.units_by_id = {row["unit_id"]: row for row in self.units}
            self.enabled = True
        except Exception as exc:  # pragma: no cover - load-time diagnostics
            self.load_error = f"Failed to load commentarial layer: {exc}"
            self.enabled = False

    def _load_support_files(self, bundle_dir: Path) -> dict[str, Any]:
        support_specs = {
            "handoff_manifest": bundle_dir / "handoff_manifest.json",
            "acceptance_report": bundle_dir / "acceptance_report.json",
            "anchor_audit": bundle_dir / "commentarial_anchor_audit.json",
            "manual_review_queue": bundle_dir / "manual_review_queue.json",
            "tag_schema": bundle_dir / "commentarial_tag_schema.json",
            "tag_guide": bundle_dir / "commentarial_tag_guide.md",
            "usecase_matrix": bundle_dir / "commentarial_usecase_matrix.md",
            "handoff_readme": bundle_dir / "commentarial_handoff_readme.md",
            "next_step": bundle_dir / "coding_agent_next_step.md",
            "patch_round3_notes": bundle_dir / "commentarial_patch_round3_notes.md",
            "multi_anchor_rule_guide": bundle_dir / "multi_anchor_rule_guide.md",
            "theme_tier_guide": bundle_dir / "theme_tier_guide.md",
            "integration_constraints": bundle_dir / "coding_agent_integration_constraints.md",
        }
        loaded: dict[str, Any] = {}
        for key, path in support_specs.items():
            if not path.exists():
                continue
            if path.suffix == ".json":
                loaded[key] = load_json(path)
            else:
                loaded[key] = path.read_text(encoding="utf-8")
        return loaded

    def _hydrate_unit(self, unit: dict[str, Any]) -> dict[str, Any]:
        source_info = self.source_meta.get(str(unit.get("source_id") or ""), {})
        resolved_links = self.resolved_links_by_unit.get(str(unit["unit_id"]), [])

        resolved_primary: list[str] = []
        resolved_supporting: list[str] = []
        unresolved_anchor_keys: list[str] = []
        for link in resolved_links:
            if str(link.get("anchor_key_kind")) != "passage_no":
                continue
            anchor_key = str(link.get("anchor_passage_id") or "")
            resolution_status = str(link.get("resolution_status") or "")
            if resolution_status.startswith("resolved"):
                resolved_id = link.get("resolved_canonical_passage_id")
                if not resolved_id:
                    continue
                if link.get("anchor_role") == "supporting":
                    resolved_supporting.append(str(resolved_id))
                else:
                    resolved_primary.append(str(resolved_id))
            else:
                unresolved_anchor_keys.append(anchor_key)

        normalized_search_text = compact_text(
            " ".join(
                part
                for part in (
                    unit.get("title"),
                    unit.get("retrieval_text"),
                    unit.get("summary_text"),
                    unit.get("quoted_original_text"),
                    unit.get("commentary_text"),
                )
                if part
            )
        )
        hydrated = {
            **unit,
            "work_title": source_info.get("work_title"),
            "resolved_links": resolved_links,
            "resolved_primary_anchor_passage_ids": sorted(set(resolved_primary)),
            "resolved_supporting_anchor_passage_ids": sorted(set(resolved_supporting)),
            "unresolved_anchor_keys": sorted(set(unresolved_anchor_keys)),
            "normalized_search_text": normalized_search_text,
            "normalized_title": compact_text(unit.get("title") or ""),
            "original_anchor_text": extract_original_text(unit),
        }
        return hydrated

    def detect_route(self, query_text: str) -> CommentarialRoutePlan | None:
        if not self.enabled:
            return None

        normalized_query = compact_text(query_text)
        if not normalized_query:
            return None

        commentators = detect_commentators(query_text)
        requested_anchor_keys = extract_requested_anchor_keys(query_text)
        focus_text = self._build_focus_text(query_text, commentators, requested_anchor_keys)
        named_hints = match_query_hints(query_text, normalized_query, NAMED_HINTS)
        comparison_hints = match_query_hints(query_text, normalized_query, COMPARISON_HINTS)
        generic_commentarial_hints = match_query_hints(query_text, normalized_query, GENERIC_COMMENTARIAL_HINTS)
        meta_learning_hints = match_query_hints(query_text, normalized_query, META_LEARNING_HINTS)
        meta_topic_hints = match_query_hints(query_text, normalized_query, META_TOPIC_HINTS)
        learning_context_hints = match_query_hints(query_text, normalized_query, META_LEARNING_CONTEXT_HINTS)
        definition_hints = match_query_hints(query_text, normalized_query, DEFINITION_HINTS)
        topic_signals = self._collect_topic_signals(
            query_text=query_text,
            normalized_query=normalized_query,
            focus_text=focus_text,
            requested_anchor_keys=requested_anchor_keys,
        )
        meta_band = self._classify_meta_band(
            meta_learning_hints=meta_learning_hints,
            meta_topic_hints=meta_topic_hints,
            learning_context_hints=learning_context_hints,
            requested_anchor_keys=requested_anchor_keys,
            topic_signals=topic_signals,
        )

        route_scores: dict[str, float] = {
            ROUTE_ASSISTIVE: 12.0,
            ROUTE_NAMED: 0.0,
            ROUTE_COMPARISON: 0.0,
            ROUTE_META: 0.0,
        }
        matched_signals: list[dict[str, Any]] = []
        rejected_signals: list[dict[str, Any]] = []

        def add_signal(route: str, signal: str, detail: str, weight: float) -> None:
            route_scores[route] += weight
            matched_signals.append(
                {
                    "route": route,
                    "signal": signal,
                    "detail": detail,
                    "weight": round(weight, 3),
                }
            )

        if len(commentators) == 1:
            add_signal(ROUTE_NAMED, "commentator_alias", commentators[0], 28.0)
        elif len(commentators) >= 2:
            add_signal(ROUTE_COMPARISON, "dual_commentator_alias", " / ".join(commentators), 24.0)
            add_signal(ROUTE_NAMED, "multi_commentator_context", " / ".join(commentators), 10.0)

        if named_hints:
            add_signal(ROUTE_NAMED, "named_hint", " / ".join(named_hints), 10.0 + min(6.0, len(named_hints) * 2.0))
        if comparison_hints:
            add_signal(
                ROUTE_COMPARISON,
                "comparison_hint",
                " / ".join(comparison_hints),
                18.0 + min(8.0, len(comparison_hints) * 2.0),
            )
        if generic_commentarial_hints:
            detail = " / ".join(generic_commentarial_hints)
            if comparison_hints:
                add_signal(ROUTE_COMPARISON, "generic_comparison_frame", detail, 10.0)
            else:
                add_signal(ROUTE_NAMED, "generic_commentarial_frame", detail, 8.0)

        if meta_band == META_BAND_STRONG:
            detail = " / ".join(meta_learning_hints or learning_context_hints or meta_topic_hints)
            add_signal(ROUTE_META, "meta_band_strong", detail, 30.0)
        elif meta_band == META_BAND_TOPIC:
            detail = " / ".join(meta_topic_hints or learning_context_hints or meta_learning_hints)
            add_signal(ROUTE_META, "meta_band_topic", detail, 20.0)

        if requested_anchor_keys:
            detail = " / ".join(requested_anchor_keys)
            add_signal(ROUTE_NAMED, "passage_anchor", detail, 12.0)
            add_signal(ROUTE_COMPARISON, "passage_anchor", detail, 10.0)
            if meta_band is not None:
                add_signal(ROUTE_META, "passage_anchor", detail, 6.0)

        framework_topics = topic_signals["framework_topics"]
        if framework_topics:
            detail = " / ".join(framework_topics)
            add_signal(ROUTE_NAMED, "framework_topic", detail, 5.0)
            add_signal(ROUTE_COMPARISON, "framework_topic", detail, 6.0)
            if meta_band is not None:
                add_signal(
                    ROUTE_META,
                    "framework_topic",
                    detail,
                    12.0 if meta_band == META_BAND_TOPIC else 8.0,
                )

        disease_topics = topic_signals["disease_topics"]
        if disease_topics and not framework_topics:
            detail = " / ".join(disease_topics[:3])
            add_signal(ROUTE_NAMED, "disease_topic", detail, 4.0)
            add_signal(ROUTE_COMPARISON, "disease_topic", detail, 4.0)
            if meta_band is not None and learning_context_hints:
                add_signal(ROUTE_META, "disease_topic", detail, 6.0)

        formula_topics = topic_signals["formula_topics"]
        if formula_topics:
            detail = " / ".join(formula_topics[:3])
            add_signal(ROUTE_NAMED, "formula_topic", detail, 6.0)
            add_signal(ROUTE_COMPARISON, "formula_topic", detail, 4.0)
            if meta_band == META_BAND_STRONG and learning_context_hints:
                add_signal(ROUTE_META, "formula_topic", detail, 4.0)

        if definition_hints:
            add_signal(ROUTE_ASSISTIVE, "definition_hint", " / ".join(definition_hints), 14.0)
            rejected_signals.append(
                {
                    "route": ROUTE_META,
                    "signal": "definition_hint",
                    "reason": "plain_definition_prefers_canonical_or_assistive",
                    "detail": " / ".join(definition_hints),
                }
            )

        if commentators and meta_band is not None:
            route_scores[ROUTE_META] -= 12.0
            rejected_signals.append(
                {
                    "route": ROUTE_META,
                    "signal": "commentator_alias",
                    "reason": "single_commentator_query_should_prefer_named_or_comparison",
                    "detail": " / ".join(commentators),
                }
            )

        if comparison_hints and len(commentators) == 1 and not generic_commentarial_hints:
            route_scores[ROUTE_COMPARISON] -= 10.0
            rejected_signals.append(
                {
                    "route": ROUTE_COMPARISON,
                    "signal": "single_commentator_comparison_conflict",
                    "reason": "comparison_requires_dual_view_signal",
                    "detail": commentators[0],
                }
            )

        focus_terms = [
            term
            for term in build_query_terms(focus_text or normalized_query)
            if 2 <= len(term) <= 12
        ][:18]
        preview_targets = {
            ROUTE_ASSISTIVE: tuple(),
            ROUTE_NAMED: commentators or tuple(COMMENTATOR_SOURCE_IDS.keys()),
            ROUTE_COMPARISON: tuple(COMMENTATOR_SOURCE_IDS.keys()),
            ROUTE_META: tuple(COMMENTATOR_SOURCE_IDS.keys()),
        }
        preview_hits: dict[str, dict[str, Any]] = {}
        for route_name in route_scores:
            preview = self._preview_route_hits(
                route=route_name,
                terms=focus_terms,
                commentators=preview_targets[route_name],
                meta_band=meta_band,
            )
            preview_hits[route_name] = preview
            if preview["count"] <= 0:
                continue
            if route_name == ROUTE_META and meta_band is None:
                continue
            weight = min(12.0, preview["best"] * 2.0 + min(4.0, preview["count"]))
            if route_name == ROUTE_ASSISTIVE:
                weight = min(weight, 6.0)
            add_signal(
                route_name,
                "normalized_query_hit",
                f"{preview['count']} hits / best={preview['best']}",
                weight,
            )

        route_priority = {
            ROUTE_COMPARISON: 4,
            ROUTE_NAMED: 3,
            ROUTE_META: 2,
            ROUTE_ASSISTIVE: 1,
        }
        best_route = max(route_scores, key=lambda route: (route_scores[route], route_priority[route]))
        explicit_thresholds = {
            ROUTE_NAMED: 24.0,
            ROUTE_COMPARISON: 26.0,
            ROUTE_META: 24.0,
        }
        assistive_score = route_scores[ROUTE_ASSISTIVE]
        explicit = best_route != ROUTE_ASSISTIVE and (
            route_scores[best_route] >= explicit_thresholds[best_route]
            and route_scores[best_route] - assistive_score >= 6.0
        )
        chosen_route = best_route if explicit else ROUTE_ASSISTIVE

        if chosen_route == ROUTE_COMPARISON and route_scores[ROUTE_NAMED] >= explicit_thresholds[ROUTE_NAMED]:
            rejected_signals.append(
                {
                    "route": ROUTE_NAMED,
                    "signal": "route_competition",
                    "reason": "comparison_outscored_named",
                    "detail": f"comparison={route_scores[ROUTE_COMPARISON]:.1f}, named={route_scores[ROUTE_NAMED]:.1f}",
                }
            )
        if chosen_route == ROUTE_NAMED and route_scores[ROUTE_META] >= 18.0:
            rejected_signals.append(
                {
                    "route": ROUTE_META,
                    "signal": "route_competition",
                    "reason": "named_outscored_meta",
                    "detail": f"named={route_scores[ROUTE_NAMED]:.1f}, meta={route_scores[ROUTE_META]:.1f}",
                }
            )
        if chosen_route == ROUTE_ASSISTIVE and best_route != ROUTE_ASSISTIVE:
            rejected_signals.append(
                {
                    "route": best_route,
                    "signal": "explicit_threshold",
                    "reason": "signal_not_strong_enough_for_explicit_commentarial_route",
                    "detail": f"{best_route}={route_scores[best_route]:.1f}, assistive={assistive_score:.1f}",
                }
            )

        selected_commentators = tuple()
        if chosen_route == ROUTE_NAMED:
            selected_commentators = commentators or tuple(COMMENTATOR_SOURCE_IDS.keys())
        elif chosen_route == ROUTE_COMPARISON:
            selected_commentators = commentators if len(commentators) >= 2 else tuple(COMMENTATOR_SOURCE_IDS.keys())

        debug = {
            "chosen_route": chosen_route,
            "route_scores": {route: round(score, 3) for route, score in route_scores.items()},
            "matched_signals": matched_signals,
            "rejected_signals": rejected_signals,
            "meta_band": meta_band,
            "focus_text": focus_text,
            "commentators": list(selected_commentators),
            "requested_anchor_keys": list(requested_anchor_keys),
            "topic_signals": topic_signals,
            "preview_hits": preview_hits,
            "explicit": explicit,
        }
        self._last_route_debug = debug
        return CommentarialRoutePlan(
            route=chosen_route,
            commentators=selected_commentators,
            requested_anchor_keys=requested_anchor_keys,
            focus_text=focus_text,
            explicit=explicit,
            meta_band=meta_band if chosen_route == ROUTE_META else None,
            debug=debug,
        )

    def get_last_route_debug(self) -> dict[str, Any] | None:
        return self._last_route_debug

    def _collect_topic_signals(
        self,
        *,
        query_text: str,
        normalized_query: str,
        focus_text: str,
        requested_anchor_keys: tuple[str, ...],
    ) -> dict[str, Any]:
        formula_topics = []
        seen_formula_topics: set[str] = set()
        for match in FORMULA_QUERY_RE.finditer(query_text):
            candidate = match.group(0)
            candidate = re.sub(r"^(?:这个|这里|这块|这一块|关于)", "", candidate)
            candidate = re.sub(r"^[^汤散丸饮方]*对", "", candidate)
            candidate = re.sub(r"(?:的|这一块)+$", "", candidate)
            candidate = candidate.strip()
            if not candidate or candidate in seen_formula_topics:
                continue
            seen_formula_topics.add(candidate)
            formula_topics.append(candidate)
        disease_topics = tuple(dict.fromkeys(match.group(0) for match in DISEASE_TOPIC_RE.finditer(query_text)))
        framework_topics = match_query_hints(query_text, normalized_query, FRAMEWORK_TOPIC_HINTS)
        book_topics = match_query_hints(query_text, normalized_query, BOOK_META_HINTS)
        return {
            "formula_topics": tuple(formula_topics),
            "disease_topics": disease_topics,
            "framework_topics": framework_topics,
            "book_topics": book_topics,
            "has_requested_anchor": bool(requested_anchor_keys),
            "focus_text": focus_text,
        }

    def _classify_meta_band(
        self,
        *,
        meta_learning_hints: tuple[str, ...],
        meta_topic_hints: tuple[str, ...],
        learning_context_hints: tuple[str, ...],
        requested_anchor_keys: tuple[str, ...],
        topic_signals: dict[str, Any],
    ) -> str | None:
        framework_topics = topic_signals["framework_topics"]
        book_topics = topic_signals["book_topics"]
        disease_topics = topic_signals["disease_topics"]
        formula_topics = topic_signals["formula_topics"]

        if meta_learning_hints:
            return META_BAND_STRONG

        if learning_context_hints and book_topics and not (framework_topics or disease_topics or formula_topics or requested_anchor_keys):
            return META_BAND_STRONG

        has_book_method_scope = bool(book_topics) and bool(meta_topic_hints) and not (
            disease_topics or formula_topics or requested_anchor_keys
        )
        if has_book_method_scope:
            return META_BAND_STRONG

        if meta_topic_hints and (
            framework_topics
            or disease_topics
            or requested_anchor_keys
            or (learning_context_hints and (book_topics or formula_topics))
        ):
            return META_BAND_TOPIC

        return None

    def _preview_route_hits(
        self,
        *,
        route: str,
        terms: list[str],
        commentators: tuple[str, ...],
        meta_band: str | None,
    ) -> dict[str, Any]:
        if not terms:
            return {"count": 0, "best": 0, "top_unit_ids": []}

        count = 0
        best = 0
        top_units: list[str] = []
        for unit in self.units:
            if route == ROUTE_NAMED and not self._is_named_unit_candidate(unit, commentators):
                continue
            if route == ROUTE_COMPARISON and not self._is_comparison_unit_candidate(unit, commentators):
                continue
            if route == ROUTE_META and not self._is_meta_unit_candidate(unit, meta_band):
                continue
            if route == ROUTE_ASSISTIVE and not self._is_assistive_unit_candidate(unit):
                continue
            hit_count = self._count_query_term_hits(unit, terms)
            if hit_count <= 0:
                continue
            count += 1
            best = max(best, hit_count)
            if len(top_units) < 3:
                top_units.append(str(unit.get("unit_id")))
        return {
            "count": count,
            "best": best,
            "top_unit_ids": top_units,
        }

    def _build_focus_text(
        self,
        query_text: str,
        commentators: tuple[str, ...],
        requested_anchor_keys: tuple[str, ...],
    ) -> str:
        focus = query_text
        for commentator in commentators:
            focus = focus.replace(commentator, " ")
        for alias, _canonical_name in sorted(
            COMMENTATOR_QUERY_ALIASES.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            focus = focus.replace(alias, " ")
        for noise_pattern in FOCUS_NOISE_PATTERNS:
            focus = re.sub(noise_pattern, " ", focus)
        for anchor_key in requested_anchor_keys:
            raw = anchor_key.split(":", 1)[-1]
            number = re.match(r"(\d+)", raw)
            if not number:
                continue
            focus = re.sub(rf"(?:第\s*)?{int(number.group(1))}\s*[AaBb上下]?\s*条", " ", focus)
        compact_focus = compact_text(focus)
        compact_focus = re.sub(r"(?:的|这一块)+$", "", compact_focus)
        if compact_focus in {"的", "是的", "对", "这里", "这块", "这一块"}:
            compact_focus = ""
        return compact_focus or extract_focus_text(query_text) or compact_text(query_text)

    def build_extension(
        self,
        query_text: str,
        payload: dict[str, Any],
        route_plan: CommentarialRoutePlan | None = None,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        plan = route_plan
        if payload.get("answer_mode") == "refuse" and (plan is None or not plan.explicit):
            return None
        if plan is None:
            plan = CommentarialRoutePlan(
                route=ROUTE_ASSISTIVE,
                commentators=tuple(),
                requested_anchor_keys=extract_requested_anchor_keys(query_text),
                focus_text=extract_focus_text(query_text) or compact_text(query_text),
                explicit=False,
            )

        sections = self._build_sections(plan, query_text)
        if not sections:
            return None

        return {
            "route": plan.route,
            "source_aware": True,
            "lead_note": self._build_lead_note(plan.route),
            "sections": sections,
        }

    def build_shadow_query(self, route_plan: CommentarialRoutePlan, fallback_query: str) -> str:
        if route_plan.requested_anchor_keys:
            ranked = self._rank_units(route_plan, fallback_query)
            for unit, _score in ranked:
                original_text = str(unit.get("original_anchor_text") or "")
                if not original_text:
                    continue
                for anchor_key in route_plan.requested_anchor_keys:
                    if anchor_key not in (unit.get("anchor_candidates") or []):
                        continue
                    segment = extract_anchor_segment(anchor_key, original_text)
                    if segment:
                        return segment
        if route_plan.focus_text:
            return route_plan.focus_text
        return fallback_query

    def _build_sections(self, plan: CommentarialRoutePlan, query_text: str) -> list[dict[str, Any]]:
        if plan.route == ROUTE_ASSISTIVE:
            return self._build_assistive_sections(plan, query_text)
        if plan.route == ROUTE_META:
            return self._build_explicit_sections(
                plan,
                limit_key="meta_limit_per_commentator",
                default_title="名家学习方法",
                comparison_layout=False,
            )
        if plan.route == ROUTE_COMPARISON:
            return self._build_explicit_sections(
                plan,
                limit_key="comparison_limit_per_commentator",
                default_title="名家比较",
                comparison_layout=True,
            )
        return self._build_explicit_sections(
            plan,
            limit_key="named_limit_per_commentator",
            default_title="名家视角",
            comparison_layout=False,
        )

    def _build_assistive_sections(
        self,
        plan: CommentarialRoutePlan,
        query_text: str,
    ) -> list[dict[str, Any]]:
        limit = int(self.config.get("assistive_limit", 2))
        scored = self._rank_units(plan, query_text)
        items = []
        for unit, score in scored:
            if not unit.get("eligible_for_default_assistive_retrieval"):
                continue
            if not unit.get("never_use_in_primary", False):
                continue
            if unit.get("use_for_confidence_gate"):
                continue
            if unit.get("anchor_type") == "theme":
                continue
            bucket = self._classify_display_bucket(unit, plan.route)
            if bucket == "exclude":
                continue
            items.append(self._build_item(unit, score))
            if len(items) >= limit:
                break
        if not items:
            return []
        return [
            {
                "section_id": "commentarial_assistive",
                "title": "名家补充解读",
                "view_mode": plan.route,
                "layout": "stacked",
                "collapsed_by_default": True,
                "items": items,
            }
        ]

    def _build_explicit_sections(
        self,
        plan: CommentarialRoutePlan,
        *,
        limit_key: str,
        default_title: str,
        comparison_layout: bool,
    ) -> list[dict[str, Any]]:
        limit = int(self.config.get(limit_key, 3))
        commentator_targets = plan.commentators or tuple(COMMENTATOR_SOURCE_IDS.keys())
        sections: list[dict[str, Any]] = []
        for commentator in commentator_targets:
            scoped_plan = CommentarialRoutePlan(
                route=plan.route,
                commentators=(commentator,),
                requested_anchor_keys=plan.requested_anchor_keys,
                focus_text=plan.focus_text,
                explicit=plan.explicit,
                meta_band=plan.meta_band,
                debug=plan.debug,
            )
            ranked = self._rank_units(scoped_plan, scoped_plan.focus_text)
            main_items: list[dict[str, Any]] = []
            folded_items: list[dict[str, Any]] = []
            for unit, score in ranked:
                bucket = self._classify_display_bucket(unit, plan.route)
                if bucket == "exclude":
                    continue
                target = folded_items if bucket == "folded" else main_items
                target.append(self._build_item(unit, score))
                if len(main_items) >= limit and len(folded_items) >= 2:
                    break
            if not main_items and not folded_items:
                continue
            if main_items:
                sections.append(
                    {
                        "section_id": f"commentarial_{plan.route}_{commentator}_main",
                        "title": commentator if comparison_layout else f"{commentator}视角",
                        "commentator": commentator,
                        "view_mode": plan.route,
                        "layout": "comparison" if comparison_layout else "stacked",
                        "collapsed_by_default": False,
                        "items": main_items[:limit],
                    }
                )
            if folded_items:
                sections.append(
                    {
                        "section_id": f"commentarial_{plan.route}_{commentator}_folded",
                        "title": f"{commentator}补充主题",
                        "commentator": commentator,
                        "view_mode": plan.route,
                        "layout": "stacked",
                        "collapsed_by_default": True,
                        "items": folded_items[:2],
                    }
                )
        return sections

    def _count_query_term_hits(self, unit: dict[str, Any], terms: list[str]) -> int:
        search_text = str(unit.get("normalized_search_text") or "")
        title_text = str(unit.get("normalized_title") or "")
        if not search_text and not title_text:
            return 0

        hit_count = 0
        for term in terms[:18]:
            if term in search_text:
                hit_count += 1
            elif len(term) >= 4 and term in title_text:
                hit_count += 1
        return hit_count

    def _is_named_unit_candidate(
        self,
        unit: dict[str, Any],
        commentators: tuple[str, ...],
    ) -> bool:
        if not unit.get("eligible_for_named_view"):
            return False
        if commentators and unit.get("commentator") not in commentators:
            return False
        return True

    def _is_comparison_unit_candidate(
        self,
        unit: dict[str, Any],
        commentators: tuple[str, ...],
    ) -> bool:
        if not unit.get("eligible_for_comparison_retrieval"):
            return False
        if commentators and unit.get("commentator") not in commentators:
            return False
        return True

    def _is_assistive_unit_candidate(self, unit: dict[str, Any]) -> bool:
        return (
            bool(unit.get("eligible_for_default_assistive_retrieval"))
            and bool(unit.get("never_use_in_primary", False))
            and not bool(unit.get("use_for_confidence_gate"))
            and unit.get("anchor_type") != "theme"
        )

    def _is_meta_unit_candidate(self, unit: dict[str, Any], meta_band: str | None) -> bool:
        if meta_band is None:
            return False

        commentary_functions = set(unit.get("commentary_functions") or [])
        if not commentary_functions.intersection({"study_method", "theory_overview", "summary"}):
            return False

        anchor_type = unit.get("anchor_type")
        theme_tier = unit.get("theme_display_tier")
        if anchor_type == "theme":
            return theme_tier in {
                "tier_1_named_view_ok",
                "tier_2_fold_only",
                "tier_3_meta_learning_only",
            }

        if meta_band == META_BAND_STRONG:
            return bool(commentary_functions.intersection({"study_method", "theory_overview"})) and (
                unit.get("eligible_for_meta_learning_view") or "study_method" in commentary_functions
            )

        return bool(unit.get("eligible_for_meta_learning_view"))

    def _rank_units(
        self,
        plan: CommentarialRoutePlan,
        query_text: str,
    ) -> list[tuple[dict[str, Any], float]]:
        scored: list[tuple[dict[str, Any], float]] = []
        terms = [term for term in build_query_terms(plan.focus_text or extract_focus_text(query_text)) if len(term) >= 2]
        if not terms:
            fallback_term = compact_text(query_text)
            if fallback_term:
                terms = [fallback_term]
        for unit in self.units:
            if unit.get("low_confidence_commentarial_unit") and not (
                plan.route == ROUTE_META
                and unit.get("anchor_type") == "theme"
                and unit.get("theme_display_tier") == "tier_3_meta_learning_only"
            ):
                continue
            if plan.requested_anchor_keys and plan.route in {ROUTE_NAMED, ROUTE_COMPARISON}:
                anchor_pool = set(unit.get("anchor_candidates") or [])
                if not anchor_pool.intersection(plan.requested_anchor_keys):
                    continue
            if plan.route == ROUTE_META and not self._is_meta_unit_candidate(unit, plan.meta_band):
                continue
            if plan.route == ROUTE_COMPARISON and not self._is_comparison_unit_candidate(unit, plan.commentators):
                continue
            if plan.route == ROUTE_NAMED and not self._is_named_unit_candidate(unit, plan.commentators):
                continue
            if plan.route == ROUTE_ASSISTIVE and not self._is_assistive_unit_candidate(unit):
                continue

            score = self._score_unit(unit, plan, terms)
            if score <= 0:
                continue
            scored.append((unit, score))
        scored.sort(
            key=lambda item: (
                -item[1],
                item[0].get("needs_manual_anchor_review", False),
                item[0].get("needs_manual_content_review", False),
                item[0].get("unit_id"),
            )
        )
        return scored

    def _score_unit(
        self,
        unit: dict[str, Any],
        plan: CommentarialRoutePlan,
        terms: list[str],
    ) -> float:
        search_text = unit.get("normalized_search_text") or ""
        if not search_text:
            return 0.0

        score = 0.0
        for term in terms[:18]:
            if term in search_text:
                score += min(len(term), 10) * 1.8
            elif len(term) >= 4 and term in unit.get("normalized_title", ""):
                score += min(len(term), 8) * 1.2

        for anchor_key in plan.requested_anchor_keys:
            if anchor_key in (unit.get("primary_anchor_candidates") or []):
                score += 40.0
            elif anchor_key in (unit.get("supporting_anchor_candidates") or []):
                score += 24.0
            elif anchor_key in (unit.get("anchor_candidates") or []):
                score += 18.0

        if plan.commentators and unit.get("commentator") in plan.commentators:
            score += 28.0

        commentary_functions = set(unit.get("commentary_functions") or [])
        if plan.route == ROUTE_NAMED and commentary_functions.intersection(
            {"passage_explanation", "formula_analysis", "pathogenesis", "commentator_views"}
        ):
            score += 10.0
        if plan.route == ROUTE_COMPARISON and commentary_functions.intersection(
            {"comparison", "formula_analysis", "pathogenesis", "therapeutic_method"}
        ):
            score += 10.0
        if plan.route == ROUTE_META:
            if "study_method" in commentary_functions:
                score += 16.0
            if "theory_overview" in commentary_functions:
                score += 12.0
            if "summary" in commentary_functions:
                score += 8.0

        anchor_type = unit.get("anchor_type")
        if anchor_type == "exact":
            score += 8.0
        elif anchor_type == "excerpt":
            score += 6.0
        elif anchor_type == "multi":
            score += 4.0
        elif anchor_type == "theme":
            score += 10.0

        if unit.get("needs_manual_anchor_review"):
            score -= 8.0
        if unit.get("needs_manual_content_review"):
            score -= 8.0

        if plan.route == ROUTE_ASSISTIVE and unit.get("anchor_type") == "theme":
            score -= 100.0
        if plan.route == ROUTE_META:
            theme_tier = unit.get("theme_display_tier")
            if anchor_type == "theme":
                score += 14.0
            else:
                score -= 4.0
            if plan.meta_band == META_BAND_STRONG:
                if "study_method" in commentary_functions:
                    score += 12.0
                if anchor_type == "theme":
                    score += 6.0
            elif plan.meta_band == META_BAND_TOPIC:
                if "theory_overview" in commentary_functions:
                    score += 8.0
                if "summary" in commentary_functions:
                    score += 6.0
            if theme_tier == "tier_3_meta_learning_only":
                score += 28.0
            elif theme_tier == "tier_2_fold_only":
                score += 10.0
            elif theme_tier == "tier_1_named_view_ok":
                score += 8.0
        if plan.route == ROUTE_COMPARISON and anchor_type == "theme":
            score += 8.0
        return score

    def _classify_display_bucket(self, unit: dict[str, Any], route: str) -> str:
        if (
            route == ROUTE_META
            and unit.get("anchor_type") == "theme"
            and unit.get("theme_display_tier") == "tier_3_meta_learning_only"
        ):
            return "main"
        if unit.get("needs_manual_content_review"):
            return "exclude" if route == ROUTE_ASSISTIVE else "folded"
        if unit.get("needs_manual_anchor_review"):
            return "exclude" if route == ROUTE_ASSISTIVE else "folded"
        if unit.get("anchor_type") == "theme":
            tier = unit.get("theme_display_tier")
            if tier == "tier_4_do_not_default_display":
                return "exclude"
            if route == ROUTE_ASSISTIVE:
                return "exclude"
            if route == ROUTE_META:
                if tier == "tier_3_meta_learning_only":
                    return "main"
                if tier == "tier_2_fold_only":
                    return "folded"
                if tier == "tier_1_named_view_ok":
                    return "main"
                return "exclude"
            if route in {ROUTE_NAMED, ROUTE_COMPARISON}:
                if tier == "tier_1_named_view_ok":
                    return "main"
                if tier == "tier_2_fold_only":
                    return "folded"
                return "exclude"
        if route == ROUTE_META:
            return "folded"
        if unit.get("anchor_type") == "multi" and unit.get("anchor_priority_mode") == "unresolved_multi":
            return "folded"
        return "main"

    def _build_item(self, unit: dict[str, Any], score: float) -> dict[str, Any]:
        return {
            "unit_id": unit["unit_id"],
            "commentator": unit.get("commentator"),
            "source_id": unit.get("source_id"),
            "work_title": unit.get("work_title"),
            "title": unit.get("title"),
            "summary_text": unit.get("summary_text") or snippet_text(unit.get("commentary_text")),
            "quoted_original_text": unit.get("quoted_original_text") or unit.get("original_anchor_text"),
            "display_text": unit.get("display_text"),
            "anchor_type": unit.get("anchor_type"),
            "anchor_priority_mode": unit.get("anchor_priority_mode"),
            "theme_display_tier": unit.get("theme_display_tier"),
            "primary_anchor_candidates": list(unit.get("primary_anchor_candidates") or []),
            "supporting_anchor_candidates": list(unit.get("supporting_anchor_candidates") or []),
            "resolved_primary_anchor_passage_ids": list(unit.get("resolved_primary_anchor_passage_ids") or []),
            "resolved_supporting_anchor_passage_ids": list(unit.get("resolved_supporting_anchor_passage_ids") or []),
            "unresolved_anchor_keys": list(unit.get("unresolved_anchor_keys") or []),
            "never_use_in_primary": bool(unit.get("never_use_in_primary")),
            "use_for_confidence_gate": bool(unit.get("use_for_confidence_gate")),
            "needs_manual_anchor_review": bool(unit.get("needs_manual_anchor_review")),
            "needs_manual_content_review": bool(unit.get("needs_manual_content_review")),
            "low_confidence_commentarial_unit": bool(unit.get("low_confidence_commentarial_unit")),
            "score": round(float(score), 3),
        }

    def _build_lead_note(self, route: str) -> str:
        if route == ROUTE_ASSISTIVE:
            return "以下名家内容仅作补充解读，默认不进入 primary_evidence，也不参与 confidence gate。"
        if route == ROUTE_META:
            return "以下为名家学习方法与教学视角，仍与 canonical 主证据层分离展示。"
        if route == ROUTE_COMPARISON:
            return "以下为名家比较视角；原典 citation 与主证据层仍保持 canonical 优先。"
        return "以下为点名名家视角；原典主依据与 canonical citation 仍保持独立。"
