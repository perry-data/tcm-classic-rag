# Goldset v2 Batch B Plan v1

## 目标

Batch B 在当前已通过 evaluator v1 的 `artifacts/evaluation/goldset_v2_working_102.json` 基础上新增 24 条全新样本，形成 `artifacts/evaluation/goldset_v2_working_126.json`。本轮只做新增样本，不修改旧 102 条，不回头修 Batch A，不修改 retrieval、rerank、gating、answer assembler、API、frontend 或 evaluator v1。

Batch B 继续服务《伤寒论》单书研读支持系统的评估定位：证据溯源、题型分层、允许 strong / weak / refuse，不把系统扩展为临床诊疗或外部知识问答工具。

## 本轮配额

| question_type | working_102 | Batch B added | working_126 | remaining_to_150 |
| --- | ---: | ---: | ---: | ---: |
| source_lookup | 30 | 5 | 35 | 5 |
| comparison | 20 | 5 | 25 | 5 |
| meaning_explanation | 18 | 6 | 24 | 6 |
| general_overview | 14 | 3 | 17 | 3 |
| refusal | 20 | 5 | 25 | 5 |
| **Total** | **102** | **24** | **126** | **24** |

新增 question_id 范围为 `eval_seed_q103` 到 `eval_seed_q126`，全部从一开始标为 `manual_independent`。非 refusal 样本的 gold source 只指向：

- `data/processed/zjshl_dataset_v2/main_passages.json`
- `data/processed/zjshl_dataset_v2/annotations.json`

refusal 样本 gold evidence 为空，source_refs 只记录结构化语料边界，不把 evaluator report、系统 replay 或旧示例答案作为 gold 来源。

## 设计策略

source_lookup 新增 5 条，优先选择系统中已有较稳定 formula anchor 的普通方文题，避免引入一批需要额外大规模 alias 清洗的高风险标题。本轮覆盖茯苓甘草汤、芍药甘草附子汤、黄芩汤、桂枝附子汤、真武汤等方文。

comparison 新增 5 条，优先选择双实体边界清楚、方名稳定、双方方文和语境可从 main_passages 独立核对的题。题面对双方对象直接命名，不故意加入校注噪声极重或切分不稳的标题。

meaning_explanation 新增 6 条，保持 strong / weak 结构平衡。strong 题使用正文定义句式，例如 `名曰`、`何谓`；weak 题使用注解解释或正文语境作为 secondary，不设置 primary evidence。

general_overview 新增 3 条，只选边界相对稳定的分支整理主题：结胸、太阳中风、咽痛。每题由多个 main_passages 分支共同支撑，不做单条直答，不复刻 q004 级别的高风险广义主题。

refusal 新增 5 条，继续覆盖真实越界场景：个人诊疗、体重/剂量换算、现代病名疗效判断、跨书价值判断、个体化七天用药方案。题面尽量自然，gold evidence 保持为空。

## 后续剩余数量

Batch B 完成后 working set 从 102 条增加到 126 条。到 150 条目标还剩 24 条，建议 Batch C 继续按相同比例补齐：

- source_lookup: +5
- comparison: +5
- meaning_explanation: +6
- general_overview: +3
- refusal: +5

本轮不提前实现 Batch C，不扩到 200-250，不写论文正文。
