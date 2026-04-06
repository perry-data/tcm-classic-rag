# Retrieval Precision Patch Note

## 目标

收紧 `run_minimal_retrieval.py` 中 `strong` 模式的主证据选择，避免相近方名仅因局部短语重叠而进入 `primary_evidence`。

## 本轮调整

- 为查询增加 `query_theme` 推断。当前重点覆盖方名类问题，如 `黄连汤方`、`桂枝汤`。
- 为候选增加 `topic_anchor` 和 `topic_consistency` 判断。
- 对标题锚点与查询方名完全一致的候选增加精度加分。
- 对仅属于扩展方名或局部短语命中的候选降低分数，并禁止其 A 级主条直接进入 `primary_evidence`。
- `chunks` 仍然只承担召回入口，真正进入 `primary_evidence` 的仍是回指后的 `records_main_passages`。
- `annotations` 仍然只进 `secondary_evidence`，`passages` / `ambiguous_passages` 仍然只进 `risk_materials`。

## 结果

- `黄连汤方的条文是什么？` 仍然返回 `strong`。
- 该样例的 `primary_evidence` 已从：
  - `ZJSHL-CH-009-P-0017`
  - `ZJSHL-CH-009-P-0019`
  - `ZJSHL-CH-010-P-0145`
  收紧为：
  - `ZJSHL-CH-010-P-0145`
  - `ZJSHL-CH-010-P-0146`
  - `ZJSHL-CH-010-P-0147`
- 原先误混入的“葛根黄芩黄连汤方”相关 A 级主条已降到 `secondary_evidence`，并打上 `topic_mismatch_demoted`。

## 未改动范围

- 未修改数据库结构
- 未启用 `annotation_links`
- 未引入向量检索
- 未实现回答生成
