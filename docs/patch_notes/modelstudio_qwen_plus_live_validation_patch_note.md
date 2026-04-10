# Model Studio Qwen Plus Live Validation Patch Note

## 本轮目标

在 provider / model 已切换完成的基础上，使用本地正确的 Alibaba Cloud Model Studio 配置，补一轮真实 live-call 成功验证，并形成正式 artifact。

本轮未改 retrieval / rerank / gating / payload contract / frontend，未更换 provider、model 或 prompt 架构。

## 本轮使用配置

- provider: `Alibaba Cloud Model Studio`
- interface: `OpenAI-compatible Chat Completions`
- model: `qwen-plus`
- mode: `non-thinking`
- base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`

说明：

- 本轮使用的是本地 `.env` 中的真实北京百炼配置。
- 真实 API key 未打印、未写入仓库、未出现在提交内容中。

## 执行命令

```bash
./.venv/bin/python -m backend.api.minimal_api \
  --llm-smoke \
  --llm-enabled \
  --llm-examples-out artifacts/llm_api_examples_modelstudio_live.json \
  --llm-smoke-checks-out artifacts/llm_api_smoke_checks_modelstudio_live.md
```

## 产物

- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/llm_api_examples_modelstudio_live.json`
- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/llm_api_smoke_checks_modelstudio_live.md`

## live-call 结果摘要

### 成功走到真实 LLM 返回的样例

以下 4 条 non-refuse 样例全部成功走到真实 LLM 返回：

1. `黄连汤方的条文是什么？`
2. `烧针益阳而损阴是什么意思？`
3. `太阳病应该怎么办？`
4. `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`

这些样例的共同结果是：

- `attempted = True`
- `used_llm = True`
- `answer_source = "llm"`
- `fallback_used = False`
- `fallback_reason = null`

### 仍未调用 LLM 的样例

以下样例继续按设计跳过 LLM：

1. `书中有没有提到量子纠缠？`

该样例结果为：

- `attempted = False`
- `used_llm = False`
- `answer_source = "baseline_refuse"`
- `skipped_reason = "refuse_mode"`

说明：

- `refuse` 路径仍然没有触发 live-call。
- 这与本轮要求一致。

## fallback 情况

本轮 non-refuse 样例没有发生 fallback。

- fallback 条数：`0`
- fallback 原因类型：`none`

`refuse` 的 `baseline_refuse` 不属于 fallback，而是规则层设计中的显式跳过。

## validator 情况

本轮没有出现 validator reject。

- validator reject 条数：`0`
- 原因类型：`none`

说明：

- 所有真实 LLM 返回都通过了现有 JSON 解析与 validator 约束。
- weak 模式保留了“需核对 / 暂不能视为确定答案”语气。
- baseline 的编号结构要求没有被破坏。

## answer_text 变化情况

4 条 non-refuse live-call 样例的 `answer_text` 都发生了变化：

- `黄连汤方的条文是什么？`：`answer_text_changed = True`
- `烧针益阳而损阴是什么意思？`：`answer_text_changed = True`
- `太阳病应该怎么办？`：`answer_text_changed = True`
- `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`：`answer_text_changed = True`

变化性质：

- 主要是语言整理、结构压缩、标点与条目表达优化。
- 没有扩展到 citations / record_id / chapter_id 生成。
- 没有改变 strong / weak / refuse 的职责边界。

## 对 mode / evidence / citations 的影响

本轮 smoke 结论：

- `mode_match_kept = True`
- `evidence_unchanged = True`
- `citations_unchanged = True`
- `refuse_skips_llm = True`
- `llm_attempted_for_non_refuse = True`
- `answer_text_non_empty = True`

说明：

- `answer_mode` 没变
- evidence slots 没变
- citations 没变
- payload contract 没变
- 变化仅发生在 `answer_text`

## 逐类结论

1. source lookup strong：live-call 成功，`answer_source=llm`，无 fallback。
2. weak meaning explanation：live-call 成功，保留“需核对”语气，validator 通过。
3. general strong：live-call 成功，分支结构保留，mode / evidence / citations 稳定。
4. comparison strong：live-call 成功，编号结构保留，mode / evidence / citations 稳定。
5. refuse boundary：仍跳过 LLM，保持 deterministic refusal。

## 本轮结论

本轮已满足 live-call 验收条件：

1. 至少一条 non-refuse 样例真实 live-call 成功
2. `refuse` 仍跳过 LLM
3. mode 不变
4. evidence / citations 不变
5. 已生成 live smoke artifact
6. 已清楚记录成功与 fallback 情况

实际结果比最低验收更强：4 条 non-refuse 样例全部成功走到了真实 Model Studio `qwen-plus` 返回。
