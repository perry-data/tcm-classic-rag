# 分层启用字段建议

## 1. 目的

本文件用于约束后续数据库阶段如何给记录打标，以承接 `06_layered_enablement_policy.md` 中的分层启用策略。

这里给出的只是字段与标签建议，不代表本轮就要修改原始数据文件。

## 2. 总体建议

后续数据库阶段不要只保存“原始文本内容”，还应保存“运行时启用标签”。最少应让系统能回答以下问题：

- 这条记录来自哪一类对象？
- 它是否允许参与召回？
- 它属于哪一层证据等级？
- 它能不能展示给用户？
- 若能展示，是否必须带风险提示？
- 它在默认排序中的权重层级是什么？

## 3. 建议字段

| 字段名 | 类型建议 | 说明 | 典型取值 |
| --- | --- | --- | --- |
| `dataset_variant` | string | 数据来源版本 | `safe` / `full` |
| `source_object` | string | 原始对象类型 | `passages` / `main_passages` / `chunks` / `annotations` / `annotation_links` / `ambiguous_passages` |
| `source_type` | string | 业务角色类型 | `main_text` / `chunk` / `annotation` / `ledger_text` / `risk_registry` / `link_relation` |
| `retrieval_allowed` | boolean | 是否允许参与召回 | `true` / `false` |
| `evidence_level` | string | 分层等级 | `A` / `B` / `C` / `D` |
| `display_allowed` | string | 是否允许前台展示 | `primary` / `secondary` / `risk_only` / `preview_only` / `false` |
| `risk_flag` | string or array | 风险标签 | `none` / `annotation_unlinked` / `ambiguous_source` / `ledger_mixed_roles` / `strong_evidence_insufficient` |
| `requires_disclaimer` | boolean | 是否要求前台提示 | `true` / `false` |
| `default_weight_tier` | string | 默认排序权重层级 | `highest` / `high` / `medium` / `medium_low` / `low` / `lowest` / `off` |

## 4. 可选补充字段

如果后续数据库阶段允许增加更多字段，建议补充：

| 字段名 | 说明 |
| --- | --- |
| `citation_role` | 例如 `canonical` / `supplementary` / `annotation_reference` / `preview` |
| `review_status` | 例如 `verified` / `unverified` / `ambiguous` / `disabled` |
| `display_section` | 例如 `primary_evidence` / `secondary_evidence` / `review_materials` |
| `derived_from_policy` | 记录该条标签来自哪版策略，例如 `layered_enablement_policy_v1` |
| `source_record_ids` | 对 chunk 或派生对象保存原始关联记录 ID |

## 5. 各类对象建议打标

### 5.1 safe `chunks`

| 字段 | 建议值 |
| --- | --- |
| `dataset_variant` | `safe` |
| `source_object` | `chunks` |
| `source_type` | `chunk` |
| `retrieval_allowed` | `true` |
| `evidence_level` | `C` |
| `display_allowed` | `preview_only` |
| `risk_flag` | `none` |
| `requires_disclaimer` | `false` |
| `default_weight_tier` | `highest` |

说明：它是召回主骨架，但不是最终规范证据。

### 5.2 safe `main_passages` 且 `retrieval_primary=true`

| 字段 | 建议值 |
| --- | --- |
| `dataset_variant` | `safe` |
| `source_object` | `main_passages` |
| `source_type` | `main_text` |
| `retrieval_allowed` | `true` |
| `evidence_level` | `A` |
| `display_allowed` | `primary` |
| `risk_flag` | `none` |
| `requires_disclaimer` | `false` |
| `default_weight_tier` | `high` |

### 5.3 safe `main_passages` 且 `retrieval_primary=false`

| 字段 | 建议值 |
| --- | --- |
| `dataset_variant` | `safe` |
| `source_object` | `main_passages` |
| `source_type` | `main_text` |
| `retrieval_allowed` | `true` |
| `evidence_level` | `B` |
| `display_allowed` | `secondary` |
| `risk_flag` | `short_text_demoted` |
| `requires_disclaimer` | `false` |
| `default_weight_tier` | `medium` |

说明：允许被召回和展示，但不进入主依据位。

### 5.4 full `annotations`

| 字段 | 建议值 |
| --- | --- |
| `dataset_variant` | `full` |
| `source_object` | `annotations` |
| `source_type` | `annotation` |
| `retrieval_allowed` | `true` |
| `evidence_level` | `B` |
| `display_allowed` | `secondary` |
| `risk_flag` | `annotation_unlinked` |
| `requires_disclaimer` | `true` |
| `default_weight_tier` | `medium_low` |

说明：按注解原文片段使用，不可假定它已经正确挂到某一正文。

### 5.5 full `passages`

| 字段 | 建议值 |
| --- | --- |
| `dataset_variant` | `full` |
| `source_object` | `passages` |
| `source_type` | `ledger_text` |
| `retrieval_allowed` | `true` |
| `evidence_level` | `C` |
| `display_allowed` | `risk_only` |
| `risk_flag` | `ledger_mixed_roles` |
| `requires_disclaimer` | `true` |
| `default_weight_tier` | `low` |

说明：它是总账层，不是默认主证据层。

### 5.6 `ambiguous_passages`

| 字段 | 建议值 |
| --- | --- |
| `dataset_variant` | `full` |
| `source_object` | `ambiguous_passages` |
| `source_type` | `risk_registry` |
| `retrieval_allowed` | `true` |
| `evidence_level` | `C` |
| `display_allowed` | `risk_only` |
| `risk_flag` | `ambiguous_source` |
| `requires_disclaimer` | `true` |
| `default_weight_tier` | `lowest` |

说明：只用于低权重召回和风险判断，不可作为主证据。

### 5.7 `annotation_links`

| 字段 | 建议值 |
| --- | --- |
| `dataset_variant` | `full` |
| `source_object` | `annotation_links` |
| `source_type` | `link_relation` |
| `retrieval_allowed` | `false` |
| `evidence_level` | `D` |
| `display_allowed` | `false` |
| `risk_flag` | `disabled_link_layer` |
| `requires_disclaimer` | `false` |
| `default_weight_tier` | `off` |

说明：当前阶段默认禁用；未来灰度启用前应重新验收。

## 6. 记录级打标建议

后续数据库阶段建议不是只给“表”打标，而是给“记录”打标。至少应支持以下细粒度规则：

1. 同一 `main_passages` 表内，不同记录可分别是 A 或 B。
2. 同一 `passages` 表内，不同记录可因为 `text_role`、`dataset_variant`、`risk_flag` 不同而采用不同权重。
3. `annotations` 即使允许展示，也必须单独带 `requires_disclaimer = true`。
4. 任何来自 `ambiguous_passages` 的关联记录，至少要带 `risk_flag = ambiguous_source`。

## 7. 最低落地要求

若数据库阶段只能先落地最少字段，建议优先实现以下 7 个：

1. `dataset_variant`
2. `source_object`
3. `retrieval_allowed`
4. `evidence_level`
5. `display_allowed`
6. `risk_flag`
7. `default_weight_tier`

这 7 个字段已经足以支撑分层召回、证据筛选和前台展示分区。
