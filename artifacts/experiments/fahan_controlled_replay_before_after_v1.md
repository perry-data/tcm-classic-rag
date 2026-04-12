# fahan_controlled_replay_before_after_v1

## 实验设置

- 实验开关：`TCM_ENABLE_FAHAN_CONTROLLED_REPLAY_V1`
- allowlist：
  - `ZJSHL-CH-006-P-0120`
  - `ZJSHL-CH-006-P-0127`
- 放回层级：
  - `recall = true`
  - `vector = false`
  - `primary_candidate = false`
- synthetic replay record：
  - `record_table = controlled_replay_main_passages`
  - 只允许进入 `secondary_evidence`

## 总结

本轮实验结果很明确：

- `0120 / 0127` 在 flag 打开后，已经能稳定进入 `raw_candidates` 与 `secondary_evidence`
- `什么是发汗药` 的最终答案几乎没有变化，主依据仍然是 `safe:main_passages:ZJSHL-CH-010-P-0137`
- 这说明问题不再只是“证据池里没有关键条目”，而是“关键条目进来了，但没有进入主裁决 / answer_text”
- 两个回归查询 `太阳病是什么`、`竹叶石膏汤方有什么作用` 未观察到外溢回归

## Query 1: 什么是发汗药

### Before

- top 检索候选：
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0358`
  - `safe:main_passages:ZJSHL-CH-009-P-0123`
  - `safe:chunks:ZJSHL-CK-M-0948`
  - `safe:main_passages:ZJSHL-CH-019-P-0109`
- evidence slots：
  - `primary`: `safe:main_passages:ZJSHL-CH-010-P-0137`
  - `secondary`: `safe:main_passages:ZJSHL-CH-009-P-0123`, `safe:main_passages:ZJSHL-CH-019-P-0109`
  - `review`: `full:passages:ZJSHL-CH-006-P-0120`, `full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`
- final `answer_mode`: `strong`
- final `answer_text`：

```text
根据主依据，直接相关的主条如下：
1. 证云：不可发汗，发汗则谵语。是发汗攻太阳之邪，少阳之邪益甚干胃，必发谵语。此云慎勿下之，攻少阳之邪，太阳之邪乘虚入里，必作结胸。经曰：太阳少阳并病，而反下之，成结胸。
```

- 是否仍然出现“只直出怪条、不解释”：`是`

### After

- top 检索候选：
  - `controlled:main_passages:ZJSHL-CH-006-P-0127`
  - `controlled:main_passages:ZJSHL-CH-006-P-0120`
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0358`
  - `safe:main_passages:ZJSHL-CH-009-P-0123`
- evidence slots：
  - `primary`: `safe:main_passages:ZJSHL-CH-010-P-0137`
  - `secondary`: `controlled:main_passages:ZJSHL-CH-006-P-0127`, `controlled:main_passages:ZJSHL-CH-006-P-0120`, `safe:main_passages:ZJSHL-CH-009-P-0123`, `safe:main_passages:ZJSHL-CH-019-P-0109`
  - `review`: `full:passages:ZJSHL-CH-006-P-0120`, `full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`
- final `answer_mode`: `strong`
- final `answer_text`：

```text
根据主依据，直接相关的主条如下：
1. 证云：不可发汗，发汗则谵语。是发汗攻太阳之邪，少阳之邪益甚干胃，必发谵语。此云慎勿下之，攻少阳之邪，太阳之邪乘虚入里，必作结胸。经曰：太阳少阳并病，而反下之，成结胸。
```

- 是否仍然出现“只直出怪条、不解释”：`是`

### 观察

- 本轮受控回放已经把 `0120 / 0127` 从“只在 review 里出现”推进到了“稳定进入 raw candidates + secondary evidence”
- 但 final answer 完全没有吸收这两条 query-critical 证据
- 因此“什么是发汗药”的主问题，已经不能只归因为 safe 误杀；更主要卡在：
  - primary evidence 仍被 `ZJSHL-CH-010-P-0137` 占据
  - answer_text 仍只跟随 primary 直出

## Query 2: 桂枝汤是发汗药吗

### Before

