# Formula Medium Span Fix Before/After v1

## Summary

| formula | before_span | after_span | before_comp | after_comp | before_decoction | after_decoction | before_usage | after_usage | confidence | conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 乌梅丸 | ["ZJSHL-CH-015-P-0221", "ZJSHL-CH-015-P-0221"] | ["ZJSHL-CH-015-P-0219", "ZJSHL-CH-015-P-0225"] | ["ZJSHL-CH-015-P-0221"] | ["ZJSHL-CH-015-P-0221", "ZJSHL-CH-015-P-0222", "ZJSHL-CH-015-P-0223"] | [] | ["ZJSHL-CH-015-P-0225"] | [] | ["ZJSHL-CH-015-P-0219", "ZJSHL-CH-015-P-0220"] | medium -> high | 完整组成、丸法/服法和蛔厥使用语境均已定位；展示层去除赵本异文噪声，primary 回指仍只会落到 safe main passages。 |
| 旋复代赭石汤 | ["ZJSHL-CH-010-P-0106", "ZJSHL-CH-010-P-0106"] | ["ZJSHL-CH-010-P-0104", "ZJSHL-CH-010-P-0106"] | ["ZJSHL-CH-010-P-0106"] | ["ZJSHL-CH-010-P-0106"] | [] | [] | [] | ["ZJSHL-CH-010-P-0104", "ZJSHL-CH-010-P-0105"] | medium -> medium | 组成和使用语境可审计，但当前可用数据中未找到独立煎服法 span，故不升 high。 |
| 栀子浓朴汤 | ["ZJSHL-CH-009-P-0170", "ZJSHL-CH-009-P-0170"] | ["ZJSHL-CH-009-P-0168", "ZJSHL-CH-009-P-0170"] | ["ZJSHL-CH-009-P-0170"] | ["ZJSHL-CH-009-P-0170"] | [] | [] | [] | ["ZJSHL-CH-009-P-0168", "ZJSHL-CH-009-P-0169"] | medium -> medium | 使用语境已补齐，但没有独立煎服法 span，组成行仍来自 variant-heavy 行，故保持 medium。 |
| 桂枝甘草龙骨牡蛎汤 | ["ZJSHL-CH-009-P-0298", "ZJSHL-CH-009-P-0298"] | ["ZJSHL-CH-009-P-0296", "ZJSHL-CH-009-P-0298"] | ["ZJSHL-CH-009-P-0298"] | ["ZJSHL-CH-009-P-0298"] | [] | [] | [] | ["ZJSHL-CH-009-P-0296", "ZJSHL-CH-009-P-0297"] | medium -> high | 方名、组成和使用语境连续且边界稳定；无相邻方串入，故可按 composition+usage 对象升 high。 |
| 茵陈蒿汤 | ["ZJSHL-CH-011-P-0141", "ZJSHL-CH-011-P-0141"] | ["ZJSHL-CH-011-P-0141", "ZJSHL-CH-011-P-0143"] | ["ZJSHL-CH-011-P-0141"] | ["ZJSHL-CH-011-P-0141"] | [] | ["ZJSHL-CH-011-P-0143"] | [] | ["ZJSHL-CH-011-P-0200"] | medium -> high | 组成、煎服法和精确使用语境均已定位，且 composition display 无显著异文污染，故可升 high。 |
| 麻黄附子甘草汤 | ["ZJSHL-CH-014-P-0069", "ZJSHL-CH-014-P-0069"] | ["ZJSHL-CH-014-P-0067", "ZJSHL-CH-014-P-0071"] | ["ZJSHL-CH-014-P-0069"] | ["ZJSHL-CH-014-P-0069"] | [] | ["ZJSHL-CH-014-P-0071"] | [] | ["ZJSHL-CH-014-P-0067", "ZJSHL-CH-014-P-0068"] | medium -> high | 组成、使用语境和煎服法连续且与相邻麻黄附子细辛汤边界清楚，故可升 high。 |

## Per Formula Notes

