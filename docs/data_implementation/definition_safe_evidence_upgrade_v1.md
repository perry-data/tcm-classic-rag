# Definition Safe Evidence Upgrade v1

## Scope

本轮只建立 definition / term safe evidence 的最小闭环：把少量目前只能停在 support/review 的定义句、解释句、类属句，整理成可审计的 `definition_terms` 主证据对象。

冻结边界保持不变：

- 不改 prompt、前端、API payload 顶层 contract、answer_mode 定义。
- 不重新放开 `full:passages:*` 进入 `primary_evidence`。
- 不改 formula object、commentarial 主逻辑。
- runtime 只在 definition priority 候选层接入新的安全对象。

## Problem

上一轮 boundary regression 已经证明 `full:passages:*` 不再进入 `primary_evidence`。代价是部分 definition / meaning query 只能 weak，因为关键定义材料还留在 raw full passages：

- `什么是发汗药`：关键句 `桂枝汤者，发汗药也。` 在 `full:passages:ZJSHL-CH-006-P-0120`，只能 secondary/review。
- `发汗药是什么意思`：关键解释句 `发汗药，须温暖服者，易为发散也。` 在 `full:passages:ZJSHL-CH-006-P-0127`，只能 secondary/review。
- `坏病是什么 / 坏病是什么意思`：关键句 `谓之坏病，言为医所坏病也` 在 `full:passages:ZJSHL-CH-008-P-0227`，只能 secondary/review。

这不是 prompt 问题，也不是前端展示问题；瓶颈在证据对象层没有把定义句从 raw full passage 中拆出来并标为安全主证据候选。

## Data Object

新增 SQLite 表 / 视图：

- `definition_term_registry`：人工审定的概念登记表，包含 safe 与 review-only 候选。
- `retrieval_ready_definition_view`：只暴露 `is_safe_primary_candidate=1` 的概念对象给 runtime。

新增 runtime source：

- `source_object = definition_terms`
- `record_id = safe:definition_terms:<concept_id>`
- `evidence_level = A`
- `display_allowed = primary`
- `policy_source_id = definition_term_object_view`

原始 `full:passages:*` 表保持 C / risk_only，不改变其 primary eligibility。

## Initial Concepts

| concept_id | term | type | primary sentence | primary source | promoted |
| --- | --- | --- | --- | --- | --- |
| `DEF-FAHAN-YAO` | 发汗药 | therapeutic_category | 发汗药，须温暖服者，易为发散也。 | `ZJSHL-CH-006-P-0127` | yes |
| `DEF-XIA-YAO` | 下药 | therapeutic_category | 承气汤者，下药也。 | `ZJSHL-CH-006-P-0120` | yes |
| `DEF-HUAI-BING` | 坏病 | disease_state_term | 太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。 | `ZJSHL-CH-008-P-0227` | yes |
| `DEF-YANG-JIE` | 阳结 | pulse_pattern_term | 其脉浮而数，能食，不大便者，此为实，名曰阳结也。 | `ZJSHL-CH-003-P-0004` | yes |
| `DEF-YIN-JIE` | 阴结 | pulse_pattern_term | 其脉沉而迟，不能食，身体重，大便反硬，名曰阴结也。 | `ZJSHL-CH-003-P-0004` | yes |
| `DEF-SHEN-DAN` | 神丹 | drug_name_term | 神丹者，发汗之药也。 | `ZJSHL-CH-006-P-0118` | no |

`DEF-SHEN-DAN` 只登记不提升，因为当前来源仍是 annotation/full passage 对照材料，不能为了 strong 数量越过审计边界。

## Runtime Wiring

`DefinitionRuntimeIndex` 从 `retrieval_ready_definition_view` 读取安全概念对象，并将其加入 retrieval raw candidate 集合。

`AnswerAssembler` 的 definition priority 只做两点接线：

- 允许 `definition_terms` 作为 definition / meaning family 的 primary source。
- 对 `definition_terms` 使用 registry 中的 `primary_evidence_type`、`canonical_term`、`query_aliases_json` 做候选评分。

如果没有命中 `definition_terms`，现有 secondary/review fallback 保持不变。

## Validation

回归脚本：

```bash
./.venv/bin/python scripts/data_implementation/build_definition_term_registry_v1.py
./.venv/bin/python scripts/data_implementation/run_definition_safe_evidence_regression_v1.py
./.venv/bin/python -m unittest tests.test_definition_primary_boundary
```

验证重点：

- support-only definition query 至少部分由 weak 升为 strong。
- `primary_evidence` 可来自 `safe:definition_terms:*` 或既有 `safe:main_passages:*`。
- `full:passages:*` 仍不得进入 `primary_evidence`。
- formula object regression 仍保持 strong，且 formula primary 仍只来自 safe main。
