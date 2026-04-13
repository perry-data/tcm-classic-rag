# Chat History v1 Patch Note

## 新增页面 / 组件 / API

### 前端

- 将原单轮页面重构为 `sidebar + current conversation` 两栏布局
- 新增 sidebar 历史会话列表
- 新增 `New chat`
- 新增历史搜索框
- 新增当前会话高亮
- 新增单条会话 `...` 菜单与 `Delete`
- 新增会话空状态、加载状态、无结果状态
- 新增多轮消息流渲染：
  - `user` 消息卡片
  - `assistant` 消息卡片
  - pending assistant 占位
- 新增 `/chat/{id}` 前端壳路由支持

### 后端

- 新增独立会话持久化层：`backend/chat_history/store.py`
- 新增最小 conversation API：
  - `POST /api/v1/conversations`
  - `GET /api/v1/conversations`
  - `GET /api/v1/conversations/{id}`
  - `DELETE /api/v1/conversations/{id}`
  - `POST /api/v1/conversations/{id}/messages`
- 新增前端壳路由：
  - `GET /chat`
  - `GET /chat/{id}`
- 新增独立 SQLite 持久化文件默认路径：
  - `artifacts/chat_history_v1.db`

## 仍未实现

- project / folder / archive 管理
- shared link / shared conversations
- 会话重命名
- 多端同步
- Archive 视图与恢复
- 会话级 streaming persistence 专线
- 大规模历史列表性能优化

## 已知风险

- 当前 `POST /api/v1/conversations/{id}/messages` 走的是最小同步实现；前端有 pending 状态，但未做单独的 conversation-stream transport。
- 完整端到端发送仍依赖当前本地检索模型与 FAISS 资源可用；如果本机缺少离线模型缓存，服务启动会失败。
- 历史搜索当前为 SQLite `LIKE` 方案，适合 v1 最小量级，不包含 FTS 专项优化。
- 删除为物理删除；archive 结构仅在数据层设计上预留，未暴露 UI。

## 如何手工验证

### 基础验证

1. 启动服务：
   - `python -m backend.api.minimal_api --host 127.0.0.1 --port 8000`
2. 打开：
   - `http://127.0.0.1:8000/`
3. 点击 `New chat`
4. 确认左侧出现新会话，主区显示“当前会话还没有消息”
5. 发送第一条问题
6. 确认：
   - 主区出现 user / assistant 两条新消息
   - 左侧标题由首问自动生成
7. 再发送第二条问题
8. 确认消息继续追加到当前会话而不是覆盖旧内容

### 历史恢复

1. 再创建一个新会话并发送另一条问题
2. 回到左侧点击第一个会话
3. 确认主区恢复该会话完整消息流
4. 在该旧会话下继续发送
5. 确认新消息继续落在该旧会话下

### 搜索

1. 在 sidebar 搜索框输入首问关键词
2. 确认会话列表按标题或消息内容过滤
3. 点击任意结果
4. 确认主区直接打开对应会话

### 删除

1. 在任意会话条目打开 `...`
2. 点击 `Delete`
3. 在确认弹窗中确认
4. 确认：
   - 左侧会话消失
   - 若删除的是当前会话，主区回到空白态

## 本地验证记录

已完成：

- `python3 -m py_compile backend/api/minimal_api.py backend/chat_history/__init__.py backend/chat_history/store.py`
- `node --check frontend/app.js`
- 离线自测 `ConversationStore`：
  - 创建会话
  - 追加消息
  - 标题自动生成
  - 关键词搜索
  - 删除会话
- 路由辅助逻辑自测：
  - `/chat/{id}` 壳路由判定
  - conversation detail / messages route 判定

受本机离线模型缓存缺失影响，未在当前环境完成完整 `minimal_api` 启动后的端到端消息发送验证。
