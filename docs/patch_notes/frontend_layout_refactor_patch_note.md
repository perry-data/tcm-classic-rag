# Frontend Layout Refactor Patch Note

## 本轮目标

本轮不再继续在旧“表单页 + 结果面板”结构上做局部补丁，而是在现有单页前端内完成一次受控重构：

- 将页面改成单轮对话式研读页
- 把当前回答组织成一条完整的 assistant response
- 把主依据 / 补充依据 / 核对材料 / 引用 / 改问建议收束为“当前回答的展开区”
- 修复 evidence card 标题 / 正文重复的问题

## 本轮范围

仅改动：

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

并补充：

- `docs/patch_notes/frontend_layout_refactor_patch_note.md`
- `artifacts/demo/frontend_layout_refactor_demo.md`
- `artifacts/demo/frontend_layout_refactor_before_after.md`

本轮未改动：

- 后端 retrieval / rerank / prompt 主逻辑
- answer payload 顶层字段语义
- evaluator / goldset / 评估逻辑
- 多轮会话系统
- 前端技术栈

## 页面结构重构

### 变更前

- 顶部是主表单区
- 中部是 summary + answer + 多个整页散落 section
- 用户问题和系统回答不在同一阅读轴线
- 证据区更像报表面板，而不是当前回答的展开

### 变更后

页面改为三层：

1. 对话展示区
   - `user-message-card`
   - `assistant-message`
2. 当前回答的展开区
   - 主依据
   - 补充依据
   - 核对材料
   - 回答引用
   - 改问建议
3. 底部 composer
   - 输入框
   - 提交按钮
   - 样例入口（降级为二级入口）

关键变化：

- 输入区不再占据页面顶部主视觉
- `query` 显示在回答上方，形成单轮阅读流
- `strong / weak / refuse / error` 都围绕一条 assistant response 组织，而不是散落成多个独立页块

## 代码改动

### `frontend/index.html`

- 删除顶部主表单 + summary panel 结构
- 新增 `user-message-card`，用于展示当前用户问题
- 新增 `assistant-message`，统一承接：
  - mode summary
  - progress
  - answer text
  - disclaimer
  - review / refuse / error callout
- 将证据相关 section 全部收纳到 `assistant-supporting`
- 将输入区改为页面底部 composer，并把样例入口改为 `details` 二级入口

### `frontend/styles.css`

- 重写页面布局样式，使其更像单轮对话页而不是表单页
- 新增用户消息气泡与 assistant response card 样式
- 为回答主体和展开区建立层级：
  - 回答正文优先
  - 证据区次级
  - 核对材料默认折叠
- 新增底部 composer 样式，并在桌面端使用 sticky bottom 形式承接继续提问
- 保留原有 mode / progress / callout / evidence card 的语义色彩，但重组在新的信息架构内

### `frontend/app.js`

- 保留现有流式增强、同步回退、超时、中断、重试逻辑
- 增加 `setQueryEcho()`，把当前问题稳定渲染到 user card
- 增加 `scrollConversationIntoView()`，提交后将单轮问答区域带回视口
- 保留 `review` 默认折叠逻辑
- 新增 evidence / citation 标题解析与去重逻辑
- 暴露最小 `window.__frontendTestHooks`，用于本地 DOM 仿真验证渲染结果

## Evidence Card 去重规则

本轮在前端实现统一标题策略，不改 payload：

### 1. 主文 / 正文类优先使用结构化简标题

对以下来源对象，不再优先直接使用原始正文首句做 `h3`：

- `main_passages`
- `passages`
- `ambiguous_passages`
- `annotations`
- `chunks`

改为优先生成结构化标题，例如：

- `辨太阳病脉证并治法第七 · 条文 0145`
- `辨脉法第一 · 注解 0016`
- `辨太阳病脉证并治法第七 · 条文 0145`

### 2. 标题 / 正文相似性去重

前端会对标题和 `snippet` 做：

- `NFKC` 归一化
- 去空格
- 去标点
- 小写化

若判定：

- 两者等价
- 或正文以标题为开头且高度近似

则不保留重复标题。

策略顺序：

1. 优先替换成结构化简标题
2. 若仍与正文重复，则隐藏标题

### 3. 引用区同步使用同一规则

`citations` 也复用同一标题解析规则，只在前面附加 `citation_id`，例如：

- `c1 · 辨脉法第一 · 注解 0016`

## 保留不变的状态机边界

以下逻辑保留：

- `loading`
- `strong`
- `weak_with_review_notice`
- `refuse`
- `error`
- 流式失败后回退同步请求
- retry
- `review` 默认折叠
- `Cmd/Ctrl + Enter`

本轮改变的是展示组织方式，不是这些状态的业务语义。

## 本轮验证

### 结构验证

通过真实页面 HTML 确认：

- `user-message-card` 位于 `assistant-message` 之前
- `composer-shell` 位于页面底部
- 证据与附加信息均位于 assistant card 内的 `assistant-supporting`

### 场景验证

1. `strong`
   - query：`黄连汤方的条文是什么？`
   - 实际接口返回：`answer_mode = strong`
   - 前端渲染验证：
     - `modeBadge = 可参考`
     - 主依据区可见
     - review toggle 可见
     - review body 默认折叠

2. `weak_with_review_notice`
   - query：`烧针益阳而损阴是什么意思？`
   - 实际接口返回：`answer_mode = weak_with_review_notice`
   - 前端渲染验证：
     - 标题为“需核对的回答”
     - `primary` 隐藏
     - `secondary` / `review` / `review_notice` 可见

3. `refuse`
   - query：`书中有没有提到量子纠缠？`
   - 实际接口返回：`answer_mode = refuse`
   - 前端渲染验证：
     - 拒答原因可见
     - 改问建议可见
     - 空证据提示可见

4. `error`
   - 方式：使用前端测试钩子模拟 `stream_and_fallback_failed`
   - 前端渲染验证：
     - `modeBadge = 请求异常`
     - 错误区可见
     - 标题为“流式与标准请求都未完成”
     - 回答正文回落为“本次请求未完成，请重试。”

### 去重样本验证

以弱结果首条注解为例：

- 原始 `title`：
  - `卫阳也荣阴也烧针益阳而损阴荣气微者谓阴虚也内经曰`
- 原始 `snippet`：
  - `卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也……`

改造后前端展示为：

- `h3 = 辨脉法第一 · 注解 0016`
- `snippet = 卫阳也，荣阴也。烧针益阳而损阴……`

因此不再出现标题 / 正文双份显示。

## 结论

本轮完成的是前端信息架构级重构，而不是视觉小修：

- 页面从“查询表单页”切换为“单轮对话式研读页”
- 证据区回收到“当前回答的展开区”
- evidence card 去重规则前移到前端统一处理
- 原有状态机与流式 / 回退 / 重试逻辑保持不变
