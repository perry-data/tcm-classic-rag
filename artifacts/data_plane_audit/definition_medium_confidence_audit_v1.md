# Definition Medium Confidence Audit v1

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
