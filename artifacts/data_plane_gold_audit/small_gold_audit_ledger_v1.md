# Small Gold Audit Ledger v1

- generated_at_utc: `2026-04-23T01:12:04.679074+00:00`
- object_count: `26`
- verdict_counts: `{"gold_needs_sentence_reselection": 1, "gold_needs_span_fix": 6, "gold_not_ready_for_promotion": 1, "gold_review_only": 3, "gold_safe_primary_but_medium": 15}`
- recommended_change_counts: `{"alias_cleanup": 1, "defer": 3, "none": 15, "sentence_reselection": 1, "span_fix": 6}`

| object_type | canonical_name | source_confidence | verdict | should_change_now | recommended_change_type | primary_support_passage_id | gold_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| definition_term | 下药 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-006-P-0120 | “承气汤者，下药也”是自足类属句，足以支撑短问法；但原 passage 同段混有汗下风险与《金匮玉函》材料，不能升 high。 |
| definition_term | 两感 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-006-P-0057 | “表里俱病者，谓之两感”语义闭合，canonical identity 稳定；medium 的根因只是来源层不是干净 main-only。 |
| definition_term | 代阴 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-010-P-0174 | primary evidence text 已抽出核心定义，术语身份成立；但 source sentence 带赵本异文，作为金标准只能保留 medium。 |
| definition_term | 伏气 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-004-P-0164 | “冬时感寒，伏藏于经中，不即发者，谓之伏气”定义完整；medium 仅因来源来自 full/risk 层。 |
| definition_term | 内烦 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-009-P-0306 | 句子能解释“内烦”在当前条文中的含义，但强依赖“太阳病吐之”语境，因此只可作为 medium safe primary。 |
| definition_term | 发汗药 | medium | gold_needs_sentence_reselection | true | sentence_reselection | ZJSHL-CH-006-P-0127 | “发汗药，须温暖服者，易为发散也”说明服法与药势，不是严格回答“发汗药是什么”的类属定义。 |
| definition_term | 四逆 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-015-P-0203 | “四逆者，四肢不温也”短而闭合，alias“四肢不温/手足不温”合理；medium 仅因原句来自 full/risk 层。 |
| definition_term | 坏病 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-008-P-0227 | 定义句自足且包含“为医所坏病”解释，但它的成立依赖误治上下文，因此不应升 high。 |
| definition_term | 时行之气 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-006-P-0015 | “四时气候不正为病，谓之时行之气”定义闭合，alias“时气”有学习者价值；medium 源于原载体层。 |
| definition_term | 水结胸 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-010-P-0026 | 主句明确把“水饮结于胸胁”命名为水结胸，定义充分；medium 是因为同段还有大柴胡汤/大陷胸汤用法语境。 |
| definition_term | 湿痹 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-007-P-0170 | stripped primary text 可以独立解释湿痹，但原句含赵本注和一云材料，金标准上只能承认为 medium。 |
| definition_term | 盗汗 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-010-P-0018 | “睡而汗出者，谓之盗汗”是非常干净的定义句，learner alias“睡着出汗”也合理；medium 只因来源层不是 high-safe main。 |
| definition_term | 结阴 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-010-P-0174 | 命名句可独立成义，但与代阴同段且上下句是结代脉族解释，不能给 high。 |
| definition_term | 虚烦 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-009-P-0157 | 句子虽长，但核心因果和命名关系完整；source layer 与病机解释混合，故维持 medium。 |
| definition_term | 阳易 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-017-P-0046 | 阳易对象身份稳定，当前没有再把“阴阳易”强行归到阳易；medium 是因为同段同时定义易/阳易/阴易。 |
| definition_term | 阴易 | medium | gold_safe_primary_but_medium | false | none | ZJSHL-CH-017-P-0046 | 阴易对象身份稳定，已避免与阳易共享“阴阳易”alias；medium 合理。 |
| formula | 乌梅丸 | medium | gold_needs_span_fix | false | span_fix | ZJSHL-CH-015-P-0221 | 当前 passage 只覆盖组成开头，且带赵本“枚/个”异文；不能判为完整高置信方文。 |
| formula | 旋复代赭石汤 | medium | gold_needs_span_fix | false | span_fix | ZJSHL-CH-010-P-0106 | 标题和药味均含赵本无“石”字，且缺 decoction/usage span；medium 合理。 |
| formula | 栀子浓朴汤 | medium | gold_needs_span_fix | false | span_fix | ZJSHL-CH-009-P-0170 | 当前只有药味组成行，且多处赵本异文；可检索但不可升 high。 |
| formula | 桂枝甘草龙骨牡蛎汤 | medium | gold_needs_span_fix | false | span_fix | ZJSHL-CH-009-P-0298 | 对象身份成立，但当前行只有组成且含去皮/炙异文；缺少完整方文边界证据。 |
| formula | 茵陈蒿汤 | medium | gold_needs_span_fix | false | span_fix | ZJSHL-CH-011-P-0141 | 组成行干净度尚可，但缺少煎服/用法 span；继续 medium 更稳。 |
| formula | 麻黄附子甘草汤 | medium | gold_needs_span_fix | false | span_fix | ZJSHL-CH-014-P-0069 | 方名和组成稳定，但附子炮制处含赵本异文，且缺少后续用法边界。 |
| review_only_term | 神丹 | review_only | gold_review_only | false | defer | ZJSHL-CH-006-P-0118 | “神丹者，发汗之药也”有类属信息，但对象更像注释汇编中的药名训诂，缺少独立 canonical 支撑。 |
| review_only_term | 将军 | review_only | gold_review_only | false | defer | ZJSHL-CH-010-P-0021 | “大黄谓之将军”偏药名别称/训诂，不应作为当前 definition family 的 safe primary。 |
| review_only_term | 两阳 | review_only | gold_not_ready_for_promotion | false | defer | ZJSHL-CH-009-P-0276 | “风与火气，谓之两阳”必须依赖后续病机展开；单句对普通学习者不够自足。 |
| review_only_term | 胆瘅 | review_only | gold_review_only | true | alias_cleanup | ZJSHL-CH-012-P-0214 | 核心句来自《内经》曰式 commentarial citation；当前降级正确，不能恢复 safe primary。 |
