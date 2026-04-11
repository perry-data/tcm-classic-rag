# Frontend Second Submit Hang Hotfix Demo

## 目标

证明两件事：

1. 修复前，第一问成功后前端逻辑锁没有释放
2. 修复后，第二问、第三问与失败后重试都能继续正常发出

## 修复前后对照

同一份成功流式响应，使用 fake DOM 驱动旧版与新版 `frontend/app.js`：

- 修复前
  - `requestInFlight = true`
  - `submitDisabled = true`
  - `statusText = 请求已完成`
  - 说明 UI 已显示完成，但逻辑锁仍残留
- 修复后
  - `requestInFlight = false`
  - `submitDisabled = false`
  - `statusText = 请求已完成`

这说明根因就是成功路径绕开了统一 cleanup。

## 当前前端专项回归

### `strong -> strong`

- 第一次：`黄连汤方的条文是什么？`
- 第二次：`桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
- 结果：
  - 两次都只触发 `/api/v1/answers/stream`
  - 每次结束后都恢复为：
    - `requestInFlight = false`
    - `submitDisabled = false`

### `strong -> weak`

- 第一次结束后继续提交 `烧针益阳而损阴是什么意思？`
- 结果：
  - 正常进入 `weak_with_review_notice`
  - 未停留在“发送中”

### `weak -> refuse`

- 紧接着提交 `书中有没有提到量子纠缠？`
- 结果：
  - 正常进入 `refuse`
  - 未残留错误态或 loading 锁

### `stream unavailable -> fallback success`

- 模拟流式不可用，随后走标准接口成功
- 请求序列：
  - `/api/v1/answers/stream`
  - `/api/v1/answers`
- 紧接着下一问仍可继续成功

### `double failure -> retry`

- 通过 `failNextRequest({ stream, fallback })` 模拟流式和标准同时失败
- 结果：
  - 当前轮进入独立错误态
  - 下一次重试同一问题可恢复成功
  - 失败后下一问不会被卡死

### `3 submits in a row`

- `黄连汤方的条文是什么？`
- `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
- `书中有没有提到量子纠缠？`
- 结果：
  - 三次都成功
  - 每一轮结束后都已复位

## 真实接口与后端终端

本地服务：

- `http://127.0.0.1:8001/`

真实流式接口返回：

- `黄连汤方的条文是什么？` -> `strong`
- `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？` -> `strong`
- `烧针益阳而损阴是什么意思？` -> `weak_with_review_notice`
- `书中有没有提到量子纠缠？` -> `refuse`

后端终端新增可见日志：

- `[api:request] path=/api/v1/answers/stream mode=strong query=黄连汤方的条文是什么？`
- `[api:request] path=/api/v1/answers/stream mode=strong query=桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
- `[api:request] path=/api/v1/answers/stream mode=weak_with_review_notice query=烧针益阳而损阴是什么意思？`
- `[api:request] path=/api/v1/answers/stream mode=refuse query=书中有没有提到量子纠缠？`

这表明第二次、第三次请求都真正进入了后端处理链路。
