# 评估优化任务拆解 v1

- 文档版本：v1
- 文档日期：2026-04-09
- 文档定位：把 `evaluation_upgrade_spec_v1.md` 拆成可执行任务顺序

## 1. 执行原则

本轮只服务“评估优化”这一条主线，因此任务拆解遵守四条原则：

1. 先做自动化主骨架，再做人工 review。
2. 先做 full 150 可复跑的东西，再做代表性样本的精细评价。
3. 先复用 `evaluator_v1`，不重写整套评估链。
4. 不在任务中夹带 retrieval / prompt / frontend 改造。

## 2. 正式实现顺序

## 任务 1：扩出 evaluator_v2 主骨架

### 目标

在 `run_evaluator_v1.py` 的基础上，形成 `run_evaluator_v2.py`，先把 full 150 的结构化评估骨架跑通。

### 必做内容

1. 复用当前 goldset 150、schema v1、local_assembler / api replay 入口。
2. 补进 retrieval 级指标字段。
3. 补进 failure taxonomy 字段。
4. 保留 v1 已有的 mode / citation / unsupported_assertion 检查。
5. 输出 `evaluator_v2_report.json` 与 `evaluator_v2_report.md`。

### 为什么排第 1

因为 retrieval 指标与 taxonomy 是后续所有评估升级的主骨架。  
没有这一层，answer_text review 和 latency benchmark 都会缺少统一汇总容器。

### 交付结果

1. `scripts/run_evaluator_v2.py`
2. `artifacts/evaluation/evaluator_v2_report.json`
3. `artifacts/evaluation/evaluator_v2_report.md`

## 任务 2：冻结 retrieval 指标与 taxonomy 语义

### 目标

把 v2 主骨架中的 retrieval 指标与 failure taxonomy 从“有字段”推进到“语义冻结、可直接分析”。

### 必做内容

1. 固定 `Hit@K` 的 K 值集合。
2. 固定 rerank delta 的统计定义。
3. 固定一级 / 二级 taxonomy 类别。
4. 把 `question_type` 分组统计写进汇总。
5. 对齐 `config/evaluation/evaluator_v2_metric_schema_draft.json`。

### 为什么排第 2

因为第 1 步可能先把结构跑起来，但还不代表指标定义已经稳定。  
只有把 retrieval 与 taxonomy 的语义冻结，后面的 answer_text 与 latency artifact 才能对齐同一份 schema。

### 交付结果

1. retrieval metric definitions 对齐到 schema draft
2. `docs/evaluation/evaluation_failure_taxonomy_v1.md`
3. taxonomy definitions 写入独立文档并与 report 对齐
4. `evaluator_v2_report.*` 字段结构稳定

## 任务 3：补 answer_text 质量规约与 review set

### 目标

建立最小人工 review 机制，正式回答“baseline vs qwen-plus 的 answer_text 到底有没有更好”。

### 必做内容

1. 固定 `20` 条 non-refuse review set。
2. 固定四维 rubric：
   - clarity
   - structure
   - evidence_faithfulness
   - mode_boundary_preservation
3. 生成 baseline vs `qwen-plus` 对照结果。
4. 保存结构化 review artifact 与 Markdown 摘要。

### 为什么排第 3

因为这一步依赖前两步已经把 question set、report 语义和失败语言定住。  
如果先做人评，再回头改 question set 或字段结构，返工成本会很高。

### 交付结果

1. `config/evaluation/answer_text_review_set_v1.json`
2. `docs/evaluation/answer_text_quality_rubric_v1.md`
3. `artifacts/evaluation/answer_text_quality_review_v1.json`
4. `artifacts/evaluation/answer_text_quality_review_v1.md`

## 任务 4：补 latency mini-benchmark

### 目标

补齐当前性能证据缺口，但只做到单机、单用户、固定 query set 的最小版本。

### 必做内容

1. 固定 10 条 benchmark query。
2. 固定重复次数为 5。
3. 固定走 `POST /api/v1/answers`。
4. 产出 baseline mode latency artifact。
5. 若 live 配置可用，补 llm-enabled mode latency artifact。
6. 输出 overall / by question_type / by query 三层汇总。

### 为什么排第 4

因为 latency 是独立证据项，不依赖前端，也不应反过来阻塞 retrieval / answer_text 评估主骨架。  
把它放在第 4 步，最符合“先把评估主报告立住，再补性能证据”的顺序。

### 交付结果

1. `scripts/run_latency_mini_benchmark_v1.py`
2. `config/evaluation/latency_benchmark_query_set_v1.json`
3. `artifacts/evaluation/latency_mini_benchmark_v1.json`
4. `artifacts/evaluation/latency_mini_benchmark_v1.md`

## 3. 依赖关系

任务依赖固定如下：

1. 任务 1 是所有后续任务的前置。
2. 任务 2 依赖任务 1 已跑通。
3. 任务 3 依赖任务 2 的字段与语义冻结。
4. 任务 4 可在任务 2 完成后启动，但最终汇总仍应放在全部任务完成之后。

## 4. 每步完成标准

| 任务 | 完成标准 | 失败表现 |
| --- | --- | --- |
| 任务 1 | full 150 可复跑，并生成 v2 JSON/MD 报告 | 仍只有 v1 粒度报告，或没有 retrieval/taxonomy 字段 |
| 任务 2 | retrieval 指标、taxonomy 类别与 schema draft 对齐 | 字段存在但定义不清，无法稳定复用 |
| 任务 3 | review set、rubric、review artifact 三者同时存在 | 只有 rubric，没有实际评分结果 |
| 任务 4 | 至少 baseline latency artifact 生成；live 可用时补 llm-enabled | 没有结构化 latency 结果，只剩零散命令输出 |

## 5. 建议的提交节奏

为避免一轮提交过大，建议实现时按以下节奏提交：

1. evaluator_v2 主骨架与 schema draft
2. retrieval 指标 / taxonomy 冻结
3. answer_text rubric 与 review artifact
4. latency mini-benchmark 与最终汇总

## 6. 任务拆解结论

本轮评估优化的正确推进方式，不是同时散开做很多评估，而是严格按以下顺序：

1. 先扩 `evaluator_v2` 主骨架
2. 再冻结 retrieval 指标与 taxonomy
3. 再做 answer_text review
4. 最后补 latency mini-benchmark

只有按这个顺序推进，下一轮 retrieval / prompt 优化才会拥有统一、稳定、可复跑的评估底座。
