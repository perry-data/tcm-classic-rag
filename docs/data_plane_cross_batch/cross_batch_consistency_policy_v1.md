# Cross-Batch AHV Consistency Policy v1

## Non-Expansion Rule

- 本 policy 只约束 AHV v1/AHV2 已有 safe primary 对象。
- 不新增第三批对象，不恢复 raw full/ambiguous passage 到 primary。

## Confidence Rule

- AHV v1/AHV2 safe primary 统一保留 `source_confidence=medium`。
- support/review-only 对象保持 `source_confidence=review_only`，不得拥有 active learner-safe normalization。

## Primary Evidence Type Rule

| concept_type | primary_evidence_type | cross_batch_scope_type | scope |
| --- | --- | --- | --- |
| disease_course_term | exact_term_definition | named_condition_definition | 病证/状态对象统一标为 named_condition_definition，不外扩到治疗、病机或整段材料。 |
| disease_location_term | exact_term_definition | named_condition_definition | 病证/状态对象统一标为 named_condition_definition，不外扩到治疗、病机或整段材料。 |
| disease_person_state_term | exact_term_definition | named_condition_definition | 病证/状态对象统一标为 named_condition_definition，不外扩到治疗、病机或整段材料。 |
| disease_state_term | exact_term_definition | named_condition_definition | 病证/状态对象统一标为 named_condition_definition，不外扩到治疗、病机或整段材料。 |
| pathogen_category_term | exact_term_definition | pathogen_category_definition | 分类枚举对象统一标为 pathogen_category_definition，只保留自足枚举句。 |
| post_recovery_term | exact_term_definition | post_recovery_definition | 瘥后复病对象统一标为 post_recovery_definition，劳复、食复、过经互不归一。 |
| pulse_pathology_term | exact_term_definition | pulse_pathology_definition | 脉病理分类对象统一标为 pulse_pathology_definition，后文解释只作 supporting evidence。 |
| pulse_pattern_term | exact_term_definition | pulse_pattern_definition | 脉象对象统一标为 pulse_pattern_definition，仅表示命名脉象句或短定义句。 |
| pulse_qi_state_term | exact_term_definition | pulse_state_definition | 脉象所见气血状态对象统一标为 pulse_state_definition，限定为原句判断义。 |
| qi_blood_state_term | exact_term_definition | body_state_definition | 气血/身体状态对象统一标为 body_state_definition，限定为原句命名或判断义。 |
| seasonal_disease_term | exact_term_definition | seasonal_disease_definition | 时病/外感病名对象统一标为 seasonal_disease_definition，仅保留闭合命名/定义句。 |
| six_channel_disease_term | exact_term_definition | channel_disease_outline | 六经病对象统一标为 channel_disease_outline，仅表示提纲句/总纲句，不代表该篇全部证治。 |

## Alias And Normalization Rule

- AHV v1/AHV2 active learner term surfaces must use `match_mode=exact`.
- active single-character alias is forbidden.
- active alias pointing to multiple concepts is forbidden.
- inactive risky/ambiguous aliases may stay registered for audit, but must not route into AHV primary.

## Intent Guard Rule

- `X 是什么 / X 是什么意思 / 何谓 X` may use the matching AHV definition object.
- treatment, formula, mechanism, source-passage, and comparison questions must not be hijacked by a single AHV definition object.
