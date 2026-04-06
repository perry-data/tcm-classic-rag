# Evaluation Baseline v1 Patch Note

## 1. 本轮新增了什么

本轮新增的是“评估基线 v1”，不是功能补丁。

新增内容包括：

1. `docs/evaluation/evaluation_spec_v1.md`
   - 定义评估目标、题型、维度和 v1 边界。
2. `docs/evaluation/evaluation_plan_v1.md`
   - 定义本轮为何先做 seed goldset，以及如何扩展到 200–250 条。
3. `docs/evaluation/annotation_guideline_v1.md`
   - 定义人工标注规则、标准依据写法和引用判定标准。
4. `config/evaluation/goldset_schema_v1.json`
   - 定义 goldset 的结构化字段，支持 retrieval 与 answer 两类评估。
5. `artifacts/evaluation/goldset_v1_seed.json`
   - 建立首批 seed questions，覆盖条文、解释、泛问、比较和拒答。
6. `artifacts/evaluation/evaluation_seed_smoke_checks.md`
   - 记录当前 seed 的最小验证结果、覆盖情况和可支撑的后续评估。

## 2. 为什么这轮先做评估基线

原因很直接：

1. 开题报告已经明确承诺“功能测试 + 自建金标准测试集 + 人工核对引用”。
2. 当前项目虽然主链已跑通，但尚未建立可正式写入论文第 4 章的评估底座。
3. 如果继续加功能而不先建立评估口径，后续很难统一判断“系统到底有没有变好”。

因此，本轮优先级不是继续扩功能，而是先把“怎么评估系统”正式立起来。

## 3. 为什么这轮不接 Prompt / LLM

本轮明确不接 Prompt / LLM，原因有三点：

1. 当前正式系统边界已冻结为 evidence-driven answer assembler，而不是外接真实 LLM。
2. 在 goldset、标注规则和引用核对标准未建立前，先接 LLM 只会把评估问题复杂化。
3. 当前最缺的是统一评估底座，不是新的生成能力。

所以，本轮保持：

1. 不改 API。
2. 不改 answer payload contract。
3. 不改 retrieval 主链。
4. 不补新业务功能。

## 4. 为什么先做 seed goldset，而不是直接凑满 200–250 条

本轮先做 seed goldset，是因为当前更需要先冻结：

1. schema；
2. 标注规则；
3. 题型口径；
4. 引用正确/错引/无证据断言的判定方式。

如果这些规则尚未稳定就直接硬扩到 200–250 条，后续会出现大面积返工。

seed goldset 的作用是：

1. 先建立正式样板；
2. 先验证当前系统可消费；
3. 先让论文第 4 章有正式评估入口；
4. 再为后续扩容提供稳定模板。

## 5. 当前仍未完成什么

本轮完成后，仍未完成的内容包括：

1. 200–250 条完整 goldset。
2. 独立 evaluator runner 与自动化指标统计。
3. 双人标注一致性抽查。
4. 真实 LLM / Prompt 栈接入后的专项评估。
5. 多书扩展下的跨书评估口径。

## 6. 本轮归类原则

本轮没有把新文件散落在根目录，而是按用途归档：

1. 评估文档放入 `docs/evaluation/`
2. patch note 放入 `docs/patch_notes/`
3. schema 放入 `config/evaluation/`
4. seed 数据与 smoke checks 放入 `artifacts/evaluation/`

这与当前项目已有的 `docs / config / artifacts` 分工保持一致，也便于后续扩写和审查。
