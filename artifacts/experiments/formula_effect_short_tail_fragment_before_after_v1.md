# formula_effect_short_tail_fragment_before_after_v1

## Delta 概览

- baseline short-tail 样本总数：`27` queries
- baseline short-tail 公式数：`9`
- `short_tail_fragment_primary`：`27` -> `0`
- 脱离 short-tail 的 query 数：`27`
- 脱离 short-tail 的 formula 数：`9`
- 其中回到 `direct_context_main_selected`：`21` queries
- 其中转入 `cross_chapter_bridge_primary`：`6` queries
- stable positive 回退 query 数：`0`
- review-only weak 误抬 query 数：`0`

## 代表性样本一：动作尾巴残片回退

### 文蛤散方有什么作用

- before primary：`safe:main_passages:ZJSHL-CH-010-P-0040`
- before primary_context_clause：`与`
- before answer 首句：根据当前主依据，文蛤散在书中的直接使用语境，是“与”。
- after primary：`safe:main_passages:ZJSHL-CH-010-P-0040`
- after primary_context_clause：`反不渴者，寒在表也`
- after answer 首句：根据当前主依据，文蛤散在书中的直接使用语境，是“反不渴者，寒在表也”。
- primary_context_clause 是否从短残片变成完整直接语境：`是`
- answer_text 是否更自然：`是`。首句不再直接暴露 `与 / 不瘥` 这类动作残片。
- 是否引入新的误伤：`未见`。primary 仍在 `main_passages`，answer_mode 仍为 `strong`。

## 代表性样本二：短但完整的直接语境不再误判

### 半夏散及汤方有什么作用

- before primary_context_clause：`少阴病咽中痛`
- after primary_context_clause：`少阴病咽中痛`
- after answer 首句：根据当前主依据，半夏散及汤在书中的直接使用语境，是“少阴病咽中痛”。
- primary_context_clause 是否不再被视为短残片：`是`。这类样本的 primary 没换 record，修复点主要是 compact direct clause 判定更稳了。
- answer_text 是否更自然：`是`。即使文本几乎不变，回答也不再被错误地归到 short-tail bucket。
- 是否引入新的误伤：`未见`。没有把 review-only 证据拉进 strong 主依据。

## 保留边界：短尾修掉后暴露为 bridge

### 栀子甘草豉汤方有什么作用

- before primary_context_clause：`若少气`
- after primary_context_clause：`少气`
- after pattern：`cross_chapter_bridge_primary`
- primary_context_clause 是否已经摆脱短残片：`是`。
- answer_text 是否更自然：`是`。但这类样本仍然不是 fully clean，因为现在暴露的是 chapter 归属问题，而不是短尾残片。
- 是否引入新的误伤：`否`。这是原有 bridge 问题被重新显影，不是 review-only 被误抬。

## 稳定性抽查

- 小柴胡汤方有什么作用：仍为 `strong`，pattern=`direct_context_main_selected`。
- 乌梅丸方有什么作用：仍为 `weak_with_review_notice`，primary 仍为空，未把 review-only weak 误抬成 strong。
