# Safe Promotion Policy v1

## 1. 目的

本策略用于回答一个核心问题：

什么样的句子可以从 raw/full passage 中被抽出，升格为安全的 definition/concept primary；什么样的句子只能继续停留在 support/review。

本策略只允许“句段升格为对象”，不允许“整条 raw `full:passages:*` 重新越权进入 `primary_evidence`”。

## 2. 升格单位

安全升格的最小单位是：

- 单句
- 或能从原 passage 中稳定切出的短句段

不允许直接把一整条 mixed-role full passage 作为 primary 重新上浮。

## 3. 可升格对象范围

本轮主要针对 definition / concept primary，对应对象为：

- `definition_term_registry`
- `retrieval_ready_definition_view`

句段角色上，优先考虑：

- `definition_sentence`
- `membership_sentence`
- 可独立成义的 `explanation_sentence`

默认不直接升格为 definition primary 的角色：

- `formula_name_sentence`
- `formula_composition_sentence`
- `formula_decoction_sentence`
- `formula_usage_sentence`
- `variant_note_sentence`
- `editorial_note_sentence`
- `commentary_like_sentence`
- `risk_sentence`

其中 formula 相关句段应该留在 formula object 主线，不应被混入 term definition primary。

## 4. Safe Promotion Criteria

一个句段要进入 safe primary，至少同时满足以下条件：

### 4.1 术语锚点明确

- 句内能明确定位 canonical term；
- 学习者问法可以稳定归一回该 term；
- 不依赖额外上下文才能知道“这句话到底在解释谁”。

### 4.2 句段可独立成义

- 单句或短句段本身就能表达：
  - “X 是什么”
  - “X 属于什么”
  - “X 指什么状态/病机/脉象”
- 不需要再拼接后文版本差异或长段按语，才能形成基本定义。

### 4.3 编校污染可剥离

- 升格部分不能夹带：
  - `赵本`
  - `医统本`
  - `一云`
  - `注`
  - `详见`
  - 明显异文校勘说明

若原 passage 含这些内容，只能在可稳定剥离之后，抽出干净定义句升格。

### 4.4 注释/按语污染不可上主证据

- 如果句段核心信息其实来自后人按语、注解、释义扩写，而不是可作为 learner-facing 主证据的正文级句段，则不能升格为 safe primary。

### 4.5 多义短词必须可控

- 对二字短词、术语缩略词、多义词，只有在 term alias 与 query normalization 能稳定收束到单一概念时，才允许升格。
- 否则只能留在 review/support。

### 4.6 记录必须可审计

每个被升格的 definition/concept 对象必须能追溯到：

- `primary_support_passage_id`
- `primary_source_table`
- `source_passage_ids_json`
- `promotion_source_layer`
- `promotion_reason`

没有可审计来源的对象不能进入 safe primary。

## 5. Review-Only Criteria

以下情况默认只能留在 `review_only` 或 support/review 层：

### 5.1 版本差异污染无法干净剥离

- 术语定义句与异文、校勘、版本比较严重缠绕；
- 拆出来后语义已经不完整。

### 5.2 依赖长上下文才能成立

- 单句看不出所指对象；
- 必须依赖上下两三句才知道这句到底在解释哪一个概念。

### 5.3 术语高度多义

- 如短词可能同时指病机、症状、药名、方义；
- 现有 alias/normalization 还无法安全判定唯一 canonical term。

### 5.4 注释性材料强于正文信息

- 内容主要来自按语、训诂、释名，而不是可直接给学习者的主证据句。

### 5.5 药名/别名高风险词

- 本轮典型 review-only：
  - `神丹`
  - `将军`
  - `两阳`

这类词在原文环境中容易受注释、训诂、语境切换影响，暂不提升为 definition primary。

## 6. Source Confidence 规则

### 6.1 `high`

适用条件：

- 来源于 `safe_main_passage`
- 句段边界清晰
- 术语锚点明确
- 无明显编校/注释污染

当前代表：

- `阳结`
- `阴结`
- `阳不足`
- `阴不足`
- `关格`
- `脏结`

### 6.2 `medium`

适用条件：

- 原始定义价值明确；
- 但来源于 `records_passages` / `risk_registry_ambiguous` / mixed-role passage；
- 需要经过句段抽取与人工复核后，才能作为 safe primary。

当前大部分新扩容 term 属于这一类。

### 6.3 `review_only`

适用条件：

- 仍有未解的上下文依赖、多义性、注释污染或语义不完整问题；
- 不允许进入 `retrieval_ready_definition_view`。

## 7. 最小人工复核机制

本轮采用“轻量但刚性”的人工复核，不追求全量精标，但每个 promoted term 至少过以下检查：

1. 确认 canonical term 是否唯一。
2. 确认 primary 句段是否能单独成立。
3. 确认是否含版本差异/注释污染。
4. 确认是否应标为 `safe_primary` 还是 `review_only`。
5. 填写：
   - `source_confidence`
   - `promotion_source_layer`
   - `promotion_reason`
   - `review_only_reason`（如适用）

这一步的目标不是把所有数据都人工重做，而是确保每一个被升格的 primary object 都能解释“为什么它可以上 primary”。

## 8. 特殊情形处理

### 8.1 版本差异污染

- 原则：版本差异不能上 primary。
- 处理：
  - 若可剥离，则只取干净定义句；
  - 若不可剥离，则保留在 support/review。

### 8.2 按语/注释污染

- 原则：按语、后设解释默认不做 primary。
- 处理：
  - 可当 review/support；
  - 除非能抽出明确、独立、非按语依赖的正文定义句。

### 8.3 单句语义不完整

- 原则：不完整句不升格。
- 处理：
  - 若能拼成一个稳定短句段且仍干净，可考虑升格；
  - 否则只保留为 support/review。

### 8.4 多义短词

- 原则：没有 normalization 收束，不升格。
- 处理：
  - 先补 alias 与 learner lexicon；
  - 再决定是否进入 safe primary。

### 8.5 依赖上下文的定义句

- 原则：上下文依赖过强，不升格。
- 处理：
  - 若能通过 term anchor + sentence split 解决，则升级；
  - 若不能，则保留在 review/support。

## 9. 当前 v1 执行结果

按本策略，本轮结果为：

- `definition_term_registry = 32`
- `safe_primary = 29`
- `review_only = 3`
- `promoted_from_full_risk_layer = 23`
- `safe_main_passage = 9`

这说明当前策略不是“保守到什么都不上”，也不是“激进到把脏 full passage 全放回 primary”，而是在安全边界内做了可审计的对象化升格。

## 10. Runtime 不变量

本策略下，runtime 必须始终满足：

1. raw `full:passages:*` 不能直接进入 `primary_evidence`；
2. definition/concept primary 只能来自 `definition_terms` 这样的对象层；
3. review-only term 不能偷偷进入 `retrieval_ready_definition_view`；
4. formula query 仍优先走 formula object，而不是被 definition object 抢路；
5. retrieval trace 必须能看出对象来源与升格路径。

这五条是后续所有 data-plane 迭代都不能破坏的硬边界。
