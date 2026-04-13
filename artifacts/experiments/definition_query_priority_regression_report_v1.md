# definition_query_priority_regression_report_v1

## 实验设置

- 开关：`TCM_ENABLE_DEFINITION_QUERY_PRIORITY_RULES_V1`
- before：`TCM_ENABLE_DEFINITION_QUERY_PRIORITY_RULES_V1=0`
- after：`TCM_ENABLE_DEFINITION_QUERY_PRIORITY_RULES_V1=1`
- 本轮额外边界收紧：
  - `definition_query_priority_rules_v1.json` 新增 `组成` / `药味` block hints。
  - `what_means` 对六经提纲主题新增 outline-topic guard，并补上 `什么意思` / `是什么意思` 的后缀消歧，避免短后缀误绕过 guard。
- 未变更：raw retrieval candidate 生成、annotation / annotation_links、formula_effect 专题逻辑、comparison 专题逻辑。

## 总体摘要

- family query count: `16`
- total query count (含 cross-family controls): `20`
- positive hit: `7/7`
- boundary hold: `6/6`
- negative hold: `3/3`
- cross-family control hold: `4/4`

## Family: what_is

### Query: 什么是发汗药

- regression_tag: `positive`
- expected_primary_type: `term_membership_sentence`
- expected_behavior_note: 应把“桂枝汤者，发汗药也”这类归类句抬成 primary，而不是继续让发汗语境主条占住 primary。
- route: before=`standard`, after=`definition_priority:what_is`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "chunks:safe:chunks:ZJSHL-CK-M-0358", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0123", "chunks:safe:chunks:ZJSHL-CK-M-0948", "main_passages:safe:main_passages:ZJSHL-CH-019-P-0109"]`
- raw_top_candidates_after: `["passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "chunks:safe:chunks:ZJSHL-CK-M-0358", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0123", "chunks:safe:chunks:ZJSHL-CK-M-0948", "main_passages:safe:main_passages:ZJSHL-CH-019-P-0109"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-010-P-0137"]`
- primary_evidence_after: `["passages:full:passages:ZJSHL-CH-006-P-0120"]`
- after_selected_evidence_type: `term_membership_sentence`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`based_on_evidence_explanation`
- improved_to_evidence_explanation: `True`
- risk_summary: 命中预期 evidence type

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

### Query: 阳结是什么

