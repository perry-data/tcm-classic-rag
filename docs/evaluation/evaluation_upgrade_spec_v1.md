# 评估优化实现规格 v1

- 文档版本：v1
- 文档日期：2026-04-09
- 文档定位：把“第一轮唯一优化目标：评估优化”冻结成可直接进入实现轮次的正式规格
- 输入依据：
  - `docs/project_optimization/optimization_matrix_v1.md`
  - `docs/project_optimization/optimization_priority_decision_v1.md`
  - `docs/evaluation/evaluation_spec_v1.md`
  - `docs/evaluation/evaluation_plan_v1.md`
  - `scripts/run_evaluator_v1.py`
  - `config/evaluation/goldset_schema_v1.json`
  - `artifacts/evaluation/goldset_v2_working_150.json`
  - `artifacts/evaluation/modelstudio_qwen_plus_regression_report.md`
  - `docs/patch_notes/modelstudio_qwen_plus_live_validation_patch_note.md`
  - 当前 regression / smoke / patch notes

## 1. 目标与非目标

### 1.1 本轮目标

本轮只做一件事：

> 把当前“评估基线 v1”升级为“可支撑下一轮 retrieval / prompt 优化的评估优化 v1”。

这不是要把评估体系做成完整平台，而是补齐当前最值得先补、且最直接支持后续优化的四项内容：

1. retrieval 级指标
2. answer_text 质量评价规约
3. latency mini-benchmark
4. failure taxonomy

### 1.2 明确非目标

以下事项不属于本轮规格：

1. 不直接做 retrieval 调优。
2. 不直接做 prompt 调优。
3. 不改 payload contract。
4. 不改前端。
5. 不扩到 200–250 条 goldset。
6. 不做用户满意度问卷。
7. 不做双人标注一致性研究。
8. 不做多书评估。
9. 不做并发压测、生产级性能测试或线上日志评估。

## 2. 当前基线

当前 v1 评估底座已经具备以下条件：

1. `evaluation_spec_v1.md` 已冻结评估对象、题型、维度与系统边界。
2. `evaluation_plan_v1.md` 已冻结评估实施原则与扩展路径。
3. `run_evaluator_v1.py` 已能 replay goldset，并输出 JSON / Markdown 两种报告。
4. `goldset_v2_working_150.json` 已形成 150 条单书《伤寒论》评估集。
5. 当前 150 条回放结果稳定：
   - `total_questions = 150`
   - `mode_match = 150/150`
   - `citation_check_required_basic_pass = 120/120`
   - `failure_count = 0`
6. `qwen-plus` live validation 已成功，但当前评估还没有正式覆盖 answer_text 质量收益与 llm-enabled latency。

当前 v1 的主要不足不是“没有评估”，而是：

1. 更擅长判断系统有没有回归；
2. 不够擅长判断下一轮该先优化哪一层、优化后是否真的变好。

## 3. 第一轮评估优化的最小范围

### 3.1 结论先行

第一轮评估优化明确纳入以下四项，而且都只做**最小可实施版**：

1. retrieval 级指标：纳入
2. answer_text 质量评价规约：纳入
3. latency mini-benchmark：纳入
4. failure taxonomy：纳入

这里的“纳入”不等于把每项都做成大工程，而是只做到：

1. 能支撑下一轮 retrieval 优化；
2. 能支撑下一轮 prompt / answer_text 优化；
3. 能直接进入论文第 4 章；
4. 不破坏当前正式系统边界。

### 3.2 范围判断矩阵

| 项目 | 是否纳入 | 本轮纳入的最小形态 | 为什么纳入 | 本轮暂不纳入的扩展形态 | 实现成本 | 对论文收益 | 对后续 retrieval / prompt 优化的支撑作用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval 级指标 | 纳入 | 在 150 条 goldset 上补 fused/rerank `Hit@K`、题型分组命中率、rerank 前后 rank delta | 当前最缺 retrieval 级诊断尺子；没有它就无法严谨推进检索优化 | 不做 MRR/NDCG、不做复杂分支级 ablation、不做多书检索对比 | 中 | 高 | 直接支撑后续 retrieval 参数调整与误差定位 |
| answer_text 质量评价规约 | 纳入 | 对非 refusal 的代表性样本集做 baseline vs `qwen-plus` 的人工 rubric 评分 | live-call 已成功，但还没有正式办法证明 answer_text 到底有没有更好 | 不做大规模全量 150 条人工评分、不做双人一致性研究、不做用户满意度问卷 | 中 | 高 | 直接支撑后续 prompt/answer_text 优化与 validator 调整 |
| latency mini-benchmark | 纳入 | 做单机、单用户、固定 query set 的 API benchmark，输出均值 / p50 / p95 | 当前性能方向没有基线；不先测量，就无法判断后续性能是否值得调 | 不做并发压测、不做生产环境压测、不做复杂 profiling 平台 | 低中 | 中高 | 支撑后续是否值得做性能优化，也能比较 baseline 与 llm-enabled 成本 |
| failure taxonomy | 纳入 | 建立轻量可机读分类，覆盖 retrieval / citation / mode / evidence / answer_text / latency 主要失败类型 | 目前只有 pass/fail，不够支撑后续定向优化与论文失败分析 | 不做复杂根因树推断、不做全自动因果诊断 | 低中 | 很高 | 为 retrieval 与 prompt 优化提供共同的失败语言与统计口径 |

