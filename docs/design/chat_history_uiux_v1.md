# Chat History UI/UX v1

## 目标与范围

本轮目标是在不改现有 answer payload contract、不过度触碰问答主链的前提下，为当前《伤寒论》RAG MVP 增加最小历史聊天记录能力：

- 左侧历史会话列表
- 新建会话
- 点击旧会话恢复完整聊天并继续发送
- 标题自动生成
- 最小搜索（搜索标题与消息内容）
- 单条会话删除

本轮实现只面向单用户、本地同源前后端场景，不引入 project、shared link、archive 管理页或多人协作模型。

## 页面信息架构

页面采用两栏布局：

- 左侧 `history sidebar`
  - `New chat`
  - 搜索框
  - 历史会话列表
  - loading / empty / no results 状态
- 右侧 `chat panel`
  - 当前会话标题与状态
  - 当前会话完整消息流
  - 底部 composer

路由约定：

- `/`
  - 空白新会话入口
- `/chat/{conversation_id}`
  - 直接恢复指定会话

数据接口约定：

- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{id}`
- `DELETE /api/v1/conversations/{id}`
- `POST /api/v1/conversations/{id}/messages`

## 用户主路径

### 1. 新建并开始聊天

- 用户点击 `New chat`，创建一个空白会话。
- 主区显示“当前会话还没有消息”空状态。
- 用户发送第一条问题后：
  - 后端在当前会话下写入 `user` / `assistant` 消息对
  - 会话标题由首问自动截断生成
  - 左侧列表立即更新最近时间与高亮状态

### 2. 从历史恢复旧会话

- 用户点击左侧任一会话项。
- 主区根据 `GET /api/v1/conversations/{id}` 恢复完整消息流。
- 用户继续发送后，新消息继续追加到同一会话，不影响其他历史会话。

### 3. 搜索历史

- 用户在 sidebar 顶部输入关键词。
- 前端对 `GET /api/v1/conversations?search=...` 做最小 debounce。
- 搜索范围覆盖：
  - 会话标题
  - 已保存 user / assistant 消息内容
- 点击搜索结果后直接进入对应会话。

### 4. 删除会话

- 用户打开单条会话 `...` 菜单。
- 点击 `Delete` 后弹浏览器确认。
- 确认后删除会话及其消息。
- 若删除的是当前会话，主区回退到空白新会话入口态。

## 组件清单

### Sidebar

- `HistorySidebar`
- `NewChatButton`
- `HistorySearchInput`
- `ConversationList`
- `ConversationListItem`
- `ConversationItemMenu`
- `SidebarLoadingState`
- `SidebarEmptyState`
- `SidebarNoResultsState`

### Main Panel

- `ConversationHeader`
- `ConversationEmptyState`
- `ConversationLoadingState`
- `MessageFeed`
- `UserMessageCard`
- `AssistantMessageCard`
- `PendingAssistantCard`
- `Composer`
- `SampleQueries`

### Assistant Message 内部展开

- `ModeBadge`
- `ModeSummary`
- `AnswerBlock`
- `ReviewNoticeCallout`
- `RefuseReasonCallout`
- `PrimaryEvidencePanel`
- `SecondaryEvidencePanel`
- `ReviewMaterialsPanel`
- `CitationsPanel`
- `FollowupsPanel`

## 状态设计

### Sidebar 状态

- `loading`
- `empty`
- `search_no_results`
- `active_conversation_highlight`
- `deleting`

### Main 状态

- `blank_new_chat`
- `conversation_loading`
- `conversation_loaded`
- `conversation_pending_send`
- `message_render_fallback`

## 持久化与解耦策略

- 新增独立 SQLite：`artifacts/chat_history_v1.db`
- 新增表：
  - `conversations`
  - `messages`
- 会话层只保存：
  - 会话元数据
  - user / assistant 消息
  - assistant 的完整 answer payload JSON

这样做的目的：

- 不改现有主问答数据库结构
- 不改现有 `/api/v1/answers` payload
- 不要求重构 retrieval / assembler / annotation 主链

## 暂不实现内容

- project / folder / pin / star
- shared link / shared conversations
- archive 管理页
- 手动重命名会话
- 多账号或多端同步
- 虚拟滚动与大规模历史性能优化
- 会话内流式 persistence 专线
- 对现有问答主链做结构性重构
