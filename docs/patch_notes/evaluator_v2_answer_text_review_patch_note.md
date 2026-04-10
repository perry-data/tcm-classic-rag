# evaluator_v2 Answer_text Review Patch Note

- 日期：2026-04-10
- 类型：evaluation artifact / minimal review integration
- 对应轮次：评估优化第三步的最小版

## 1. 本轮做了什么

本轮只做 `answer_text review` 的最小接入，没有改 retrieval、rerank、prompt、goldset、API 或前端。

新增产物：

1. `docs/evaluation/answer_text_review_rubric_v1.md`
2. `artifacts/evaluation/answer_text_review_sample_v1.json`
3. `artifacts/evaluation/answer_text_review_report_v1.md`
4. `docs/patch_notes/evaluator_v2_answer_text_review_patch_note.md`

最小更新：

1. `scripts/run_evaluator_v2.py`
2. `config/evaluation/evaluator_v2_metric_schema_draft.json`
3. `artifacts/evaluation/evaluator_v2_report.json`
4. `artifacts/evaluation/evaluator_v2_report.md`

## 2. 本轮接通了什么

### 2.1 Rubric

本轮把 answer_text review 的四个维度冻结为：

1. `clarity`
2. `structure`
3. `evidence_faithfulness`
4. `mode_boundary_preservation`

评分统一使用 `0 / 1 / 2`。

### 2.2 样本集

本轮没有对 150 条全量做人评，只抽了 `7` 条最小样本，用来接通 review 回路。

覆盖包括：

1. `strong`
2. `weak_with_review_notice`
3. `refuse`
4. `general_overview`
5. `source_lookup`
6. retrieval 诊断样本

### 2.3 主报告接入

本轮对 `run_evaluator_v2.py` 做了最小更新：

1. 当 `artifacts/evaluation/answer_text_review_sample_v1.json` 存在时
2. 自动把 `answer_text_quality_review` summary 写入 `evaluator_v2_report.json/.md`

该 summary 当前承载：

1. `enabled`
2. `sample_count`
3. `rubric_dimensions`
4. `summary_notes`
5. `artifact_path`

## 3. 本轮实际 review 结论

当前最小 review 的正式结论是：

1. 共审阅 `7` 条样本
2. 发现 `2` 条 style-only `answer_text_quality_issue` 候选
3. 未发现 boundary-affecting 候选

主要问题集中在：

1. 弱答解释题偏“材料直贴”
2. general_overview 偏长、偏分支堆叠

相对稳定的类型是：

1. source_lookup
2. comparison
3. refuse

## 4. 与退出码和既有 report 的关系

本轮必须明确：

1. answer_text review 仍是诊断层 artifact
2. 不影响 `failure_count`
3. 不影响 `--fail-on-evaluation-failure`
4. 不自动改写 existing failure taxonomy 计数

因此：

1. 这轮是“把 review 接进来”
2. 不是“把人工结果接成强失败规则”

## 5. schema 与 report 的最小变化

### 5.1 schema

本轮只做最小对齐：

1. 为 `answer_text_quality_review` 增加更明确的字段描述
2. 将 `artifact_path` 固定为 object 形态下的必填字段

### 5.2 evaluator_v2 report

本轮更新后：

1. `answer_text_quality_review` 不再只是纯 `null` 预留位
2. 现在可以承载 sampled manual review summary

对既有 report 读取的影响：

1. 低
2. 已有 retrieval / taxonomy / summary 结构未变
3. 只是把原先的 `null` 扩成了有内容的 summary object

## 6. 本轮没有做什么

以下内容本轮都没有做：

1. 没有做 prompt 调优
2. 没有做 retrieval 调优
3. 没有做 latency benchmark
4. 没有改 goldset
5. 没有做 150 条全量人工评审
6. 没有改前端 / API / payload contract

## 7. 本轮完成后的意义

做完这一步以后，项目协调层已经可以回答：

1. 当前 answer_text 是怎么审的
2. 审的是哪几条
3. 审出来的主要问题集中在哪
4. 这些结论是否足以支撑下一步 prompt / 生成质量优化

本轮的答案是：

1. 已有统一 rubric
2. 已有最小样本集
3. 已有 review 报告
4. 已能支撑下一步“定向优化 general_overview 与 weak answer 的表达组织”，但还不支撑全量质量结论
