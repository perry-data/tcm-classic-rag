# Commentarial Eval Snapshot

## handoff bundle 核心统计

当前接入所依赖的 handoff bundle 已达到可接入状态，核心规模如下：

- commentarial unit 总数：`711`
- 刘渡舟单元：`438`
- 郝万山单元：`273`
- anchor 类型分布：`exact=549`、`theme=97`、`multi=59`、`excerpt=6`
- manual review queue：`64`
- `unresolved_multi`：`10`
- theme display tier：`tier_1=55`、`tier_2=20`、`tier_3=1`、`tier_4=21`

从 acceptance report 可以直接确认两条关键硬约束已经在数据侧成立：

- `all_units_never_use_in_primary_true = true`
- `all_units_use_for_confidence_gate_false = true`

这意味着运行时只需要维持保守接入规则，就可以在不破坏 canonical 主链路的前提下安全接入名家层。

## 当前测试与回归摘要

本轮新增并通过了 `tests/test_commentarial_route_robustness.py`，与原有 `tests/test_commentarial_integration.py` 共同形成两层保障：

- commentarial integration 基线：`9` 项测试通过
- route robustness + 红线回归：`7` 项测试通过
- 本轮 commentarial 相关回归合计：`16` 项测试通过

新增回归主要覆盖了三类真实用户表达差异：

- named 口语变体：如“刘老怎么看第141条”“郝万山老师怎么看桂枝汤”
- comparison 口语变体：如“两位老师对少阳病的解释有何区别”
- meta learning 口语变体：如“学习伤寒论有什么方法”

同时还验证了以下红线未被破坏：

- commentarial 不进入 `primary_evidence`
- commentarial 不参与 confidence gate
- assistive 下 canonical 主证据仍存在
- `unresolved_multi` 不会成为唯一主锚
- `tier_4_do_not_default_display` 不会默认进入正文
- named / comparison / meta route 不污染 canonical citation 结构

## 真实 API 样例摘要

本轮已通过真实本地 HTTP 调用生成：

- [commentarial_api_examples.json](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/commentarial_api_examples.json)
- [commentarial_api_smoke_checks.md](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/commentarial_api_smoke_checks.md)

四类 query 的实际结果如下：

- `刘渡舟怎么看第141条？`
  命中 `named_view`，返回刘渡舟单家视角；canonical 侧因强证据不足，整体 answer mode 为 `weak_with_review_notice`。
- `两家如何解释少阳病？`
  命中 `comparison_view`，返回刘渡舟与郝万山双分区，同时 canonical 侧仍保有主证据与 citation。
- `怎么学《伤寒论》？`
  命中 `meta_learning_view`，返回学习法 / 教学视角区块，其中主展示与折叠展示并存。
- `桂枝汤是什么？`
  命中 `assistive_view`，canonical `primary_evidence` 仍在主展示位，commentarial 只作为折叠补充解读。

真实 API smoke 结果还额外确认：

- 四个样例的 HTTP `response_status` 全部为 `200`
- payload 顶层字段保持稳定
- `query` 字段已回显原始用户问句
- assistive 默认折叠仍成立
- commentarial 的 `never_use_in_primary` 与 `use_for_confidence_gate=false` 仍然成立

## 现存边界与风险点

当前仍然存在以下开放边界：

- 显式名家问句在 canonical 强证据不足时，仍可能返回 `weak_with_review_notice`
- `unresolved_multi` 仍保留人工复核，不做单主锚化
- `tier_4_do_not_default_display` 主题继续被排除在默认正文外
- source-aware anchor resolution 仍以“按来源保守挂接”为主，不追求跨讲稿的全局统一编号

## 为什么这些边界不构成项目失败

这些边界并不说明系统“做不出来”，恰恰说明本项目把“证据强弱”和“解释丰富度”分开处理了。

如果为了演示效果而把名家讲稿直接并入 `primary_evidence`，或者为了看起来更完整而把 `unresolved_multi` 强行定为唯一主锚，那么系统虽然会显得更“满”，但会明显削弱证据溯源的可信度。当前方案选择保守设计：让 canonical 层负责主证据与 citation，让 commentarial 层负责解释、比较与学习辅助。这种分层不仅更符合论文主题中的“检索增强生成与证据溯源”要求，也更适合在答辩时说明工程边界、风险控制与设计取舍。
