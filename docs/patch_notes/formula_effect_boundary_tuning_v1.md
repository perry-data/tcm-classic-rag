# formula_effect_boundary_tuning_v1

## 1. 本轮范围

本轮只做 `formula_effect_query` 的最小 primary evidence / answer assembly 优化实验：

- 保留既有 `formula_effect_query` 专用路径
- 不扩更多 family
- 不碰 annotation / annotation_links
- 不改 raw retrieval candidate 生成
- 不重写 assembler 全局逻辑

实验输入与样本集见：

- `docs/design/formula_effect_primary_prioritization_v1.md`
- `artifacts/experiments/formula_effect_regression_set_v1.json`
- `artifacts/experiments/formula_effect_before_after_v1.md`

## 2. 哪些样本改善了

本轮最明确的改善集中在 `桂枝汤` 的三种作用问法：

- `桂枝汤方有什么作用`
- `桂枝汤方主治什么`
- `桂枝汤方用于什么情况`

改善方式一致：

- `primary_evidence` 从 `safe:main_passages:ZJSHL-CH-009-P-0055`
  - `欲解外者，宜桂枝汤主之`
- 切到 `safe:main_passages:ZJSHL-CH-008-P-0215`
  - `啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣乾呕者，桂枝汤主之`

结果表现：

- answer_text 不再围绕短片段 `欲解外` 组织
- 回答开始稳定变成“基于直接使用语境解释”
- `primary_evidence` 也更像“直接作用依据”，而不是仅仅“提到该方的承接句”

`竹叶石膏汤方有什么作用` 继续保持稳定：

- before / after 都维持 `伤寒解后，虚羸少气，气逆欲吐`
- 说明 v1 没有破坏原本已经稳定的正样本

## 3. 哪些只是边界守住

以下样本本轮不追求“更好”，重点是“不被误吸”：

### 3.1 组成类

- `桂枝汤方由什么组成`
- `竹叶石膏汤方的组成是什么`

结果：

- 继续走组成类路径
- 继续按方文组成直读输出
- 没有被 formula_effect v1 改写成作用解释

### 3.2 条文类

- `桂枝汤方的条文是什么`
- `黄连汤方的条文是什么`

结果：

- 继续按条文 / 方文查看输出
- 没有被作用类 answer assembly 误吸

### 3.3 比较类

- `桂枝汤方和麻黄汤方有什么区别`
- `桂枝汤方比麻黄汤方多了什么`

结果：

- 继续走 comparison 专用路径
- primary 仍以两侧方文为主
- 没有被单方作用类 primary prioritization 打断

### 3.4 跨 family 控制样本

- `什么是发汗药`
- `桂枝汤是发汗药吗`
- `太阳病是什么意思`
- `书中有没有提到量子纠缠`

结果：

- definition priority 的既有改善保持不变
- `太阳病是什么意思` 维持原路线
- refusal 控制样本仍拒答

## 4. 哪些仍受 raw recall 或既有路由限制

### 4.1 黄连汤仍然只能 weak

`黄连汤方有什么作用` 本轮没有被误抬成 strong，这是刻意保守的结果：

- 当前能稳定拿到的直接语境仍主要在 `passages` / review 层
- 因此 after 仍是 `weak_with_review_notice`
- 这是“边界守住”，不是“没有改善”

### 4.2 太阳病这类控制样本不在本轮优化范围

`太阳病是什么意思` 当前仍是标准路径输出，并不是本轮要优化的对象。

这条样本的作用只是证明：

- formula_effect v1 没有外溢回 definition / outline 相关边界

### 4.3 raw candidate 不变时，仍只能做 assembly 级改善

本轮改善主要依赖：

- support row 的优先级调整
- context clause 的抽取清洗

没有改善的场景，很多不是因为 v1 无效，而是因为：

- raw recall 本身没带回更好的直接使用语境
- 或该 query 根本不应进入 formula_effect 路径

## 5. 本轮是否值得继续扩大

结论：`值得，但应继续保持“小步扩大”`

原因：

- before / after 显示 raw recall 基本不变，但 `primary_evidence` 与 `answer_text` 已出现明确改善
- 至少三条代表性 query 已从短片段/承接句切回更像“直接作用依据”的主条
- 组成类 / 条文类 / 比较类边界目前守住
- `竹叶石膏汤` 这类稳定正样本没有回归
- `黄连汤` 这类 review-only 样本也没有被误抬

建议的下一步仍应维持同样节奏：

- 继续在 formula_effect family 内做小批量扩样
- 优先观察是否还有 `宜X汤 / 与X汤`、多方并列、校勘噪声导致的坏 primary
- 暂不扩大到新 family，更不要顺手重写 retrieval 或 annotation
