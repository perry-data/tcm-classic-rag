# Object Audit Ledger v1

- generated_at_utc: `2026-04-24T00:16:59.087232+00:00`
- audit_label_counts: `{"alias_insufficient": 2, "boundary_unclear": 3, "clean_enough": 21, "context_dependent": 3, "editorial_contaminated": 6, "promotion_too_aggressive": 1, "review_only_expected": 3, "span_uncertain": 1}`
- audit_decision_counts: `{"adjust_aliases": 2, "adjust_sentence_source": 2, "downgrade_to_review_only": 1, "keep_as_is": 26, "upgrade_confidence": 9}`

| canonical_name | audit_label | audit_decision | before | after | primary_support_passage_id | main_risk_reason | fix_action | primary_evidence_text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 下药 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-006-P-0120 | 来源于 mixed-role risk passage，但抽出的类属句自足且 learner short-query 受益明显。 | none | 承气汤者，下药也 |
| 两感 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-006-P-0057 | 定义句极短且闭合，但来源层仍是 records_passages。 | none | 表里俱病者，谓之两感 |
| 代阴 | boundary_unclear | keep_as_is | medium | medium | ZJSHL-CH-010-P-0174 | 定义句所在主 passage 含 inline 版本差异标记，句段可抽出但不够高置信。 | none | 脉来动而中止，不能自还，因而复动， 名曰代阴也 |
| 伏气 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-004-P-0164 | 定义句完整，但来源仍在 risk/full 层。 | none | 冬时感寒，伏藏于经中，不即发者，谓之伏气 |
| 内烦 | context_dependent | keep_as_is | medium | medium | ZJSHL-CH-009-P-0306 | 主句是吐后语境里的症状命名句，能解释 term，但依赖临床上下文。 | none | 太阳病吐之，但太阳病当恶寒，今反不恶寒，不欲近衣，此为吐之内烦也 |
| 发汗药 | context_dependent | keep_as_is | medium | medium | ZJSHL-CH-006-P-0127 | 当前主句更像使用解释，不是最短定义句；但对 learner-facing 类别解释更稳。 | none | 发汗药，须温暖服者，易为发散也 |
| 四逆 | boundary_unclear | adjust_sentence_source | medium | medium | ZJSHL-CH-015-P-0203 | 句段角色规则把“四逆者，四肢不温也”误判成 formula_composition_sentence。 | tighten_sentence_role_formula_dosage_rule | 四逆者，四肢不温也 |
| 坏病 | context_dependent | keep_as_is | medium | medium | ZJSHL-CH-008-P-0227 | 定义句自足，但自带误治前提语境，因此不升 high。 | none | 太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也 |
| 奔豚 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-009-P-0109 | 命名句短而独立，风险主要在 source layer 而非句义。 | none | 肾之积，名曰奔豚 |
| 小结胸 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-010-P-0030 | 分型句闭合，长段风险已被 sentence-level extraction 隔离。 | none | 正在心下，按之则痛，是热气犹浅，谓之小结胸 |
| 并病 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-009-P-0064 | 定义句可独立成义，但仍属于传经上下文中的概念命名。 | none | 太阳病未解，传并入阳明，而太阳证未罢者，名曰并病 |
| 时行之气 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-006-P-0015 | 定义句完整，风险主要来自原始载体层级。 | none | 四时气候不正为病，谓之时行之气 |
| 水结胸 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-010-P-0026 | 分型说明足够完整，且已把后续方药句留在 support。 | none | 但结胸无大热者，非热结也，是水饮结于胸胁，谓之水结胸 |
| 消渴 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-009-P-0137 | 命名句附带病机短解释，适合作 learner-facing primary。 | none | 饮水多，而小便少者，谓之消渴，里热甚实也 |
| 湿痹 | editorial_contaminated | adjust_sentence_source | medium | medium | ZJSHL-CH-007-P-0170 | 原句含赵本/一云类 inline variant note，role 判定应基于 strip 后句面。 | strip_variant_then_reclassify_sentence_role | 太阳病，关节疼痛而烦，脉沉而细者，此名湿痹 |
| 盗汗 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-010-P-0018 | 定义句极短且 learner alias 清晰，风险主要来自 source layer。 | none | 睡而汗出者，谓之盗汗 |
| 结阴 | boundary_unclear | keep_as_is | medium | medium | ZJSHL-CH-010-P-0174 | 与代阴共用一条带 variant 干扰的脉象段，仍不适合升 high。 | none | 又脉来动而中止，更来小数，中有还者反动，名曰结阴也 |
| 肺痿 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-008-P-0235 | 命名句足够自足，长段病机说明已留在 support/review。 | none | 吐脓血，谓之肺痿 |
| 胆瘅 | promotion_too_aggressive | downgrade_to_review_only | medium | review_only | ZJSHL-CH-012-P-0214 | 当前 primary sentence 直接带《内经》曰 commentarial citation，升格过激。 | downgrade_definition_object_and_remove_safe_primary_surfaces | 有病口苦者，名曰胆瘅 |
| 虚烦 | clean_enough | keep_as_is | medium | medium | ZJSHL-CH-009-P-0157 | 定义句完整，后续 variant/commentary 已留在 support。 | none | 发汗吐下后，邪热乘虚客于胸中，谓之虚烦者热也，胸中烦热郁闷而不得发散者是也 |
| 阳易 | alias_insufficient | adjust_aliases | medium | medium | ZJSHL-CH-017-P-0046 | 与阴易共享 learner alias“阴阳易”，当前 runtime 会强行落到阳易。 | remove_shared_ambiguous_alias | 男子病新瘥未平复，而妇人与之交，得病，名曰阳易 |
| 阴易 | alias_insufficient | adjust_aliases | medium | medium | ZJSHL-CH-017-P-0046 | 与阳易共享 learner alias“阴阳易”，会造成单边误归一。 | remove_shared_ambiguous_alias | 妇人病新瘥未平腹，男子与之交，得病，名曰阴易 |
| 风温 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-008-P-0203 | 主句来自 safe main passage，句义完整；原 medium 主要是 role heuristics 未把“X为病”识别成定义句。 | upgrade_confidence_after_role_reclassify | 风温为病，脉阴阳俱浮，自汗出，身重，多眠睡，息必鼾，语言难出 |
| 乌梅丸 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-015-P-0221 | 当前仅有带异文标记的组成行，缺少独立 usage/decoction span。 | none |  |
| 四逆加人参汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-029-P-0001 | 主行已内联“馀根据四逆汤法服”，builder 之前未把 inline usage 计入高置信。 | upgrade_confidence_for_inline_inherited_usage |  |
| 四逆加猪胆汁汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-029-P-0002 | 主行内联前法服用与替代说明，足以构成高置信继承型方文。 | upgrade_confidence_for_inline_inherited_usage |  |
| 旋复代赭石汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-010-P-0106 | 标题与药味中均带赵本异文，且无独立 usage/decoction span。 | none |  |
| 柴胡加芒硝汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-026-P-0005 | 主行含加减关系与“服不解，更服”使用信息，builder 低估了 inline usage。 | upgrade_confidence_for_inline_inherited_usage |  |
| 栀子浓朴汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-009-P-0170 | 药味行异文较多，且仅有组成行。 | none |  |
| 桂枝加浓朴杏子汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0003 | 继承型公式稳定，主行已含“馀根据前法”。 | upgrade_confidence_for_inline_inherited_usage |  |
| 桂枝加芍药汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-028-P-0004 | 主行是稳定加减公式，前法继承明确。 | upgrade_confidence_for_inline_inherited_usage |  |
| 桂枝去桂加茯苓白术汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0013 | 主行同时含继承关系、煎服方式和“小便利则愈”的使用语义。 | upgrade_confidence_for_inline_inherited_usage |  |
| 桂枝去芍药加附子汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0006 | 主行继承关系与加附子边界清晰。 | upgrade_confidence_for_inline_inherited_usage |  |
| 桂枝去芍药汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0005 | 主行是纯净的基方去味关系，前法继承清楚。 | upgrade_confidence_for_inline_inherited_usage |  |
| 桂枝甘草龙骨牡蛎汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-009-P-0298 | 仅有药味组成行，且标题/药味异文较多。 | none |  |
| 茵陈蒿汤 | span_uncertain | keep_as_is | medium | medium | ZJSHL-CH-011-P-0141 | 当前只有组成行，缺独立 decoction/usage span。 | none |  |
| 麻黄附子甘草汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-014-P-0069 | 主行含赵本变体，且没有额外 usage/decoction span。 | none |  |
| 两阳 | review_only_expected | keep_as_is | review_only | review_only | ZJSHL-CH-009-P-0276 | 术语定义强依赖后续病机展开，当前不适合 learner-facing 主定义对象。 | none | 风与火气，谓之两阳 |
| 将军 | review_only_expected | keep_as_is | review_only | review_only | ZJSHL-CH-010-P-0021 | 更偏药名训诂/注解层，不是当前 definition family 的安全主对象。 | none | 大黄谓之将军，以苦荡涤 |
| 神丹 | review_only_expected | keep_as_is | review_only | review_only | ZJSHL-CH-006-P-0118 | 证据主要来自注释汇编层，缺独立 canonical 支撑。 | none | 神丹者，发汗之药也 |