- regression_tag: `positive`
- expected_primary_type: `term_membership_sentence`
- expected_behavior_note: 应验证 what_is 不是只对“发汗药”生效，能把“名曰阳结也”类归类句抬成 primary。
- route: before=`standard`, after=`definition_priority:what_is`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["annotations:full:annotations:ZJSHL-CH-003-P-0005", "chunks:safe:chunks:ZJSHL-CK-M-0008", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0017", "chunks:safe:chunks:ZJSHL-CK-M-0002", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0004", "chunks:safe:chunks:ZJSHL-CK-M-0486"]`
- raw_top_candidates_after: `["annotations:full:annotations:ZJSHL-CH-003-P-0005", "chunks:safe:chunks:ZJSHL-CK-M-0008", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0017", "chunks:safe:chunks:ZJSHL-CK-M-0002", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0004", "chunks:safe:chunks:ZJSHL-CK-M-0486"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-003-P-0004", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0017", "main_passages:safe:main_passages:ZJSHL-CH-010-P-0019"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-003-P-0017"]`
- after_selected_evidence_type: `term_membership_sentence`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`based_on_evidence_explanation`
- improved_to_evidence_explanation: `True`
- risk_summary: 命中预期 evidence type

before:

```text
根据主依据，直接相关的主条如下：
1. 问曰：脉有阳结阴结者，何以别之。答曰：其脉浮而数，能食，不大便者，此为实，名曰阳结也。期十七日当剧。其脉沉而迟，不能食，身体重，大便反硬，名曰阴结也。期十四日当剧。
2. 脉赵本注：「一云秋脉」蔼蔼，如车盖者，名曰阳结也。
3. 邪在表则见阳脉，邪在里则见阴脉，邪气内陷，动数之脉所以变迟，而浮脉独不变者，以邪结胸中，上焦阳结，脉不得而沉也。客气者，外邪乘胃中空虚入里，结于胸膈，膈中拒痛者，客气动膈也。《金匮要略》曰：短气不足以息者，实也。短气躁医统本作「躁」烦，心中...
```

after:

```text
书中并不是先给“阳结”下一条抽象定义，现有可直接对应该问法的归类句是“脉蔼蔼，如车盖者，名曰阳结也。”。
也就是说，这里是用具体对象的归属来说明“阳结”这一类。
补充说明：问曰：脉有阳结阴结者，何以别之。
```

### Query: 坏病是什么

- regression_tag: `positive`
- expected_primary_type: `term_membership_sentence`
- expected_behavior_note: 应优先利用“谓之坏病”类解释句，而不是退回泛检索主条直出。
- route: before=`standard`, after=`definition_priority:what_is`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["passages:full:passages:ZJSHL-CH-008-P-0227", "passages:full:passages:ZJSHL-CH-008-P-0226", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-008-P-0226"]`
- raw_top_candidates_after: `["passages:full:passages:ZJSHL-CH-008-P-0227", "passages:full:passages:ZJSHL-CH-008-P-0226", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-008-P-0226"]`
- primary_evidence_before: `[]`
- primary_evidence_after: `["passages:full:passages:ZJSHL-CH-008-P-0227"]`
- after_selected_evidence_type: `term_membership_sentence`
- hit_expected_evidence_type: `True`
- answer_mode: before=`weak_with_review_notice`, after=`strong`
- answer_style: before=`weak_notice_answer`, after=`based_on_evidence_explanation`
- improved_to_evidence_explanation: `True`
- risk_summary: 命中预期 evidence type

before:

```text
正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前仅检索到风险层材料：太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。不可复与桂枝汤。审观脉证，知犯何逆，而治之逆者，随所逆而救之。
```

after:

```text
书中并不是先给“坏病”下一条抽象定义，现有可直接对应该问法的归类句是“太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。”。
也就是说，这里是用具体对象的归属来说明“坏病”这一类。
```

### Query: 发汗药的组成是什么

- regression_tag: `boundary`
- expected_primary_type: `none`
- expected_behavior_note: “组成是什么”属于边界句式，不应再被 what_is family 吸入 definition priority。
- route: before=`standard`, after=`standard`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "passages:full:passages:ZJSHL-CH-006-P-0127", "chunks:safe:chunks:ZJSHL-CK-M-0358", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0123", "chunks:safe:chunks:ZJSHL-CK-M-0356"]`
- raw_top_candidates_after: `["passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "passages:full:passages:ZJSHL-CH-006-P-0127", "chunks:safe:chunks:ZJSHL-CK-M-0358", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0123", "chunks:safe:chunks:ZJSHL-CK-M-0356"]`
- primary_evidence_before: `[]`
- primary_evidence_after: `[]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`weak_with_review_notice`, after=`weak_with_review_notice`
- answer_style: before=`weak_notice_answer`, after=`weak_notice_answer`
- improved_to_evidence_explanation: `False`
- risk_summary: 未观察到 definition priority 外溢

before:

```text
正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前可先参考辅助材料：发汗，病不解，反恶寒者，虚故也，芍药甘草附子汤主之。
```

after:

```text
正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前可先参考辅助材料：发汗，病不解，反恶寒者，虚故也，芍药甘草附子汤主之。
```

## Family: what_means

### Query: 发汗药是什么意思

- regression_tag: `positive`
- expected_primary_type: `exact_term_explanation`
- expected_behavior_note: 应优先选中“发汗药，须温暖服者...”这类直接解释句，并把答案从 weak/辅助材料提升到基于依据解释。
- route: before=`standard`, after=`definition_priority:what_means`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["passages:full:passages:ZJSHL-CH-006-P-0127", "passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "chunks:safe:chunks:ZJSHL-CK-M-0358", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0123", "chunks:safe:chunks:ZJSHL-CK-M-0378"]`
- raw_top_candidates_after: `["passages:full:passages:ZJSHL-CH-006-P-0127", "passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "chunks:safe:chunks:ZJSHL-CK-M-0358", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0123", "chunks:safe:chunks:ZJSHL-CK-M-0378"]`
- primary_evidence_before: `[]`
- primary_evidence_after: `["passages:full:passages:ZJSHL-CH-006-P-0127"]`
- after_selected_evidence_type: `exact_term_explanation`
- hit_expected_evidence_type: `True`
- answer_mode: before=`weak_with_review_notice`, after=`strong`
- answer_style: before=`weak_notice_answer`, after=`based_on_evidence_explanation`
- improved_to_evidence_explanation: `True`
- risk_summary: 命中预期 evidence type

before:

```text
正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前可先参考辅助材料：发汗，病不解，反恶寒者，虚故也，芍药甘草附子汤主之。
```

after:

```text
从现有解释句看，“发汗药”可先参考“发汗药，须温暖服者，易为发散也。”来理解。
直接依据：发汗药，须温暖服者，易为发散也。
补充说明：桂枝汤者，发汗药也。承气汤者，下药也。
```

### Query: 阳结是什么意思

- regression_tag: `positive`
- expected_primary_type: `term_membership_sentence`
- expected_behavior_note: 应验证 what_means 对脉象类术语也能稳定选中“名曰阳结也”类句子。
- route: before=`standard`, after=`definition_priority:what_means`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["annotations:full:annotations:ZJSHL-CH-003-P-0005", "chunks:safe:chunks:ZJSHL-CK-M-0008", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0017", "chunks:safe:chunks:ZJSHL-CK-M-0002", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0004", "chunks:safe:chunks:ZJSHL-CK-M-0486"]`
- raw_top_candidates_after: `["annotations:full:annotations:ZJSHL-CH-003-P-0005", "chunks:safe:chunks:ZJSHL-CK-M-0008", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0017", "chunks:safe:chunks:ZJSHL-CK-M-0002", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0004", "chunks:safe:chunks:ZJSHL-CK-M-0486"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-003-P-0017", "main_passages:safe:main_passages:ZJSHL-CH-003-P-0004", "main_passages:safe:main_passages:ZJSHL-CH-010-P-0019"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-003-P-0017"]`
- after_selected_evidence_type: `term_membership_sentence`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`based_on_evidence_explanation`
- improved_to_evidence_explanation: `True`
- risk_summary: 命中预期 evidence type

before:

```text
根据主依据，直接相关的主条如下：
1. 脉赵本注：「一云秋脉」蔼蔼，如车盖者，名曰阳结也。
2. 问曰：脉有阳结阴结者，何以别之。答曰：其脉浮而数，能食，不大便者，此为实，名曰阳结也。期十七日当剧。其脉沉而迟，不能食，身体重，大便反硬，名曰阴结也。期十四日当剧。
3. 邪在表则见阳脉，邪在里则见阴脉，邪气内陷，动数之脉所以变迟，而浮脉独不变者，以邪结胸中，上焦阳结，脉不得而沉也。客气者，外邪乘胃中空虚入里，结于胸膈，膈中拒痛者，客气动膈也。《金匮要略》曰：短气不足以息者，实也。短气躁医统本作「躁」烦，心中...
```

after:

```text
从现有解释句看，“阳结”可先参考“脉蔼蔼，如车盖者，名曰阳结也。”来理解。
直接依据：脉蔼蔼，如车盖者，名曰阳结也。
补充说明：问曰：脉有阳结阴结者，何以别之。
```

### Query: 坏病是什么意思

- regression_tag: `positive`
- expected_primary_type: `term_membership_sentence`
- expected_behavior_note: 应验证“谓之X”类术语解释可被 what_means 稳定抬升。
- route: before=`standard`, after=`definition_priority:what_means`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["passages:full:passages:ZJSHL-CH-008-P-0227", "passages:full:passages:ZJSHL-CH-008-P-0226", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-008-P-0226"]`
- raw_top_candidates_after: `["passages:full:passages:ZJSHL-CH-008-P-0227", "passages:full:passages:ZJSHL-CH-008-P-0226", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-008-P-0226"]`
- primary_evidence_before: `[]`
- primary_evidence_after: `["passages:full:passages:ZJSHL-CH-008-P-0227"]`
- after_selected_evidence_type: `term_membership_sentence`
- hit_expected_evidence_type: `True`
- answer_mode: before=`weak_with_review_notice`, after=`strong`
- answer_style: before=`weak_notice_answer`, after=`based_on_evidence_explanation`
- improved_to_evidence_explanation: `True`
- risk_summary: 命中预期 evidence type

before:

```text
正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前仅检索到风险层材料：太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。不可复与桂枝汤。审观脉证，知犯何逆，而治之逆者，随所逆而救之。
```

after:

```text
从现有解释句看，“坏病”可先参考“太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。”来理解。
直接依据：太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。
```

### Query: 太阳病是什么意思

- regression_tag: `boundary`
- expected_primary_type: `none`
- expected_behavior_note: 已有六经提纲主题不应被 what_means 抢走；本轮应验证 outline-topic guard 能阻止 definition priority 外溢。
- route: before=`standard`, after=`standard`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["chunks:safe:chunks:ZJSHL-CK-M-0257", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0195", "main_passages:safe:main_passages:ZJSHL-CH-007-P-0157", "chunks:safe:chunks:ZJSHL-CK-M-0465", "passages:full:passages:ZJSHL-CH-009-P-0306", "chunks:safe:chunks:ZJSHL-CK-M-0272"]`
- raw_top_candidates_after: `["chunks:safe:chunks:ZJSHL-CK-M-0257", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0195", "main_passages:safe:main_passages:ZJSHL-CH-007-P-0157", "chunks:safe:chunks:ZJSHL-CK-M-0465", "passages:full:passages:ZJSHL-CH-009-P-0306", "chunks:safe:chunks:ZJSHL-CK-M-0272"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-009-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0220", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0195"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-009-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0220", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0195"]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`primary_clause_dump`
- improved_to_evidence_explanation: `False`
- risk_summary: 未观察到 definition priority 外溢

before:

```text
根据主依据，直接相关的主条如下：
1. 太阳病，项背强几几，无汗，恶风，葛根汤主之。
2. 太阳病，头痛发热，汗出恶风者，赵本无「者」字桂枝汤主之。
3. 太阳病，或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，名曰赵本作「为」伤寒。
```

after:

```text
根据主依据，直接相关的主条如下：
1. 太阳病，项背强几几，无汗，恶风，葛根汤主之。
2. 太阳病，头痛发热，汗出恶风者，赵本无「者」字桂枝汤主之。
3. 太阳病，或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，名曰赵本作「为」伤寒。
```

## Family: category_membership_yesno

### Query: 桂枝汤是发汗药吗

- regression_tag: `positive`
- expected_primary_type: `subject_predicate_definition`
- expected_behavior_note: 应直接回到“桂枝汤者，发汗药也”，避免继续输出“可发汗语境”主条堆叠。
- route: before=`standard`, after=`definition_priority:category_membership_yesno`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "chunks:safe:chunks:ZJSHL-CK-M-0720", "main_passages:safe:main_passages:ZJSHL-CH-013-P-0008", "chunks:safe:chunks:ZJSHL-CK-M-0952", "main_passages:safe:main_passages:ZJSHL-CH-020-P-0002"]`
- raw_top_candidates_after: `["passages:full:passages:ZJSHL-CH-006-P-0120", "ambiguous_passages:full:ambiguous_passages:ZJSHL-CH-006-P-0120", "chunks:safe:chunks:ZJSHL-CK-M-0720", "main_passages:safe:main_passages:ZJSHL-CH-013-P-0008", "chunks:safe:chunks:ZJSHL-CK-M-0952", "main_passages:safe:main_passages:ZJSHL-CH-020-P-0002"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-013-P-0008", "main_passages:safe:main_passages:ZJSHL-CH-020-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0051"]`
- primary_evidence_after: `["passages:full:passages:ZJSHL-CH-006-P-0120"]`
- after_selected_evidence_type: `subject_predicate_definition`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`based_on_evidence_explanation`
- improved_to_evidence_explanation: `True`
- risk_summary: 命中预期 evidence type

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

### Query: 承气汤是下药吗

- regression_tag: `boundary`
- expected_primary_type: `none`
- expected_behavior_note: 当前 raw retrieval 若没带回“承气汤者，下药也”，应保持 fallback，不要为命中 family 硬抢 primary。
- route: before=`standard`, after=`definition_priority:category_membership_yesno`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["chunks:safe:chunks:ZJSHL-CK-M-1004", "main_passages:safe:main_passages:ZJSHL-CH-024-P-0067", "chunks:safe:chunks:ZJSHL-CK-M-0887", "main_passages:safe:main_passages:ZJSHL-CH-015-P-0316", "chunks:safe:chunks:ZJSHL-CK-F-0005", "chunks:safe:chunks:ZJSHL-CK-F-0054"]`
- raw_top_candidates_after: `["chunks:safe:chunks:ZJSHL-CK-M-1004", "main_passages:safe:main_passages:ZJSHL-CH-024-P-0067", "chunks:safe:chunks:ZJSHL-CK-M-0887", "main_passages:safe:main_passages:ZJSHL-CH-015-P-0316", "chunks:safe:chunks:ZJSHL-CK-F-0005", "chunks:safe:chunks:ZJSHL-CK-F-0054"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-015-P-0316", "main_passages:safe:main_passages:ZJSHL-CH-024-P-0067", "main_passages:safe:main_passages:ZJSHL-CH-011-P-0086"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-015-P-0316", "main_passages:safe:main_passages:ZJSHL-CH-024-P-0067", "main_passages:safe:main_passages:ZJSHL-CH-011-P-0086"]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`primary_clause_dump`
- improved_to_evidence_explanation: `False`
- risk_summary: family 命中但保持 fallback，未观察到 primary 误吸

before:

```text
根据主依据，直接相关的主条如下：
1. 下利，谵语者，有燥屎也，宜小承气汤。赵本有「小承气汤方」详见卷五
2. 下利，脉反滑，当有所去，下之赵本无「之」字乃愈，宜大承气汤。
3. 阳明病，谵语发潮热，脉滑而疾者，小承气汤主之。因与承气汤一升，腹中转失赵本无「失」字气者，更服一升；若不转失气，赵本作「转气者」勿更与之。明日赵本有「又」字不大便，脉反微涩者，里虚也，为难治，不可更与承气汤也。
```

after:

```text
根据主依据，直接相关的主条如下：
1. 下利，谵语者，有燥屎也，宜小承气汤。赵本有「小承气汤方」详见卷五
2. 下利，脉反滑，当有所去，下之赵本无「之」字乃愈，宜大承气汤。
3. 阳明病，谵语发潮热，脉滑而疾者，小承气汤主之。因与承气汤一升，腹中转失赵本无「失」字气者，更服一升；若不转失气，赵本作「转气者」勿更与之。明日赵本有「又」字不大便，脉反微涩者，里虚也，为难治，不可更与承气汤也。
```

### Query: 高血压能用桂枝汤吗

- regression_tag: `negative`
- expected_primary_type: `none`
- expected_behavior_note: 现代病名疗效类应被统一拒答边界拦截，不应落入归类 yes/no family。
- route: before=`policy_refusal`, after=`policy_refusal`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["chunks:safe:chunks:ZJSHL-CK-M-0720", "main_passages:safe:main_passages:ZJSHL-CH-013-P-0008", "chunks:safe:chunks:ZJSHL-CK-M-0281", "chunks:safe:chunks:ZJSHL-CK-M-0911", "main_passages:safe:main_passages:ZJSHL-CH-016-P-0034", "chunks:safe:chunks:ZJSHL-CK-M-0292"]`
- raw_top_candidates_after: `["chunks:safe:chunks:ZJSHL-CK-M-0720", "main_passages:safe:main_passages:ZJSHL-CH-013-P-0008", "chunks:safe:chunks:ZJSHL-CK-M-0281", "chunks:safe:chunks:ZJSHL-CK-M-0911", "main_passages:safe:main_passages:ZJSHL-CH-016-P-0034", "chunks:safe:chunks:ZJSHL-CK-M-0292"]`
- primary_evidence_before: `[]`
- primary_evidence_after: `[]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`refuse`, after=`refuse`
- answer_style: before=`policy_refusal_answer`, after=`policy_refusal_answer`
- improved_to_evidence_explanation: `False`
- risk_summary: 未观察到 definition priority 外溢

before:

```text
该问题超出《伤寒论》单书研读支持边界，暂不提供诊疗、剂量、现代病名疗效或跨书价值判断。
```

after:

```text
该问题超出《伤寒论》单书研读支持边界，暂不提供诊疗、剂量、现代病名疗效或跨书价值判断。
```

### Query: 我发烧能用桂枝汤吗

- regression_tag: `negative`
- expected_primary_type: `none`
- expected_behavior_note: 个体化用药 yes/no 应被拒答边界拦截，不应进入归类 primary prioritization。
- route: before=`policy_refusal`, after=`policy_refusal`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["chunks:safe:chunks:ZJSHL-CK-M-0720", "main_passages:safe:main_passages:ZJSHL-CH-013-P-0008", "chunks:safe:chunks:ZJSHL-CK-M-0952", "main_passages:safe:main_passages:ZJSHL-CH-020-P-0002", "chunks:safe:chunks:ZJSHL-CK-M-0281", "chunks:safe:chunks:ZJSHL-CK-M-0292"]`
- raw_top_candidates_after: `["chunks:safe:chunks:ZJSHL-CK-M-0720", "main_passages:safe:main_passages:ZJSHL-CH-013-P-0008", "chunks:safe:chunks:ZJSHL-CK-M-0952", "main_passages:safe:main_passages:ZJSHL-CH-020-P-0002", "chunks:safe:chunks:ZJSHL-CK-M-0281", "chunks:safe:chunks:ZJSHL-CK-M-0292"]`
- primary_evidence_before: `[]`
- primary_evidence_after: `[]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`refuse`, after=`refuse`
- answer_style: before=`policy_refusal_answer`, after=`policy_refusal_answer`
- improved_to_evidence_explanation: `False`
- risk_summary: 未观察到 definition priority 外溢

before:

```text
该问题超出《伤寒论》单书研读支持边界，暂不提供诊疗、剂量、现代病名疗效或跨书价值判断。
```

after:

```text
该问题超出《伤寒论》单书研读支持边界，暂不提供诊疗、剂量、现代病名疗效或跨书价值判断。
```

## Family: category_membership_open

### Query: 桂枝汤是什么药

- regression_tag: `boundary`
- expected_primary_type: `none`
- expected_behavior_note: 当前 open family 更受 raw retrieval 约束；若未召回归类句，应 fallback，而不是抢错 primary。
- route: before=`standard`, after=`definition_priority:category_membership_open`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "chunks:safe:chunks:ZJSHL-CK-F-0001", "chunks:safe:chunks:ZJSHL-CK-F-0097", "main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "chunks:safe:chunks:ZJSHL-CK-F-0107", "chunks:safe:chunks:ZJSHL-CK-F-0108"]`
- raw_top_candidates_after: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "chunks:safe:chunks:ZJSHL-CK-F-0001", "chunks:safe:chunks:ZJSHL-CK-F-0097", "main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "chunks:safe:chunks:ZJSHL-CK-F-0107", "chunks:safe:chunks:ZJSHL-CK-F-0108"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-028-P-0004", "main_passages:safe:main_passages:ZJSHL-CH-025-P-0005"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-028-P-0004", "main_passages:safe:main_passages:ZJSHL-CH-025-P-0005"]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`primary_clause_dump`
- improved_to_evidence_explanation: `False`
- risk_summary: family 命中但保持 fallback，未观察到 primary 误吸

before:

```text
根据主依据，直接相关的主条如下：
1. 桂枝加芍药生姜人参新加汤方：于第二卷桂枝汤方内，更加芍药、生姜各一两，人参三两，馀根据桂枝汤法服。
2. 桂枝加芍药汤方：于第二卷桂枝汤方内，更加芍药三两，随医统本作「通」前共六两，馀根据桂枝汤法。
3. 桂枝去芍药汤方：于桂枝汤方内，去芍药，馀根据前法。
```

after:

```text
根据主依据，直接相关的主条如下：
1. 桂枝加芍药生姜人参新加汤方：于第二卷桂枝汤方内，更加芍药、生姜各一两，人参三两，馀根据桂枝汤法服。
2. 桂枝加芍药汤方：于第二卷桂枝汤方内，更加芍药三两，随医统本作「通」前共六两，馀根据桂枝汤法。
3. 桂枝去芍药汤方：于桂枝汤方内，去芍药，馀根据前法。
```

### Query: 桂枝汤属于什么药

- regression_tag: `boundary`
- expected_primary_type: `none`
- expected_behavior_note: 应验证“属于什么药”问法在 raw recall 不足时维持 fallback，不产生过度抢占。
- route: before=`standard`, after=`definition_priority:category_membership_open`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "chunks:safe:chunks:ZJSHL-CK-F-0097", "main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "chunks:safe:chunks:ZJSHL-CK-F-0108", "main_passages:safe:main_passages:ZJSHL-CH-028-P-0004", "chunks:safe:chunks:ZJSHL-CK-F-0090"]`
- raw_top_candidates_after: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "chunks:safe:chunks:ZJSHL-CK-F-0097", "main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "chunks:safe:chunks:ZJSHL-CK-F-0108", "main_passages:safe:main_passages:ZJSHL-CH-028-P-0004", "chunks:safe:chunks:ZJSHL-CK-F-0090"]`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-028-P-0004", "main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-025-P-0005"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-028-P-0004", "main_passages:safe:main_passages:ZJSHL-CH-026-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-025-P-0005"]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`primary_clause_dump`, after=`primary_clause_dump`
- improved_to_evidence_explanation: `False`
- risk_summary: family 命中但保持 fallback，未观察到 primary 误吸

before:

```text
根据主依据，直接相关的主条如下：
1. 桂枝加芍药汤方：于第二卷桂枝汤方内，更加芍药三两，随医统本作「通」前共六两，馀根据桂枝汤法。
2. 桂枝加芍药生姜人参新加汤方：于第二卷桂枝汤方内，更加芍药、生姜各一两，人参三两，馀根据桂枝汤法服。
3. 桂枝去芍药汤方：于桂枝汤方内，去芍药，馀根据前法。
```

after:

```text
根据主依据，直接相关的主条如下：
1. 桂枝加芍药汤方：于第二卷桂枝汤方内，更加芍药三两，随医统本作「通」前共六两，馀根据桂枝汤法。
2. 桂枝加芍药生姜人参新加汤方：于第二卷桂枝汤方内，更加芍药、生姜各一两，人参三两，馀根据桂枝汤法服。
3. 桂枝去芍药汤方：于桂枝汤方内，去芍药，馀根据前法。
```

### Query: 承气汤是什么药

- regression_tag: `boundary`
- expected_primary_type: `none`
- expected_behavior_note: 应验证 open family 的当前短板主要是 raw recall，不是 assembler 乱抬 primary。
- route: before=`standard`, after=`definition_priority:category_membership_open`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `["main_passages:safe:main_passages:ZJSHL-CH-009-P-0261", "main_passages:safe:main_passages:ZJSHL-CH-011-P-0068", "chunks:safe:chunks:ZJSHL-CK-F-0029", "chunks:safe:chunks:ZJSHL-CK-F-0005", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0264", "main_passages:safe:main_passages:ZJSHL-CH-015-P-0316"]`
- raw_top_candidates_after: `["main_passages:safe:main_passages:ZJSHL-CH-009-P-0261", "main_passages:safe:main_passages:ZJSHL-CH-011-P-0068", "chunks:safe:chunks:ZJSHL-CK-F-0029", "chunks:safe:chunks:ZJSHL-CK-F-0005", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0264", "main_passages:safe:main_passages:ZJSHL-CH-015-P-0316"]`
- primary_evidence_before: `[]`
- primary_evidence_after: `[]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`weak_with_review_notice`, after=`weak_with_review_notice`
- answer_style: before=`weak_notice_answer`, after=`weak_notice_answer`
- improved_to_evidence_explanation: `False`
- risk_summary: family 命中但保持 fallback，未观察到 primary 误吸

before:

```text
正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前可先参考辅助材料：潮热者实，得大便微硬者，便可攻之；若便不硬者，则热未成实，虽有潮热亦未可攻。若不大便六七日，恐有燥屎，当先与小承气汤渍之，如有燥屎，小承气汤药势缓，不能宣泄，必转气下失；若不转失气，是胃中无燥屎，但肠间少硬尔，止初头硬，后必溏，攻之则虚其胃...
```

after:

```text
正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前可先参考辅助材料：潮热者实，得大便微硬者，便可攻之；若便不硬者，则热未成实，虽有潮热亦未可攻。若不大便六七日，恐有燥屎，当先与小承气汤渍之，如有燥屎，小承气汤药势缓，不能宣泄，必转气下失；若不转失气，是胃中无燥屎，但肠间少硬尔，止初头硬，后必溏，攻之则虚其胃...
```

### Query: 神丹是什么药

- regression_tag: `negative`
- expected_primary_type: `none`
- expected_behavior_note: 非方名药类问法也应保持 fallback；若 raw 未召回“神丹者，发汗之药也”，不应输出伪确定答案。
- route: before=`standard`, after=`definition_priority:category_membership_open`
- raw_top_candidates_changed: `False`
- raw_top_candidates_before: `[]`
- raw_top_candidates_after: `[]`
- primary_evidence_before: `[]`
- primary_evidence_after: `[]`
- after_selected_evidence_type: `none`
- hit_expected_evidence_type: `True`
- answer_mode: before=`refuse`, after=`refuse`
- answer_style: before=`other`, after=`other`
- improved_to_evidence_explanation: `False`
- risk_summary: family 命中但保持 fallback，未观察到 primary 误吸

before:

```text
当前未检索到足以支撑回答的依据，暂不提供答案。
```

after:

```text
当前未检索到足以支撑回答的依据，暂不提供答案。
```

## Cross-Family Controls

### Query: 桂枝汤和麻黄汤有什么区别

- regression_tag: `negative`
- expected_route: `comparison`
- expected_behavior_note: 比较类应保持 comparison 专用路径，不应被 definition priority family 吸入。
- route: before=`comparison`, after=`comparison`
- route_as_expected: `True`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0022"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0022"]`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`other`, after=`other`

after:

```text
从现有方文与相关条文看，桂枝汤方与麻黄汤方在显式组成和相关条文语境上并不相同。
1. 条文语境：桂枝汤方相关条文可见“欲解外者，宜”；麻黄汤方相关条文可见“伤寒脉浮紧，不发汗，因致衄者”。
2. 出处线索：桂枝汤方的方文见“辨太阳病脉证并治法上第五”；麻黄汤方的方文见“辨太阳病脉证并治第六”；桂枝汤方相关条文位于“辨太阳病脉证并治第六”；麻黄汤方相关条文位于“辨太阳病脉证并治第六”。
以上差异仅按当前可见条文与方文整理；若要逐字核对，请继续查看引用。
```

### Query: 太阳病应该怎么办

- regression_tag: `negative`
- expected_route: `general`
- expected_behavior_note: 怎么办类应保持 general 路径，不应被 definition priority 外溢。
- route: before=`general`, after=`general`
- route_as_expected: `True`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0195", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0220"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0195", "main_passages:safe:main_passages:ZJSHL-CH-009-P-0002", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0220"]`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`general_branching_answer`, after=`general_branching_answer`

after:

```text
这是一个总括性问题，书中谈“太阳病”并非只有一个固定治法，需要分情况看。
以下先按当前能稳定抓到的典型分支整理：
1. 先辨伤寒：先看或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，书中把它单列成一个分支，提示“太阳病”并非只有一种证候。 依据：太阳病，或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，名曰赵本作「为」伤寒。
2. 葛根汤这一支：若见项背强几几，无汗，恶风，条文多归到“葛根汤”这一支。 依据：太阳病，项背强几几，无汗，恶风，葛根汤主之。
3. 桂枝汤这一支：若见头痛发热，汗出恶风者，条文多归到“桂枝汤”这一支。 依据：太阳病，头痛发热，汗出恶风者，赵本无「者」字桂枝汤主之。
当前回答只列若干典型分支，不等于穷尽全部“太阳病”处理。
```

### Query: 桂枝汤的组成是什么

- regression_tag: `boundary`
- expected_route: `formula_composition`
- expected_behavior_note: 组成类应保持 formula_composition 专用路径，不应被 what_is 抢走。
- route: before=`formula_composition`, after=`formula_composition`
- route_as_expected: `True`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0219"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-008-P-0217", "main_passages:safe:main_passages:ZJSHL-CH-008-P-0219"]`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`other`, after=`other`

after:

```text
根据当前主依据，桂枝汤方的组成可先按方文直读：
1. 桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温
2. 右伍味，㕮咀。赵本有「三味」二字以水柒升，微火煑取三升，去滓，适寒温，服壹升。服已须臾，歠热稀粥壹升馀，以助药力，温覆令壹时许，遍身漐漐，微似有汗者益佳，不可令如水流漓，病必不除。若壹服汗出病差，停后服，不必尽剂；若不汗，更服，依前法；又不...
```

### Query: 竹叶石膏汤方有什么作用

- regression_tag: `boundary`
- expected_route: `formula_effect`
- expected_behavior_note: 作用类应保持 formula_effect 专用路径，不应被 definition priority family 吸入。
- route: before=`formula_effect`, after=`formula_effect`
- route_as_expected: `True`
- primary_evidence_before: `["main_passages:safe:main_passages:ZJSHL-CH-017-P-0063"]`
- primary_evidence_after: `["main_passages:safe:main_passages:ZJSHL-CH-017-P-0063"]`
- answer_mode: before=`strong`, after=`strong`
- answer_style: before=`other`, after=`other`

after:

```text
根据当前主依据，竹叶石膏汤在书中的直接使用语境，是“伤寒解后，虚羸少气，气逆欲吐”。
也就是说，它更偏向用于伤寒解后，虚羸少气，气逆欲吐这类情况。
依据条文：伤寒解后，虚羸少气，气逆欲吐者，赵本无「者」字竹叶石膏汤主之。
补充方文：竹叶石膏汤方：竹叶二把。辛平 石膏一斤。甘寒 半夏半升，洗。辛温 人参三。赵本作「二」两。
```
