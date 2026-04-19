# Commentarial Route V2 Design

## 1. 背景

commentarial layer v1 已经完成最小可用接入，但 route 判定仍明显偏规则链：

- `named_view` 主要靠名家 alias + `怎么看 / 怎么讲` 一类提示词。
- `comparison_view` 主要靠 `两家 / 区别 / 不同` 一类提示词。
- `meta_learning_view` 基本只对 `怎么学 / 学习方法 / 入门` 这类强学习表达敏感。
- 默认问法仍落到 assistive，但 route 本身缺少可解释的竞争过程。

这会带来两个问题：

1. 路由覆盖偏窄。真实用户更常见的是自然表达、绕一点的表达、混合表达，而不是人工写出来的提示词模板。
2. meta route 过窄。它更像“只收 study_method”，对“六经框架如何把握”“初学者如何理解少阳病”这一类教学导向问题召回不足。

## 2. 为什么不直接上复杂分类器

本轮目标不是重构系统，也不是引入新的外部分类服务。这里继续保持轻量工程化方案，原因有三条：

- 当前 bundle 规模只有 711 个 commentarial unit，route 类型也只有四类，先做可解释的 planner 成本更低。
- 论文与答辩需要能解释“为什么分到这个 route”，黑盒分类器反而不利于展示工程取舍。
- 当前系统已有明确红线：canonical-first、commentarial 不进 `primary_evidence`、不进 confidence gate、`tier_4` 不默认展示。轻量 planner 更容易围绕这些红线做约束。

因此 v2 选择的是“混合评分式 route planner”，而不是外接复杂模型分类器。

## 3. v2 的核心改动

### 3.1 从 if-else 命中链改为 route 竞争打分

`detect_route()` 现在会同时为四个候选 route 打分：

- `named_view`
- `comparison_view`
- `meta_learning_view`
- `assistive_view`

每个 route 都不是“命中一个 hint 就直接跳转”，而是把多个信号累加后再竞争。

### 3.2 纳入的主要信号

当前评分至少综合了这些信号：

- 名家 alias / 显式点名
- comparison 表达
- 学习 / 读法 / 框架 / 入门 / 把握 / 理解路径表达
- 条号、方名、病名、六经主题表达
- query normalization 后的 route 预览命中
- 冲突抑制信号

其中 “query normalization 后的命中” 不是直接跑正式检索，而是基于 `focus_text` 对 commentarial unit 做轻量 preview，给 planner 一个 route-aware 的语义命中参考。

### 3.3 route 竞争的设计意图

这个竞争逻辑重点解决三类冲突：

- `两位老师怎么看少阳病？`
  不再被 `怎么看` 误吸到 named，而是因为双家 + comparison frame + framework topic 被 comparison 拉高。
- `初学者应该怎么理解少阳病？`
  不再因为没有 `怎么学` 被错过，而是由 meta topic band + 六经/病机类主题信号进入 meta。
- `刘老怎么讲少阳病？`
  即便出现 `怎么理解 / 怎么讲` 这类 meta 易混表达，显式点名名家仍会把 route 拉回 named。

## 4. meta learning 的分层放宽

### 4.1 v1 为什么窄

v1 在运行时实际上把 meta 候选压得很死：

- 路由侧只认强学习表达。
- 排序侧又进一步偏向 `study_method`。
- theme 里虽然有不少 `theory_overview / summary / 六经框架` 单元，但没有被自然纳入 meta。

结果就是：

- “怎么学《伤寒论》”能进 meta。
- “少阳病应该怎么理解”“六经辨证怎么把握”这类教学理解题不够自然。

### 4.2 v2 的三层 meta 口径

v2 没有把 meta 一把放开，而是分成三层：

#### 第一层：强 meta

典型问法：

- 怎么学《伤寒论》
- 初学者怎么读《伤寒论》
- 读伤寒论应该先抓框架还是先背条文

这类 route 会优先放大：

- `study_method`
- `tier_3_meta_learning_only`
- 教学导向 theme

#### 第二层：学习理解型 meta

典型问法：

- 初学者应该怎么理解少阳病
- 少阳病应该怎么理解
- 六经辨证入门应该先抓什么
- 学习伤寒论时少阳病这一块应该怎么把握

这类 route 在 `study_method` 之外，还允许：

- `theory_overview`
- `summary`
- 教学相关的 `tier_1_named_view_ok / tier_2_fold_only / tier_3_meta_learning_only` theme

也就是说，meta 不再只召回“学习方法”本身，而会放进“理解这个主题时需要的框架性说明”。

#### 第三层：普通解释题

典型问法：

- 少阳病是什么意思
- 桂枝汤是什么
- 黄连汤方的条文是什么

这类仍默认回到 canonical / assistive，不会轻易被 meta 吞掉。

## 5. v2 允许哪些 unit 进入 meta

为了避免“放宽召回 = 破坏边界”，v2 仍做了强约束：

- 非 meta function 的单元不进 meta。
- `tier_4_do_not_default_display` 仍不进入默认正文。
- theme 只允许 `tier_1 / tier_2 / tier_3` 进入 meta。
- exact / multi 单元只有在具备 `study_method / theory_overview / summary` 且满足 band 条件时才可进入 meta。

换句话说，v2 放宽的是“教学导向解释单元”，不是“所有与主题相关的 commentarial 单元”。

## 6. 为什么这样放宽不会破坏 canonical-first

本轮改的是 route planner 和 meta 候选口径，不改以下红线：

- canonical layer 仍是默认主证据层
- commentarial layer 默认不进入 `primary_evidence`
- commentarial layer 默认不参与 confidence gate
- assistive 模式下 commentarial 仍默认折叠
- `unresolved_multi` 仍不强行单主锚化
- `tier_4_do_not_default_display` 仍不默认进入正文

也就是说，v2 放宽的是“名家层怎么展示得更自然”，不是“名家层去替 canonical 做主依据”。

## 7. explainability / debug 设计

v2 planner 现在会保留轻量 debug 信息，核心字段包括：

- `chosen_route`
- `route_scores`
- `matched_signals`
- `rejected_signals`

这套 debug 不需要暴露给最终用户，但对后续三件事有价值：

- 测试里解释 route 竞争结果
- 调权重时定位误判来源
- 论文里说明为什么不是纯规则命中

## 8. 当前取舍

v2 依然不是“语义分类器”，它仍是轻量工程化 planner，所以还有保守边界：

- 分数来自规则 + preview hit，而不是训练得到的概率模型。
- 某些极绕的自然语言仍可能需要继续调权重。
- 部分 meta query 的主答案 mode 仍可能受 canonical 证据约束而保持 `weak_with_review_notice` 或 `refuse`。

但在当前项目阶段，这种方案已经比 v1 更稳，同时又足够可解释、可测试、可论文化。
