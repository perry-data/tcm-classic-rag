# commentarial formula precision snapshot

## 本轮修复了什么
- 在 `assistive_view` 下增加了 formula topic 抽取，并把单方问法切换到严格方剂一致性模式。
- 对 commentarial unit 增加了 formula consistency hard gate：只有标题、条文主挂接、summary/commentary lead 明确聚焦该方的单元才允许进入 assistive 排序池。
- 对多方混讲、顺带提方、列表/索引类内容增加了保守过滤；没有高一致性单元时直接不显示 commentarial。

## 原问题为什么会发生
- 原 assistive commentarial 主要依赖宽松 lexical overlap 打分，缺少“问的是哪一个方”这一层 hard constraint。
- 许多 unit 在正文里会顺带提到别的方，导致 `小青龙汤` 之类 query 也能把 `五苓散`、`小柴胡汤` 或更宽泛的专题单元抬进前列。
- route v2 和 canonical 主回答本身没有错，错误集中在 assistive candidate pool 过宽、rerank 不够保守。

## 修复后如何保证不再串方
- `小青龙汤有哪些功效？` 现在只返回 `cmu_liu_p041`、`cmu_liu_p042` 两个小青龙汤一致单元，不再回出 `cmu_liu_p072`（五苓散）或 `cmu_liu_p105`（小柴胡汤顺带提方）。
- `桂枝汤有哪些功效？` 现在优先返回 `cmu_liu_p014`、`cmu_liu_p013`，不再回出风温/奔豚等仅顺带提到桂枝汤的单元。
- `小柴胡汤有哪些功效？` 现在返回 `cmu_hao_rw116`、`cmu_hao_rw117` 这类标题即聚焦小柴胡汤的单元，不再被“小建中汤先与、小柴胡汤后与”这一类多方条文污染。
- `五苓散有哪些功效？` 现在返回 `cmu_liu_p073`、`cmu_liu_p074`，不再回出霍乱总论或桂枝去桂加茯苓白术汤类比较/顺带提方单元。

## 哪些情况仍会保守地不显示 commentarial
- 明确是单方 query，但 bundle 中只有顺带提方、对比段、宽泛综述或索引类命中。
- 当前快照中的 `白散方有哪些功效？` 就会直接不挂 commentarial，而不是乱给其他方的名家补充。

## 红线是否守住
- canonical layer 仍是默认主证据层。
- commentarial 仍不进入 `primary_evidence`，也不参与 confidence gate。
- assistive commentarial 仍默认折叠展示。
- `tier_4_do_not_default_display`、`unresolved_multi` 等既有边界未被放宽。
- route v2 主体和 commentarial 接入架构未被推翻，只是在 assistive route 上加了单方精度约束。

## 验证
- `python -m unittest tests.test_commentarial_formula_precision`
- `python -m unittest tests.test_commentarial_integration tests.test_commentarial_route_robustness tests.test_commentarial_route_v2`
