# Goldset Expansion to 150 Plan v1

## 目标

本计划把当前 72 条已 formalized 的 `goldset_v1_seed.json` 扩容到约 150 条。扩容继续服务《伤寒论》单书研读支持系统的评估定位：证据溯源、题型分层、允许 weak / refuse，不以真实临床处方或外部知识覆盖为目标。

## 总体配比

最终目标配比为 150 条：

| question_type | target | current_v1_72 | Batch A added | working_102 | remaining_to_150 |
| --- | ---: | ---: | ---: | ---: | ---: |
| source_lookup | 40 | 20 | 10 | 30 | 10 |
| comparison | 30 | 12 | 8 | 20 | 10 |
| meaning_explanation | 30 | 14 | 4 | 18 | 12 |
| general_overview | 20 | 12 | 2 | 14 | 6 |
| refusal | 30 | 14 | 6 | 20 | 10 |
| **Total** | **150** | **72** | **30** | **102** | **48** |

## Batch A 范围

本轮只做 Batch A 的 30 条新增样本，question_id 为 `eval_seed_q073` 到 `eval_seed_q102`。旧 72 条冻结，不修改任何既有 question_id、gold、source_refs 或断言。v1 基线文件仍保留在 `artifacts/evaluation/goldset_v1_seed.json`，本轮并行产出 `artifacts/evaluation/goldset_v2_working_102.json`。

只做 30 条的原因：

1. 先把 72 -> 150 的扩容拆成可审查批次，降低一次性引入题型偏差和边界不稳的风险。
2. Batch A 覆盖五类题型，但避免同时做 Batch B / C，以便先用 evaluator v1 观察 102 条 working set 的运行表现。
3. 本轮不改 retrieval、rerank、gating、answer assembler、API、frontend 或 evaluator v1，新增样本质量可以单独归因。

## Batch A 设计策略

Batch A 严格新增 30 条：source_lookup +10、comparison +8、meaning_explanation +4、general_overview +2、refusal +6。全部新增样本从一开始标为 `manual_independent`，gold 来源只指向 `data/processed/zjshl_dataset_v2/main_passages.json` 和 `data/processed/zjshl_dataset_v2/annotations.json`。

source_lookup 侧重新方文、连续组成和煎服法；comparison 先拆 A/B 对象，再核对双方方文和直接语境；meaning_explanation 使用注解直接解释和正文语境，但保持 weak 边界；general_overview 只新增少阳病核心边界和伤寒瘥后处理分支两个相对稳定主题；refusal 增加诊疗建议、剂量/处方推荐、现代医学判断和跨书外部知识强问等真实越界场景。

## 后续剩余数量

从 working 102 到目标 150 还需新增 48 条：source_lookup +10、comparison +10、meaning_explanation +12、general_overview +6、refusal +10。后续可拆成 Batch B / Batch C，但本轮不提前实现。