## 4. 四项纳入内容的正式规格

## 4.1 Retrieval 级指标

### 4.1.1 本轮为什么纳入

原因有四点：

1. 当前 `evaluator_v1` 更偏最终 payload 层，不能细看 retrieval 与 rerank 到底表现如何。
2. 下一轮若推进 retrieval 优化，没有检索级指标就无法证明优化是否有效。
3. `goldset_schema_v1.json` 已经具备 `retrieval_assertions`、`gold_passage_ids` 等字段，可以复用，不必重建数据底座。
4. retrieval 指标属于当前评估体系最缺、却最直接服务后续优化的一层。

### 4.1.2 本轮只做到哪里

本轮 retrieval 级指标只做到以下最小集合：

1. `fused_hit_at_k`
   - 至少统计 `K = 1, 3, 5, 10`
   - 观察 gold passage 是否进入融合候选前 K
2. `rerank_hit_at_k`
   - 至少统计 `K = 1, 3, 5, 10`
   - 观察 gold passage 是否进入 rerank 后前 K
3. `best_gold_rank_before_rerank`
4. `best_gold_rank_after_rerank`
5. `rerank_rank_delta`
   - 定义为 rerank 后最优 gold rank 相对融合阶段的变化
6. 按题型汇总
   - source_lookup
   - meaning_explanation
   - general_overview
   - comparison
   - refusal

### 4.1.3 本轮暂不纳入什么

本轮明确不纳入：

1. MRR、NDCG、MAP 等更复杂排序指标
2. sparse / dense / fused / rerank 的全量大表对比平台
3. 多书、跨书或外部语料检索指标
4. 检索参数自动搜索

原因：

1. 当前目标是先补“足够用的诊断尺子”，不是建完整 IR 实验平台。
2. 更复杂指标对下一轮单书 MVP 优化的边际收益不足。

## 4.2 Answer_text 质量评价规约

### 4.2.1 本轮为什么纳入

原因有四点：

1. `qwen-plus` live validation 已成功，说明 answer_text 质量已经进入正式系统边界。
2. 当前还没有正式口径去判断：LLM 版 answer_text 相比 baseline 到底是更清楚了，还是只是更长了。
3. 如果后续要做 prompt / answer_text 优化，必须先有评价规约。
4. 这项收益对论文与答辩都很直接，因为老师最先感知的是最终回答文本。

### 4.2.2 本轮只做到哪里

本轮只做**代表性人工 rubric**，不做大规模人工评分。

固定要求如下：

1. review set 范围：
   - 只覆盖 non-refuse 题
   - 总量建议 `20` 条
   - 推荐分布：
     - source_lookup：5
     - meaning_explanation：5
     - general_overview：5
     - comparison：5
2. 每条样本都做 baseline vs `qwen-plus` 对照
3. rubric 维度最小固定为四项：
   - `clarity`：表达是否清楚
   - `structure`：结构是否有助于研读
   - `evidence_faithfulness`：是否忠于既有证据边界
   - `mode_boundary_preservation`：是否保持 strong / weak 的边界语气
4. 评分建议：
   - 每维 `0 / 1 / 2`
   - 0 = 明显不满足
   - 1 = 基本满足
   - 2 = 明显更好
5. 必须保留 reviewer note，避免只剩数字没有解释

### 4.2.3 本轮暂不纳入什么

本轮明确不纳入：

1. 全 150 条人工评分
2. 双人标注一致性实验
3. 用户满意度问卷
4. 多模型大规模盲测

原因：

1. 当前更缺的是“先有可执行尺子”，不是“先把人工工作量做满”。
2. 这些扩展更适合作为后续增强项或论文展望。

## 4.3 Latency Mini-Benchmark

### 4.3.1 本轮为什么纳入

原因有三点：

