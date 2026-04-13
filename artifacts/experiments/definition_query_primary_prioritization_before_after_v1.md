# definition_query_primary_prioritization_before_after_v1

## 实验设置

- 开关：`TCM_ENABLE_DEFINITION_QUERY_PRIORITY_RULES_V1`
- before：`TCM_ENABLE_DEFINITION_QUERY_PRIORITY_RULES_V1=0`
- after：`TCM_ENABLE_DEFINITION_QUERY_PRIORITY_RULES_V1=1`
- 变更层级：
  - query family 识别
  - assembler 侧 primary candidate prioritization
  - 非破坏性的 answer assembly 输入优先级调整
- 未变更：
  - annotation 仍关闭
  - annotation_links 仍关闭
  - retrieval raw candidate 生成逻辑未改
  - `definition_outline_query` / `formula_effect_query` 既有专用路径保留

## 总结

- 本轮关键现象是：`raw_top_candidates` 基本不变，但 `primary_evidence` 发生了正确切换。
- `什么是发汗药` 不再由 `safe:main_passages:ZJSHL-CH-010-P-0137` 占 primary，而是改由 `full:passages:ZJSHL-CH-006-P-0120` 承担 primary。
- `桂枝汤是发汗药吗` 不再堆叠若干“可发汗语境”主条，而是直接使用 `桂枝汤者，发汗药也。` 组织答案。
- `太阳病是什么` 与 `竹叶石膏汤方有什么作用` 未观察到外溢回归。

## Query 1: 什么是发汗药

### Raw Top Candidates

- before：
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0358`
  - `safe:main_passages:ZJSHL-CH-009-P-0123`
  - `safe:chunks:ZJSHL-CK-M-0948`
  - `safe:main_passages:ZJSHL-CH-019-P-0109`
- after：
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0358`
  - `safe:main_passages:ZJSHL-CH-009-P-0123`
  - `safe:chunks:ZJSHL-CK-M-0948`
  - `safe:main_passages:ZJSHL-CH-019-P-0109`

### Evidence 变化

- `primary_evidence`
  - before：`safe:main_passages:ZJSHL-CH-010-P-0137`
  - after：`full:passages:ZJSHL-CH-006-P-0120`
- `secondary_evidence`
  - before：`safe:main_passages:ZJSHL-CH-009-P-0123`, `safe:main_passages:ZJSHL-CH-019-P-0109`
  - after：`safe:main_passages:ZJSHL-CH-010-P-0137`, `safe:main_passages:ZJSHL-CH-009-P-0123`, `safe:main_passages:ZJSHL-CH-019-P-0109`
- `review_materials`
  - before：`full:passages:ZJSHL-CH-006-P-0120`, `full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`
  - after：`full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`

### Final 输出

- `answer_mode`
  - before：`strong`
  - after：`strong`
- `answer_text`

before:

```text
根据主依据，直接相关的主条如下：
1. 证云：不可发汗，发汗则谵语。是发汗攻太阳之邪，少阳之邪益甚干胃，必发谵语。此云慎勿下之，攻少阳之邪，太阳之邪乘虚入里，必作结胸。经曰：太阳少阳并病，而反下之，成结胸。
```

after:

```text
书中并不是先给“发汗药”下一条抽象定义，现有可直接对应该问法的归类句是“桂枝汤者，发汗药也。承气汤者，下药也。”。
也就是说，这里是用具体对象的归属来说明“发汗药”这一类。
```

- `definition_priority_debug`
  - family：`what_is`
  - selected evidence type：`term_membership_sentence`
- 是否从“主条直出”改善为“基于依据解释”：`是`

### 观察

- raw top candidates 没变，说明这次不是 rerank/recall 修复。
- 真正变化发生在 assembler 对 `full:passages:ZJSHL-CH-006-P-0120` 的 primary 提升。
- 这满足了“至少什么是发汗药不再由明显无关主条占 primary”的验收条件。

