# AHV Adversarial Failures v1

## Before-Fix Failures

- fail_count_before_fix: `20`
- wrong_ahv_primary_hit_count: `2`
- wrong_term_normalization_count: `18`
- disabled_alias_still_hit_count: `2`
- non_definition_intent_hijack_count: `8`

| query_id | query_type | query | matched_ahv_terms | ahv_primary_terms | fail_reason |
| --- | --- | --- | --- | --- | --- |
| similar_05 | similar_concept_false_trigger | 刚痓和柔痓有什么不同 | 刚痓,柔痓 | - | wrong AHV term normalization: 刚痓,柔痓 |
| similar_06 | similar_concept_false_trigger | 柔痓和痓病是一回事吗 | 柔痓,痓病 | - | wrong AHV term normalization: 柔痓,痓病 |
| similar_07 | similar_concept_false_trigger | 痉病和痓病是同一个词吗 | 痓病 | - | wrong AHV term normalization: 痓病 |
| similar_09 | similar_concept_false_trigger | 结脉和促脉有什么区别 | 结脉,促脉 | - | wrong AHV term normalization: 结脉,促脉 |
| similar_11 | similar_concept_false_trigger | 滑脉和革脉有什么不同 | 滑脉,革脉 | - | wrong AHV term normalization: 滑脉,革脉 |
| similar_14 | similar_concept_false_trigger | 劳复和食复一样吗 | 劳复,食复 | - | wrong AHV term normalization: 劳复,食复 |
| similar_17 | similar_concept_false_trigger | 伤寒和温病有什么区别 | 伤寒,温病 | - | wrong AHV term normalization: 伤寒,温病 |
| similar_18 | similar_concept_false_trigger | 伤寒和暑病有什么区别 | 伤寒,暑病 | - | wrong AHV term normalization: 伤寒,暑病 |
| similar_19 | similar_concept_false_trigger | 伤寒和冬温有什么区别 | 伤寒,冬温 | - | wrong AHV term normalization: 伤寒,冬温 |
| similar_20 | similar_concept_false_trigger | 太阳病和伤寒是一回事吗 | 太阳病,伤寒 | - | wrong AHV term normalization: 太阳病,伤寒 |
| disabled_alias_02 | disabled_alias_recheck | 暑病者是什么意思 | - | 暑病 | wrong AHV primary hit: 暑病 |
| disabled_alias_03 | disabled_alias_recheck | 寒疫是什么意思 | - | 时行寒疫 | wrong AHV primary hit: 时行寒疫 |
| non_definition_01 | non_definition_intent | 太阳病有哪些方？ | 太阳病 | - | wrong AHV term normalization: 太阳病 |
| non_definition_02 | non_definition_intent | 伤寒怎么治疗？ | 伤寒 | - | wrong AHV term normalization: 伤寒 |
| non_definition_03 | non_definition_intent | 温病与伤寒如何区分？ | 温病,伤寒 | - | wrong AHV term normalization: 温病,伤寒 |
| non_definition_04 | non_definition_intent | 霍乱用什么方？ | 霍乱 | - | wrong AHV term normalization: 霍乱 |
| non_definition_05 | non_definition_intent | 劳复应该怎么处理？ | 劳复 | - | wrong AHV term normalization: 劳复 |
| non_definition_06 | non_definition_intent | 食复怎么治？ | 食复 | - | wrong AHV term normalization: 食复 |
| non_definition_07 | non_definition_intent | 结脉有什么方？ | 结脉 | - | wrong AHV term normalization: 结脉 |
| non_definition_08 | non_definition_intent | 革脉预后如何？ | 革脉 | - | wrong AHV term normalization: 革脉 |

## After-Fix Status

- fail_count_after_fix: `0`
- wrong_ahv_primary_hit_count: `0`
- wrong_term_normalization_count: `0`
- disabled_alias_still_hit_count: `0`
- non_definition_intent_hijack_count: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`

No remaining adversarial failures are marked as routing/intent debt in this pass.
