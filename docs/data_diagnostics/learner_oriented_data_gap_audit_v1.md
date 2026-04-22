# 面向普通学习者的数据层缺口审计 v1

生成时间：2026-04-21

目标用户是中医爱好者和普通学习者。审计重点不是学术整理是否完整，而是当前数据底座能否承接“口语问法、方名简称、症状术语、学习视角、名家讲稿视角”的真实提问。

## 1. 方剂名规范化

已有：

- runtime 会从 `records_main_passages WHERE text LIKE '%方：%'` 动态抽取方剂 catalog。
- assembler 里有少量方名归一逻辑，例如“厚朴/浓朴”“杏仁/杏子”，以及“汤/汤方”后缀处理。
- `aliases.json` 有 46 条基础 alias，其中包含桂枝汤、麻黄汤、小柴胡汤等少量方名。

缺失：

- 没有独立持久的 `formula_canonical_registry` 表。
- 没有记录 canonical formula -> 方名段、组成段、煎服法段、方后说明段的结构化关系。
- 没有把方剂别名、异写、简称、去“方”后缀等统一做成 runtime 可查询表。

最可能导致：

- 方剂定位题候选里混入相邻方或同章方。
- 方剂作用题只能依赖当前命中的片段，没有稳定区分“方名段/组成段/主治语境/煎服法”。
- citation 有时看起来跳跃，因为连续方文没有被数据层显式标成一个 formula span。

## 2. 方剂别名 / 异写 / 简称映射

已有：

- `data/processed/zjshl_dataset_v2/aliases.json`，46 条。
- 代码层少量 hard-coded 归一。

缺失：

- `aliases.json` 没有进入 `vw_retrieval_records_unified` 或 query rewrite/normalization runtime。
- 未覆盖常见普通学习者问法，例如“桂枝汤”和“桂枝汤方”的统一、错别字、繁简、口语简称。
- 没有 alias 的 confidence、source、scope、是否适用于 formula/symptom/concept 的字段。

最可能导致：

- exact lexical hit 很强但候选不稳。
- 简称问法弱召回或被误判为 generic。
- 对比题中两个方名解析不稳定，进一步影响 commentarial route。

## 3. 症状 / 证候 / 治法术语映射

已有：

- `aliases.json` 包含少量症状现代释义，如“恶寒/怕冷”“汗出/出汗”等。
- retrieval 的 `build_query_terms` 会做字符级/短 ngram 匹配。

缺失：

- 没有 `symptom_alias_registry`、`pattern_term_registry`、`treatment_method_registry`。
- 没有把“怕冷、发冷、恶寒”“拉肚子、下利”“胸口堵、心下痞”等普通问法系统性归并。
- 没有术语层级，如 symptom -> pattern -> treatment method -> related formula。

最可能导致：

- 口语症状题空召回或落到风险材料。
- 术语解释题过度保守，因为 secondary/review 命中多，primary 缺少概念锚。
- answer citation 不自然，只能引用当前命中长段，而不是稳定术语定义/上下文窗口。

## 4. 口语问法到书面术语的归并

已有：

- `backend/retrieval/minimal.py` 有 `QUESTION_NOISE_PHRASES`，可剥掉“请问/书中/是什么意思”等噪声。
- assembler 有多个 query detector：comparison、formula composition、formula effect、definition outline、general question、policy refusal。

缺失：

- 这些归并大多是代码规则，不是可审计的数据表。
- 没有记录“普通学习者口语表达 -> canonical term / query intent / query family”的映射来源。
- 没有可导出的 normalization trace，例如原始 query 命中了哪个 alias、哪个 intent、哪个 canonical object。

最可能导致：

- “这个方干什么的”“这个证怎么理解”“初学者先抓什么”这类问题依赖 detector 命中，边界不可系统维护。
- 新增口语问法需要改代码而不是补词表。

## 5. 条文主题标签

已有：

- `chapter_id/chapter_name/chapter_type`
- `text_role/role_confidence`
- 部分 commentarial 单元有 `teaching_points`、`commentary_functions`

缺失：

- canonical passage 没有 `topic_tags` / `concept_tags` / `formula_tags` / `symptom_tags`。
- 没有“太阳病提纲、方剂组成、主治语境、煎服法、禁忌、病机解释、比较关系”等学习主题标签。
- `text_role` 粒度还不足以支持普通学习者的主题检索。

最可能导致：

- broad/general 问题只能靠多次检索和启发式分支组织。
- “学习路径/先抓什么/重点是什么”容易混入泛论、索引、讲稿长段。
- 评测集中 `general_overview` 数量最少，数据层也缺少支撑这类问题的主题结构。

## 6. 名家讲稿单元到 canonical 对象的结构化对齐

已有：

- commentarial units 711 条。
- resolved anchor links 831 条。
- anchor_type：exact 549、theme 97、multi 59、excerpt 6。
- 每个单元已有 `primary_anchor_candidates`、`supporting_anchor_candidates`、`commentary_functions`、eligibility flags。
- 全部 `never_use_in_primary=True`，符合 current evidence boundary。

缺失：

- 对齐关系没有进入 SQLite runtime schema。
- 没有按 canonical passage/formula/topic 建稳定反向索引。
- `theme_only_no_passage_resolution=97`，说明相当一部分讲稿单元没有具体 canonical passage anchor。
- `needs_manual_anchor_review=60`、`needs_manual_content_review=6`，仍有复核队列。

最可能导致：

- commentarial 辅助内容有时“能显示但不够贴题”。
- pairwise formula comparison 可能回退到泛论/assistive material。
- 名家材料与 canonical 主证据在展示上并列出现，但读者难以判断它是专讲、比较、泛论还是顺带提及。

## 7. 讲稿单元范围类型缺失

已有：

- `commentary_functions`
- `eligible_for_default_assistive_retrieval`
- `eligible_for_named_view`
- `eligible_for_comparison_retrieval`
- `eligible_for_meta_learning_view`
- `theme_display_tier`

缺失：

- 没有明确 `unit_scope_type`：
  - `single_formula`
  - `single_passage`
  - `comparison`
  - `broad_discussion`
  - `incidental_mention`
  - `study_method`
- 没有 `main_focus_terms` 与 `incidental_terms` 的分离字段。
- 没有“这个单元是否专讲目标方/条文”的 confidence。

最可能导致：

- 顺带提及段进入主要展示。
- 两方对比题被单方讲解或泛论段污染。
- 普通学习者看到“名家视角”时误以为其直接回答了当前问题。

## 8. 数据缺口优先级

最容易导致检索不稳：

- 方剂 canonical registry 缺失。
- 方剂 alias / variant registry 未 runtime 化。
- chunk 回指没有 formula span / neighbor window 约束。

最容易导致串方：

- 方名仅从文本标题动态抽取，没有持久 formula_id。
- 对比题没有 pairwise relation object。
- commentarial 缺少 `unit_scope_type` 和 `main_focus_terms`。

最容易导致过度保守：

- 术语/症状/治法口语映射缺失。
- 条文主题标签缺失。
- meaning query 缺少 stable canonical context window。

最容易导致空召回：

- alias 表未进入 runtime。
- 普通学习者问法没有数据化 normalization。

最容易导致引用不自然：

- 方剂连续段没有 formula span registry。
- `source_file/source_item_no/passage_order_in_chapter` 没有被用于 citation label 和邻接窗口。
