# Source Lookup Reannotation Guideline v1

- 文档日期：2026-04-07
- 适用范围：`question_type = source_lookup`
- 本轮目标：把方名/条文出处类题从 replay 回填 gold 收紧为可人工说明的独立 gold

## 1. 什么叫独立 gold

source_lookup 的独立 gold 必须先从题面目标出发，而不是从当前系统 replay citations 出发。

本轮采用的独立 gold 标准：

1. 题面明确问“某方的条文是什么”时，先识别题面方名，例如“桂枝汤方”“麻黄汤方”。
2. 到 `data/processed/zjshl_dataset_v2/main_passages.json` 中核对含有该方名的方文起始段。
3. 再按原文相邻关系补足连续方文，例如组成延续、`上/右/以上若干味` 开头的制法或煎服法。
4. 可接受紧邻方后说明，但必须标为 `secondary`；它可以帮助核对方义或组成差异，不能替代方名段与组成段。
5. 若只能靠当前系统 citations 才能知道 gold 是什么，不得标为 `manual_independent`。

## 2. gold_record_ids / gold_passage_ids 写法

1. `gold_passage_ids` 写 canonical passage id，例如 `ZJSHL-CH-009-P-0022`。
2. `gold_record_ids` 对 source_lookup v1 优先写 `safe:main_passages:<passage_id>`。
3. 若某段只存在于 `annotations.json` 或 `passages.json` 的 commentary 层，本轮不把它升入 source_lookup 的主 gold；后续如要评估注解层引用，可单独开 meaning_explanation 或 citation-layering 修订。
4. 每条 source_lookup 至少应有一个明示方名的方文起始段。
5. 连续组成段、制法/煎服法段可进入 gold，作为同一方文块的完整出处。

## 3. 一方多段和连续方文

一方多段时按以下顺序判断：

1. 明示方名的起始段是核心 gold，例如 `麻黄汤方：...`。
2. 若下一段仍在列组成，例如仅列剩余药味，应纳入 `primary`。
3. 若后文出现 `上四味`、`上七味`、`右三味` 等制法/煎服法，并紧接该方文，应纳入 `primary`。
4. 若中间隔着方义解释，但后文仍是该方制法，应保留这个连续方文块；方义解释用 `secondary`，制法仍用 `primary`。
5. 不纳入下一方、下一证、加减变化或跨方比较段，除非题面明确要求这些内容。

## 4. 方后说明处理

方后说明不是 source_lookup 的主判分依据，但可以作为可接受补充：

1. 若方后说明紧邻该方文，并直接解释本方组成或方义，可保留在 `gold_evidence_spans`，`evidence_role` 标为 `secondary`。
2. 若方后说明只是进入下一证、下一方或泛泛病机说明，不纳入本题 gold。
3. 如果 evaluator 只命中 secondary 方后说明而完全没有命中方名段或连续方文，后续人工评估时应判为引用不充分。

## 5. 本轮不处理

1. 不处理 `comparison`、`general_overview`、`meaning_explanation`、`refusal`。
2. 不新增问题。
3. 不修改 retrieval、rerank、gating、answer assembler、API 或 frontend。
4. 不重写 evaluator v1。
