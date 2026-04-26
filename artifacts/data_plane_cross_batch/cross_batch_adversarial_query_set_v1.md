# Cross-Batch AHV Adversarial Query Set v1

- query_count: `120`
- query_type_counts: `{"ahv2_canonical_guard": 20, "ahv_v1_canonical_guard": 20, "alias_partial_negative": 20, "cross_batch_concept_conflict": 25, "formula_guard": 5, "non_definition_intent": 20, "review_only_rejected_guard": 10}`

| query_id | query_type | query | expected_behavior |
| --- | --- | --- | --- |
| ahv_v1_canonical_01 | ahv_v1_canonical_guard | 何谓太阳病 | 必须命中 AHV v1 `太阳病` safe primary。 |
| ahv_v1_canonical_02 | ahv_v1_canonical_guard | 伤寒是什么 | 必须命中 AHV v1 `伤寒` safe primary。 |
| ahv_v1_canonical_03 | ahv_v1_canonical_guard | 温病是什么意思 | 必须命中 AHV v1 `温病` safe primary。 |
| ahv_v1_canonical_04 | ahv_v1_canonical_guard | 暑病是什么意思 | 必须命中 AHV v1 `暑病` safe primary。 |
| ahv_v1_canonical_05 | ahv_v1_canonical_guard | 冬温是什么 | 必须命中 AHV v1 `冬温` safe primary。 |
| ahv_v1_canonical_06 | ahv_v1_canonical_guard | 时行寒疫是什么 | 必须命中 AHV v1 `时行寒疫` safe primary。 |
| ahv_v1_canonical_07 | ahv_v1_canonical_guard | 刚痓是什么 | 必须命中 AHV v1 `刚痓` safe primary。 |
| ahv_v1_canonical_08 | ahv_v1_canonical_guard | 柔痓是什么意思 | 必须命中 AHV v1 `柔痓` safe primary。 |
| ahv_v1_canonical_09 | ahv_v1_canonical_guard | 痓病是什么 | 必须命中 AHV v1 `痓病` safe primary。 |
| ahv_v1_canonical_10 | ahv_v1_canonical_guard | 结脉是什么 | 必须命中 AHV v1 `结脉` safe primary。 |
| ahv_v1_canonical_11 | ahv_v1_canonical_guard | 促脉是什么 | 必须命中 AHV v1 `促脉` safe primary。 |
| ahv_v1_canonical_12 | ahv_v1_canonical_guard | 弦脉是什么 | 必须命中 AHV v1 `弦脉` safe primary。 |
| ahv_v1_canonical_13 | ahv_v1_canonical_guard | 滑脉是什么意思 | 必须命中 AHV v1 `滑脉` safe primary。 |
| ahv_v1_canonical_14 | ahv_v1_canonical_guard | 革脉是什么 | 必须命中 AHV v1 `革脉` safe primary。 |
| ahv_v1_canonical_15 | ahv_v1_canonical_guard | 行尸是什么意思 | 必须命中 AHV v1 `行尸` safe primary。 |
| ahv_v1_canonical_16 | ahv_v1_canonical_guard | 内虚是什么意思 | 必须命中 AHV v1 `内虚` safe primary。 |
| ahv_v1_canonical_17 | ahv_v1_canonical_guard | 血崩是什么 | 必须命中 AHV v1 `血崩` safe primary。 |
| ahv_v1_canonical_18 | ahv_v1_canonical_guard | 霍乱是什么 | 必须命中 AHV v1 `霍乱` safe primary。 |
| ahv_v1_canonical_19 | ahv_v1_canonical_guard | 劳复是什么意思 | 必须命中 AHV v1 `劳复` safe primary。 |
| ahv_v1_canonical_20 | ahv_v1_canonical_guard | 食复是什么意思 | 必须命中 AHV v1 `食复` safe primary。 |
| ahv2_canonical_01 | ahv2_canonical_guard | 荣气微是什么意思 | 必须命中 AHV2 `荣气微` safe primary。 |
| ahv2_canonical_02 | ahv2_canonical_guard | 卫气衰是什么意思 | 必须命中 AHV2 `卫气衰` safe primary。 |
| ahv2_canonical_03 | ahv2_canonical_guard | 阳气微是什么意思 | 必须命中 AHV2 `阳气微` safe primary。 |
| ahv2_canonical_04 | ahv2_canonical_guard | 亡血是什么意思 | 必须命中 AHV2 `亡血` safe primary。 |
| ahv2_canonical_05 | ahv2_canonical_guard | 平脉是什么意思 | 必须命中 AHV2 `平脉` safe primary。 |
| ahv2_canonical_06 | ahv2_canonical_guard | 数脉是什么意思 | 必须命中 AHV2 `数脉` safe primary。 |
| ahv2_canonical_07 | ahv2_canonical_guard | 毛脉是什么意思 | 必须命中 AHV2 `毛脉` safe primary。 |
| ahv2_canonical_08 | ahv2_canonical_guard | 纯弦脉是什么意思 | 必须命中 AHV2 `纯弦脉` safe primary。 |
| ahv2_canonical_09 | ahv2_canonical_guard | 残贼是什么意思 | 必须命中 AHV2 `残贼` safe primary。 |
| ahv2_canonical_10 | ahv2_canonical_guard | 八邪是什么意思 | 必须命中 AHV2 `八邪` safe primary。 |
| ahv2_canonical_11 | ahv2_canonical_guard | 湿家是什么意思 | 必须命中 AHV2 `湿家` safe primary。 |
| ahv2_canonical_12 | ahv2_canonical_guard | 风湿是什么意思 | 必须命中 AHV2 `风湿` safe primary。 |
| ahv2_canonical_13 | ahv2_canonical_guard | 水逆是什么意思 | 必须命中 AHV2 `水逆` safe primary。 |
| ahv2_canonical_14 | ahv2_canonical_guard | 半表半里证是什么意思 | 必须命中 AHV2 `半表半里证` safe primary。 |
| ahv2_canonical_15 | ahv2_canonical_guard | 过经是什么意思 | 必须命中 AHV2 `过经` safe primary。 |
| ahv2_canonical_16 | ahv2_canonical_guard | 结胸是什么意思 | 必须命中 AHV2 `结胸` safe primary。 |
| ahv2_canonical_17 | ahv2_canonical_guard | 阳明病是什么 | 必须命中 AHV2 `阳明病` safe primary。 |
| ahv2_canonical_18 | ahv2_canonical_guard | 太阴病是什么 | 必须命中 AHV2 `太阴病` safe primary。 |
| ahv2_canonical_19 | ahv2_canonical_guard | 少阴病是什么 | 必须命中 AHV2 `少阴病` safe primary。 |
| ahv2_canonical_20 | ahv2_canonical_guard | 厥阴病是什么 | 必须命中 AHV2 `厥阴病` safe primary。 |
| conflict_01 | cross_batch_concept_conflict | 太阳病和阳明病有什么区别 | 六经比较不得被单个 AHV 对象抢 primary。 |
| conflict_02 | cross_batch_concept_conflict | 伤寒和温病有什么区别 | 伤寒/温病比较不得被单个 AHV 对象抢 primary。 |
| conflict_03 | cross_batch_concept_conflict | 伤寒和暑病是一回事吗 | 近义/关系问法不得单点归一。 |
| conflict_04 | cross_batch_concept_conflict | 刚痓和柔痓有什么不同 | 刚痓/柔痓比较不得单点归一。 |
| conflict_05 | cross_batch_concept_conflict | 痓病和刚痓是什么关系 | 宽窄关系问法不得被单个对象抢 primary。 |
| conflict_06 | cross_batch_concept_conflict | 结脉和促脉有什么区别 | 脉象比较不得单点归一。 |
| conflict_07 | cross_batch_concept_conflict | 弦脉和纯弦脉有什么区别 | 相近脉象比较不得单点归一。 |
| conflict_08 | cross_batch_concept_conflict | 滑脉和数脉有什么区别 | 脉象比较不得单点归一。 |
| conflict_09 | cross_batch_concept_conflict | 劳复和食复一样吗 | 瘥后复病关系问法不得单点归一。 |
| conflict_10 | cross_batch_concept_conflict | 结胸和水逆有什么不同 | 病证比较不得单点归一。 |
| conflict_11 | cross_batch_concept_conflict | 半表半里证和结胸有什么关系 | 关系问法不得单点归一。 |
| conflict_12 | cross_batch_concept_conflict | 水逆和水结胸是一回事吗 | 近词比较不得单点归一。 |
| conflict_13 | cross_batch_concept_conflict | 少阴病和厥阴病有什么区别 | 六经比较不得单点归一。 |
| conflict_14 | cross_batch_concept_conflict | 太阴病和阳明病有什么区别 | 六经比较不得单点归一。 |
| conflict_15 | cross_batch_concept_conflict | 温病和暑病有什么关系 | 时病关系问法不得单点归一。 |
| conflict_16 | cross_batch_concept_conflict | 冬温和温病是一回事吗 | 宽窄关系不得误归一。 |
| conflict_17 | cross_batch_concept_conflict | 时行寒疫和伤寒有什么不同 | 相近外感病名不得误归一。 |
| conflict_18 | cross_batch_concept_conflict | 平脉和数脉有什么区别 | 脉象比较不得单点归一。 |
| conflict_19 | cross_batch_concept_conflict | 毛脉和革脉有什么区别 | 脉象比较不得单点归一。 |
| conflict_20 | cross_batch_concept_conflict | 残贼和八邪有什么关系 | 分类/病理关系不得单点归一。 |
| conflict_21 | cross_batch_concept_conflict | 湿家和风湿有什么区别 | 湿病相关概念不得互抢。 |
| conflict_22 | cross_batch_concept_conflict | 阳气微和内虚有什么关系 | 跨批次状态概念不得误归一。 |
| conflict_23 | cross_batch_concept_conflict | 亡血和血崩是一回事吗 | 气血状态/病名不得误归一。 |
| conflict_24 | cross_batch_concept_conflict | 过经和劳复有什么不同 | 病程/复病概念不得误归一。 |
| conflict_25 | cross_batch_concept_conflict | 太阳病和少阴病怎样区分 | 六经区分问法不得单点归一。 |
| non_definition_01 | non_definition_intent | 阳明病用什么方 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_02 | non_definition_intent | 少阴病怎么治 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_03 | non_definition_intent | 厥阴病有哪些方 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_04 | non_definition_intent | 霍乱用什么方 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_05 | non_definition_intent | 结胸怎么治 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_06 | non_definition_intent | 水逆用什么方 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_07 | non_definition_intent | 伤寒怎么治疗 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_08 | non_definition_intent | 温病怎么治 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_09 | non_definition_intent | 劳复应该怎么处理 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_10 | non_definition_intent | 食复应该怎么处理 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_11 | non_definition_intent | 弦脉预后如何 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_12 | non_definition_intent | 革脉说明什么 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_13 | non_definition_intent | 结脉有什么方 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_14 | non_definition_intent | 太阳病的条文是什么 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_15 | non_definition_intent | 阳明病的条文是什么 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_16 | non_definition_intent | 太阴病的病机是什么 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_17 | non_definition_intent | 半表半里证用什么方 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_18 | non_definition_intent | 风湿如何治疗 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_19 | non_definition_intent | 亡血怎么处理 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| non_definition_20 | non_definition_intent | 过经之后用什么方 | 治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。 |
| negative_alias_01 | alias_partial_negative | 温是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_02 | alias_partial_negative | 寒是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_03 | alias_partial_negative | 阳是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_04 | alias_partial_negative | 阴是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_05 | alias_partial_negative | 数是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_06 | alias_partial_negative | 毛是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_07 | alias_partial_negative | 纯是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_08 | alias_partial_negative | 弦是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_09 | alias_partial_negative | 水是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_10 | alias_partial_negative | 过是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_11 | alias_partial_negative | 半表是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_12 | alias_partial_negative | 复习是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_13 | alias_partial_negative | 劳动是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_14 | alias_partial_negative | 食物是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_15 | alias_partial_negative | 太阳能是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_16 | alias_partial_negative | 阳明山是什么 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_17 | alias_partial_negative | 少阴影是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_18 | alias_partial_negative | 太阴历是什么 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_19 | alias_partial_negative | 厥是什么意思 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| negative_alias_20 | alias_partial_negative | 八邪游戏是什么 | 单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。 |
| review_only_01 | review_only_rejected_guard | 神丹是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_02 | review_only_rejected_guard | 将军是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_03 | review_only_rejected_guard | 两阳是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_04 | review_only_rejected_guard | 胆瘅是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_05 | review_only_rejected_guard | 火劫发汗是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_06 | review_only_rejected_guard | 肝乘脾是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_07 | review_only_rejected_guard | 反是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_08 | review_only_rejected_guard | 复是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_09 | review_only_rejected_guard | 寒格是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| review_only_10 | review_only_rejected_guard | 清邪中上是什么意思 | review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。 |
| formula_guard_01 | formula_guard | 桂枝去芍药汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_02 | formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_03 | formula_guard | 四逆加人参汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_04 | formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
| formula_guard_05 | formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。 |
