# Commentarial Demo Summary

## 当前能力概述

本系统已在 canonical-first RAG 主链路不变的前提下，完成 commentarial layer 的最小可用接入。当前名家层能够以“独立解释层”的身份参与回答组织，用于补充刘渡舟、郝万山两家对《伤寒论》条文、证候、方证与学习方法的说明，但不会替代 canonical 主证据层，也不会改写现有 `strong / weak_with_review_notice / refuse` 三模式框架。

结合本轮真实 API 样例，可以确认 commentarial 已经具备四类最小路由能力：

- `named_view`：面向点名名家的单家视角，例如“刘渡舟怎么看第141条？”
- `comparison_view`：面向两家并列比较，例如“两家如何解释少阳病？”
- `meta_learning_view`：面向学习方法、教学视角与读书路径，例如“怎么学《伤寒论》？”
- `assistive_view`：面向默认问法下的折叠补充，例如“桂枝汤是什么？”

## 四类 route 的一句话解释

- `named_view`：在不动 canonical 主证据的前提下，单独抽取指定名家的解释单元，形成“某家怎么看”的旁路视角。
- `comparison_view`：将刘渡舟、郝万山分区展示，帮助用户对比两家解释框架，而不是把两家内容混成一个主结论。
- `meta_learning_view`：优先调用“学习方法 / 教学导向 / 六经框架”类单元，用于支持“怎么学《伤寒论》”这类元学习问题。
- `assistive_view`：默认问法下只提供折叠式名家补充，canonical 仍然承担主回答与主引用。

## 关键边界说明

- canonical layer 仍是默认主证据层。
- commentarial layer 默认不进入 `primary_evidence`。
- commentarial layer 默认不参与 confidence gate。
- assistive 模式下，名家内容默认折叠，不能压过 canonical 回答。
- `unresolved_multi` 不会被强行当作唯一主锚，只允许折叠或人工复核。
- `tier_4_do_not_default_display` 主题不会默认进入正文展示。

## unresolved / conflict / manual review 的保守策略

本轮接入继续保持“宁可少展示，也不伪造确定性”的保守策略：

- `conflicting_source_scope`：按 source-aware 方式处理，不把两家讲稿中编号冲突的条文硬合并成一个全局主锚。
- `unresolved_multi`：不在接入层强行单主锚化，只允许折叠展示或保留人工复核。
- `manual_review_queue`：对 OCR 修补痕迹、多锚并列、低置信内容继续保留人工介入入口，不把它们包装成强证据。

## 适合演示的推荐 query

- `刘渡舟怎么看第141条？`
- `郝万山老师怎么看桂枝汤？`
- `两家如何解释少阳病？`
- `两位老师对少阳病的解释有何区别？`
- `怎么学《伤寒论》？`
- `学习伤寒论有什么方法？`
- `桂枝汤是什么？`
- `少阳病是什么意思？`

## 演示时可直接强调的结论

本轮强化后的系统，已经能够清楚展示“canonical 给主依据，commentarial 给解释层”的双层结构。它不是把名家讲稿直接塞进主证据槽，而是在真实 API 返回中稳定体现 route、section、折叠策略、source-aware 挂接与边界约束，因此可以直接作为论文截图、演示案例与答辩说明材料使用。
