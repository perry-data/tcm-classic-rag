# AHV Adversarial Query Set v1

- query_count: `87`
- query_type_counts: `{"ahv_canonical_guard": 20, "disabled_alias_recheck": 5, "formula_guard": 5, "gold_safe_definition_guard": 5, "negative_unrelated": 10, "non_definition_intent": 8, "partial_word_literal_similarity": 10, "review_only_boundary_guard": 4, "similar_concept_false_trigger": 20}`

| query_id | query_type | query | expected_behavior |
| --- | --- | --- | --- |
| ahv_canonical_01 | ahv_canonical_guard | 何谓太阳病 | 必须命中 太阳病 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_02 | ahv_canonical_guard | 伤寒是什么 | 必须命中 伤寒 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_03 | ahv_canonical_guard | 温病是什么意思 | 必须命中 温病 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_04 | ahv_canonical_guard | 暑病是什么意思 | 必须命中 暑病 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_05 | ahv_canonical_guard | 冬温是什么 | 必须命中 冬温 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_06 | ahv_canonical_guard | 时行寒疫是什么 | 必须命中 时行寒疫 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_07 | ahv_canonical_guard | 刚痓是什么 | 必须命中 刚痓 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_08 | ahv_canonical_guard | 柔痓是什么意思 | 必须命中 柔痓 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_09 | ahv_canonical_guard | 痓病是什么 | 必须命中 痓病 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_10 | ahv_canonical_guard | 结脉是什么 | 必须命中 结脉 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_11 | ahv_canonical_guard | 促脉是什么 | 必须命中 促脉 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_12 | ahv_canonical_guard | 弦脉是什么 | 必须命中 弦脉 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_13 | ahv_canonical_guard | 滑脉是什么意思 | 必须命中 滑脉 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_14 | ahv_canonical_guard | 革脉是什么 | 必须命中 革脉 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_15 | ahv_canonical_guard | 行尸是什么意思 | 必须命中 行尸 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_16 | ahv_canonical_guard | 内虚是什么意思 | 必须命中 内虚 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_17 | ahv_canonical_guard | 血崩是什么 | 必须命中 血崩 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_18 | ahv_canonical_guard | 霍乱是什么 | 必须命中 霍乱 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_19 | ahv_canonical_guard | 劳复是什么意思 | 必须命中 劳复 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| ahv_canonical_20 | ahv_canonical_guard | 食复是什么意思 | 必须命中 食复 的 AHV safe definition primary，且不得混入其他 AHV primary。 |
| similar_01 | similar_concept_false_trigger | 春温病是什么意思 | 春温/温病相近词不得因包含“温病”而命中温病 AHV。 |
| similar_02 | similar_concept_false_trigger | 寒疫病是什么意思 | 寒疫/时行寒疫相近词不得命中时行寒疫 AHV。 |
| similar_03 | similar_concept_false_trigger | 痉是什么意思 | 单字异体痉不得命中刚痓、柔痓或痓病 AHV。 |
| similar_04 | similar_concept_false_trigger | 痓是什么意思 | 单字痓不得命中痓病 AHV。 |
| similar_05 | similar_concept_false_trigger | 刚痓和柔痓有什么不同 | 刚痓/柔痓比较意图不得被单个 AHV definition primary 抢占。 |
| similar_06 | similar_concept_false_trigger | 柔痓和痓病是一回事吗 | 柔痓/痓病关系问法不得被单个 AHV definition primary 抢占。 |
| similar_07 | similar_concept_false_trigger | 痉病和痓病是同一个词吗 | 痉病/痓病关系问法不得被单个 AHV definition primary 抢占。 |
| similar_08 | similar_concept_false_trigger | 结是什么意思 | 单字结不得命中结脉 AHV。 |
| similar_09 | similar_concept_false_trigger | 结脉和促脉有什么区别 | 结脉/促脉比较意图不得被 AHV definition primary 抢占。 |
| similar_10 | similar_concept_false_trigger | 促是什么意思 | 单字促不得命中促脉 AHV。 |
| similar_11 | similar_concept_false_trigger | 滑脉和革脉有什么不同 | 滑脉/革脉比较意图不得被 AHV definition primary 抢占。 |
| similar_12 | similar_concept_false_trigger | 滑象是什么意思 | 滑象不得因字面相近命中滑脉 AHV。 |
| similar_13 | similar_concept_false_trigger | 革象是什么意思 | 革象不得因字面相近命中革脉 AHV。 |
| similar_14 | similar_concept_false_trigger | 劳复和食复一样吗 | 劳复/食复关系问法不得被单个 AHV definition primary 抢占。 |
| similar_15 | similar_concept_false_trigger | 劳病是什么意思 | 劳病不得命中劳复 AHV。 |
| similar_16 | similar_concept_false_trigger | 食病是什么意思 | 食病不得命中食复 AHV。 |
| similar_17 | similar_concept_false_trigger | 伤寒和温病有什么区别 | 伤寒/温病比较意图不得被 AHV definition primary 抢占。 |
| similar_18 | similar_concept_false_trigger | 伤寒和暑病有什么区别 | 伤寒/暑病比较意图不得被 AHV definition primary 抢占。 |
| similar_19 | similar_concept_false_trigger | 伤寒和冬温有什么区别 | 伤寒/冬温比较意图不得被 AHV definition primary 抢占。 |
| similar_20 | similar_concept_false_trigger | 太阳病和伤寒是一回事吗 | 太阳病/伤寒关系问法不得被单个 AHV definition primary 抢占。 |
| disabled_alias_01 | disabled_alias_recheck | 春温是什么意思 | 停用 alias 春温不得重新命中温病 AHV。 |
| disabled_alias_02 | disabled_alias_recheck | 暑病者是什么意思 | 停用 alias 暑病者不得重新命中暑病 AHV。 |
| disabled_alias_03 | disabled_alias_recheck | 寒疫是什么意思 | 停用 alias 寒疫不得重新命中时行寒疫 AHV。 |
| disabled_alias_04 | disabled_alias_recheck | 劳动病是什么 | 停用 alias 劳动病不得重新命中劳复 AHV。 |
| disabled_alias_05 | disabled_alias_recheck | 强食复病是什么意思 | 停用 alias 强食复病不得重新命中食复 AHV。 |
| partial_word_01 | partial_word_literal_similarity | 太阳是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_02 | partial_word_literal_similarity | 寒是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_03 | partial_word_literal_similarity | 温是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_04 | partial_word_literal_similarity | 暑是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_05 | partial_word_literal_similarity | 弦是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_06 | partial_word_literal_similarity | 滑是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_07 | partial_word_literal_similarity | 革是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_08 | partial_word_literal_similarity | 劳是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_09 | partial_word_literal_similarity | 食是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| partial_word_10 | partial_word_literal_similarity | 复是什么意思 | 单字或普通部分词不得触发 AHV term normalization 或 AHV primary。 |
| non_definition_01 | non_definition_intent | 太阳病有哪些方？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| non_definition_02 | non_definition_intent | 伤寒怎么治疗？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| non_definition_03 | non_definition_intent | 温病与伤寒如何区分？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| non_definition_04 | non_definition_intent | 霍乱用什么方？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| non_definition_05 | non_definition_intent | 劳复应该怎么处理？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| non_definition_06 | non_definition_intent | 食复怎么治？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| non_definition_07 | non_definition_intent | 结脉有什么方？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| non_definition_08 | non_definition_intent | 革脉预后如何？ | 非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。 |
| negative_01 | negative_unrelated | 太阳能是什么意思 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_02 | negative_unrelated | 食物中毒是什么意思 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_03 | negative_unrelated | 劳动合同是什么 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_04 | negative_unrelated | 皮革是什么 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_05 | negative_unrelated | 滑雪是什么意思 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_06 | negative_unrelated | 内虚拟机是什么 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_07 | negative_unrelated | 霍乱疫苗是什么 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_08 | negative_unrelated | 暑假是什么 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_09 | negative_unrelated | 温度是什么意思 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| negative_10 | negative_unrelated | 复习是什么意思 | 明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。 |
| formula_guard_01 | formula_guard | 桂枝去芍药汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_02 | formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_03 | formula_guard | 四逆加人参汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_04 | formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_05 | formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| gold_safe_definition_01 | gold_safe_definition_guard | 下药是什么意思 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV primary 抢占。 |
| gold_safe_definition_02 | gold_safe_definition_guard | 四逆是什么意思 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV primary 抢占。 |
| gold_safe_definition_03 | gold_safe_definition_guard | 盗汗是什么意思 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV primary 抢占。 |
| gold_safe_definition_04 | gold_safe_definition_guard | 水结胸是什么 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV primary 抢占。 |
| gold_safe_definition_05 | gold_safe_definition_guard | 坏病是什么 | 既有 gold-safe definition guard 必须保持 strong，且不得被 AHV primary 抢占。 |
| review_only_boundary_01 | review_only_boundary_guard | 神丹是什么意思 | review-only boundary 不得进入 definition primary。 |
| review_only_boundary_02 | review_only_boundary_guard | 将军是什么意思 | review-only boundary 不得进入 definition primary。 |
| review_only_boundary_03 | review_only_boundary_guard | 口苦病是什么意思 | review-only boundary 不得进入 definition primary。 |
| review_only_boundary_04 | review_only_boundary_guard | 胆瘅病是什么意思 | review-only boundary 不得进入 definition primary。 |
