# Formula Medium Span Fix v1

## Scope

- 本轮只处理 small gold audit v1 中 6 个 `gold_needs_span_fix` formula medium。
- 不改 prompt、前端、API payload、answer_mode、commentarial 或 definition/concept 主线。
- raw full/passages 可作为 formula span 的可审计 support，但回归确认 primary evidence 仍只来自 `safe:main_passages:*`。

## Classification

- 类别1 已可升 high: `["乌梅丸", "桂枝甘草龙骨牡蛎汤", "茵陈蒿汤", "麻黄附子甘草汤"]`
- 类别2 已修但仍保持 medium: `["旋复代赭石汤", "栀子浓朴汤"]`
- 类别3 当前不建议继续投入: `[]`

## Before/After

| formula | before_span | after_span | before_comp | after_comp | before_decoction | after_decoction | before_usage | after_usage | confidence | conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 乌梅丸 | ["ZJSHL-CH-015-P-0221", "ZJSHL-CH-015-P-0221"] | ["ZJSHL-CH-015-P-0219", "ZJSHL-CH-015-P-0225"] | ["ZJSHL-CH-015-P-0221"] | ["ZJSHL-CH-015-P-0221", "ZJSHL-CH-015-P-0222", "ZJSHL-CH-015-P-0223"] | [] | ["ZJSHL-CH-015-P-0225"] | [] | ["ZJSHL-CH-015-P-0219", "ZJSHL-CH-015-P-0220"] | medium -> high | 完整组成、丸法/服法和蛔厥使用语境均已定位；展示层去除赵本异文噪声，primary 回指仍只会落到 safe main passages。 |
| 旋复代赭石汤 | ["ZJSHL-CH-010-P-0106", "ZJSHL-CH-010-P-0106"] | ["ZJSHL-CH-010-P-0104", "ZJSHL-CH-010-P-0106"] | ["ZJSHL-CH-010-P-0106"] | ["ZJSHL-CH-010-P-0106"] | [] | [] | [] | ["ZJSHL-CH-010-P-0104", "ZJSHL-CH-010-P-0105"] | medium -> medium | 组成和使用语境可审计，但当前可用数据中未找到独立煎服法 span，故不升 high。 |
| 栀子浓朴汤 | ["ZJSHL-CH-009-P-0170", "ZJSHL-CH-009-P-0170"] | ["ZJSHL-CH-009-P-0168", "ZJSHL-CH-009-P-0170"] | ["ZJSHL-CH-009-P-0170"] | ["ZJSHL-CH-009-P-0170"] | [] | [] | [] | ["ZJSHL-CH-009-P-0168", "ZJSHL-CH-009-P-0169"] | medium -> medium | 使用语境已补齐，但没有独立煎服法 span，组成行仍来自 variant-heavy 行，故保持 medium。 |
| 桂枝甘草龙骨牡蛎汤 | ["ZJSHL-CH-009-P-0298", "ZJSHL-CH-009-P-0298"] | ["ZJSHL-CH-009-P-0296", "ZJSHL-CH-009-P-0298"] | ["ZJSHL-CH-009-P-0298"] | ["ZJSHL-CH-009-P-0298"] | [] | [] | [] | ["ZJSHL-CH-009-P-0296", "ZJSHL-CH-009-P-0297"] | medium -> high | 方名、组成和使用语境连续且边界稳定；无相邻方串入，故可按 composition+usage 对象升 high。 |
| 茵陈蒿汤 | ["ZJSHL-CH-011-P-0141", "ZJSHL-CH-011-P-0141"] | ["ZJSHL-CH-011-P-0141", "ZJSHL-CH-011-P-0143"] | ["ZJSHL-CH-011-P-0141"] | ["ZJSHL-CH-011-P-0141"] | [] | ["ZJSHL-CH-011-P-0143"] | [] | ["ZJSHL-CH-011-P-0200"] | medium -> high | 组成、煎服法和精确使用语境均已定位，且 composition display 无显著异文污染，故可升 high。 |
| 麻黄附子甘草汤 | ["ZJSHL-CH-014-P-0069", "ZJSHL-CH-014-P-0069"] | ["ZJSHL-CH-014-P-0067", "ZJSHL-CH-014-P-0071"] | ["ZJSHL-CH-014-P-0069"] | ["ZJSHL-CH-014-P-0069"] | [] | ["ZJSHL-CH-014-P-0071"] | [] | ["ZJSHL-CH-014-P-0067", "ZJSHL-CH-014-P-0068"] | medium -> high | 组成、使用语境和煎服法连续且与相邻麻黄附子细辛汤边界清楚，故可升 high。 |

## Regression

- exact formula strong after: `6/6`
- comparison strong after: `2/2`
- forbidden primary after: `0`
- primary non-safe-main after: `0`
- bad anchors top5 after: `0`
