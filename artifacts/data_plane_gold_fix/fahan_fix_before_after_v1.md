# 发汗药 Fix Before/After v1

## Decision

采用方案2：未找到比当前句更合格、更 learner-facing 且可独立成义的安全 definition/membership primary。当前句保留，但对象语义显式落为 explanation-primary，不再按严格术语定义对象理解。

## Registry Before/After

- primary sentence: `发汗药，须温暖服者，易为发散也` -> `发汗药，须温暖服者，易为发散也`
- primary_evidence_type: `exact_term_explanation` -> `exact_term_explanation`
- definition evidence ids: `[]` -> `[]`
- explanation evidence ids: `["ZJSHL-CH-006-P-0127"]` -> `["ZJSHL-CH-006-P-0127"]`
- membership evidence ids: `["ZJSHL-CH-006-P-0120"]` -> `["ZJSHL-CH-006-P-0120"]`
- promotion_reason: `exact sentence promoted out of mixed full passage` -> `gold_fix_v1_explanation_primary_not_strict_definition`

## Notes Before

从 risk_only full passage 中抽出解释句与类属句，避免整段混入《金匮玉函》警示材料。

## Notes After

从 risk_only full passage 中抽出解释句与类属句，避免整段混入《金匮玉函》警示材料。 gold_fix_v1: no safer standalone membership/definition sentence was selected; keep the current sentence as explanation-primary, not definition-primary. ZJSHL-CH-006-P-0120 remains support membership evidence only.

## Query Behavior

| category | query | before_mode | after_mode | before_focus | after_focus | before_target_hit | after_target_hit | primary_after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fahan | 什么是发汗药 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
| fahan | 发汗药是什么意思 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
| fahan | 发汗药是干什么的 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
| fahan | 发汗的药是什么意思 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
