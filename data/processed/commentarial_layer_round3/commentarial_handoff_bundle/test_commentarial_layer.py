#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Round3 tester for commentarial layer handoff bundle.

Examples:
  python scripts/test_commentarial_layer.py --validate
  python scripts/test_commentarial_layer.py --audit-summary
  python scripts/test_commentarial_layer.py --bundle-check
  python scripts/test_commentarial_layer.py --passage-id 141
  python scripts/test_commentarial_layer.py --keyword "桂枝汤"
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "commentarial_layer"
BUNDLE_DIR = ROOT / "commentarial_handoff_bundle"
BUNDLE_ZIP = ROOT / "commentarial_handoff_bundle.zip"

REQUIRED_FIELDS = [
    "unit_id", "source_id", "commentator", "title", "text",
    "anchor_type", "anchor_candidates", "commentary_functions",
    "display_role", "selection_flag", "use_for_confidence_gate",
    "raw_text", "retrieval_text", "display_text", "summary_text",
    "quoted_original_text", "commentary_text", "teaching_points",
    "comparison_focus", "eligible_for_named_view",
    "eligible_for_explanatory_retrieval",
    "eligible_for_comparison_retrieval",
    "eligible_for_meta_learning_view",
    "eligible_for_default_assistive_retrieval",
    "never_use_in_primary", "needs_manual_anchor_review",
    "needs_manual_content_review", "low_confidence_commentarial_unit",
    "primary_anchor_candidates", "supporting_anchor_candidates",
    "anchor_priority_mode", "primary_anchor_selection_reason",
    "supporting_anchor_selection_reason", "multi_anchor_confidence"
]

BOOL_FIELDS = [
    "eligible_for_named_view", "eligible_for_explanatory_retrieval",
    "eligible_for_comparison_retrieval", "eligible_for_meta_learning_view",
    "eligible_for_default_assistive_retrieval", "never_use_in_primary",
    "needs_manual_anchor_review", "needs_manual_content_review",
    "low_confidence_commentarial_unit", "use_for_confidence_gate"
]

THEME_TIERS = {
    "tier_1_named_view_ok",
    "tier_2_fold_only",
    "tier_3_meta_learning_only",
    "tier_4_do_not_default_display",
}

BUNDLE_REQUIRED_FILES = [
    "commentarial_sources.json",
    "commentarial_units.jsonl",
    "commentarial_anchor_links.jsonl",
    "acceptance_report.json",
    "commentarial_anchor_audit.json",
    "manual_review_queue.json",
    "commentarial_tag_schema.json",
    "commentarial_tag_guide.md",
    "commentarial_usecase_matrix.md",
    "commentarial_handoff_readme.md",
    "coding_agent_integration_constraints.md",
    "coding_agent_next_step.md",
    "commentarial_patch_round3_notes.md",
    "handoff_manifest.json",
    "test_commentarial_layer.py",
]

MANIFEST_REQUIRED_KEYS = [
    "bundle_version", "unit_count_total", "unit_count_by_commentator",
    "anchor_type_counts", "multi_unit_count", "theme_unit_count",
    "manual_review_queue_count", "files_in_bundle", "main_risks",
    "what_coding_agent_must_do_next", "what_coding_agent_must_not_do",
    "known_open_issues"
]

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_jsonl(path: Path):
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items

def normalize_passage_key(value: str):
    v = value.strip()
    if v.startswith("PASSAGE_NO:"):
        body = v.split(":", 1)[1]
        m = re.match(r"^(\d{1,3})([AB])?$", body)
        if m:
            return f"PASSAGE_NO:{int(m.group(1)):03d}{m.group(2) or ''}"
        return v
    m = re.match(r"^(\d{1,3})([上下AB])?$", v)
    if not m:
        return v
    n = int(m.group(1))
    side = m.group(2)
    if side == "上":
        side = "A"
    elif side == "下":
        side = "B"
    else:
        side = side or ""
    return f"PASSAGE_NO:{n:03d}{side}"

