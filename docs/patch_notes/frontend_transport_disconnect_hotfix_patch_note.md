# Frontend Transport Disconnect Hotfix Patch Note

## 本轮目标

本轮只处理 benign transport disconnect：

- 客户端主动断开连接
- 浏览器 / fetch / AbortController 中止请求
- keep-alive 连接被客户端提前 reset

本轮不改：

- retrieval / rerank / prompt 主逻辑
- answer payload 语义
- 前端布局与 UI
- evaluator / goldset / 评估逻辑

## 最终定位

这次不是业务错误，而是 benign transport disconnect。

已确认异常主要分成两类：

1. 写回阶段断开
   - `BrokenPipeError`
   - `ConnectionResetError`
   - 栈可能落在 `_send_json -> end_headers / wfile.write`

2. 读请求阶段断开
   - `ConnectionResetError`
   - 栈可能早于 `do_POST()`，直接落在 `BaseHTTPRequestHandler.handle_one_request()` 的 `rfile.readline()`

第二类说明只在 `_send_json()` 里补 try/except 不够，必须在更外层补收口。

## 本轮代码改动

### `backend/api/minimal_api.py`

- 新增模块级 `is_benign_disconnect_exception()`：
  - 识别 `BrokenPipeError`
  - 识别 `ConnectionResetError`
  - 识别 `ConnectionAbortedError`
  - 额外兼容常见 disconnect errno：`32 / 53 / 54 / 104`
- `MinimalApiHTTPServer.handle_error()`：
  - 对 benign disconnect 直接静默返回
  - 对其他异常继续走默认错误输出
- `MinimalApiHandler.handle_one_request()`：
  - 捕获读请求阶段的 benign disconnect
  - 设 `close_connection = True` 后安静收口
- `MinimalApiHandler.finish()`：
  - 补 flush/close 阶段的 benign disconnect 收口
- 保留并复用已有 `_send_json()` / `_send_file()` / 流式写回路径中的 transport guard

## 为什么这样是安全的

本轮没有把所有异常统一静默处理。

实际策略是：

- 只有 `is_benign_disconnect_exception(exc) == True` 时才静默收口
- 其余异常：
  - handler 层继续 `raise`
  - server 层继续调用 `super().handle_error(...)`

也就是说，真正业务异常和未知异常仍然会正常暴露。

## 前端核查结论

本轮未修改 `frontend/app.js`。

已确认当前前端：

- 流式与 fallback 各自使用独立 `AbortController`
- 前端主动 `abort` 属于预期 transport 行为
- fallback 成功后不会再误报 error

因此这轮不需要继续动前端。

## 最小验证

### 正常请求

- `黄连汤方的条文是什么？` -> `strong`
- `烧针益阳而损阴是什么意思？` -> `weak_with_review_notice`
- `书中有没有提到量子纠缠？` -> `refuse`

三类请求在本轮修复后都保持正常完成。

### client disconnect

已做两种本地 socket reset 验证：

1. 请求读取阶段 reset
   - 在 header 尚未完整读完时客户端直接 RST
   - 之前可能在 `handle_one_request.readline()` 刷 traceback
   - 修复后终端无新 traceback

2. 同步 JSON 写回阶段 reset
   - 有效请求发出后立即 RST
   - 之前可能在 `_send_json -> end_headers / wfile.write` 刷 traceback
   - 修复后终端无新 traceback

## 修复前后差异

### 修复前

- benign disconnect 会被当成整段服务器异常栈输出
- 读请求前断开与写回阶段断开都可能污染终端

### 修复后

- benign disconnect 被视为正常 transport 事件
- 服务端安静收口，不再打印整段 traceback
- 真正异常仍保留默认暴露路径
