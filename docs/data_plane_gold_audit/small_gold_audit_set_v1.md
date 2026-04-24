# Small Gold Audit Set v1

## Scope

- generated_at_utc: `2026-04-23T01:12:04.679074+00:00`
- total objects: `26`
- definition medium objects: `16`
- formula medium objects: `6`
- review-only boundary objects: `4`

## Verdict Counts

- `{"gold_needs_sentence_reselection": 1, "gold_needs_span_fix": 6, "gold_not_ready_for_promotion": 1, "gold_review_only": 3, "gold_safe_primary_but_medium": 15}`

## Table 1: 当前可直接信任的对象

| canonical_name | object_type | verdict | reason |
| --- | --- | --- | --- |
| 下药 | definition_term | gold_safe_primary_but_medium | “承气汤者，下药也”是自足类属句，足以支撑短问法；但原 passage 同段混有汗下风险与《金匮玉函》材料，不能升 high。 |
| 两感 | definition_term | gold_safe_primary_but_medium | “表里俱病者，谓之两感”语义闭合，canonical identity 稳定；medium 的根因只是来源层不是干净 main-only。 |
| 代阴 | definition_term | gold_safe_primary_but_medium | primary evidence text 已抽出核心定义，术语身份成立；但 source sentence 带赵本异文，作为金标准只能保留 medium。 |
| 伏气 | definition_term | gold_safe_primary_but_medium | “冬时感寒，伏藏于经中，不即发者，谓之伏气”定义完整；medium 仅因来源来自 full/risk 层。 |
| 内烦 | definition_term | gold_safe_primary_but_medium | 句子能解释“内烦”在当前条文中的含义，但强依赖“太阳病吐之”语境，因此只可作为 medium safe primary。 |
| 四逆 | definition_term | gold_safe_primary_but_medium | “四逆者，四肢不温也”短而闭合，alias“四肢不温/手足不温”合理；medium 仅因原句来自 full/risk 层。 |
| 坏病 | definition_term | gold_safe_primary_but_medium | 定义句自足且包含“为医所坏病”解释，但它的成立依赖误治上下文，因此不应升 high。 |
| 时行之气 | definition_term | gold_safe_primary_but_medium | “四时气候不正为病，谓之时行之气”定义闭合，alias“时气”有学习者价值；medium 源于原载体层。 |
| 水结胸 | definition_term | gold_safe_primary_but_medium | 主句明确把“水饮结于胸胁”命名为水结胸，定义充分；medium 是因为同段还有大柴胡汤/大陷胸汤用法语境。 |
| 湿痹 | definition_term | gold_safe_primary_but_medium | stripped primary text 可以独立解释湿痹，但原句含赵本注和一云材料，金标准上只能承认为 medium。 |
| 盗汗 | definition_term | gold_safe_primary_but_medium | “睡而汗出者，谓之盗汗”是非常干净的定义句，learner alias“睡着出汗”也合理；medium 只因来源层不是 high-safe main。 |
| 结阴 | definition_term | gold_safe_primary_but_medium | 命名句可独立成义，但与代阴同段且上下句是结代脉族解释，不能给 high。 |
| 虚烦 | definition_term | gold_safe_primary_but_medium | 句子虽长，但核心因果和命名关系完整；source layer 与病机解释混合，故维持 medium。 |
| 阳易 | definition_term | gold_safe_primary_but_medium | 阳易对象身份稳定，当前没有再把“阴阳易”强行归到阳易；medium 是因为同段同时定义易/阳易/阴易。 |
| 阴易 | definition_term | gold_safe_primary_but_medium | 阴易对象身份稳定，已避免与阳易共享“阴阳易”alias；medium 合理。 |

## Table 2: 当前不能直接信任但可修的对象

| canonical_name | object_type | recommended_change_type | followup |
| --- | --- | --- | --- |
| 发汗药 | definition_term | sentence_reselection | 下一轮应寻找更直接的 membership/definition sentence，或把当前对象标为 explanation-primary 而非 definition-primary。 |
| 乌梅丸 | formula | span_fix | 下一轮补完整 composition span，再决定是否升 high。 |
| 旋复代赭石汤 | formula | span_fix | 清理 canonical title display 与 composition span 后再复核。 |
| 栀子浓朴汤 | formula | span_fix | 补煎服/用法 span 或明确 composition-only formula policy。 |
| 桂枝甘草龙骨牡蛎汤 | formula | span_fix | 补齐 span 与 variant-stripped composition display。 |
| 茵陈蒿汤 | formula | span_fix | 查找相邻煎服句并补 span。 |
| 麻黄附子甘草汤 | formula | span_fix | 补 span 并记录 variant-stripped 药味。 |
| 胆瘅 | review_only_term | alias_cleanup | 建议清理 review-only 对象上的 learner aliases“口苦病/胆瘅病”，防止未来 runtime 误启用。 |

## Table 3: 当前应明确保守的对象

| canonical_name | verdict | reason | followup |
| --- | --- | --- | --- |
| 神丹 | gold_review_only | “神丹者，发汗之药也”有类属信息，但对象更像注释汇编中的药名训诂，缺少独立 canonical 支撑。 | 若后续要升格，必须找到非注释汇编层的稳定药名证据。 |
| 将军 | gold_review_only | “大黄谓之将军”偏药名别称/训诂，不应作为当前 definition family 的 safe primary。 | 若要支持，应先建立药名别称对象层，而不是放入 general definition safe primary。 |
| 两阳 | gold_not_ready_for_promotion | “风与火气，谓之两阳”必须依赖后续病机展开；单句对普通学习者不够自足。 | 下一轮需要一组病机解释 support object，而不是只升格命名句。 |
| 胆瘅 | gold_review_only | 核心句来自《内经》曰式 commentarial citation；当前降级正确，不能恢复 safe primary。 | 建议清理 review-only 对象上的 learner aliases“口苦病/胆瘅病”，防止未来 runtime 误启用。 |

## Regression Summary

- forbidden primary total: `0`
- formula strong: `8 / 8`
- formula bad anchors top5 total: `0`
- review-only / not-ready definition primary conflicts: `0`
- gold safe primary hits: `13 / 13`
