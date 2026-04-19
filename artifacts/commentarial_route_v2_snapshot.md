# Commentarial Route V2 Snapshot

## 本轮做了什么

本轮把 commentarial route 从“规则命中即跳转”的 v1 逻辑，升级为“多 route 竞争打分”的 v2 planner。

当前 planner 会同时对以下 route 打分：

- `named_view`
- `comparison_view`
- `meta_learning_view`
- `assistive_view`

评分信号已经覆盖：

- 名家 alias / 显式点名
- comparison 表达
- 学习 / 读法 / 入门 / 框架 / 把握 / 理解路径表达
- 条号 / 方名 / 病名 / 六经主题表达
- query normalization 后的 route preview hit
- 冲突抑制信号

同时新增了 route debug 结构，便于输出：

- `chosen_route`
- `route_scores`
- `matched_signals`
- `rejected_signals`

## meta learning 放宽后的新增覆盖

v2 不再只把 `study_method` 当作 meta 的唯一入口。

当前 meta 已经能自然覆盖两类新增问法：

### 强 meta

- `怎么学《伤寒论》？`
- `初学者怎么读《伤寒论》？`
- `读伤寒论应该先抓框架还是先背条文？`

### 学习理解型 meta

- `初学者应该怎么理解少阳病？`
- `少阳病应该怎么理解？`
- `六经辨证入门应该先抓什么？`
- `学习伤寒论时少阳病这一块应该怎么把握？`

对这类 query，meta route 现在已经能召回：

- `study_method`
- `theory_overview`
- `summary`
- `tier_1_named_view_ok`
- `tier_2_fold_only`
- `tier_3_meta_learning_only`

但仍明确排除：

- `tier_4_do_not_default_display`

## 哪些问法仍故意不放进 meta

以下 query 仍默认保留 canonical / assistive 路径：

- `少阳病是什么意思？`
- `桂枝汤是什么？`
- `黄连汤方的条文是什么？`

原因很直接：

- 这些问法是普通解释题，不是学习方法题，也不是教学框架题。
- 如果让 meta 过度吞并普通解释题，会稀释 canonical-first 的主证据结构。

## 自然表达覆盖提升点

本轮 route v2 已经覆盖更自然的 named / comparison 表达：

### named

- `刘老对141条怎么说？`
- `刘老师这里怎么讲第141条？`
- `郝老师对桂枝汤是怎么理解的？`
- `郝万山对桂枝汤的看法是什么？`

### comparison

- `刘渡舟和郝万山对少阳病的看法有什么不同？`
- `两位老师怎么看少阳病？`
- `少阳病这两家解释有何分歧？`

这意味着 route 不再只依赖非常板的模板问句。

## 红线是否守住

本轮回归继续确认以下边界没有被打穿：

- canonical layer 仍是默认主证据层
- commentarial layer 默认不进入 `primary_evidence`
- commentarial layer 默认不参与 confidence gate
- assistive 模式下 commentarial 仍默认折叠
- `unresolved_multi` 不强行单主锚化
- `tier_4_do_not_default_display` 不默认进正文

## 测试与回归

本轮执行：

- `python -m unittest tests.test_commentarial_integration tests.test_commentarial_route_robustness tests.test_commentarial_route_v2`

结果：

- `22` 项测试通过

其中新增重点覆盖：

- named 自然表达
- comparison 自然表达
- meta learning 自然表达
- 普通解释题防误伤
- route debug 可解释性
- 红线回归

## 当前仍保留的工程边界

v2 已经是可封板的 route 版本，但仍保留一条有意识的保守边界：

- route 命中 `meta_learning_view`，不等于 canonical 主回答一定能升到 `strong`

例如：

- `六经辨证入门应该先抓什么？`

当前 route 已能稳定进入 meta，且 commentarial section 会返回教学导向内容；但最终 `answer_mode` 仍可能受 canonical 证据条件影响。这不属于 route 失败，而是 canonical-first 主链路仍在发挥约束作用。