- top 检索候选：
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0720`
  - `safe:main_passages:ZJSHL-CH-013-P-0008`
  - `safe:chunks:ZJSHL-CK-M-0952`
  - `safe:main_passages:ZJSHL-CH-020-P-0002`
- evidence slots：
  - `primary`: `safe:main_passages:ZJSHL-CH-013-P-0008`, `safe:main_passages:ZJSHL-CH-020-P-0002`, `safe:main_passages:ZJSHL-CH-009-P-0051`
  - `secondary`: `safe:main_passages:ZJSHL-CH-009-P-0098`, `safe:main_passages:ZJSHL-CH-008-P-0246`, `safe:main_passages:ZJSHL-CH-008-P-0229`, `safe:main_passages:ZJSHL-CH-009-P-0096`
  - `review`: `full:passages:ZJSHL-CH-006-P-0120`, `full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`
- final `answer_mode`: `strong`
- final `answer_text`：

```text
根据主依据，直接相关的主条如下：
1. 太阴病脉浮者，可发汗，宜桂枝汤。赵本有「桂枝汤方」详见卷二
2. 发汗多，亡阳谵语者，不可下，与柴胡桂枝汤和其荣卫，以通津液，后自愈。赵本有「柴胡桂枝汤方」详见卷十
3. 太阳赵本有「桂枝汤方」详见本书卷二病，外证未解，脉浮弱者，当以汗解，宜桂枝汤。
```

- 是否仍然出现“只直出怪条、不解释”：`是`

### After

- top 检索候选：
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `controlled:main_passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0720`
  - `safe:main_passages:ZJSHL-CH-013-P-0008`
  - `safe:chunks:ZJSHL-CK-M-0952`
- evidence slots：
  - `primary`: `safe:main_passages:ZJSHL-CH-013-P-0008`, `safe:main_passages:ZJSHL-CH-020-P-0002`, `safe:main_passages:ZJSHL-CH-009-P-0051`
  - `secondary`: `controlled:main_passages:ZJSHL-CH-006-P-0120`, `safe:main_passages:ZJSHL-CH-009-P-0098`, `safe:main_passages:ZJSHL-CH-008-P-0246`, `controlled:main_passages:ZJSHL-CH-006-P-0127`, `safe:main_passages:ZJSHL-CH-009-P-0096`
  - `review`: `full:passages:ZJSHL-CH-006-P-0120`, `full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`
- final `answer_mode`: `strong`
- final `answer_text`：

```text
根据主依据，直接相关的主条如下：
1. 太阴病脉浮者，可发汗，宜桂枝汤。赵本有「桂枝汤方」详见卷二
2. 发汗多，亡阳谵语者，不可下，与柴胡桂枝汤和其荣卫，以通津液，后自愈。赵本有「柴胡桂枝汤方」详见卷十
3. 太阳赵本有「桂枝汤方」详见本书卷二病，外证未解，脉浮弱者，当以汗解，宜桂枝汤。
```

- 是否仍然出现“只直出怪条、不解释”：`是`

### 观察

- 对 yes/no 倾向很强的 query，`0120` 已经成功回到 candidate chain
- 但主答案仍然没有直接回答“是 / 否”，而是继续堆叠若干可发汗语境条
- 这进一步说明：仅补 recall，不足以修复答案层表现

## Query 3: 太阳病是什么

### Before

- top 检索候选：
  - `safe:main_passages:ZJSHL-CH-007-P-0157`
  - `safe:chunks:ZJSHL-CK-M-0257`
  - `safe:main_passages:ZJSHL-CH-008-P-0195`
  - `full:passages:ZJSHL-CH-009-P-0306`
  - `safe:chunks:ZJSHL-CK-M-0299`
  - `safe:main_passages:ZJSHL-CH-009-P-0002`
- evidence slots：
  - `primary`: `safe:main_passages:ZJSHL-CH-008-P-0191`
  - `secondary`: `safe:main_passages:ZJSHL-CH-008-P-0193`, `safe:main_passages:ZJSHL-CH-008-P-0195`, `safe:main_passages:ZJSHL-CH-009-P-0002`, `safe:main_passages:ZJSHL-CH-008-P-0220`, `safe:main_passages:ZJSHL-CH-007-P-0157`
  - `review`: `full:passages:ZJSHL-CH-009-P-0306`, `full:passages:ZJSHL-CH-007-P-0164`
- final `answer_mode`: `strong`
- final `answer_text`：

```text
书中对“太阳病”的提纲性表述，可先看“太阳之为病，脉浮，头项强痛而恶寒。”
主依据条文：太阳之为病，脉浮，头项强痛而恶寒。
其余相关条文可再看补充依据，用来展开外证、分类或治法，但不替代这条提纲句。
```

- 是否仍然出现“只直出怪条、不解释”：`否`

### After

- top 检索候选：无变化
- evidence slots：无变化
- final `answer_mode`: `strong`
- final `answer_text`：与 before 一致
- 是否仍然出现“只直出怪条、不解释”：`否`

### 观察

- 本轮 controlled replay 没有影响这个 query
- regression check 通过

## Query 4: 竹叶石膏汤方有什么作用

### Before

- top 检索候选：
  - `full:ambiguous_passages:ZJSHL-CH-017-P-0064`
  - `safe:main_passages:ZJSHL-CH-017-P-0063`
  - `safe:chunks:ZJSHL-CK-M-0922`
  - `full:passages:ZJSHL-CH-017-P-0063`
  - `safe:main_passages:ZJSHL-CH-017-P-0065`
  - `full:passages:ZJSHL-CH-017-P-0065`
- evidence slots：
  - `primary`: `safe:main_passages:ZJSHL-CH-017-P-0063`
  - `secondary`: `safe:main_passages:ZJSHL-CH-017-P-0065`
  - `review`: `full:passages:ZJSHL-CH-017-P-0065`, `full:passages:ZJSHL-CH-017-P-0063`
- final `answer_mode`: `strong`
- final `answer_text`：

```text
根据当前主依据，竹叶石膏汤在书中的直接使用语境，是“伤寒解后，虚羸少气，气逆欲吐”。
也就是说，它更偏向用于伤寒解后，虚羸少气，气逆欲吐这类情况。
依据条文：伤寒解后，虚羸少气，气逆欲吐者，赵本无「者」字竹叶石膏汤主之。
补充方文：竹叶石膏汤方：竹叶二把。辛平 石膏一斤。甘寒 半夏半升，洗。辛温 人参三。赵本作「二」两。
```

- 是否仍然出现“只直出怪条、不解释”：`否`

### After

- top 检索候选：无变化
- evidence slots：无变化
- final `answer_mode`: `strong`
- final `answer_text`：与 before 一致
- 是否仍然出现“只直出怪条、不解释”：`否`

### 观察

- 本轮 controlled replay 没有影响这个 query
- regression check 通过

## 结论

### 1. allowlist + feature flag 是否工作

`是`

证据：

- `什么是发汗药` 打开 flag 后，`controlled:main_passages:ZJSHL-CH-006-P-0127` 与 `controlled:main_passages:ZJSHL-CH-006-P-0120` 进入了 raw top candidates
- 同一 query 的 `secondary_evidence` 也稳定出现了这两条
- `桂枝汤是发汗药吗` 打开 flag 后，`controlled:main_passages:ZJSHL-CH-006-P-0120` 进入 raw top candidates，并进入 `secondary_evidence`

### 2. “什么是发汗药”的问题主要卡在哪里

结论：`主要卡在 primary evidence / answer assembly，不再只是 evidence pool`

理由：

- before 时，关键条目 `0120` 只以 `review material` 形式存在
- after 时，关键条目 `0120 / 0127` 已经回到 `raw_candidates + secondary_evidence`
- 但 final primary 仍是 `safe:main_passages:ZJSHL-CH-010-P-0137`
- final `answer_text` 也完全未变

因此本轮最小实验已经把问题切分得更清楚：

- safe 误杀确实是原因之一
- 但不是唯一主因
- 仅把 `0120 / 0127` 回放到 recall，不足以让答案恢复正常

### 3. 是否值得继续做下一轮

`值得，但方向应聚焦在 main_passages 的 primary 裁决，不是继续扩 annotation`

更具体地说，下一轮若继续，应优先考虑：

- 仅围绕“发汗药”类 query，再做一个更窄的 primary candidate / evidence prioritization 实验
- 继续保持 `annotation` 与 `annotation_links` 关闭
- 继续避免大规模向量索引扩放

### 4. 本轮不建议做什么

- 不建议因为本轮 recall 生效，就直接恢复 `annotation_links`
- 不建议立刻把 allowlist 扩成大批量 `main_passages`
- 不建议在没有进一步验证前，把 `0120 / 0127` 直接抬成默认 primary
- 不建议用 prompt 特判“发汗药”来掩盖主依据裁决问题
