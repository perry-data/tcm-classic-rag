# Frontend Layout Refactor Demo

## 演示目标

本轮演示重点是两件事：

1. 页面是否已经从“表单页 / 结果面板”切换为“单轮对话式研读页”
2. evidence card 是否已经修掉标题 / 正文重复问题

## 新布局核心结构

页面现在按单轮阅读流组织：

1. 用户问题卡
   - 展示当前 `query`
2. assistant response card
   - 模式头
   - 回答正文
   - disclaimer
   - review / refuse / error callout
3. 当前回答展开区
   - 主依据
   - 补充依据
   - 核对材料
   - 回答引用
   - 改问建议
4. 底部 composer
   - 输入框
   - 提交按钮
   - 二级样例入口

这意味着：

- 输入框已从顶部主区域移到底部
- 用户问题与系统回答在同一轴线上
- 证据不再是另一页结果面板，而是当前回答的展开

## 场景演示

### 1. Strong

query：

- `黄连汤方的条文是什么？`

真实接口返回：

- `answer_mode = strong`

前端在新布局下的表现：

- 用户问题显示在 `user-message-card`
- assistant card 顶部 badge 显示 `可参考`
- 回答正文位于主体区优先阅读
- 主依据区可见并位于回答下方
- 核对材料 toggle 可见，但默认折叠

验证摘要：

- `modeBadge = 可参考`
- `primaryVisible = true`
- `reviewToggleVisible = true`
- `reviewCollapsed = true`

### 2. Weak With Review Notice

query：

- `烧针益阳而损阴是什么意思？`

真实接口返回：

- `answer_mode = weak_with_review_notice`

前端在新布局下的表现：

- assistant card 顶部标题为“需核对的回答”
- 主体区先展示回答正文
- `review_notice` 单独高亮
- `secondary_evidence` 和 `review_materials` 位于下方展开区
- `primary_evidence` 不显示

验证摘要：

- `modeTitle = 需核对的回答`
- `primaryVisible = false`
- `secondaryVisible = true`
- `reviewVisible = true`
- `reviewNoticeVisible = true`

### 3. Refuse

query：

- `书中有没有提到量子纠缠？`

真实接口返回：

- `answer_mode = refuse`

前端在新布局下的表现：

- assistant card 顶部标题为“当前不支持这样回答”
- 拒答原因在主体区下方单独展示
- 改问建议保留在当前回答的展开区
- 因无证据条目，空证据提示出现

验证摘要：

- `modeTitle = 当前不支持这样回答`
- `refuseVisible = true`
- `followupsVisible = true`
- `emptyEvidenceVisible = true`
- `followupCount = 3`

### 4. Error

测试方式：

- 使用前端测试钩子模拟 `stream_and_fallback_failed`

前端在新布局下的表现：

- 顶部 mode badge 切换为 `请求异常`
- 错误区显示在 assistant response card 内
- 标题为 `流式与标准请求都未完成`
- 回答正文收尾为 `本次请求未完成，请重试。`
- 页面仍保持同一条对话轴线，而不是跳出到独立错误页

验证摘要：

- `modeBadge = 请求异常`
- `errorVisible = true`
- `errorTitle = 流式与标准请求都未完成`
- `answerText = 本次请求未完成，请重试。`

## Evidence Card 去重演示

### 去重样本

弱结果首条注解原始数据：

- `title = 卫阳也荣阴也烧针益阳而损阴荣气微者谓阴虚也内经曰`
- `snippet = 卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也……`

旧展示问题：

- 标题和正文几乎是同一句内容
- 用户会看到一条长句以两种字号重复出现

新展示结果：

- evidence card 标题：
  - `辨脉法第一 · 注解 0016`
- citation 标题：
  - `c1 · 辨脉法第一 · 注解 0016`
- 正文仍显示真实 `snippet`

验证摘要：

- `titleEqualsSnippet = false`
- `titleContainedInSnippet = false`

## 结构性结论

本轮不是换一层皮，而是把页面阅读路径重组为：

- 先看问题
- 再看回答
- 然后在回答下面展开依据与附加信息
- 输入器留在底部，便于自然继续提问

这已经满足“单轮对话式研读页面”的目标边界。
