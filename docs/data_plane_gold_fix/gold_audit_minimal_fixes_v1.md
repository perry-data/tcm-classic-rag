# Gold Audit Minimal Fixes v1

## Scope

- 本轮只落实 small gold audit v1 指出的两个立即问题：`发汗药` primary sentence 裁决、`胆瘅` review-only alias cleanup。
- 未扩容 definition/formula 对象，未修改 prompt、前端、API payload、answer_mode 或 commentarial 主逻辑。

## 发汗药

- 结论：采用方案2，保留当前句并显式标为 explanation-primary。
- 理由：`桂枝汤者，发汗药也` 是具体方剂归属句，不是“发汗药”本身的独立定义；当前句能解释服法与发散机制，但不能当严格 definition-primary。
- 落地：`primary_evidence_type` 维持 `exact_term_explanation`，`promotion_reason` 改为 `gold_fix_v1_explanation_primary_not_strict_definition`，notes 写明不是 strict definition。

## 胆瘅

- 结论：继续 review-only，清理 `口苦病` / `胆瘅病` learner alias 风险。
- 落地：`query_aliases_json` 与 `learner_surface_forms_json` 清空；`retrieval_text` 移除风险 alias；`term_alias_registry` 只保留 canonical `胆瘅`。

## Regression Summary

- forbidden_primary after: `0`
- 胆瘅 risk alias after: `0`
- 胆瘅 learner lexicon risk after: `0`
- formula strong after: `2/2`
- gold-safe definition hit after: `2`
