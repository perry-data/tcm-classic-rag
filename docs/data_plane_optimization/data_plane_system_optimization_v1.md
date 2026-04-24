# Data Plane System Optimization v1

## 1. 本轮目标与冻结边界

本轮只做 data plane 系统级优化，不触碰 prompt、前端、API payload 顶层 contract、`answer_mode` 定义、commentarial 主逻辑，也不重新放开 raw `full:passages:*` 进入 `primary_evidence`。

本轮目标是把系统从“依赖脏 `full passage` + 少量手工 definition 补丁”推进到“有对象层、有句段角色层、有 learner normalization 层、runtime 能优先命中安全对象层”的状态。

## 2. 基线快照

基线数据库为 `/tmp/zjshl_v1_before_data_plane_v1.db`，升级后数据库为 `artifacts/zjshl_v1.db`。

| 指标 | 基线 | 本轮后 |
| --- | ---: | ---: |
| `definition_term_registry` | 6 | 32 |
| `retrieval_ready_definition_view` | 5 | 29 |
| `term_alias_registry` | 0 | 86 |
| `learner_query_normalization_lexicon` | 0 | 97 |
| `sentence_role_registry` | 0 | 11030 |
| 回归集 `strong` | 19 | 39 |
| 回归集 `weak_with_review_notice` | 9 | 2 |
| 回归集 `refuse` | 13 | 0 |
| `forbidden primary` | 0 | 0 |
| `formula bad anchors top5` | 0 | 0 |
| `support_only` | 9 | 2 |

## 3. 本轮完成的对象层重构

### 3.1 Formula object 主线保持并纳入统一 trace

- 保留既有：
  - `formula_canonical_registry`
  - `formula_alias_registry`
  - `retrieval_ready_formula_view`
- 维持 formula query 在 runtime 的优先对象命中逻辑。
- 对 `source_confidence=medium` 的 formula 做了集中审计，当前仍有 14 条，主要集中在单条 heading 型方文、相邻方紧邻、附方/连续方边界不够稳的条目。
- 本轮 formula 主线要求是“不回退且可审计”，回归结果显示精确方题、相近方题、比较题、易串方题全部保持 `strong`，且 bad anchor 没有反弹。

### 3.2 Definition / concept object 扩容

本轮从“小样板”扩成了一个可运行的 definition/concept 对象层：

- `definition_term_registry`：32 个 concept/term 对象
- `retrieval_ready_definition_view`：29 个 safe primary definition 对象
- `safe_primary`：29
- `review_only`：3
- `source_confidence` 分布：
  - `high`: 6
  - `medium`: 23
  - `review_only`: 3
- `promotion_source_layer` 分布：
  - `promoted_from_full_risk_layer`: 23
  - `safe_main_passage`: 9

覆盖的对象类型包括：

- 治法/药类术语：`发汗药`、`下药`
- 病机/病态术语：`坏病`、`两感`、`伏气`、`消渴`、`风温`、`奔豚`、`湿痹`、`胆瘅`、`水结胸`
- 脉象/证候术语：`阳结`、`阴结`、`阳不足`、`阴不足`、`代阴`
- 书中高频关键概念：`小结胸`、`脏结`、`虚烦`、`内烦`、`盗汗`、`肺痿`、`四逆`

### 3.3 Sentence / segment role 对象层

新增 `sentence_role_registry`，把 runtime 之前只能看到的一整段 passage，拆成句段级可标注对象。当前共 11030 条句段记录。

当前句段 `primary_role` 统计：

- `definition_sentence`: 246
- `membership_sentence`: 155
- `explanation_sentence`: 8190
- `formula_name_sentence`: 212
- `formula_composition_sentence`: 898
- `formula_decoction_sentence`: 48
- `formula_usage_sentence`: 952
- `variant_note_sentence`: 110
- `risk_sentence`: 219

同时，`role_tags_json` 记录了混合角色与污染标签，用于识别：

- `commentary_like_sentence`
- `editorial_note_sentence`
- `variant_note_sentence`

这层 registry 的作用不是直接替代 answer assembler，而是给 definition/concept 的安全升格提供可审计的切分依据。

### 3.4 Learner normalization 对象层

新增两层 learner-oriented normalization 对象：

- `term_alias_registry`
- `learner_query_normalization_lexicon`

当前规模：

- `term_alias_registry`: 86
- `learner_query_normalization_lexicon`: 97
  - `term_surface`: 83
  - `query_family`: 14

覆盖了：

- 普通术语问法：`什么是{topic}`、`{topic}是什么意思`
- 短术语问法：`什么是下药`
- 口语问法：`睡着出汗是什么意思`
- 类属问法：`{topic}是什么药`
- 学习者口语映射：
  - `泻下药 -> 下药`
  - `四肢不温 -> 四逆`
  - `气从少腹上冲 -> 奔豚`
  - `时气 -> 时行之气`
  - `水饮结胸 -> 水结胸`

## 4. Runtime 接线

本轮 runtime 接线只做对象层增强，不改 answer contract。

### 4.1 Retrieval request 新增 term normalization

