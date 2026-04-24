# Gold Audit Minimal Fix Recommendations v1

本文件只记录 small gold audit v1 的最小修正建议；本轮未直接批量修改 registry。

| canonical_name | recommended_change_type | should_change_now | recommendation |
| --- | --- | --- | --- |
| 发汗药 | sentence_reselection | true | 下一轮应寻找更直接的 membership/definition sentence，或把当前对象标为 explanation-primary 而非 definition-primary。 |
| 乌梅丸 | span_fix | false | 下一轮补完整 composition span，再决定是否升 high。 |
| 旋复代赭石汤 | span_fix | false | 清理 canonical title display 与 composition span 后再复核。 |
| 栀子浓朴汤 | span_fix | false | 补煎服/用法 span 或明确 composition-only formula policy。 |
| 桂枝甘草龙骨牡蛎汤 | span_fix | false | 补齐 span 与 variant-stripped composition display。 |
| 茵陈蒿汤 | span_fix | false | 查找相邻煎服句并补 span。 |
| 麻黄附子甘草汤 | span_fix | false | 补 span 并记录 variant-stripped 药味。 |
| 神丹 | defer | false | 若后续要升格，必须找到非注释汇编层的稳定药名证据。 |
| 将军 | defer | false | 若要支持，应先建立药名别称对象层，而不是放入 general definition safe primary。 |
| 两阳 | defer | false | 下一轮需要一组病机解释 support object，而不是只升格命名句。 |
| 胆瘅 | alias_cleanup | true | 建议清理 review-only 对象上的 learner aliases“口苦病/胆瘅病”，防止未来 runtime 误启用。 |
