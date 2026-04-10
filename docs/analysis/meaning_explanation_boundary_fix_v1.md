# Batch A meaning_explanation boundary fix v1

## 目标范围

本轮只修 `eval_seed_q093` 暴露出的 meaning_explanation 强弱边界问题，不修改 `goldset_v2_working_102.json`，不修改旧 72 条，不继续 Batch B，也不处理 `eval_seed_q095` / `eval_seed_q096`。

## 失败根因

`eval_seed_q093` 的 query 为 `心下痞，按之濡是什么意思？`，goldset 明确要求 `expected_mode = weak_with_review_notice`，并设置 `must_keep_primary_empty = true`。修复前系统输出 `strong`：

| question_id | 修复前 actual_mode | primary | total_evidence | citations | failed_checks |
| --- | --- | ---: | ---: | ---: | --- |
| `eval_seed_q093` | `strong` | 1 | 8 | 1 | `mode_match, primary_empty_check, unsupported_assertion_check` |

根因不是 citation 没命中，而是标准 answer assembler 对 meaning explanation 的证据分层过于激进。retrieval 命中了正文 `ZJSHL-CH-010-P-0083`，其内容为 `心下痞，按之濡，其脉关上浮者，大黄黄连泻心汤主之。`。这条正文提供题面短语的语境，但不是独立定义或解释句；直接解释来自注解 `ZJSHL-CH-010-P-0084`，因此按 goldset 边界应保持 weak，并把正文/注解都作为 secondary 或 review 使用。

旧 strong meaning_explanation 样本的主证据则不同：`eval_seed_q034`、`eval_seed_q035`、`eval_seed_q036`、`eval_seed_q038` 的正文主证据包含 `名曰`、`谓之` 或 `者...也` 等定义句式，可以保留 strong。

## 修复策略

在 `backend/answers/assembler.py` 的标准组装路径中增加 meaning_explanation 边界收束：

- 仅对 query 中包含 `是什么意思` 或 `什么意思` 的解释问法生效。
- 仅在当前 retrieval mode 已经是 `strong` 且存在 primary_evidence 时检查。
- 若 primary_evidence 中没有 `名曰`、`谓之` 或 `者...也` 这类定义句式，则把 primary_evidence demote 到 secondary_evidence，并将 answer_mode 改为 `weak_with_review_notice`。
- demote 后保留证据记录和 citation 可见性，但 `primary_evidence` 归零，避免把只提供语境的正文包装成解释题主依据。

本轮没有修改 evaluator、goldset 或 expected_mode；也没有处理 general_overview 的 q095/q096。

## 修复后结果

完整重跑 `goldset_v2_working_102.json` 后：

| question_id | 修复后 actual_mode | primary | total_evidence | citations | gold_citation_check | unsupported_assertion_check | failed_checks |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `eval_seed_q093` | `weak_with_review_notice` | 0 | 8 | 8 | PASS | PASS | 无 |

完整 102 题 evaluator 汇总：

- total_questions: `102`
- mode_match_count: `100/102`
- citation_basic_pass: `81/82`
- failure_count: `2`，较 source_lookup 修复后的 `3` 下降 1
- meaning_explanation 题型：`18/18` mode match，`18/18` citation basic pass，`failure_count = 0`

旧 72 条 meaning_explanation 样本检查：旧 meaning_explanation 共 14 条，修复后 `14/14` 仍通过；其中旧 strong 样本 `eval_seed_q034`、`eval_seed_q035`、`eval_seed_q036`、`eval_seed_q038` 均保持 strong。

## 未处理项

本轮剩余失败均为任务约束中明确不处理的 general_overview 样本：

- `eval_seed_q095`
- `eval_seed_q096`
