# Comparison Reannotation Guideline v1

- 文档日期：2026-04-08
- 适用范围：`question_type = comparison`
- 本轮目标：把比较题中依赖系统样例或 evaluator replay 回填的 gold，收紧为可由题面两端对象和 `main_passages.json` 原文独立说明的 gold

## 1. 什么叫 comparison 的独立 gold

comparison 的独立 gold 必须从题面两端对象出发，而不是从当前系统 citations 出发。

本轮采用的独立 gold 标准：

1. 先拆出题面 A/B 两端对象，例如“A 方 vs B 方”或“A 条文语境 vs B 条文语境”。
2. 到 `data/processed/zjshl_dataset_v2/main_passages.json` 中核对双方核心方文或直接条文。
3. 若方文被拆为相邻段，连续组成、`上/右若干味` 制法或煎服法可并入同一方文块。
4. 方后说明或病证语境只有在能直接指向题面对象时才可进入 gold，并应标为 `secondary`。
5. 只能提示待核对、歧义或当前系统只能弱回答的语境，不得伪装成稳定 `primary`；可标为 `review` 并保留 weak 边界。
6. 若某段只能从当前 replay citations 反推出来，且题面与原文不能独立解释其必要性，不得保留为 `manual_independent` gold。

## 2. evidence_role 写法

1. `primary`：双方方名起始段、组成延续段、紧邻制法或煎服法。它们定义 A/B 方的可比较主体。
2. `secondary`：直接主治条文、紧邻方后说明、或原文中直接比较两方差异的语境段。
3. `review`：可帮助人工核对，但不应支撑 strong 主结论的歧义语境或弱边界材料。

## 3. gold_record_ids / gold_passage_ids 写法

1. `gold_passage_ids` 写 canonical passage id，例如 `ZJSHL-CH-009-P-0022`。
2. 本轮 comparison 优先使用 `safe:main_passages:<passage_id>`。
3. 不继续把 `full:passages:*` 或 `full:ambiguous_passages:*` 作为唯一 gold 来源；如果系统实际 replay 命中 full/ambiguous 层，只能通过 canonical passage id 与人工核对段对应。
4. 每条 strong comparison 至少应覆盖 A/B 两端的核心方文。
5. weak comparison 可把 A/B 方文放入 `secondary`，但应在 `answer_assertions` 与日志中保留弱回答边界。

## 4. 本轮处理边界

1. 只处理 `question_type = comparison`。
2. 不处理 `source_lookup`、`general_overview`、`meaning_explanation`、`refusal`。
3. 不新增问题，不改 retrieval / rerank / gating / answer assembler，不改 API / frontend，不重写 evaluator v1。
4. 如果发现 replay 语境误入，例如把其他方、变方或非题面对象作为比较语境，应移出 gold，除非原文能明确说明它是题面比较所需的核对材料。