1. 开题报告里有“响应速度 / 性能测试”承诺，当前仍缺正式 artifact。
2. 没有 latency baseline，就无法判断后续是否需要真的做性能优化。
3. latency 测量成本相对低，且能直接补论文与答辩的证据短板。

### 4.3.2 本轮只做到哪里

本轮只做**单机、单用户、本地 API 路径**的 mini-benchmark。

固定要求如下：

1. benchmark query set：
   - 总量建议 `10` 条
   - 每类题型 `2` 条
   - 继续保持单书《伤寒论》边界
2. 调用路径：
   - 固定走 `POST /api/v1/answers`
   - 不测前端
3. 运行模式：
   - baseline mode：必须
   - llm-enabled mode：应做；若 live 配置不可用，则记录 blocker 并降级为 partially done
4. 每条 query 重复次数：
   - 固定 `5` 次
   - 总调用量为 `10 * 5 = 50` 次 / mode
5. 输出指标最小集合：
   - `count`
   - `mean_ms`
   - `p50_ms`
   - `p95_ms`
   - `min_ms`
   - `max_ms`
6. 必须同时输出：
   - overall summary
   - by question_type summary
   - by query summary

### 4.3.3 本轮暂不纳入什么

本轮明确不纳入：

1. 并发压测
2. 生产环境 benchmark
3. 复杂 tracing / flamegraph / profiler 平台
4. 前端交互层性能测试

原因：

1. 当前项目定位仍是本地演示型 MVP。
2. 本轮只需要补出最小可复核证据，不需要扩成完整性能工程。

## 4.4 Failure Taxonomy

### 4.4.1 本轮为什么纳入

原因有四点：

1. 当前 `evaluator_v1` 只有 `failed_checks`，还不够支撑下一轮定向优化。
2. 后续 retrieval、prompt、latency 三类优化都需要共同的失败语言。
3. 论文第 4 章与答辩都会需要“失败样本如何分类”的说明。
4. taxonomy 成本低，但收益高。

### 4.4.2 本轮只做到哪里

本轮 taxonomy 只做到**轻量二级分类**。

一级分类建议固定为：

1. `retrieval_failure`
2. `citation_failure`
3. `answer_mode_failure`
4. `evidence_layering_failure`
5. `unsupported_assertion_failure`
6. `answer_text_quality_issue`
7. `llm_runtime_issue`
8. `latency_issue`

二级子类建议最小固定为：

1. `gold_miss_in_fused_topk`
2. `gold_miss_after_rerank`
3. `citation_not_in_gold`
4. `expected_weak_but_actual_strong`
5. `expected_refuse_but_not_refuse`
6. `primary_should_be_empty`
7. `strong_without_gold_evidence`
8. `clarity_low`
9. `structure_low`
10. `evidence_faithfulness_low`
11. `mode_boundary_broken`
12. `llm_fallback_triggered`
13. `llm_validator_reject`
14. `latency_over_threshold`

每条失败记录最少包含：

1. `question_id`
2. `question_type`
3. `category`
4. `subcategory`
5. `severity`
6. `notes`

### 4.4.3 本轮暂不纳入什么

本轮明确不纳入：

1. 自动根因推断树
2. 复杂 blame attribution
3. 多级因果链自动生成

原因：

1. 当前最需要的是“能归类”，不是“自动解释一切”。

## 5. 本轮明确不纳入的评估项

为防止范围继续膨胀，本轮明确不纳入以下内容：

1. 200–250 goldset 扩容
2. 用户满意度评估
3. 双人标注一致性
4. 多书评估
5. prompt A/B 实验平台
6. retrieval 参数搜索平台
7. 前端可用性测试
8. 并发 / 生产级性能评估

这些事项不是不重要，而是：

1. 对当前第一轮评估优化不是最关键；
2. 会明显拉高实现成本；
3. 不利于“只服务评估优化”这一条主线。

## 6. 正式产物清单

## 6.1 本轮规格冻结后，下一实现轮次必须新增的文件

### 脚本

1. `scripts/run_evaluator_v2.py`
   - 基于 `run_evaluator_v1.py` 扩展
   - 负责 full 150 replay、retrieval 指标、failure taxonomy 汇总
2. `scripts/run_latency_mini_benchmark_v1.py`
   - 负责固定 query set 的 API benchmark

### 配置

1. `config/evaluation/evaluator_v2_metric_schema_draft.json`
   - 本轮先冻结 draft
   - 下一轮实现时对齐 JSON 输出结构
2. `config/evaluation/answer_text_review_set_v1.json`
   - 固定 20 条 non-refuse 代表样本
3. `config/evaluation/latency_benchmark_query_set_v1.json`
   - 固定 10 条 benchmark query

### 文档

