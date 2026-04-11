# Frontend Transport Hotfix Patch Note

## 本轮目标

只修当前请求链路故障：

- 修复前端“流式失败 -> 同步回退”状态机
- 修复同步 JSON 返回路径的 client disconnect 收尾

本轮不改：

- retrieval / rerank / prompt 主逻辑
- `backend/answers/assembler.py` 业务裁决
- answer payload 顶层语义
- 页面布局与视觉风格

## 最终定位到的根因

根因有两部分，但主因在前端：

1. `frontend/app.js`
   - 请求状态机把 stream 与 fallback 的 transport 生命周期都挂在全局字段上，清理与异常归因不够稳。
   - `submitQuery()` 中存在 fallback 重入风险：当流式分支返回“不可流式”并进入同步回退后，若该回退抛错，外层 `catch` 会再次发起一次 fallback。
   - `AbortError` 归因依赖全局 `activeController`，容易把当前 transport 与上一个 transport 混在一起。

2. `backend/api/minimal_api.py`
   - 流式路径已经对 `BrokenPipeError / ConnectionResetError` 做了收口。
   - 普通 `do_POST -> _send_json()` 路径没有同等级保护，客户端提前断开时会把 transport 级异常打成整段栈。

## 本轮代码改动

### `frontend/app.js`

- 将 timer / controller 清理从零散全局字段收束为当前 active transport。
- `AbortError` 改为优先绑定当前 transport 的本地 controller 归因，不再依赖可能已切换的全局 controller。
- 重写 `submitQuery()` 的主流程：
  - 先尝试 stream
  - 明确记录一次 `streamError`
  - 再最多执行一次 fallback
  - 不再允许 fallback 重入
- stream / fallback 成功后立即清掉本 transport 的 timer，避免残留软提示或误触发硬超时。
- 新增仅测试用的 `window.__frontendTestHooks.failNextRequest()`，用于可控模拟：
  - 只让流式失败
  - 让流式和同步一起失败

### `backend/api/minimal_api.py`

- 新增 `_is_client_disconnect()` transport guard。
- `_send_json()` 在 `end_headers()` / `wfile.write()` 遇到 client disconnect 时静默收尾并关闭连接。
- `_send_file()` 同步补齐同类 guard，避免静态资源路径留下同类栈。
- 流式路径同步扩充 `ConnectionAbortedError`，与 JSON 路径保持一致。

## 修复后行为

### 正常 query

- stream 成功时，页面直接完成，不进入 fallback。
- stream 失败时，fallback 可独立完成并收尾到最终 payload。
- `strong / weak_with_review_notice / refuse` 不再被统一覆盖成错误态。

### 真正失败时

- 仍会进入独立错误态。
- 错误标题仍为“流式与标准请求都未完成”。
- retry 按钮仍可用。

### client disconnect

- 同步 JSON 返回阶段若客户端提前断开，服务端不再打印整段 `BrokenPipeError` 栈。
- 这类异常仍被视为 transport 级中断，而不是业务成功。

## 最小验证结论

- `strong`：stream 正常完成，最终模式正常。
- `weak_with_review_notice`：`primary_evidence = []`，`review_notice` 仍可见。
- `refuse`：最终仍为 `refuse`，不会被错误态覆盖。
- `error`：通过测试 hook 可稳定模拟双失败，错误态仍保留。
- `client disconnect`：同步 JSON 路径已验证不会再打印 `BrokenPipeError` 栈。
