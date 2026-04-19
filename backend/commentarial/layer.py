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

NAMED_HINTS = (
    "怎么看",
    "怎么讲",
    "怎么解释",
    "如何解释",
    "怎么理解",
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
)

GENERIC_COMMENTARIAL_HINTS = (
    "名家",
    "讲稿",
    "两家",
    "这两家",
    "两位老师",
    "两位名家",
)

FOCUS_NOISE_PATTERNS = (
    r"老师",
    r"老",
    r"怎么看",
    r"怎么讲",
    r"怎么解释",
    r"如何解释",
    r"怎么理解",
    r"比较",
    r"区别",
    r"不同",
    r"异同",
    r"相比",
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
    r"名家",
    r"两家",
    r"两位老师",
    r"两位名家",
    r"这两家",
    r"是",
)


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


@dataclass(frozen=True)
class CommentarialRoutePlan:
    route: str
    commentators: tuple[str, ...]
    requested_anchor_keys: tuple[str, ...]
    focus_text: str
    explicit: bool


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

        if query_has_any_hint(query_text, normalized_query, META_LEARNING_HINTS) or (
            "学习" in normalized_query and "方法" in normalized_query
        ):
            return CommentarialRoutePlan(
                route=ROUTE_META,
                commentators=commentators,
                requested_anchor_keys=requested_anchor_keys,
                focus_text=focus_text,
                explicit=True,
            )

        has_named_hint = query_has_any_hint(query_text, normalized_query, NAMED_HINTS)
        has_comparison_hint = query_has_any_hint(query_text, normalized_query, COMPARISON_HINTS)
        has_generic_commentarial = query_has_any_hint(query_text, normalized_query, GENERIC_COMMENTARIAL_HINTS)

        if has_comparison_hint and (commentators or has_generic_commentarial):
            effective_commentators = commentators or tuple(COMMENTATOR_SOURCE_IDS.keys())
            return CommentarialRoutePlan(
                route=ROUTE_COMPARISON,
                commentators=effective_commentators,
                requested_anchor_keys=requested_anchor_keys,
                focus_text=focus_text,
                explicit=True,
            )

        if commentators or (has_named_hint and has_generic_commentarial):
            effective_commentators = commentators or tuple(COMMENTATOR_SOURCE_IDS.keys())
            return CommentarialRoutePlan(
                route=ROUTE_NAMED,
                commentators=effective_commentators,
                requested_anchor_keys=requested_anchor_keys,
                focus_text=focus_text,
                explicit=True,
            )

        return None

    def _build_focus_text(
        self,
        query_text: str,
        commentators: tuple[str, ...],
        requested_anchor_keys: tuple[str, ...],
    ) -> str:
        focus = query_text
        for commentator in commentators:
            focus = focus.replace(commentator, " ")
        for alias in COMMENTATOR_QUERY_ALIASES:
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
        if compact_focus in {"的", "是的"}:
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
        if plan is None:
            if payload.get("answer_mode") == "refuse":
                return None
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
            )
            ranked = self._rank_units(scoped_plan, scoped_plan.focus_text)
            main_items: list[dict[str, Any]] = []
            folded_items: list[dict[str, Any]] = []
            for unit, score in ranked:
                bucket = self._classify_display_bucket(unit, plan.route)
                if bucket == "exclude":
                    continue
                if plan.route == ROUTE_META and not unit.get("eligible_for_meta_learning_view"):
                    continue
                if plan.route == ROUTE_COMPARISON and not unit.get("eligible_for_comparison_retrieval"):
                    continue
                if plan.route == ROUTE_NAMED and not unit.get("eligible_for_named_view"):
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
            if plan.commentators and unit.get("commentator") not in plan.commentators:
                continue
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
            if plan.route == ROUTE_META and not unit.get("eligible_for_meta_learning_view"):
                continue
            if plan.route == ROUTE_COMPARISON and not unit.get("eligible_for_comparison_retrieval"):
                continue
            if plan.route == ROUTE_NAMED and not unit.get("eligible_for_named_view"):
                continue
            if plan.route == ROUTE_ASSISTIVE and not unit.get("eligible_for_default_assistive_retrieval"):
                continue
            if plan.route == ROUTE_META:
                commentary_functions = set(unit.get("commentary_functions") or [])
                if unit.get("anchor_type") != "theme" and "study_method" not in commentary_functions:
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
        if plan.route == ROUTE_META and commentary_functions.intersection(
            {"study_method", "theory_overview", "summary"}
        ):
            score += 14.0

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
                score += 12.0
            else:
                score -= 8.0
            if theme_tier == "tier_3_meta_learning_only":
                score += 28.0
            elif theme_tier == "tier_2_fold_only":
                score += 6.0
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
