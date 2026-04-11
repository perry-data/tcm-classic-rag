# Frontend Second Submit Hang Hotfix Patch Note

## 本轮目标

只修当前阻塞性故障：

- 第一问完成后，第二问卡在“发送中”
- 前端看起来已拿到回答，但下一次提交经常发不出去
- 后端终端缺少稳定的第二次请求痕迹

本轮不改：

- 页面布局与视觉风格
- retrieval / rerank / prompt 主链
- answer payload 顶层语义
- 业务模式判定逻辑

## 最终根因

主因在 `frontend/app.js` 的请求生命周期收尾不完整：

1. `submitQuery()` 在“流式成功完成”时会直接 `return`
2. 真正负责释放逻辑锁的 `finally` 只包住了 fallback 分支
3. 结果是第一问虽然渲染完成，但这些前端状态没有统一复位：
   - `state.requestInFlight`
   - `submitButton.disabled` / `setLoading(false)`
4. UI 表面上已经显示最终回答，JS 内部却仍认为请求在飞行中，于是第二问被卡在旧状态外面

补充排查结论：

- `activeTransport` 的 timer 在纯流式成功路径里已经会被清掉，不是主因
- 但 stream reader 之前没有显式释放引用，本轮一并补了集中清理
- 旧版成功流式路径结束后，`requestInFlight = true`、`submitDisabled = true`，这正是“第二问没真正发出去”的直接原因

## 代码改动

### `frontend/app.js`

- 新增统一生命周期函数：
  - `startRequest(query)`
  - `cleanupRequestState(requestId)`
  - `settleRequestError(requestId, error)`
- 将 `submitQuery()` 改为整个请求生命周期只保留一个最终 `finally`
  - 不再允许流式成功路径绕开 cleanup
- 新增 `activeStreamReader` 跟踪与释放：
  - `registerActiveStreamReader()`
  - `releaseActiveStreamReader()`
- 在 `consumeNdjsonStream()` 的 `finally` 中显式释放 reader
- 在调试 hook `getRequestState()` 中补充：
  - `activeStreamReader`
  - `submitDisabled`

### `backend/api/minimal_api.py`

- 仅补充最小请求日志，便于排障确认“第二次请求确实已到后端”
- 新增日志格式：
  - `path=/api/v1/answers/stream mode=... query=...`
  - `path=/api/v1/answers mode=... query=...`

这部分不改变接口 contract，也不改变业务返回语义。

## 修复后行为

### 修复前

- 第一问流式成功后，页面能显示最终答案
- 但 `requestInFlight` 没有释放
- 提交按钮仍处于逻辑占用态
- 第二问常常不会真正发出

### 修复后

- 每一轮请求都有独立生命周期
- 流式成功、流式失败回退、双失败、失败后重试，最终都会汇入同一个 cleanup
- 第二问、第三问不再依赖刷新页面
- 后端终端可看到连续请求处理痕迹

## 专项回归结果

### 1. 修复前后对照（前端状态机仿真）

- 修复前：
  - 第一问成功后 `requestInFlight = true`
  - 第一问成功后 `submitDisabled = true`
- 修复后：
  - 第一问成功后 `requestInFlight = false`
  - 第一问成功后 `submitDisabled = false`

### 2. 前端状态机专项回归

基于 fake DOM + 当前 `frontend/app.js` 验证：

- `strong -> strong`
  - 两次都只请求 `/api/v1/answers/stream`
  - 每次结束后 `requestInFlight = false`
  - `submitDisabled = false`
- `strong -> weak_with_review_notice`
  - 第二次正常进入 `weak_with_review_notice`
- `weak_with_review_notice -> refuse`
  - 第二次正常进入 `refuse`
- `stream unavailable -> fallback success`
  - 请求序列为：
    - `/api/v1/answers/stream`
    - `/api/v1/answers`
  - fallback 成功后下一问仍可正常发起
- `forced double failure -> retry`
  - 双失败后进入独立错误态
  - 随后重试同一问题可恢复成功
- `3 submits in a row`
  - 第 1 次成功
  - 第 2 次成功
  - 第 3 次成功

### 3. 真实接口验证

使用本地服务 `http://127.0.0.1:8001` 验证：

- `黄连汤方的条文是什么？`
  - `/api/v1/answers/stream` 返回 `answer_mode = strong`
- `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
  - `/api/v1/answers/stream` 返回 `answer_mode = strong`
- `烧针益阳而损阴是什么意思？`
  - `/api/v1/answers/stream` 返回 `answer_mode = weak_with_review_notice`
- `书中有没有提到量子纠缠？`
  - `/api/v1/answers/stream` 返回 `answer_mode = refuse`

同时在后端终端可见：

- `[api:request] path=/api/v1/answers/stream mode=strong query=黄连汤方的条文是什么？`
- `[api:request] path=/api/v1/answers/stream mode=strong query=桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
- `[api:request] path=/api/v1/answers/stream mode=weak_with_review_notice query=烧针益阳而损阴是什么意思？`
- `[api:request] path=/api/v1/answers/stream mode=refuse query=书中有没有提到量子纠缠？`

## 结论

这次卡死不是后端主链性能问题，而是前端在“流式成功完成”路径漏掉了统一 cleanup。

真正没清干净的是：

- `state.requestInFlight`
- `setLoading(false)` 对应的提交锁释放

reader 引用收尾本轮也已补齐，但它不是首要根因。
