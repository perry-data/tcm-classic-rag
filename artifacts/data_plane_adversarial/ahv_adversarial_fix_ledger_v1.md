# AHV Adversarial Fix Ledger v1

- run_id: `ahv_adversarial_regression_v1`
- generated_at_utc: `2026-04-24T05:22:52.005720+00:00`
- db_path: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`
- changed_learner_surface_count: `28`
- downgraded_object_count: `0`
- deactivated_alias_count: `0`

## Fixes

- AHV active learner term surfaces are set to `match_mode=exact`.
- Runtime support in `backend/retrieval/minimal.py` interprets AHV term aliases as exact-match only.
- Runtime support blocks definition primary when a query exactly matches an inactive AHV alias.
- No AHV object was added or downgraded in this fix pass.

## Changed Learner Surfaces

| target_term | surface_form | active | before | after |
| --- | --- | --- | --- | --- |
| 伤寒 | 伤寒 | 1 | contains | exact |
| 伤寒 | 伤寒病 | 1 | contains | exact |
| 促脉 | 促脉 | 1 | contains | exact |
| 内虚 | 内虚 | 1 | contains | exact |
| 冬温 | 冬温 | 1 | contains | exact |
| 冬温 | 冬温病 | 1 | contains | exact |
| 刚痓 | 刚痉 | 1 | contains | exact |
| 刚痓 | 刚痓 | 1 | contains | exact |
| 劳复 | 劳复 | 1 | contains | exact |
| 太阳病 | 太阳之为病 | 1 | contains | exact |
| 太阳病 | 太阳病 | 1 | contains | exact |
| 弦脉 | 弦脉 | 1 | contains | exact |
| 时行寒疫 | 时行寒疫 | 1 | contains | exact |
| 暑病 | 暑病 | 1 | contains | exact |
| 柔痓 | 柔痉 | 1 | contains | exact |
| 柔痓 | 柔痓 | 1 | contains | exact |
| 温病 | 温病 | 1 | contains | exact |
| 滑脉 | 滑脉 | 1 | contains | exact |
| 痓病 | 痉病 | 1 | contains | exact |
| 痓病 | 痓病 | 1 | contains | exact |
| 结脉 | 结脉 | 1 | contains | exact |
| 血崩 | 崩血 | 1 | contains | exact |
| 血崩 | 血崩 | 1 | contains | exact |
| 行尸 | 行尸 | 1 | contains | exact |
| 霍乱 | 吐利霍乱 | 1 | contains | exact |
| 霍乱 | 霍乱 | 1 | contains | exact |
| 革脉 | 革脉 | 1 | contains | exact |
| 食复 | 食复 | 1 | contains | exact |

## Snapshots

- definition_term_registry: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/data_plane_adversarial/definition_term_registry_ahv_adversarial_v1_snapshot.json`
- term_alias_registry: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/data_plane_adversarial/term_alias_registry_ahv_adversarial_v1_snapshot.json`
- learner_query_normalization_lexicon: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/data_plane_adversarial/learner_query_normalization_ahv_adversarial_v1_snapshot.json`