## Query 2: 桂枝汤是发汗药吗

### Raw Top Candidates

- before：
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0720`
  - `safe:main_passages:ZJSHL-CH-013-P-0008`
  - `safe:chunks:ZJSHL-CK-M-0952`
  - `safe:main_passages:ZJSHL-CH-020-P-0002`
- after：
  - `full:passages:ZJSHL-CH-006-P-0120`
  - `full:ambiguous_passages:ZJSHL-CH-006-P-0120`
  - `safe:chunks:ZJSHL-CK-M-0720`
  - `safe:main_passages:ZJSHL-CH-013-P-0008`
  - `safe:chunks:ZJSHL-CK-M-0952`
  - `safe:main_passages:ZJSHL-CH-020-P-0002`

### Evidence 变化

- `primary_evidence`
  - before：`safe:main_passages:ZJSHL-CH-013-P-0008`, `safe:main_passages:ZJSHL-CH-020-P-0002`, `safe:main_passages:ZJSHL-CH-009-P-0051`
  - after：`full:passages:ZJSHL-CH-006-P-0120`
- `secondary_evidence`
  - before：`safe:main_passages:ZJSHL-CH-009-P-0098`, `safe:main_passages:ZJSHL-CH-008-P-0246`, `safe:main_passages:ZJSHL-CH-008-P-0229`, `safe:main_passages:ZJSHL-CH-009-P-0096`
  - after：`safe:main_passages:ZJSHL-CH-013-P-0008`, `safe:main_passages:ZJSHL-CH-020-P-0002`, `safe:main_passages:ZJSHL-CH-009-P-0051`, `safe:main_passages:ZJSHL-CH-009-P-0098`, `safe:main_passages:ZJSHL-CH-008-P-0246`
- `review_materials`
  - before：`full:passages:ZJSHL-CH-006-P-0120`, `full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`
  - after：`full:ambiguous_passages:ZJSHL-CH-006-P-0120`, `full:passages:ZJSHL-CH-010-P-0137`

### Final 输出

- `answer_mode`
  - before：`strong`
  - after：`strong`
- `answer_text`

before:

```text
根据主依据，直接相关的主条如下：
1. 太阴病脉浮者，可发汗，宜桂枝汤。赵本有「桂枝汤方」详见卷二
2. 发汗多，亡阳谵语者，不可下，与柴胡桂枝汤和其荣卫，以通津液，后自愈。赵本有「柴胡桂枝汤方」详见卷十
3. 太阳赵本有「桂枝汤方」详见本书卷二病，外证未解，脉浮弱者，当以汗解，宜桂枝汤。
```

after:

```text
从现有直接归类句看，可以把“桂枝汤”看作“发汗药”。
直接依据：桂枝汤者，发汗药也。
```

- `definition_priority_debug`
  - family：`category_membership_yesno`
  - selected evidence type：`subject_predicate_definition`
- 是否从“主条直出”改善为“基于依据解释”：`是`

### 观察

- raw retrieval 里原本就已经有正确的句子，只是一直没有被裁成 primary。
- 本轮把 yes/no 归类问法从“可发汗场景堆叠”修成了“直接归类句回答”。

## Query 3: 太阳病是什么

### Raw Top Candidates

- before / after 一致：
  - `safe:main_passages:ZJSHL-CH-007-P-0157`
  - `safe:chunks:ZJSHL-CK-M-0257`
  - `safe:main_passages:ZJSHL-CH-008-P-0195`
  - `full:passages:ZJSHL-CH-009-P-0306`
  - `safe:chunks:ZJSHL-CK-M-0299`
  - `safe:main_passages:ZJSHL-CH-009-P-0002`

### Evidence 变化

- `primary_evidence`
  - before：`safe:main_passages:ZJSHL-CH-008-P-0191`
  - after：`safe:main_passages:ZJSHL-CH-008-P-0191`
- `secondary_evidence`
  - before / after：`safe:main_passages:ZJSHL-CH-008-P-0193`, `safe:main_passages:ZJSHL-CH-008-P-0195`, `safe:main_passages:ZJSHL-CH-009-P-0002`, `safe:main_passages:ZJSHL-CH-008-P-0220`, `safe:main_passages:ZJSHL-CH-007-P-0157`

### Final 输出

- `answer_mode`
  - before：`strong`
  - after：`strong`
- `answer_text`
  - before / after 一致：

```text
书中对“太阳病”的提纲性表述，可先看“太阳之为病，脉浮，头项强痛而恶寒。”
主依据条文：太阳之为病，脉浮，头项强痛而恶寒。
其余相关条文可再看补充依据，用来展开外证、分类或治法，但不替代这条提纲句。
```

- 是否从“主条直出”改善为“基于依据解释”：`本来就已经是`

### 观察

- `definition_outline_query` 既有路径保持不变。
- 这是本轮“无明显外溢破坏”的第一条回归证据。

## Query 4: 竹叶石膏汤方有什么作用

### Raw Top Candidates

- before / after 一致：
  - `full:ambiguous_passages:ZJSHL-CH-017-P-0064`
  - `safe:main_passages:ZJSHL-CH-017-P-0063`
  - `safe:chunks:ZJSHL-CK-M-0922`
  - `full:passages:ZJSHL-CH-017-P-0063`
  - `safe:main_passages:ZJSHL-CH-017-P-0065`
  - `full:passages:ZJSHL-CH-017-P-0065`

### Evidence 变化

- `primary_evidence`
  - before：`safe:main_passages:ZJSHL-CH-017-P-0063`
  - after：`safe:main_passages:ZJSHL-CH-017-P-0063`
- `secondary_evidence`
  - before / after：`safe:main_passages:ZJSHL-CH-017-P-0065`

### Final 输出

- `answer_mode`
  - before：`strong`
  - after：`strong`
- `answer_text`
  - before / after 一致：

```text
根据当前主依据，竹叶石膏汤在书中的直接使用语境，是“伤寒解后，虚羸少气，气逆欲吐”。
也就是说，它更偏向用于伤寒解后，虚羸少气，气逆欲吐这类情况。
依据条文：伤寒解后，虚羸少气，气逆欲吐者，赵本无「者」字竹叶石膏汤主之。
补充方文：竹叶石膏汤方：竹叶二把。辛平 石膏一斤。甘寒 半夏半升，洗。辛温 人参三。赵本作「二」两。
```

- 是否从“主条直出”改善为“基于依据解释”：`本来就已经是`

### 观察

- `formula_effect_query` 既有路径保持不变。
- 这是本轮“无明显外溢破坏”的第二条回归证据。

## 结论

### 1. 本轮是否只改了 primary / answer assembly bottleneck

`是`

证据：

- `raw_top_candidates` before / after 基本一致
- 变化主要发生在 `primary_evidence` 与 `answer_text`
- 这符合“不要大改 rerank 主体”的约束

### 2. 最核心的修复是否生效

`是`

具体表现：

- `什么是发汗药` 不再由明显无关主条占 primary
- `桂枝汤是发汗药吗` 能直接回到“桂枝汤者，发汗药也”
- 系统开始出现“基于依据解释”的答案，而不是纯直出怪条

### 3. 规则是否过于针对单个 query

`否`

原因：

- 本轮按 query family 识别
- 规则用配置表达为 query pattern + evidence type preference
- 未写 `发汗药` 特判
- 未写 `太阳病` 特判
- 未按 query id 打补丁

### 4. 当前边界

- 这仍然是一个很小的 assembler 侧实验
- 目前只覆盖定义 / 术语 / 归类这一小类问法
- 对这类问法，允许严格命中的 `passages` 参与 primary 竞争
- annotation / annotation_links 仍然完全不参与
