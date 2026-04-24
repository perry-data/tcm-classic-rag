# AHV Adversarial Regression v1

本轮只做 AHV safe primary objects 的对抗回归与最小误触发修复，不新增对象，不改 prompt、前端、API payload、answer_mode、commentarial 主逻辑，也不重新放开 raw `full:passages:*` 或 `full:ambiguous_passages:*` 进入 primary。

## Scope

- covered_ahv_safe_primary_objects: `20`
- total_query_count: `87`
- query_type_counts: `{"ahv_canonical_guard":20,"similar_concept_false_trigger":20,"disabled_alias_recheck":5,"partial_word_literal_similarity":10,"non_definition_intent":8,"negative_unrelated":10,"formula_guard":5,"gold_safe_definition_guard":5,"review_only_boundary_guard":4}`
- high_risk_focus_terms: `温病`, `柔痓`, `革脉`, `行尸`, `内虚`

## Before Fix

- pass_count / fail_count: `67 / 20`
- wrong_ahv_primary_hit_count: `2`
- wrong_term_normalization_count: `18`
- disabled_alias_still_hit_count: `2`
- partial_word_false_positive_count: `0`
- non_definition_intent_hijack_count: `8`
- negative_sample_false_positive_count: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`
- ahv_canonical_guard_pass_count: `20 / 20`

Primary failure family:

- AHV `contains` normalization fired on comparison / relation / treatment / formula intent, for example `伤寒和温病有什么区别`, `劳复和食复一样吗`, `霍乱用什么方？`.
- Two inactive aliases still reached AHV primary through retrieval text rather than learner-safe alias: `暑病者是什么意思` -> `暑病`; `寒疫是什么意思` -> `时行寒疫`.

## Minimal Fix

- Updated active AHV learner term surfaces in `learner_query_normalization_lexicon` from `contains` to `exact`.
- Updated runtime definition normalization so AHV term aliases are interpreted as exact-match only.
- Added runtime primary blocking when a query exactly matches an inactive AHV alias.
- No AHV object was added, downgraded, or re-promoted.

## After Fix

- pass_count / fail_count: `87 / 0`
- wrong_ahv_primary_hit_count: `0`
- wrong_term_normalization_count: `0`
- disabled_alias_still_hit_count: `0`
- partial_word_false_positive_count: `0`
- non_definition_intent_hijack_count: `0`
- negative_sample_false_positive_count: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`
- ahv_canonical_guard_pass_count: `20 / 20`

## Artifacts

- query set: `artifacts/data_plane_adversarial/ahv_adversarial_query_set_v1.json`
- before-fix regression: `artifacts/data_plane_adversarial/ahv_adversarial_regression_before_fix_v1.json`
- after-fix regression: `artifacts/data_plane_adversarial/ahv_adversarial_regression_after_fix_v1.json`
- failure report: `artifacts/data_plane_adversarial/ahv_adversarial_failures_v1.md`
- fix ledger: `artifacts/data_plane_adversarial/ahv_adversarial_fix_ledger_v1.json`
- snapshots:
  - `artifacts/data_plane_adversarial/definition_term_registry_ahv_adversarial_v1_snapshot.json`
  - `artifacts/data_plane_adversarial/term_alias_registry_ahv_adversarial_v1_snapshot.json`
  - `artifacts/data_plane_adversarial/learner_query_normalization_ahv_adversarial_v1_snapshot.json`

## Verdict

The 20 AHV safe primary objects can remain safe primary after this adversarial pass. The main line did not regress: canonical AHV guard remains `20 / 20`, formula bad anchors remain `0`, forbidden primary remains `0`, and review-only primary conflict remains `0`.
