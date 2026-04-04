# Hybrid Answer Assembler Patch Note

## 本轮变更

- `run_answer_assembler.py` 已从旧的 minimal retrieval 切换为消费 `run_hybrid_retrieval.py` 的结果。
- answer payload 顶层字段合同保持不变，继续输出：
  - `query`
  - `answer_mode`
  - `answer_text`
  - `primary_evidence`
  - `secondary_evidence`
  - `review_materials`
  - `disclaimer`
  - `review_notice`
  - `refuse_reason`
  - `suggested_followup_questions`
  - `citations`
  - `display_sections`

## 保持不变的规则

- `annotation_links` 继续完全禁用。
- `chunks` 仍然只负责召回并回指，不直接进入 `primary_evidence`。
- `annotations` 仍然只进入 `secondary_evidence`。
- `passages` / `ambiguous_passages` 仍然只进入 `review_materials`。
- `strong / weak_with_review_notice / refuse` 三模式框架不变。
- “黄连汤方”的主证据精度补丁继续保持，不回归混入“葛根黄芩黄连汤方”相关主条。

## 本轮未做

- 没有改 answer payload 合同。
- 没有重做 dense retrieval / rerank。
- 没有改数据库 schema。
- 没有扩展到前端、API、多书或 LLM 生成。