def score_keyword(text: str, q: str):
    if not text or not q:
        return 0
    return text.count(q.strip())

def search_units(units, query, commentator=None, topn=8):
    rows = []
    for u in units:
        if commentator and u["commentator"] != commentator:
            continue
        text = f"{u.get('title','')} {u.get('retrieval_text','')} {u.get('summary_text','')}"
        sc = score_keyword(text, query)
        if sc > 0:
            rows.append({
                "unit_id": u["unit_id"],
                "commentator": u["commentator"],
                "title": u["title"],
                "anchor_type": u["anchor_type"],
                "anchor_candidates": u["anchor_candidates"],
                "score": sc,
            })
    rows.sort(key=lambda x: (-x["score"], x["unit_id"]))
    return rows[:topn]

def build_provisional_canonical_index(units, links):
    idx = {}
    for l in links:
        if l.get("anchor_key_kind") != "passage_no":
            continue
        u = next((x for x in units if x["unit_id"] == l["unit_id"]), None)
        if not u:
            continue
        pid = l["anchor_passage_id"]
        excerpt = u.get("quoted_original_text") or u.get("summary_text") or u.get("title")
        idx.setdefault(pid, {"passage_id": pid, "excerpt": excerpt[:120], "sources": []})
        idx[pid]["sources"].append(u["unit_id"])
    return idx

def search_canonical_stub(stub_index, query, topn=8):
    rows = []
    for pid, item in stub_index.items():
        sc = score_keyword(f"{pid} {item.get('excerpt','')}", query)
        if sc > 0:
            rows.append({
                "passage_id": pid,
                "excerpt": item.get("excerpt", ""),
                "source": "provisional_stub",
                "score": sc,
            })
    rows.sort(key=lambda x: (-x["score"], x["passage_id"]))
    return rows[:topn]

def validate(units, links, audit=None):
    problems = []
    unit_ids = {u["unit_id"] for u in units}
    commentators = {"刘渡舟", "郝万山"}

    for u in units:
        for k in REQUIRED_FIELDS:
            if k not in u:
                problems.append({"type": "missing_field", "unit_id": u.get("unit_id"), "field": k})
                continue
            if k in ("teaching_points", "comparison_focus", "quoted_original_text", "commentary_text", "supporting_anchor_candidates"):
                continue
            if k == "primary_anchor_candidates" and u.get("anchor_priority_mode") == "unresolved_multi":
                continue
            if u[k] in ("", None, []):
                problems.append({"type": "empty_field", "unit_id": u.get("unit_id"), "field": k})
        if u.get("commentator") not in commentators:
            problems.append({"type": "bad_commentator", "unit_id": u.get("unit_id"), "value": u.get("commentator")})
        for k in BOOL_FIELDS:
            if not isinstance(u.get(k), bool):
                problems.append({"type": "bad_bool_field", "unit_id": u.get("unit_id"), "field": k, "value": u.get(k)})
        if u.get("never_use_in_primary") is not True:
            problems.append({"type": "primary_guard_broken", "unit_id": u["unit_id"]})
        if u.get("use_for_confidence_gate") is not False:
            problems.append({"type": "confidence_gate_broken", "unit_id": u["unit_id"]})
        if u.get("anchor_type") in ("exact", "excerpt", "multi") and not any(str(x).startswith("PASSAGE_NO:") for x in u.get("anchor_candidates", [])):
            problems.append({"type": "bad_passage_anchor_candidates", "unit_id": u["unit_id"]})
        if u.get("anchor_type") == "theme" and not any(str(x).startswith("THEME:") for x in u.get("anchor_candidates", [])):
            problems.append({"type": "bad_theme_anchor_candidates", "unit_id": u["unit_id"]})
        if u.get("anchor_type") == "multi":
            for k in ["primary_anchor_candidates", "supporting_anchor_candidates", "anchor_priority_mode"]:
                if k not in u:
                    problems.append({"type": "missing_multi_priority_field", "unit_id": u["unit_id"], "field": k})
            if u.get("anchor_priority_mode") == "unresolved_multi" and u.get("primary_anchor_candidates"):
                problems.append({"type": "unresolved_multi_has_primary", "unit_id": u["unit_id"]})
        if u.get("anchor_type") == "theme":
            if u.get("theme_display_tier") not in THEME_TIERS:
                problems.append({"type": "bad_theme_display_tier", "unit_id": u["unit_id"], "value": u.get("theme_display_tier")})

    for l in links:
        if l["unit_id"] not in unit_ids:
            problems.append({"type": "dangling_link", "unit_id": l["unit_id"]})

    # distribution checks
    for k in [
        "eligible_for_named_view",
        "eligible_for_explanatory_retrieval",
        "eligible_for_comparison_retrieval",
        "eligible_for_meta_learning_view",
        "eligible_for_default_assistive_retrieval",
    ]:
        cnt = sum(1 for u in units if u.get(k))
        if cnt == 0 and k not in ("eligible_for_default_assistive_retrieval",):
            problems.append({"type": "unreasonable_bool_distribution", "field": k, "count_true": cnt, "unit_total": len(units)})
        if cnt == len(units):
            problems.append({"type": "unreasonable_bool_distribution", "field": k, "count_true": cnt, "unit_total": len(units)})

    if audit:
        bad = [x for x in audit.get("audit_entries", []) if x.get("judgement") in ("suspicious", "wrong")]
        missing = [x for x in bad if x.get("unit_id") not in unit_ids]
        if missing:
            problems.append({"type": "audit_points_to_missing_unit", "count": len(missing)})

    return problems

