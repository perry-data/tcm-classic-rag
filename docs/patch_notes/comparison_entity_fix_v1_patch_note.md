# comparison_entity_fix_v1 patch note

## 变更范围

本轮只修 `eval_seed_q085` 和 `eval_seed_q090` 对应的 comparison 双实体识别与方名归一问题，不修改 goldset，不修改旧 72 条，不继续 Batch B，不处理 source_lookup / meaning_explanation / general_overview 的剩余失败。

## 代码变更

- 在 `backend/answers/assembler.py` 中新增 formula title 的 raw anchor 抽取、校注清洗和 alias variants 生成。
- 支持清洗 `赵本作「...」`、`赵本无「...」字` 等标题校注噪声。
- 支持把 `赵本医统本并有「汤」字` 这类插入型校注归一为实际方名中的 `汤`。
- comparison 方文标题匹配改用同一套清洗逻辑，避免 canonical title 清洗后无法定位原始方文记录。

## 评估结果

- 重跑完整 `artifacts/evaluation/goldset_v2_working_102.json`。
- 新报告：
  - `artifacts/evaluation/comparison_entity_fix_v1_eval_report.json`
  - `artifacts/evaluation/comparison_entity_fix_v1_eval_report.md`
- `eval_seed_q085` 与 `eval_seed_q090` 均从 `refuse` 修复为 `strong`。
- 两题 gold citation check 均通过。
- 完整 102 题 `failure_count` 从 `7` 降至 `5`。
- comparison 题型 `failure_count = 0`。
- 旧 72 条 comparison 样本保持 `12/12` 通过；未新增旧 comparison 失败。

## 保留问题

以下失败未在本轮修复，按任务约束保留给后续专项处理：

- `eval_seed_q076`
- `eval_seed_q082`
- `eval_seed_q093`
- `eval_seed_q095`
- `eval_seed_q096`
