# Dirty Data Taxonomy v1

## 1. 扫描范围

本轮脏数据分类扫描覆盖了以下 runtime 相关表与视图：

- `records_main_passages`
- `records_passages`
- `records_annotations`
- `risk_registry_ambiguous`
- `formula_canonical_registry`
- `formula_alias_registry`
- `retrieval_ready_formula_view`
- `definition_term_registry`
- `retrieval_ready_definition_view`
- `term_alias_registry`
- `learner_query_normalization_lexicon`
- `sentence_role_registry`

本轮不是逐条人工修整所有脏 passage，而是先建立“问题总账 + 对象化治理入口”。

## 2. 脏数据主类型总表

| 脏数据类型 | 主要落点 | 量化信号 | 直接后果 | 影响优先级 |
| --- | --- | --- | --- | --- |
| mixed-role passages | `records_main_passages` `records_passages` `records_annotations` `risk_registry_ambiguous` | 2435 个 mixed-role passage | 定义句、解释句、版本差异、附加说明被卷进同一条 passage，主证据难以稳定抽取 | P0 |
| editorial / variant contamination | 同上，重点是带版本差异与编校说明的 passage | 1211 个 editorial contaminated passage | `赵本`、`医统本`、`一云`、`注`、`详见` 等内容污染学习者答案主线 | P0 |
| formula span boundary ambiguity | `formula_canonical_registry` `retrieval_ready_formula_view` 及其原始方文 passage | 106 个 formula 中仍有 14 个 `source_confidence=medium` | 相邻方、附方、连续方文的边界不够稳，容易在极近邻方名中串方 | P1 |
| concept evidence buried in risk layer | `records_passages` `risk_registry_ambiguous` 为主，部分在 `records_main_passages` | 32 个 term 中有 23 个来自 `promoted_from_full_risk_layer` | 真正有定义价值的句子只存在于 support/review/risk 层，导致空 primary、support-only、refuse | P0 |
| alias / normalization insufficiency | 原运行时缺少 term-level alias/learner lexicon；本轮新增 `term_alias_registry` 与 `learner_query_normalization_lexicon` | 新增 86 条 term alias，97 条 learner lexicon | 普通学习者问法、口语问法、短术语问法无法稳定对齐 canonical term | P0 |
| short-term / short-query retrieval weakness | `backend/retrieval/hybrid.py` 的短词 sparse 弱化 + 原先缺少 object injection | regression 中 learner_short `strong: 0 -> 9`，短术语 safe primary 23 个 | 二字词、短术语、口语短问法容易被 FTS/query focus 弱化 | P0 |

## 3. 各类问题的具体结论

### 3.1 Mixed-role passages

问题定义：

- 同一 full/main passage 中同时混有：
  - `definition_sentence`
  - `explanation_sentence`
  - `membership_sentence`
  - `variant_note_sentence`
  - `commentary_like_sentence`

当前量化：

- `mixed_role_passage_count = 2435`
- 来源分布：
  - `records_passages`: 1212
  - `records_main_passages`: 538
  - `records_annotations`: 393
  - `risk_registry_ambiguous`: 292

典型后果：

- runtime 以前面对的是整条 passage，而不是句段对象；
- 当一条 passage 里同时出现“定义句 + 解释句 + 版本差异句”时，主证据很容易要么过脏，要么完全不敢上主证据。

典型样例：

- `ZJSHL-CH-006-P-0120`
  - 包含 `桂枝汤者，发汗药也。承气汤者，下药也。`
  - 同时又混入《金匮玉函》相关异文与附加说明
- `ZJSHL-CH-003-P-0002`
  - 同一条里混有定义、解释、版本差异标记

治理判断：

- 这是 definition/concept 失败的上游根因之一；
- 最适合通过 `sentence_role_registry` 先拆句，再做安全升格，而不是直接把整条 full passage 放回 primary。

### 3.2 Editorial / variant contamination

问题定义：

- 编校、异文、版本差异、注释性材料与正文解释混写，污染主文本理解。

当前量化：

- `editorial_contaminated_passage_count = 1211`
- 来源分布：
  - `records_passages`: 604
  - `records_main_passages`: 339
  - `records_annotations`: 126
  - `risk_registry_ambiguous`: 142

常见污染触发词：

- `赵本`
- `医统本`
- `一云`
- `注`
- `详见`
- 各类异文说明句

典型后果：

- 学习者只是在问“什么是某术语”，返回的主证据却掺入版本差异；
- 答案可以检索到，但不适合直接做 learner-facing primary。

治理判断：

- 这类内容可以继续保留在 support/review；
- 若其中包含可分离的定义句，应先句段化，再只提升干净定义句，而不是整体提升原 passage。

### 3.3 Formula span boundary ambiguity

问题定义：

- 方剂对象已经建立，但部分 formula 仍只有单条 heading/相邻方边界，缺少更高把握度的 span 说明。

当前量化：

