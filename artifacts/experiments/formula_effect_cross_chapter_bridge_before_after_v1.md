# formula_effect_cross_chapter_bridge_before_after_v1

## Delta 概览

- baseline bridge 样本总数：`60` queries
- baseline bridge 公式数：`20`
- `cross_chapter_bridge_primary`：`60` -> `57`
- 改善 query 数：`3`
- 改善 formula 数：`1`
- stable positive 回退 query 数：`0`
- review-only weak 误抬 query 数：`0`

## 代表性修正样本

### 吴茱萸汤方有什么作用

- before primary：`safe:main_passages:ZJSHL-CH-014-P-0097` / `ZJSHL-CH-014`
- before primary text：少阴病，吐利，手足厥赵本作「逆」冷，烦躁欲死者，吴茱萸汤主之。赵本有「吴茱萸汤方」详见卷五
- before answer 首句：根据当前主依据，吴茱萸汤在书中的直接使用语境，是“少阴病，吐利，手足厥冷，烦躁欲死”。
- same-chapter direct candidates：`safe:main_passages:ZJSHL-CH-011-P-0156`
- after primary：`safe:main_passages:ZJSHL-CH-011-P-0156` / `ZJSHL-CH-011`
- after primary text：食谷欲呕者，赵本无「者」字属阳明也，吴茱萸汤主之。得汤反剧者，属上焦也。
- after answer 首句：根据当前主依据，吴茱萸汤在书中的直接使用语境，是“食谷欲呕者，属阳明也”。
- primary_evidence 是否切回同方正文直接语境：`是`
- answer_text 是否更自然：`是`。primary 从跨章桥接句切回公式正文 chapter 下的直接语境，回答不再依赖章际承接。
- 是否引入新的误伤：`未见`。answer_mode 仍为 `strong`，secondary/review 结构未被改写。

## 代表性保留样本

### 五苓散方有什么作用

- before primary：`safe:main_passages:ZJSHL-CH-010-P-0090` / `ZJSHL-CH-010`
- before primary text：本以下之，故心下痞，与泻心汤；痞不解，其人渴而口燥烦，小便不利者，五苓散主之。赵本有「一方云：忍之，一日乃愈」九字
- same-chapter direct candidates：`_none_`
- after primary：`safe:main_passages:ZJSHL-CH-010-P-0090` / `ZJSHL-CH-010`
- after answer 首句：根据当前主依据，五苓散在书中的直接使用语境，是“痞不解，其人渴而口燥烦，小便不利”。
- primary_evidence 是否切回同方正文直接语境：`否`。
- answer_text 是否更自然：`未强行判断为更自然`。这类样本缺少 clean same-chapter direct context，继续切换就会开始把 short-tail / context 抽取问题混入本轮 patch。
- 是否引入新的误伤：`无`。这类样本被有意保留，说明规则没有扩到别的 failure pattern。

## 稳定性抽查

- 小柴胡汤方有什么作用：仍为 `strong`，primary=`safe:main_passages:ZJSHL-CH-009-P-0229` / `ZJSHL-CH-009`。
- 乌梅丸方有什么作用：仍为 `weak_with_review_notice`，primary 仍为空，未把 review-only weak 误抬成 strong。
