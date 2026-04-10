# Frontend Minimal Chat Layout Demo

## 演示目标

本轮演示只验证三件事：

1. 页面是否已经从 demo panel 变成极简单轮对话页
2. strong / weak / refuse / error 四类状态是否都能在新布局下正常工作
3. evidence card 标题 / 正文重复问题是否没有回退

## 新布局摘要

当前页面结构已经收束为：

1. 轻 header
   - `TCM Classic RAG`
   - `《伤寒论》单轮研读`
   - 状态文字
2. 对话主区域
   - `user-message-card`
   - `assistant-message`
3. slim composer
   - 自适应单行输入器
   - `发送` 按钮
   - `样例` 二级入口

默认阅读顺序变为：

- 先看用户问题
- 再看回答正文
- 需要时再展开依据与补充信息

## 场景验证

验证日期：

- 2026-04-10

验证方式：

- 本地 API 实际返回模式
- 前端渲染钩子 `renderPayload / showErrorState / resolveRecordTitle` 断言

### 1. `strong`

query：

- `黄连汤方的条文是什么？`

本地 API 结果：

- `answer_mode = strong`

前端断言结果：

- `modeBadge = 可参考`
- `primaryVisible = true`
- `supportingVisible = true`
- `supportingOpen = false`
- `reviewNoticeVisible = true`

说明：

- 主依据直接留在回答下方
- 补充依据 / 核对材料 / 引用默认留在折叠区

### 2. `weak_with_review_notice`

query：

- `烧针益阳而损阴是什么意思？`

本地 API 结果：

- `answer_mode = weak_with_review_notice`

前端断言结果：

- `modeTitle = 需核对`
- `primaryVisible = false`
- `secondaryVisible = true`
- `reviewVisible = true`
- `reviewNoticeVisible = true`
- `supportingOpen = false`

说明：

- 正文和 `review_notice` 仍是第一阅读层
- 依据与核对材料仍被收在二级展开区

### 3. `refuse`

query：

- `书中有没有提到量子纠缠？`

本地 API 结果：

- `answer_mode = refuse`

前端断言结果：

- `modeBadge = 暂不支持`
- `refuseVisible = true`
- `followupsVisible = true`
- `emptyEvidenceVisible = true`
- `supportingOpen = true`
- `followupCount = 3`

说明：

- 拒答原因仍在主回答区
- 改问建议在该模式下默认展开，避免被埋掉

### 4. `error`

测试方式：

- 使用前端钩子模拟 `stream_and_fallback_failed`
- `streamError = 流式请求未能成功建立。`
- `fallbackError = 标准请求未能成功返回。`

前端断言结果：

- `modeBadge = 请求异常`
- `errorVisible = true`
- `errorTitle = 流式与标准请求都未完成`
- `answerText = 本次请求未完成，请重试。`

说明：

- 错误态仍然留在同一条 assistant response 内
- 不会退回成另一张说明页

## Evidence 去重样本

样本来源：

- `烧针益阳而损阴是什么意思？`
- `secondary_evidence[0]`

去重前原始字段：

- `title = 卫阳也荣阴也烧针益阳而损阴荣气微者谓阴虚也内经曰`
- `snippet = 卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》...`

前端去重后：

- `resolvedTitle = 辨脉法第一 · 注解 0016`
- `stillSimilar = false`

渲染断言：

- `firstSecondaryTitle = 辨脉法第一 · 注解 0016`

说明：

- 标题不再和正文重复
- 结构化简标题仍优先保住了来源辨识度

## 结论

本轮已经满足最小验收目标：

- 底部 composer 明显缩小
- 页面说明性废话大幅减少
- header 明显变轻
- 页面主轴回到“用户问题 + 系统回答”
- 证据区默认更克制
- evidence 去重没有回退
