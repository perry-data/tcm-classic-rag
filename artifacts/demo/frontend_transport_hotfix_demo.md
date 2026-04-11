# Frontend Transport Hotfix Demo

## 本轮验证目标

验证以下四类场景：

1. `strong`
2. `weak_with_review_notice`
3. `refuse`
4. `error`

并额外确认：

- stream 失败后 fallback 只会执行一次
- 同步 JSON client disconnect 不再刷 `BrokenPipeError` 栈

## 真实接口验证

### 1. strong

- query：`黄连汤方的条文是什么？`
- 同步接口结果：
  - `answer_mode = strong`
  - 主依据仍包含 `0145 / 0146 / 0147`
  - `review_notice` 仍存在
- 流式接口结果：
  - 可见 `evidence_ready`
  - 可见多段 `answer_delta`
  - 最终收到 `completed`

### 2. weak_with_review_notice

- query：`烧针益阳而损阴是什么意思？`
- 同步接口结果：
  - `answer_mode = weak_with_review_notice`
  - `primary_evidence = []`
  - `review_notice` 仍存在

### 3. refuse

- query：`书中有没有提到量子纠缠？`
- 流式接口结果：
  - `evidence_ready` payload 中 `answer_mode = refuse`
  - 可见 `answer_delta`
  - 最终收到 `completed`

## 前端状态机仿真验证

使用最小 fake DOM + 当前 `frontend/app.js` 执行了以下回归：

- `strong_stream`
  - 结果：`modeBadge = 可参考`
  - 只请求 `/api/v1/answers/stream`
- `weak_stream`
  - 结果：`modeBadge = 需核对`
  - `primary` 隐藏，`review_notice` 保留
- `refuse_stream`
  - 结果：`modeBadge = 暂不支持`
  - 改问建议区可见
- `strong_fallback_after_stream_error`
  - 结果：最终仍落到 `strong`
  - 请求序列只有：
    - `/api/v1/answers/stream`
    - `/api/v1/answers`
- `error_after_stream_false_and_fallback_fail`
  - 结果：进入“流式与标准请求都未完成”
  - 请求序列仍只有一次 fallback
  - 说明 fallback 重入已消失
- `controlled_double_failure`
  - 通过 `window.__frontendTestHooks.failNextRequest({ stream, fallback })`
  - 可稳定得到错误态

## client disconnect 验证

对 `POST /api/v1/answers` 主动发起一次“发送请求后立即断开连接”的本地 socket 测试：

- 结果：服务端未打印新的 `BrokenPipeError` 栈
- 随后再次请求同步接口仍可正常返回 `strong`

## 修复前 -> 修复后

### 修复前

- stream 失败后 fallback 生命周期不稳
- fallback 存在重入风险
- 同步 JSON client disconnect 会打印整段异常栈

### 修复后

- stream 与 fallback 的 controller / timer 清理按当前 transport 收束
- fallback 最多只执行一次
- 正常 query 不再统一落入错误态
- client disconnect 只做 transport 收尾，不再污染终端