def distribution(units):
    out = {
        "tag_distribution_by_commentator": {},
        "anchor_type_distribution": dict(Counter(u["anchor_type"] for u in units)),
        "flag_counts": {},
        "anchor_priority_mode_counts": {},
        "theme_display_tier_counts": {},
    }
    by_commentator = defaultdict(Counter)
    for u in units:
        for tag in u.get("commentary_functions", []):
            by_commentator[u["commentator"]][tag] += 1
    out["tag_distribution_by_commentator"] = {k: dict(v) for k, v in by_commentator.items()}
    for field in [
        "eligible_for_named_view",
        "eligible_for_comparison_retrieval",
        "eligible_for_meta_learning_view",
        "eligible_for_default_assistive_retrieval",
        "needs_manual_anchor_review",
        "needs_manual_content_review",
        "low_confidence_commentarial_unit",
    ]:
        out["flag_counts"][field] = sum(1 for u in units if u.get(field))
    out["anchor_priority_mode_counts"] = dict(Counter(u.get("anchor_priority_mode") for u in units if u.get("anchor_type") == "multi"))
    out["theme_display_tier_counts"] = dict(Counter(u.get("theme_display_tier") for u in units if u.get("anchor_type") == "theme"))
    out["unresolved_multi_count"] = sum(1 for u in units if u.get("anchor_type") == "multi" and u.get("anchor_priority_mode") == "unresolved_multi")
    out["theme_named_view_count"] = sum(1 for u in units if u.get("anchor_type") == "theme" and u.get("theme_display_tier") == "tier_1_named_view_ok")
    out["theme_fold_only_count"] = sum(1 for u in units if u.get("anchor_type") == "theme" and u.get("theme_display_tier") == "tier_2_fold_only")
    return out