- `formula_canonical_registry` 共 106 个 formula object
- 其中 `source_confidence=medium` 仍有 14 个

主要风险条目包括：

- `桂枝加浓朴杏子汤`
- `桂枝去芍药汤`
- `桂枝去芍药加附子汤`
- `桂枝去桂加茯苓白术汤`
- `四逆加人参汤`
- `四逆加猪胆汁汤`
- `乌梅丸`

典型后果：

- 对相近方名与连续方文，边界依赖现有 registry 切分结果；
- 一旦后续有人直接回退到 raw formula span 逻辑，串方风险会重新上升。

治理判断：

- 这类问题影响 formula 侧上限，但当前 formula 主线已较稳；
- 优先级低于 definition/concept buried evidence 与 learner normalization；
- 本轮先完成 medium-confidence 总账与回归防回退，下一轮可做 formula span 精修。

### 3.4 Concept evidence buried in risk layer

问题定义：

- 真正有定义价值的句子存在于 `records_passages` / `risk_registry_ambiguous` 中，但因为原始载体太脏，runtime 不敢把它们当 primary。

当前量化：

- 本轮 32 个 definition/concept 对象中：
  - 23 个来自 `promoted_from_full_risk_layer`
  - 9 个来自 `safe_main_passage`

被成功提升的代表例子：

- `下药`
- `坏病`
- `两感`
- `消渴`
- `风温`
- `虚烦`
- `内烦`
- `肺痿`
- `盗汗`

直接影响：

- 这是本轮最影响准确率的一类问题；
- 在升级前，这些 query 常见表现是：
  - `refuse`
  - `weak_with_review_notice`
  - 只有 support/review，没有主证据

治理判断：

- 这是本轮最值得优先治理的一类，因为它直接决定 `primary_evidence` 能否稳定出现。

### 3.5 Alias / normalization insufficiency

问题定义：

- learner 问法并不会稳定写成 canonical 书面术语；
- 原系统在 term-level 缺少独立 registry，definition family 也缺乏 learner surface 映射。

当前量化：

- `term_alias_registry = 86`
- `learner_query_normalization_lexicon = 97`
  - `query_family = 14`
  - `term_surface = 83`

当前已覆盖的 learner 映射样例：

- `泻下药 -> 下药`
- `发汗的药 -> 发汗药`
- `四肢不温 -> 四逆`
- `气从少腹上冲 -> 奔豚`
- `时气 -> 时行之气`
- `睡着出汗 -> 盗汗`

直接影响：

- 这类问题不解决，definition registry 再大也无法被 learner query 稳定触发。

治理判断：

- 这是和 buried evidence 并列的 P0 问题；
- 需要 registry + runtime 一起接，不是单纯加 prompt 示例。

### 3.6 Short-term / short-query retrieval weakness

问题定义：

- 短术语 query 在 sparse/FTS 侧天然更脆弱；
- 原检索实现对 sparse query term 做了长度过滤，二字词与极短 query 容易损失 lexical 侧支撑。

主要落点：

- `backend/retrieval/hybrid.py`
- 旧 runtime 对 definition family 更依赖 noise stripping，而不是 term object

当前量化结果：

- `short_term_safe_primary_count = 23`
- `short_query_safe_primary_count = 28`
- regression 中 `learner_short strong: 0 -> 9`

代表 query：

- `什么是下药`
- `下药是干什么的`
- `睡着出汗是什么意思`
- `时气是什么意思`
- `表里两感是什么意思`

治理判断：

- 这类问题不能只靠 sparse 调参；
- 必须通过：
  - term normalization
  - definition object injection
  - safe promoted term primary
 共同解决。

## 4. 哪类问题最影响准确率

按当前系统表现，最影响准确率的顺序如下：

1. `concept evidence buried in risk layer`
2. `alias / normalization insufficiency`
3. `short-term / short-query retrieval weakness`
4. `mixed-role passages`
5. `editorial / variant contamination`
6. `formula span boundary ambiguity`

原因：

- 前三类会直接造成 `refuse`、空 primary、support-only；
- 第四第五类是前三类的上游来源；
- formula span 问题重要，但当前 formula object 主线已经压住了大多数明显回退风险。

## 5. 哪类问题最适合优先治理

v1 优先治理结论：

- 第一优先：把 buried definition/concept 句子对象化并升格
- 第二优先：建立 term alias 与 learner normalization
- 第三优先：给短术语和口语问法一条稳定的 runtime 归一路径
- 第四优先：对 formula medium-confidence 条目做专门的 span 精修

因此，本轮采用的策略不是“直接重洗全库”，而是：

1. 先建立 `sentence_role_registry`
2. 再建立 `definition_term_registry` / `retrieval_ready_definition_view`
3. 再建立 `term_alias_registry` / `learner_query_normalization_lexicon`
4. 最后把对象层接回 runtime

这比继续对单个 query 打补丁更符合 data-plane 系统治理目标。