1. `docs/evaluation/answer_text_quality_rubric_v1.md`
2. `docs/evaluation/evaluation_failure_taxonomy_v1.md`

### 产物

1. `artifacts/evaluation/evaluator_v2_report.json`
2. `artifacts/evaluation/evaluator_v2_report.md`
3. `artifacts/evaluation/answer_text_quality_review_v1.json`
4. `artifacts/evaluation/answer_text_quality_review_v1.md`
5. `artifacts/evaluation/latency_mini_benchmark_v1.json`
6. `artifacts/evaluation/latency_mini_benchmark_v1.md`

## 6.2 本轮明确复用的旧文件

1. `scripts/run_evaluator_v1.py`
2. `config/evaluation/goldset_schema_v1.json`
3. `artifacts/evaluation/goldset_v2_working_150.json`
4. `artifacts/evaluation/modelstudio_qwen_plus_regression_report.md`
5. `docs/patch_notes/modelstudio_qwen_plus_live_validation_patch_note.md`
6. 现有 smoke / regression / patch notes

## 6.3 本轮明确不要求修改的旧文件

1. 不要求修改 `goldset_schema_v1.json`
2. 不要求修改 150 条 goldset 内容
3. 不要求修改 payload contract
4. 不要求修改 frontend

## 7. 验收口径

## 7.1 Done

若以下条件同时满足，则视为 done：

1. `run_evaluator_v2.py` 可在 150 条 goldset 上完整运行。
2. `evaluator_v2_report.json/.md` 实际生成，并包含：
   - retrieval `Hit@K`
   - rerank 前后 rank delta
   - 题型分组统计
   - failure taxonomy 统计
3. `answer_text_quality_rubric_v1.md` 已形成。
4. `answer_text_quality_review_v1.json/.md` 已完成，且覆盖固定 review set 的 baseline vs `qwen-plus` 对照评分。
5. `run_latency_mini_benchmark_v1.py` 可运行，且 baseline mode artifact 已生成。
6. 若 live config 可用，则 llm-enabled latency artifact 也已生成。
7. 全过程不改 retrieval / prompt / frontend / payload contract。

## 7.2 Partially Done

若满足以下情况之一，则视为 partially done：

1. `evaluator_v2` 与 retrieval 指标已完成，但 answer_text review 还只停留在 rubric 文档，尚未出正式评分 artifact。
2. baseline latency artifact 已完成，但 llm-enabled latency 因本地 live 配置不可用而未完成，且 blocker 已正式记录。
3. failure taxonomy 文档已形成，但 runner 还未把 taxonomy 真正写进 report。

换句话说，partially done 的特征是：

1. 尺子已经开始变细；
2. 但还不能完整支撑下一轮 retrieval 与 prompt 两条主线同时推进。

## 7.3 Not Done

若出现以下任一情况，则视为 not done：

1. 只有规格文档，没有可运行脚本和可复核 artifact。
2. retrieval 指标仍停留在 v1 的 citation/mode 粒度。
3. answer_text 仍无正式 rubric 或正式 review artifact。
4. latency 没有任何结构化 benchmark 结果。
5. failure taxonomy 仍不存在。

## 8. 实现顺序

本轮实现顺序固定为：

1. **先做 evaluator_v2 主报告骨架**
   - 扩展 `run_evaluator_v1.py`
   - 先让 retrieval 指标和 failure taxonomy 进入 full 150 报告
2. **再做 answer_text 质量规约与 review set**
   - 先冻结 rubric 和样本集
   - 再做 baseline vs `qwen-plus` 对照评分
3. **再做 latency mini-benchmark**
   - 走 API 路径
   - 输出 baseline 与 llm-enabled 的最小对比
4. **最后做汇总收束与验收**
   - 对齐 schema draft
   - 检查 artifact 是否齐全
   - 形成可直接引用到论文第 4 章的结果包

这个顺序不能打乱，原因是：

1. retrieval 指标和 taxonomy 是后续一切评估升级的主骨架。
2. answer_text review 需要依托稳定的 question set 与报告语义。
3. latency benchmark 最适合在前两项定住后独立补证据。

## 9. 规格结论

第一轮评估优化 v1 的结论只有一条：

> 本轮评估优化必须同时纳入 retrieval 级指标、answer_text 质量评价规约、latency mini-benchmark 和 failure taxonomy，但每一项都只做最小可实施版，不扩成大而全平台。

这样做的结果是：

1. 能直接支撑下一轮 retrieval 优化；
2. 能直接支撑下一轮 prompt / answer_text 优化；
3. 能补论文第 4 章当前最缺的量化与失败分析证据；
4. 不破坏当前稳定系统边界。