def bundle_check():
    out = {
        "bundle_dir_exists": BUNDLE_DIR.exists(),
        "bundle_zip_exists": BUNDLE_ZIP.exists(),
        "missing_files": [],
        "manifest_missing_keys": [],
    }
    if BUNDLE_DIR.exists():
        for name in BUNDLE_REQUIRED_FILES:
            if not (BUNDLE_DIR / name).exists():
                out["missing_files"].append(name)
        manifest_path = BUNDLE_DIR / "handoff_manifest.json"
        if manifest_path.exists():
            manifest = load_json(manifest_path)
            for k in MANIFEST_REQUIRED_KEYS:
                if k not in manifest:
                    out["manifest_missing_keys"].append(k)
        else:
            out["missing_files"].append("handoff_manifest.json")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage-id", dest="passage_id", help="e.g. 141 / PASSAGE_NO:141 / 128上")
    ap.add_argument("--keyword", dest="keyword", help='e.g. "桂枝汤"')
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--audit-summary", action="store_true")
    ap.add_argument("--bundle-check", action="store_true")
    args = ap.parse_args()

    sources = load_json(DATA_DIR / "commentarial_sources.json")
    units = load_jsonl(DATA_DIR / "commentarial_units.jsonl")
    links = load_jsonl(DATA_DIR / "commentarial_anchor_links.jsonl")
    audit = load_json(DATA_DIR / "commentarial_anchor_audit.json") if (DATA_DIR / "commentarial_anchor_audit.json").exists() else None

    out = {
        "sources_loaded": len(sources),
        "units_loaded": len(units),
        "links_loaded": len(links),
    }

    if args.passage_id:
        target = normalize_passage_key(args.passage_id)
        matched_links = [l for l in links if l["anchor_passage_id"] == target]
        u_map = {u["unit_id"]: u for u in units}
        matched_units = []
        for l in matched_links:
            u = u_map.get(l["unit_id"])
            if u:
                matched_units.append({
                    "unit_id": u["unit_id"],
                    "commentator": u["commentator"],
                    "title": u["title"],
                    "link_type": l["link_type"],
                    "anchor_role": l.get("anchor_role"),
                    "summary_text": u["summary_text"],
                    "needs_manual_anchor_review": u["needs_manual_anchor_review"],
                })
        out["passage_lookup"] = {"query": target, "hits": matched_units}

    if args.keyword:
        liu_hits = search_units(units, args.keyword, commentator="刘渡舟")
        hao_hits = search_units(units, args.keyword, commentator="郝万山")
        canonical_hits = search_canonical_stub(build_provisional_canonical_index(units, links), args.keyword)
        out["keyword_lookup"] = {
            "query": args.keyword,
            "canonical_hits": canonical_hits,
            "liu_hits": liu_hits,
            "hao_hits": hao_hits,
        }

    if args.validate:
        out["validation_problems"] = validate(units, links, audit)
        out["distribution"] = distribution(units)

    if args.audit_summary:
        if audit:
            suspicious = [x for x in audit.get("audit_entries", []) if x.get("judgement") == "suspicious"]
            wrong = [x for x in audit.get("audit_entries", []) if x.get("judgement") == "wrong"]
            out["audit_summary"] = {
                "sample_total": len(audit.get("audit_entries", [])),
                "summary_by_commentator_and_type": audit.get("summary_by_commentator_and_type", {}),
                "suspicious_count": len(suspicious),
                "wrong_count": len(wrong),
                "suspicious_or_wrong_unit_ids": [x["unit_id"] for x in suspicious + wrong],
                "named_view_ready_count": sum(1 for u in units if u.get("eligible_for_named_view")),
                "comparison_ready_count": sum(1 for u in units if u.get("eligible_for_comparison_retrieval")),
                "unresolved_multi_count": sum(1 for u in units if u.get("anchor_type") == "multi" and u.get("anchor_priority_mode") == "unresolved_multi"),
                "theme_display_tier_counts": dict(Counter(u.get("theme_display_tier") for u in units if u.get("anchor_type") == "theme")),
            }
        else:
            out["audit_summary"] = {"error": "commentarial_anchor_audit.json not found"}

    if args.bundle_check:
        out["bundle_check"] = bundle_check()

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
