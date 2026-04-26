# AHV2 Adversarial Query Set v1

- query_count: `94`
- query_type_counts: `{"ahv2_canonical_guard": 20, "ahv_v1_guard": 5, "disabled_alias_recheck": 5, "formula_guard": 5, "gold_safe_definition_guard": 5, "negative_unrelated": 10, "non_definition_intent": 10, "partial_word_literal_similarity": 10, "review_only_boundary_guard": 4, "similar_concept_false_trigger": 20}`

| query_id | query_type | query | expected_behavior |
| --- | --- | --- | --- |
| ahv2_canonical_01 | ahv2_canonical_guard | 荣气微是什么意思 | 必须命中 荣气微 的 AHV2 safe definition primary。 |
| ahv2_canonical_02 | ahv2_canonical_guard | 卫气衰是什么意思 | 必须命中 卫气衰 的 AHV2 safe definition primary。 |
| ahv2_canonical_03 | ahv2_canonical_guard | 阳气微是什么意思 | 必须命中 阳气微 的 AHV2 safe definition primary。 |
| ahv2_canonical_04 | ahv2_canonical_guard | 亡血是什么意思 | 必须命中 亡血 的 AHV2 safe definition primary。 |
| ahv2_canonical_05 | ahv2_canonical_guard | 平脉是什么 | 必须命中 平脉 的 AHV2 safe definition primary。 |
| ahv2_canonical_06 | ahv2_canonical_guard | 数脉是什么意思 | 必须命中 数脉 的 AHV2 safe definition primary。 |
| ahv2_canonical_07 | ahv2_canonical_guard | 毛脉是什么 | 必须命中 毛脉 的 AHV2 safe definition primary。 |
| ahv2_canonical_08 | ahv2_canonical_guard | 纯弦脉是什么意思 | 必须命中 纯弦脉 的 AHV2 safe definition primary。 |
| ahv2_canonical_09 | ahv2_canonical_guard | 残贼是什么意思 | 必须命中 残贼 的 AHV2 safe definition primary。 |
| ahv2_canonical_10 | ahv2_canonical_guard | 八邪是什么 | 必须命中 八邪 的 AHV2 safe definition primary。 |
| ahv2_canonical_11 | ahv2_canonical_guard | 湿家是什么 | 必须命中 湿家 的 AHV2 safe definition primary。 |
| ahv2_canonical_12 | ahv2_canonical_guard | 风湿是什么 | 必须命中 风湿 的 AHV2 safe definition primary。 |
| ahv2_canonical_13 | ahv2_canonical_guard | 水逆是什么意思 | 必须命中 水逆 的 AHV2 safe definition primary。 |
| ahv2_canonical_14 | ahv2_canonical_guard | 半表半里证是什么 | 必须命中 半表半里证 的 AHV2 safe definition primary。 |
| ahv2_canonical_15 | ahv2_canonical_guard | 过经是什么意思 | 必须命中 过经 的 AHV2 safe definition primary。 |
| ahv2_canonical_16 | ahv2_canonical_guard | 结胸是什么 | 必须命中 结胸 的 AHV2 safe definition primary。 |
| ahv2_canonical_17 | ahv2_canonical_guard | 阳明病是什么 | 必须命中 阳明病 的 AHV2 safe definition primary。 |
| ahv2_canonical_18 | ahv2_canonical_guard | 太阴病是什么 | 必须命中 太阴病 的 AHV2 safe definition primary。 |
| ahv2_canonical_19 | ahv2_canonical_guard | 少阴病是什么 | 必须命中 少阴病 的 AHV2 safe definition primary。 |
| ahv2_canonical_20 | ahv2_canonical_guard | 厥阴病是什么 | 必须命中 厥阴病 的 AHV2 safe definition primary。 |
| similar_01 | similar_concept_false_trigger | 荣气微弱是什么意思 | 相近词不得命中荣气微 AHV2。 |
| similar_02 | similar_concept_false_trigger | 卫气虚是什么意思 | 相近概念不得命中卫气衰 AHV2。 |
| similar_03 | similar_concept_false_trigger | 阳气不足是什么意思 | 既有阳不足对象不得误归阳气微 AHV2。 |
| similar_04 | similar_concept_false_trigger | 亡阳是什么意思 | 亡阳不得误归亡血 AHV2。 |
| similar_05 | similar_concept_false_trigger | 平是什么意思 | 单字平不得命中平脉 AHV2。 |
| similar_06 | similar_concept_false_trigger | 平脉和数脉有什么区别 | 比较意图不得被单个 AHV2 definition object 抢占。 |
| similar_07 | similar_concept_false_trigger | 数是什么意思 | 单字数不得命中数脉 AHV2。 |
| similar_08 | similar_concept_false_trigger | 毛是什么意思 | 单字毛不得命中毛脉 AHV2。 |
| similar_09 | similar_concept_false_trigger | 纯弦是什么意思 | inactive 短 alias 不得命中纯弦脉 AHV2。 |
| similar_10 | similar_concept_false_trigger | 残是什么意思 | 单字残不得命中残贼 AHV2。 |
| similar_11 | similar_concept_false_trigger | 八邪和残贼有什么区别 | 相近概念比较不得被单个 AHV2 primary 抢占。 |
| similar_12 | similar_concept_false_trigger | 湿病是什么 | 湿病不得误命中湿家 AHV2。 |
| similar_13 | similar_concept_false_trigger | 风湿病是什么 | 现代/宽泛风湿病不得命中风湿 AHV2。 |
| similar_14 | similar_concept_false_trigger | 水逆反应是什么 | 现代水逆反应不得命中水逆 AHV2。 |
| similar_15 | similar_concept_false_trigger | 半表半里和表里之间一样吗 | 关系问法不得命中半表半里证 AHV2 primary。 |
| similar_16 | similar_concept_false_trigger | 过经方是什么意思 | 相近组合词不得命中过经 AHV2。 |
| similar_17 | similar_concept_false_trigger | 结胸证和水结胸有什么区别 | 比较问法不得被结胸 AHV2 抢占。 |
| similar_18 | similar_concept_false_trigger | 阳明是什么意思 | 短概念阳明不得命中阳明病 AHV2。 |
| similar_19 | similar_concept_false_trigger | 太阴是什么意思 | 短概念太阴不得命中太阴病 AHV2。 |
| similar_20 | similar_concept_false_trigger | 少阴和厥阴有什么区别 | 六经比较不得被单个 AHV2 primary 抢占。 |
| disabled_alias_01 | disabled_alias_recheck | 平是什么意思 | inactive 单字 alias 平不得命中平脉 AHV2。 |
| disabled_alias_02 | disabled_alias_recheck | 数是什么意思 | inactive 单字 alias 数不得命中数脉 AHV2。 |
| disabled_alias_03 | disabled_alias_recheck | 毛是什么意思 | inactive 单字 alias 毛不得命中毛脉 AHV2。 |
| disabled_alias_04 | disabled_alias_recheck | 纯弦是什么意思 | inactive risky alias 纯弦不得命中纯弦脉 AHV2。 |
| disabled_alias_05 | disabled_alias_recheck | 风湿病是什么 | inactive risky alias 风湿病不得命中风湿 AHV2。 |
| partial_word_01 | partial_word_literal_similarity | 荣是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_02 | partial_word_literal_similarity | 卫是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_03 | partial_word_literal_similarity | 阳是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_04 | partial_word_literal_similarity | 血是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_05 | partial_word_literal_similarity | 平是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_06 | partial_word_literal_similarity | 数是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_07 | partial_word_literal_similarity | 毛是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_08 | partial_word_literal_similarity | 湿是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_09 | partial_word_literal_similarity | 水是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| partial_word_10 | partial_word_literal_similarity | 胸是什么意思 | 部分词或单字不得触发 AHV2 normalization/primary。 |
| non_definition_01 | non_definition_intent | 荣气微怎么治？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_02 | non_definition_intent | 卫气衰用什么方？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_03 | non_definition_intent | 水逆怎么治？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_04 | non_definition_intent | 结胸用什么方？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_05 | non_definition_intent | 半表半里证有哪些方？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_06 | non_definition_intent | 阳明病怎么治疗？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_07 | non_definition_intent | 太阴病的病机是什么？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_08 | non_definition_intent | 风湿和湿家有什么区别？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_09 | non_definition_intent | 少阴病有哪些方？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| non_definition_10 | non_definition_intent | 厥阴病怎么治？ | 治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。 |
| negative_01 | negative_unrelated | 平板电脑是什么 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_02 | negative_unrelated | 数学是什么意思 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_03 | negative_unrelated | 毛衣是什么 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_04 | negative_unrelated | 风湿免疫科是什么 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_05 | negative_unrelated | 水逆网络用语是什么意思 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_06 | negative_unrelated | 胸口健身动作是什么 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_07 | negative_unrelated | 太阴历是什么 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_08 | negative_unrelated | 阳明山在哪里 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_09 | negative_unrelated | 过经纪人是什么意思 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| negative_10 | negative_unrelated | 八邪游戏是什么 | 现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。 |
| formula_guard_01 | formula_guard | 桂枝去芍药汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV2 definition primary 抢占。 |
| formula_guard_02 | formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV2 definition primary 抢占。 |
| formula_guard_03 | formula_guard | 四逆加人参汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV2 definition primary 抢占。 |
| formula_guard_04 | formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV2 definition primary 抢占。 |
| formula_guard_05 | formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV2 definition primary 抢占。 |
| gold_safe_definition_01 | gold_safe_definition_guard | 下药是什么意思 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV2 primary 抢占。 |
| gold_safe_definition_02 | gold_safe_definition_guard | 四逆是什么意思 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV2 primary 抢占。 |
| gold_safe_definition_03 | gold_safe_definition_guard | 盗汗是什么意思 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV2 primary 抢占。 |
| gold_safe_definition_04 | gold_safe_definition_guard | 水结胸是什么 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV2 primary 抢占。 |
| gold_safe_definition_05 | gold_safe_definition_guard | 坏病是什么 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV2 primary 抢占。 |
| ahv_v1_guard_01 | ahv_v1_guard | 伤寒是什么 | AHV v1 guard 必须保持可用，不得被 AHV2 primary 抢占。 |
| ahv_v1_guard_02 | ahv_v1_guard | 霍乱是什么 | AHV v1 guard 必须保持可用，不得被 AHV2 primary 抢占。 |
| ahv_v1_guard_03 | ahv_v1_guard | 劳复是什么意思 | AHV v1 guard 必须保持可用，不得被 AHV2 primary 抢占。 |
| ahv_v1_guard_04 | ahv_v1_guard | 食复是什么意思 | AHV v1 guard 必须保持可用，不得被 AHV2 primary 抢占。 |
| ahv_v1_guard_05 | ahv_v1_guard | 结脉是什么 | AHV v1 guard 必须保持可用，不得被 AHV2 primary 抢占。 |
| review_only_boundary_01 | review_only_boundary_guard | 神丹是什么意思 | review-only boundary 不得进入 definition primary。 |
| review_only_boundary_02 | review_only_boundary_guard | 将军是什么意思 | review-only boundary 不得进入 definition primary。 |
| review_only_boundary_03 | review_only_boundary_guard | 高是什么意思 | review-only boundary 不得进入 definition primary。 |
| review_only_boundary_04 | review_only_boundary_guard | 顺是什么意思 | review-only boundary 不得进入 definition primary。 |
