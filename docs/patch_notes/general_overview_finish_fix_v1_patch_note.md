# general_overview_finish_fix_v1 patch note

## 变更范围

本轮只做 Batch A 最后两条 general_overview 收尾：`eval_seed_q095` 与 `eval_seed_q096`。未修改 goldset，未修改旧 72 条，未继续 Batch B，未顺手处理其他题型。

## 代码变更

- 在 `backend/strategies/general_question.py` 中补充 `有哪些核心表现和处理边界`、`有哪些处理分支`、`有哪些核心表现` 的 general_overview 触发短语。
- 在 `backend/answers/assembler.py` 中为 general_overview 增加章节约束下的主题别名匹配。
- 为 `少阳病` 增加章节内 `少阳` 匹配，为 `伤寒瘥后` 增加章节内 `伤寒瘥`、`大病瘥后`、`伤寒解后` 匹配。
- 在分支识别中补充 `与X汤` 方剂句式，支持 q095 将 `与小柴胡汤` 纳入 strong primary evidence。

## 评估结果

- 重跑完整 `artifacts/evaluation/goldset_v2_working_102.json`。
- 新报告：
  - `artifacts/evaluation/general_overview_finish_fix_v1_eval_report.json`
  - `artifacts/evaluation/general_overview_finish_fix_v1_eval_report.md`
- `eval_seed_q095` 从 `weak_with_review_notice` 修复为 `strong`，gold citation check 从 FAIL 修复为 PASS。
- `eval_seed_q096` 从 `weak_with_review_notice` 修复为 `strong`，gold citation check 保持 PASS。
- 完整 102 题 `failure_count` 从 `2` 降至 `0`。
- `all_checks_passed = true`。
- general_overview 题型 `14/14` mode match，`14/14` citation basic pass，`failure_count = 0`。
- 旧 72 条 general_overview 样本保持 `12/12` 通过。

## 保留问题

Batch A working 102 当前已全通过。本轮不做 Batch B、不扩容、不写论文正文。