### 乌梅丸

- issue_categories: `["composition span incomplete", "decoction/preparation span missing", "usage_context span missing", "composition display variant contaminated"]`
- composition_display_text: `乌梅丸方：乌梅三百个；细辛六两；乾姜十两；黄连一斤；当归四两；附子六两，炮；蜀椒四两，去子；桂枝六两；人参六两；黄柏六两`
- span_fix_reason: 补入 ZJSHL-CH-015-P-0222/ZJSHL-CH-015-P-0223 作为连续组成，并登记 ZJSHL-CH-015-P-0225 为丸法/服法，ZJSHL-CH-015-P-0219/0220 为使用语境。
- confidence_reason: 完整组成、丸法/服法和蛔厥使用语境均已定位；展示层去除赵本异文噪声，primary 回指仍只会落到 safe main passages。
- post_fix_classification: `high`

### 旋复代赭石汤

- issue_categories: `["title / canonical display variant contaminated", "composition display variant contaminated", "usage_context span missing", "decoction span still absent in available source"]`
- composition_display_text: `旋复代赭石汤方：旋复花三两；人参二两；生姜五两，切；半夏半升，洗；代赭石一两；大枣十二枚，擘；甘草三两，炙`
- span_fix_reason: 补入 ZJSHL-CH-010-P-0104/0105 为使用语境，并对标题和代赭石药味做 variant-stripped display。
- confidence_reason: 组成和使用语境可审计，但当前可用数据中未找到独立煎服法 span，故不升 high。
- post_fix_classification: `medium`

### 栀子浓朴汤

- issue_categories: `["usage_context span missing", "composition display variant contaminated", "decoction span still absent in available source"]`
- composition_display_text: `栀子浓朴汤方：栀子十四枚，擘；浓朴四两，姜炙，去皮；枳实四枚，水浸，去穣，炒`
- span_fix_reason: 补入 ZJSHL-CH-009-P-0168/0169 为使用语境，并清理组成展示中的赵本异文噪声。
- confidence_reason: 使用语境已补齐，但没有独立煎服法 span，组成行仍来自 variant-heavy 行，故保持 medium。
- post_fix_classification: `medium`

### 桂枝甘草龙骨牡蛎汤

- issue_categories: `["usage_context span missing", "composition display variant contaminated", "composition-only object"]`
- composition_display_text: `桂枝甘草龙骨牡蛎汤方：桂枝一两；甘草二两；牡蛎二两，熬；龙骨二两`
- span_fix_reason: 补入 ZJSHL-CH-009-P-0296/0297 为使用语境，并清理桂枝去皮、甘草炙等异文展示噪声。
- confidence_reason: 方名、组成和使用语境连续且边界稳定；无相邻方串入，故可按 composition+usage 对象升 high。
- post_fix_classification: `high`

### 茵陈蒿汤

- issue_categories: `["decoction span missing", "usage_context span missing"]`
- composition_display_text: `茵陈蒿汤方：茵陈蒿六两；栀子十四枚，擘；大黄二两，去皮`
- span_fix_reason: 补入 ZJSHL-CH-011-P-0143 为煎服法，补入 ZJSHL-CH-011-P-0200 为精确方名使用语境。
- confidence_reason: 组成、煎服法和精确使用语境均已定位，且 composition display 无显著异文污染，故可升 high。
- post_fix_classification: `high`

### 麻黄附子甘草汤

- issue_categories: `["usage_context span missing", "decoction span missing", "composition display variant contaminated"]`
- composition_display_text: `麻黄附子甘草汤方：麻黄二两，去节；甘草二两，炙；附子一枚，炮，去皮`
- span_fix_reason: 补入 ZJSHL-CH-014-P-0067/0068 为使用语境，ZJSHL-CH-014-P-0071 为煎服法，并去除附子破八片异文展示噪声。
- confidence_reason: 组成、使用语境和煎服法连续且与相邻麻黄附子细辛汤边界清楚，故可升 high。
- post_fix_classification: `high`
