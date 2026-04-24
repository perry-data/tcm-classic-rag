# Formula Medium Confidence Audit v1

| canonical_name | audit_label | audit_decision | before | after | primary_support_passage_id | main_risk_reason | fix_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 乌梅丸 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-015-P-0221 | 当前仅有带异文标记的组成行，缺少独立 usage/decoction span。 | none |
| 四逆加人参汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-029-P-0001 | 主行已内联“馀根据四逆汤法服”，builder 之前未把 inline usage 计入高置信。 | upgrade_confidence_for_inline_inherited_usage |
| 四逆加猪胆汁汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-029-P-0002 | 主行内联前法服用与替代说明，足以构成高置信继承型方文。 | upgrade_confidence_for_inline_inherited_usage |
| 旋复代赭石汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-010-P-0106 | 标题与药味中均带赵本异文，且无独立 usage/decoction span。 | none |
| 柴胡加芒硝汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-026-P-0005 | 主行含加减关系与“服不解，更服”使用信息，builder 低估了 inline usage。 | upgrade_confidence_for_inline_inherited_usage |
| 栀子浓朴汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-009-P-0170 | 药味行异文较多，且仅有组成行。 | none |
| 桂枝加浓朴杏子汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0003 | 继承型公式稳定，主行已含“馀根据前法”。 | upgrade_confidence_for_inline_inherited_usage |
| 桂枝加芍药汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-028-P-0004 | 主行是稳定加减公式，前法继承明确。 | upgrade_confidence_for_inline_inherited_usage |
| 桂枝去桂加茯苓白术汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0013 | 主行同时含继承关系、煎服方式和“小便利则愈”的使用语义。 | upgrade_confidence_for_inline_inherited_usage |
| 桂枝去芍药加附子汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0006 | 主行继承关系与加附子边界清晰。 | upgrade_confidence_for_inline_inherited_usage |
| 桂枝去芍药汤 | clean_enough | upgrade_confidence | medium | high | ZJSHL-CH-025-P-0005 | 主行是纯净的基方去味关系，前法继承清楚。 | upgrade_confidence_for_inline_inherited_usage |
| 桂枝甘草龙骨牡蛎汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-009-P-0298 | 仅有药味组成行，且标题/药味异文较多。 | none |
| 茵陈蒿汤 | span_uncertain | keep_as_is | medium | medium | ZJSHL-CH-011-P-0141 | 当前只有组成行，缺独立 decoction/usage span。 | none |
| 麻黄附子甘草汤 | editorial_contaminated | keep_as_is | medium | medium | ZJSHL-CH-014-P-0069 | 主行含赵本变体，且没有额外 usage/decoction span。 | none |
