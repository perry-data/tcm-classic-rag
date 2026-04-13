# Frontend UI/UX Polish v1

## 范围

本轮只处理聊天页的简约化修缮，不改技术栈、不改 payload contract、不新增产品功能。

本次收口的 4 个问题：

- 左侧历史栏改为稳定侧栏，列表区独立滚动
- `新建对话` 回到真正空白态，不残留旧会话状态
- 输入区明显收敛，减少高度和视觉重量
- 回复区突出回答正文，弱化证据/引用/提示的厚重堆叠感

## 代码改动

### `frontend/index.html`

- 为主消息区新增独立滚动容器 `#chat-body`
- 收紧 sidebar 文案和按钮文案
- 收紧 composer 文案、输入行数和按钮文案
- 输入框改成更极简的两行起始高度
- 输入行为改为 `Enter` 发送、`Shift + Enter` 换行
- 保留现有功能结构，但减少冗余说明文本

### `frontend/app.js`

- 新增 `resetComposerState()`，统一清空输入框和示例抽屉
- 新增 `clearActiveConversationState()`，统一清理：
  - `activeConversationId`
  - `activeConversation`
  - `pendingTurn`
  - `conversationLoading`
  - 进行中的 conversation request 序号
- 将 `新建对话` 改为回到空白起始态，而不是立即创建空会话
- 保留首次发送时的自动建会话流程，继续复用现有 `ensureConversationForSend()`
- 主区在空态/加载态下同步清空旧消息 DOM，避免旧 evidence / citation / pending 视觉残留
- 主区滚动改为操作 `#chat-body`，不再依赖整页滚动
- 调整 assistant 消息渲染顺序，让回答正文先于状态总结出现

### `frontend/styles.css`

- 全页改成更克制的浅暖中性色体系，移除重玻璃感和强装饰背景
- 将布局改为桌面端双列固定高度：
  - sidebar 自身稳定
  - 历史列表独立滚动
  - 主消息区独立滚动
- 缩小标题、圆角、padding、阴影和边框强度
- 收紧会话列表项高度和菜单按钮体积
- 收紧 composer 高度、textarea 高度和操作区留白
- 将回复区改成“正文优先、次级信息弱化”的轻量层级
- review/refuse callout 改为轻提示条，而不是厚重高权重卡片
- evidence / citation 模块改为更轻的列表式视觉，不再层层厚卡片堆叠

### `backend/api/minimal_api.py`

- 将本地最小 HTTP server 从 `HTTPServer` 切换为 `ThreadingHTTPServer`
- 不改任何 conversations / answers contract
- 只解决浏览器并发请求 `HTML + CSS + JS + conversations API` 时的阻塞问题，避免聊天页停留在初始化态

### `backend/retrieval/minimal.py`

- 将 retrieval SQLite 连接改为 `check_same_thread=False`
- 让线程版本地 server 在处理问答请求时仍可安全复用既有 retrieval 连接

## 验收关注点

- 左侧历史栏在桌面端保持稳定，列表区可单独滚动
- `新建对话` 后主区回到空白态，旧选中、旧消息、旧 pending 和旧错误提示不再残留
- 首次发送仍能正常触发创建新会话并写入消息
- 输入区和回复区都出现了肉眼可见的“收敛”
- 页面整体更偏简约、轻量、稳定，而不是更花或更厚

## 本地检查

已通过：

- `node --check frontend/app.js`
- `PYTHONPYCACHEPREFIX=/tmp/tcm_pycache python3 -m py_compile backend/api/minimal_api.py`

## 截图产物

建议配套查看：

- `artifacts/frontend_uiux_polish_v1/sidebar_stable.png`
- `artifacts/frontend_uiux_polish_v1/new_chat_reset.png`
- `artifacts/frontend_uiux_polish_v1/composer_compact.png`
- `artifacts/frontend_uiux_polish_v1/assistant_compact.png`