- formula query 仍优先走 formula object。
- 如果 formula normalization 未命中，则 definition runtime 会尝试：
  - 识别 query family
  - 抽取 topic term
  - 进行 canonical term / alias 匹配
  - 回写 `query_text_normalized`
  - 设置 `query_focus_source = term_normalization`

### 4.2 Definition object candidate 注入融合

- `retrieval_ready_definition_view` 现在和 formula view 一样，作为 runtime 的显式对象候选源进入 early candidate collection。
- `definition_terms` primary 与其 source passage 关系被显式回写到 candidate metadata 中。

### 4.3 Retrieval trace 可审计

`retrieval_trace` 新增：

- `definition_object_top_candidates`
- `term_normalization`

同时 candidate 额外暴露：

- `concept_id`
- `canonical_term`
- `promotion_source_layer`
- `primary_support_passage_id`

这样可以从 trace 直接看出：

1. 学习者问法被归一到哪个 term
2. 命中了哪个 definition object
3. 这个 object 是从安全主文本直接来，还是从 risk layer 提升而来

## 5. 脏数据治理结果

本轮不是直接清洗所有 raw/full passages，而是先把脏数据类型做了系统分类，并建立“脏 passage 不直接上 primary，而是句段化后按规则提升”的治理框架。

高价值治理结果如下：

- mixed-role passages: 2435
- editorial contaminated passages: 1211
- commentary contaminated passages: 441
- 其中最直接影响准确率的不是“脏 passage 本身”，而是：
  - 真实定义句被埋在 risk/support 层
  - learner 问法没有稳定归一
  - 二字短词被 sparse/FTS 侧弱化

本轮通过对象化与 normalization，把这几个最影响 definition/meaning 准确率的问题先拉平。

## 6. 短术语专项治理结果

短术语治理不靠 prompt 兜底，而是从对象与 normalization 层处理。

当前结果：

- `short_term_safe_primary_count`: 23
- 典型短术语 safe primary 包括：
  - `下药`
  - `坏病`
  - `两感`
  - `消渴`
  - `风温`
  - `虚烦`
  - `内烦`
  - `盗汗`
  - `肺痿`
  - `脏结`
  - `阳结`
  - `阴结`

回归集中 learner short query：

- before `strong`: 0 / 9
- after `strong`: 9 / 9

`什么是下药` 这一类问题现在不再依赖 raw passage luck，而是稳定落到 `definition_terms` primary。

## 7. 系统级回归结果

回归集覆盖：

- `formula_exact`
- `formula_similar`
- `formula_comparison`
- `formula_easy_confuse`
- `definition`
- `learner_short`
- `boundary_review_only`

主要结果：

- formula query：全部保持 `strong`
- definition / meaning query：多个原 `refuse` / `weak_with_review_notice` 提升为 `strong`
- learner-oriented query：9 条全部转为 `strong`
- review-only 边界题：
  - `神丹是什么意思` 仍为 `weak_with_review_notice`
  - `将军是什么意思` 仍为 `weak_with_review_notice`
- forbidden primary：保持 `0`
- formula bad anchor top5：保持 `0`

回归中最典型的提升包括：

- `什么是下药`: `refuse -> strong`
- `什么是坏病`: `refuse -> strong`
- `什么是消渴`: `refuse -> strong`
- `什么是风温`: `refuse -> strong`
- `什么是虚烦`: `weak_with_review_notice -> strong`
- `睡着出汗是什么意思`: `refuse -> strong`
- `四肢不温是什么`: `weak_with_review_notice -> strong`

## 8. 本轮产物

本轮新增或更新的核心产物：

- `docs/data_plane_optimization/data_plane_system_optimization_v1.md`
- `docs/data_plane_optimization/dirty_data_taxonomy_v1.md`
- `docs/data_plane_optimization/safe_promotion_policy_v1.md`
- `artifacts/data_plane_optimization/definition_term_registry_v2.json`
- `artifacts/data_plane_optimization/term_alias_registry_v1.json`
- `artifacts/data_plane_optimization/learner_query_normalization_lexicon_v1.json`
- `artifacts/data_plane_optimization/sentence_role_registry_v1.json`
- `artifacts/data_plane_optimization/data_plane_regression_v1.json`
- `artifacts/data_plane_optimization/data_plane_regression_v1.md`

脚本与测试：

- `scripts/data_plane_optimization/build_data_plane_objects_v1.py`
- `scripts/data_plane_optimization/run_data_plane_regression_v1.py`
- `tests/test_data_plane_optimization_v1.py`

## 9. 结论

这轮 v1 已经把系统的 data plane 从“只有 formula object + 少量 definition 补丁”推进到了“formula object + definition/concept object + sentence role registry + learner normalization + runtime object wiring”的状态。

最重要的不是单个 query 变好了，而是：

1. definition/concept 已经不再只能依赖脏 full passage 碰运气；
2. learner-oriented 短问法有了稳定的 normalization 入口；
3. risk/support 与 safe primary 的边界仍然守住；
4. formula 主线收益没有回退。
