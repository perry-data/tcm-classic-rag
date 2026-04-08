# Goldset v2 Batch C Plan v1

## 目标

Batch C 在当前已通过 evaluator v1 的 `artifacts/evaluation/goldset_v2_working_126.json` 基础上新增最后 24 条全新样本，形成 `artifacts/evaluation/goldset_v2_working_150.json`。本轮只做新增样本，不修改旧 126 条，不回头修 Batch A / Batch B，不修改 retrieval、rerank、gating、answer assembler、API、frontend 或 evaluator v1。

Batch C 继续服务《伤寒论》单书研读支持系统的评估定位：证据溯源、题型分层、允许 strong / weak / refuse，不把系统扩展为临床诊疗、现代病名疗效判断或外部知识问答工具。

## 本轮配额

| question_type | working_126 | Batch C added | working_150 |
| --- | ---: | ---: | ---: |
| source_lookup | 35 | 5 | 40 |
| comparison | 25 | 5 | 30 |
| meaning_explanation | 24 | 6 | 30 |
| general_overview | 17 | 3 | 20 |
| refusal | 25 | 5 | 30 |
| **Total** | **126** | **24** | **150** |

新增 question_id 范围为 `eval_seed_q127` 到 `eval_seed_q150`，全部从一开始标为 `manual_independent`。非 refusal 样本的 gold source 只指向：

- `data/processed/zjshl_dataset_v2/main_passages.json`
- `data/processed/zjshl_dataset_v2/annotations.json`

refusal 样本 gold evidence 为空，source_refs 只记录结构化语料边界，不把 evaluator report、系统 replay 或旧示例答案作为 gold 来源。

## 设计策略

source_lookup 新增 5 条，继续选择方名稳定、正文锚点清楚的普通方文题：炙甘草汤、吴茱萸汤、黄连阿胶汤、桃花汤、白头翁汤。gold 覆盖方文起始、连续组成和紧邻煎服法；方后说明只作为 secondary。

comparison 新增 5 条，优先选择双实体边界清楚、题面直接命名的方文比较：大陷胸丸 / 大陷胸汤、黄连阿胶汤 / 桃花汤、猪肤汤 / 桔梗汤、通脉四逆汤 / 四逆汤、炙甘草汤 / 桂枝甘草汤。双方核心方文为 primary，直接主治或方后说明为 secondary。

meaning_explanation 新增 6 条，保持 3 strong / 3 weak 的平衡。strong 题使用正文中可直接解释题面概念的定义句；weak 题使用注解或语境作为 secondary，primary 保持为空。

| question_id | query | expected_mode |
| --- | --- | --- |
| `eval_seed_q137` | 脉有阴阳是什么意思？ | strong |
| `eval_seed_q138` | 脉有残贼是什么意思？ | strong |
| `eval_seed_q139` | 霍乱是什么意思？ | strong |
| `eval_seed_q140` | 灾怪是什么意思？ | weak_with_review_notice |
| `eval_seed_q141` | 八邪是什么意思？ | weak_with_review_notice |
| `eval_seed_q142` | 脏结无阳证是什么意思？ | weak_with_review_notice |

general_overview 新增 3 条，只补边界较稳的分支整理题：心下痞、身黄、便脓血。每题由多个 main_passages 分支共同支撑，不做单条直答，也不再故意造高风险宽题。

refusal 新增 5 条，覆盖真实越界场景：个人服方建议、现代剂量换算、现代病名疗效判断、跨书价值判断、个体化合方用药方案。题面保持自然，gold evidence/citations 为空。

## 完成状态

Batch C 完成后 working set 从 126 条增加到 150 条，题型分布达到 source_lookup 40、comparison 30、meaning_explanation 30、general_overview 20、refusal 30。当前阶段“扩到 150 左右”的目标完成。

本轮不扩到 200-250，不写论文正文，不回头修改 Batch A / Batch B，不改系统代码。
