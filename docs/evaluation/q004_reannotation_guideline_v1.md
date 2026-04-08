# q004 Reannotation Guideline v1

- 文档日期：2026-04-08
- 适用范围：仅 `question_id = eval_seed_q004`
- 题面：`少阴病应该怎么办？`
- 最终口径：少阴病的最小稳定治法分支整理

## 1. 旧问题在哪里

q004 在 independence audit v1 中被标为 `needs_reannotation`，原因不是少阴病章中没有可用条文，而是旧 gold provenance 混杂：

1. `source_refs` 指向 `artifacts/general_question_examples.json:shaoyin_management_strong`，不是正文独立核对来源。
2. gold 集合曾因当前正式系统实际 citations 扩展，容易把“当前系统常见 strong 响应可接受 citation 集”误写成“人工独立定义的总括口径”。
3. 旧 `gold_evidence_spans` 中部分 rationale 直接引用“当前正式系统稳定选入”，不适合作为正式评估口径说明。

因此 q004 需要单题专项重标，先定义题面范围，再决定 gold。

## 2. q004 题面范围

本轮将 q004 定义为：

> 少阴病的最小稳定治法分支整理。

它不是“少阴病章全部治法穷举”，也不是“当前系统 strong 回答中常出现的 citation 集”。答题应说明少阴病不能按单一治法处理，而要按少阴病章中稳定、直接、可核对的方证分支分情况整理。

## 3. 最小稳定分支集合

本轮 q004 的 stable primary gold 只取 `data/processed/zjshl_dataset_v2/main_passages.json` 中少阴病章内直接写明“少阴病……汤主之”或“当灸之……汤主之”的方证分支：

1. `ZJSHL-CH-014-P-0062`：始得之，反发热，脉沉，麻黄附子细辛汤主之。
2. `ZJSHL-CH-014-P-0072`：得之二三日以上，心中烦，不得卧，黄连阿胶汤主之。
3. `ZJSHL-CH-014-P-0078`：得之一二日，口中和，背恶寒，当灸之，附子汤主之。
4. `ZJSHL-CH-014-P-0093`：二三日至四五日，腹痛，小便不利，下利不止便脓血，桃花汤主之。
5. `ZJSHL-CH-014-P-0112`：咽中伤生疮，不能语言，声不出，苦酒汤主之。
6. `ZJSHL-CH-014-P-0162`：四逆及或咳、悸、小便不利、腹中痛、泄利下重，四逆散主之。

这些条文共同覆盖少阴病治法总括题的最小稳定代表分支：始得兼表、阴虚烦热、阳虚背恶寒、下利便脓血、咽喉证、四逆兼证。

## 4. 不再保留的依据

1. 不再把 `artifacts/general_question_examples.json:shaoyin_management_strong` 作为 q004 source ref。
2. 不再把当前系统 replay citations 作为 q004 gold 的定义理由。
3. 不把 `full:passages:*` 或 `full:ambiguous_passages:*` 作为 q004 gold record。
4. 公式条、预后/死证条、欲解时条、非少阴病主题条文不纳入 q004 v1 最小稳定主证据集合。

## 5. 状态判断

q004 可以从 `needs_reannotation` 收口为 `manual_independent`，理由是：

1. 题面口径已经从“系统可接受 citation 集”改为“少阴病最小稳定治法分支整理”。
2. 六条 gold 都来自 `main_passages.json` 中少阴病章的直接方证条文。
3. evidence 全部为 `primary`，符合 general_overview strong 题“多分支支撑、不得单条直答”的规则。
4. source refs 改为正文数据源，不再依赖系统样例或 replay。
