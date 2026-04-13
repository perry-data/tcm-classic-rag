# formula_effect_title_or_composition_before_after_v1

## Delta 概览

- baseline title/composition 样本总数：`15` queries
- baseline title/composition 公式数：`5`
- `formula_title_or_composition_over_primary`：`15` -> `0`
- 脱离 title/composition 的 query 数：`15`
- 脱离 title/composition 的 formula 数：`5`
- 其中回到 `direct_context_main_selected`：`9` queries
- 其中转入 `cross_chapter_bridge_primary`：`6` queries
- 其中转入 `false_strong_without_direct_context`：`0` queries
- stable positive 回退 query 数：`0`
- review-only weak 误抬 query 数：`0`

## 代表性样本一：同一条正文不再被误判成组成条

### 小承气汤方有什么作用

- before primary：`safe:main_passages:ZJSHL-CH-011-P-0086`
- before primary text：阳明病，谵语发潮热，脉滑而疾者，小承气汤主之。因与承气汤一升，腹中转失赵本无「失」字气者，更服一升；若不转失气，赵本作「转气者」勿更与之。明日赵本有「又」字不大便，脉反微涩者，里虚也，为难治，不可更与承气汤也。
- before answer 首句：根据当前主依据，小承气汤在书中的直接使用语境，是“阳明病，谵语发潮热，脉滑而疾”。
- after primary：`safe:main_passages:ZJSHL-CH-011-P-0086`
- after primary text：阳明病，谵语发潮热，脉滑而疾者，小承气汤主之。因与承气汤一升，腹中转失赵本无「失」字气者，更服一升；若不转失气，赵本作「转气者」勿更与之。明日赵本有「又」字不大便，脉反微涩者，里虚也，为难治，不可更与承气汤也。
- after answer 首句：根据当前主依据，小承气汤在书中的直接使用语境，是“阳明病，谵语发潮热，脉滑而疾”。
- primary 是否从方题/组成条切到直接使用语境：`否`。这批样本里主修点主要是去掉 composition 误判，因此很多 query 的 primary row 本身并未更换。
- answer_text 是否更像“基于语境解释”：`基本持平`。这类样本的主要改善在 primary slot 归因，不一定体现在 answer 文案改写上。
- 是否引入新的误伤：`未见`。answer_mode 仍为 `strong`，review-only 弱样本没有被抬升。

## 代表性样本二：title/composition 去掉后暴露为 bridge

### 桂枝加芍药生姜人参新加汤方有什么作用

- before primary：`safe:main_passages:ZJSHL-CH-009-P-0096` / `ZJSHL-CH-009`
- after primary：`safe:main_passages:ZJSHL-CH-009-P-0096` / `ZJSHL-CH-009`
- after pattern：`cross_chapter_bridge_primary`
- primary 是否从方题/组成条切到直接使用语境：`否`。primary 仍是同一条正文，但现在更准确地暴露为 cross-chapter bridge，而不是 composition 误占。
- answer_text 是否更像“基于语境解释”：`基本持平`。这类样本的主要变化是 bucket 更准确，不是文案层重写。
- 是否引入新的误伤：`否`。这是旧的 bridge 问题被重新显影，不是新的误抬。

## 稳定性抽查

- `stable positive` 回退：`未见`。
- `review_only_should_remain_weak` 误抬：`未见`。
