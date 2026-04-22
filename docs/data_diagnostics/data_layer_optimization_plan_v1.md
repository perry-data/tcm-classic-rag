# 数据层优化建议清单 v1

生成时间：2026-04-21

本清单只提出数据层优化建议，限定在表、字段、关系、视图、metadata、chunk 类型、对齐表、规范化词表和检索对象组织层面。不涉及 prompt、前端、API payload、answer_mode 定义。

## P0：必须优先做

### P0.1 `formula_canonical_registry`

建立持久方剂规范表，不再只从 `records_main_passages WHERE text LIKE '%方：%'` 动态推断。

建议字段：

- `formula_id`
- `canonical_name`
- `normalized_name`
- `primary_formula_passage_id`
- `chapter_id`
- `formula_span_start_passage_id`
- `formula_span_end_passage_id`
- `composition_passage_ids`
- `decoction_passage_ids`
- `usage_context_passage_ids`
- `source_confidence`

优先原因：当前疑似候选池中最常见信号是 `formula_cross_target_candidates`，说明方剂相关 query 需要更强的公式级对象边界。

### P0.2 `formula_alias_registry`

把“汤/汤方”“异写”“简称”“常见错写”从代码启发式升级为可审计表。

建议字段：

- `alias`
- `normalized_alias`
- `formula_id`
- `alias_type`
- `confidence`
- `source`
- `notes`

优先原因：普通学习者不会稳定输入书内标准方名，alias 不进入 runtime 会导致召回和 routing 不稳。

### P0.3 `retrieval_ready_formula_view`

建立面向检索的反规范化 view，把 formula registry、main passages、chunk backrefs、章节信息展开到同一候选对象。

建议包含：

- formula-level retrieval text
- formula_name_text
- composition_text
- usage_context_text
- neighbor passage ids
- allowed evidence level
- source passage ids

优先原因：可以减少同章相邻方、连续方文、方后说明混杂造成的 citation 不稳定。

### P0.4 `commentarial_alignment_registry`

把 commentarial resolved links 从 JSONL 固化为可查询 registry，但仍不进入 primary。

建议字段：

- `unit_id`
- `source_id`
- `commentator`
- `resolved_canonical_passage_id`
- `resolved_formula_id`
- `anchor_role`
- `anchor_type`
- `resolution_status`
- `confidence`
- `needs_manual_anchor_review`
- `needs_manual_content_review`

优先原因：当前讲稿层已有 831 条 link，但没有进入 SQLite 统一诊断面。下一轮要优化名家材料，必须先能按 canonical object 反查。

### P0.5 `unit_scope_type`

为 commentarial unit 增加范围类型。

建议枚举：

- `single_passage`
- `single_formula`
- `comparison`
- `broad_discussion`
- `incidental_mention`
- `study_method`

优先原因：这是防止“顺带提及段进入主要展示”的关键字段。不能靠 prompt 或展示层补救。

## P1：明显值得做

### P1.1 `learner_query_normalization_lexicon`

把普通学习者口语问法映射到 canonical term / formula / symptom / intent。

建议字段：

- `surface_form`
- `normalized_form`
- `target_type`
- `target_id`
- `intent_hint`
- `confidence`
- `examples`

覆盖方向：

- 方名简称
- 症状口语
- 证候术语
- 治法术语
- “干什么/治什么/有什么用/怎么理解/先抓什么”

### P1.2 `topic_tags` / `concept_tags`

为 canonical passage 和 commentarial unit 增加学习主题标签。

建议标签层：

- formula
- symptom
- pattern
- treatment_method
- pathogenesis
- composition
- decoction_method
- contraindication
- comparison
- study_method

优先原因：目前 `general_overview` 题型少，且 broad learner query 主要靠启发式分支。主题标签能让普通学习者问题更稳。

### P1.3 canonical neighbor windows

围绕 `passage_order_in_chapter` 建稳定邻接窗口，而不是运行时临时找上下文。

建议字段：

- `passage_id`
- `prev_passage_id`
- `next_passage_id`
- `same_formula_span_ids`
- `same_topic_window_ids`
- `window_confidence`

优先原因：meaning explanation、方剂连续段、citation 自然度都依赖上下文窗口。

### P1.4 `candidate_risk_profile`

把当前分散在 `risk_flag`、`display_allowed`、`ambiguous_registry_hit`、commentarial review flags 中的风险信息整理成统一风险画像。

建议字段：

- `candidate_id`
- `risk_level`
- `risk_reasons`
- `review_required`
- `allowed_slots`
- `demotion_reason`

优先原因：可让 suspected failure pool 的自动信号更精确，减少误报。

### P1.5 pairwise relation objects

为常见方剂对比建立 pairwise relation 数据对象。

建议字段：

- `relation_id`
- `left_formula_id`
- `right_formula_id`
- `shared_context_passage_ids`
- `difference_dimensions`
- `canonical_support_passage_ids`
- `commentarial_support_unit_ids`

优先原因：对比题不应只靠两个单方检索结果拼接，否则容易出现 broad formula sweep 或单方材料污染。

## P2：可选增强

### P2.1 retrieval candidate audit view

建立 `vw_retrieval_candidate_audit`，把 raw retrieval object、evidence slot eligibility、dense/sparse eligibility、risk profile、formula/topic tags 合并，便于每次调参前导出。

### P2.2 source-aware citation label fields

利用 `source_file/source_item_no/passage_order_in_chapter` 生成更稳定的 citation label。

注意：这是数据字段准备，不是前端改版。

### P2.3 commentarial teaching-point index

把 `teaching_points` 拆成可检索字段，专门服务“怎么学/先抓什么/如何理解”的学习型问题。

### P2.4 chunk subtype refinement

在 `main_text` 和 `formula_bundle` 之外增加更细 chunk type：

- `formula_name`
- `formula_composition`
- `formula_decoction`
- `symptom_pattern`
- `treatment_method`
- `commentary_quote`

前提：不能让 chunk 越级进入 primary，只能改善 recall 和 backref。

### P2.5 offline suspected-failure review table

把 `suspected_failure_pool_v1.json` 的人工复核结果回写成独立 artifact/table：

- `candidate_id`
- `human_label`
- `confirmed_issue_type`
- `root_cause_layer`
- `recommended_data_fix`
- `do_not_fix_reason`

用于下一轮闭环，不直接改变线上系统。

## 下一轮最小实现建议

若进入“数据层最小实现改造”，建议只做 P0.1、P0.2、P0.3 的最小闭环：

1. 从当前 `records_main_passages` 抽取 `formula_canonical_registry_v1.json`。
2. 基于现有 46 条 alias 和公式名自动变体生成 `formula_alias_registry_v1.json`。
3. 生成只读 `retrieval_ready_formula_view` 或 JSON artifact。
4. 用现有 40 条疑似候选池回放，不改 prompt/UI/API。

这样可以优先验证“串方候选、方剂 citation 不稳、方剂口语问法召回不稳”是否下降。
