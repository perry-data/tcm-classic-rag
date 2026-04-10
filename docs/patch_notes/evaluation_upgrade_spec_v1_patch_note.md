# Evaluation Upgrade Spec v1 Patch Note

## 1. 本轮新增了什么

本轮没有改 retrieval、prompt、frontend 或 payload contract，而是先把“第一轮唯一优化目标：评估优化”正式冻结成实现规格。

新增文件：

1. `docs/evaluation/evaluation_upgrade_spec_v1.md`
   - 冻结第一轮评估优化的最小范围。
   - 明确 retrieval 指标、answer_text 质量规约、latency mini-benchmark、failure taxonomy 四项都纳入。
   - 明确每项只做最小可实施版，不扩成大平台。
   - 明确产物清单、验收口径与实现顺序。
2. `docs/evaluation/evaluation_upgrade_task_breakdown_v1.md`
   - 把评估优化拆成 1、2、3、4 四步顺序。
   - 明确每一步的目标、依赖、交付结果与失败表现。
3. `config/evaluation/evaluator_v2_metric_schema_draft.json`
   - 冻结 evaluator v2 主报告的 JSON 结构 draft。
   - 为后续实现 retrieval 指标、answer_text review、latency benchmark、failure taxonomy 提供统一容器。
4. `docs/patch_notes/evaluation_upgrade_spec_v1_patch_note.md`
   - 记录本轮规格冻结范围与结论摘要。

## 2. 本轮为什么先做规格，不直接做实现

原因有三点：

1. 当前系统已经进入“先评估、再单线优化”的阶段，不能边写实现边重新定义范围。
2. 评估优化涉及自动化 runner、人工 rubric、benchmark、taxonomy，若不先冻结边界，最容易失控成一轮“大杂烩”。
3. 当前下一轮真正需要的不是马上调 retrieval 或 prompt，而是一份可直接执行的评估升级规格。

## 3. 本轮冻结了什么

### 3.1 第一轮评估优化的最小范围

本轮正式冻结：

1. retrieval 级指标：纳入
2. answer_text 质量评价规约：纳入
3. latency mini-benchmark：纳入
4. failure taxonomy：纳入

但四项都只做最小版：

1. retrieval 只补 `Hit@K`、题型分组和 rerank delta
2. answer_text 只做代表性 review set 的人工 rubric
3. latency 只做本地 API 路径的 mini-benchmark
4. taxonomy 只做轻量二级分类

### 3.2 本轮明确不纳入的项

本轮正式排除：

1. retrieval 调优本身
2. prompt 调优本身
3. goldset 扩到 200–250
4. 用户满意度
5. 双人标注一致性
6. 多书评估
7. 并发压测 / 生产级性能评估
8. 前端与 payload 相关改动

## 4. 本轮关键结论

### 4.1 必须新增的实现产物

实现轮次至少需要新增：

1. `scripts/run_evaluator_v2.py`
2. `scripts/run_latency_mini_benchmark_v1.py`
3. `config/evaluation/answer_text_review_set_v1.json`
4. `config/evaluation/latency_benchmark_query_set_v1.json`
5. `docs/evaluation/answer_text_quality_rubric_v1.md`
6. `docs/evaluation/evaluation_failure_taxonomy_v1.md`
7. `artifacts/evaluation/evaluator_v2_report.json/.md`
8. `artifacts/evaluation/answer_text_quality_review_v1.json/.md`
9. `artifacts/evaluation/latency_mini_benchmark_v1.json/.md`

### 4.2 实现顺序

本轮冻结的实现顺序只有一条：

1. 先扩 `evaluator_v2` 主骨架
2. 再冻结 retrieval 指标与 taxonomy
3. 再做 answer_text review
4. 最后补 latency mini-benchmark

### 4.3 验收口径

本轮规格已明确：

1. `done` 是什么
2. `partially done` 是什么
3. `not done` 是什么

因此下一轮实现时，不会再出现“做了一部分，但到底算不算完成”这种口径不清的问题。

## 5. 本轮未做什么

本轮明确没有做以下事情：

1. 没有修改任何业务代码。
2. 没有实现 `evaluator_v2`。
3. 没有新增 benchmark 或 review artifact。
4. 没有改 retrieval / prompt / frontend / payload。

本轮只做规格冻结，不做功能实现。

## 6. 本轮正式意义

本轮完成后，评估优化这条主线已经从“方向判断”进入了“可直接开工”的状态。

也就是说，下一轮不需要再讨论“评估到底补哪些”，而是可以直接按规格实现：

1. 先补 evaluator v2
2. 再补 retrieval 指标与 taxonomy
3. 再补 answer_text review
4. 最后补 latency benchmark
