# Minimal LLM API OpenRouter Qwen Patch Note

## 本轮目标

在不改 retrieval / rerank / gating / payload contract / frontend 的前提下，为当前最小系统接入首发真实 LLM provider：

- provider: `OpenRouter`
- 默认模型示例：`qwen/qwen3-next-80b-a3b-instruct`

并补齐本地配置模板、密钥隔离、fallback、最小 smoke 与 150 条回归验证。

## 本轮改动

1. `backend/answers/assembler.py`
   - 在 `AnswerAssembler` 内新增最小 LLM 接入点。
   - 保持 `answer_mode`、evidence slots、citations、payload contract 继续由规则层控制。
   - 仅允许 LLM 参与 `answer_text`。
   - `refuse` 路径显式跳过 LLM。
   - 标准问答、comparison、general、refuse 统一收束到 `_compose_payload(...)`，确保 LLM hook 和 fallback 逻辑一致生效。

2. `backend/llm/client.py`
   - 新增固定单 provider 的 OpenRouter client。
   - 默认模型示例调整为 `qwen/qwen3-next-80b-a3b-instruct`。
   - 不再把模型名硬编码死为 `:free`；允许通过 `TCM_RAG_LLM_MODEL` 或 `--llm-model` 传入 OpenAI-compatible model identifier。
   - 当 `base_url` 为 OpenRouter 时发送 `HTTP-Referer` / `X-Title`；其他兼容端点只发送通用鉴权头，便于后续尝试其他千问兼容服务。
   - 新增最小配置读取逻辑：
     - 优先环境变量
     - 自动尝试加载仓库根目录 `.env`
   - 启用 LLM 但缺少关键配置时，显式报配置错误。

3. `backend/llm/prompt_builder.py`
   - 新增单步 prompt 组装。
   - 输入包含：`answer_mode`、`user_query`、baseline `draft_answer`、`primary/secondary/review` 证据块、硬约束。
   - 输出严格要求 JSON：`{"answer_text": "..."}`

4. `backend/llm/validator.py`
   - 新增最小输出校验。
   - 校验项包括：
     - JSON 可解析
     - `answer_text` 非空
     - 长度范围
     - 禁止生成 citation / record_id / chapter_id 等越界内容
     - `weak_with_review_notice` 必须保留“需核对”类语气
     - baseline 若带编号结构，渲染结果不得破坏编号结构

5. `backend/api/minimal_api.py`
   - 新增 `--llm-enabled`、`--llm-smoke` 等最小运行开关。
   - 新增 `artifacts/llm_api_examples.json`
   - 新增 `artifacts/llm_api_smoke_checks.md`
   - 新增 LLM config error 的显式启动报错。

6. `.env.example`
   - 新增本地模板文件，不包含真实密钥。

7. `.gitignore`
   - 继续忽略 `.env` / `.env.*`
   - 明确保留 `.env.example`

## 配置方式

本轮支持以下环境变量：

- `TCM_RAG_LLM_API_KEY`
- `TCM_RAG_LLM_MODEL`
- `TCM_RAG_LLM_BASE_URL`
- `TCM_RAG_LLM_ENABLED`

模板文件：`/Users/man_ray/Projects/Python/tcm-classic-rag/.env.example`

本地实际使用时，复制为 `.env` 并自行填写真实 OpenRouter key：

```env
TCM_RAG_LLM_API_KEY=your_openrouter_api_key_here
TCM_RAG_LLM_MODEL=qwen/qwen3-next-80b-a3b-instruct
TCM_RAG_LLM_BASE_URL=https://openrouter.ai/api/v1
TCM_RAG_LLM_ENABLED=true
```

## 回退策略

以下情况一律自动回退 baseline `answer_text`：

- API 超时
- provider 返回错误
- JSON 解析失败
- 输出为空
- 输出越界
- `weak_with_review_notice` 丢失“需核对”语气
- baseline 编号结构被破坏

`refuse` 路径不调用 LLM，继续完全走 deterministic refusal。

## 本轮验证

### 1. 代码级自检

- `python -m py_compile backend/answers/assembler.py backend/api/minimal_api.py backend/llm/__init__.py backend/llm/client.py backend/llm/prompt_builder.py backend/llm/validator.py`
- 通过

### 2. LLM config error

在未提供 key 时执行：

```bash
./.venv/bin/python -m backend.api.minimal_api --llm-smoke --llm-enabled
```

返回：

```text
[llm:config_error] LLM is enabled but TCM_RAG_LLM_API_KEY is missing. Populate .env or export the variable before starting the service.
```

说明：

- 配置缺失时不会悄悄降级成“假启用”
- 会显式报错，阻止误判为已接通真实 provider

### 3. 最小 LLM smoke

已生成：

- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/llm_api_examples.json`
- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/llm_api_smoke_checks.md`

本次仓库内没有真实 `.env`，因此 smoke 使用占位环境变量触发 OpenRouter 客户端链路，并验证 fallback：

- `黄连汤方的条文是什么？`
- `烧针益阳而损阴是什么意思？`
- `太阳病应该怎么办？`
- `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
- `书中有没有提到量子纠缠？`

smoke 结论：

- `answer_mode` 与 baseline 一致
- evidence slots 不变
- citations 不变
- `refuse` 路径跳过 LLM
- strong / weak 的 `answer_text` 非空
- 当前环境下 OpenRouter 请求失败时，已正确 fallback 到 baseline `answer_text`

当前 smoke 记录到的 fallback 原因为：

- `OpenRouter request failed: [Errno 8] nodename nor servname provided, or not known`

这说明当前验证环境未完成真实外网调用；代码已进入真实 provider client 路径，但 live generation 仍需本地真实 `.env` 配置后复跑。

### 4. 150 条 evaluator v1 回归

命令：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py \
  --goldset artifacts/evaluation/goldset_v2_working_150.json \
  --report-json artifacts/evaluation/minimal_llm_api_regression_report.json \
  --report-md artifacts/evaluation/minimal_llm_api_regression_report.md \
  --fail-on-evaluation-failure
```

结果：

- total_questions: `150`
- mode_match_count: `150/150`
- citation_check_required_basic_pass: `120/120`
- failure_count: `0`
- all_checks_passed: `True`

说明：

- 默认 deterministic 主链未被本轮接入破坏
- `mode_match`、`citation_basic_pass`、`failure_count` 均未劣化

## 当前已知边界

1. 本轮已完成真实 OpenRouter 接口代码接入，但仓库内没有真实 `.env`，因此尚未在当前工作区留下“真实 key + live generation 成功”的运行证据。
2. 当前 `artifacts/llm_api_*` 产物证明了：
   - LLM hook 已接上
   - `refuse` 不调用 LLM
   - fallback 可触发
   - payload contract / evidence / citations 保持稳定
3. 若需完成 live provider 验证，只需补本地 `.env` 后重新执行 `--llm-smoke`，无需改代码。

## 建议下一个动作

1. 用户本地创建 `/Users/man_ray/Projects/Python/tcm-classic-rag/.env`
2. 填入真实 `TCM_RAG_LLM_API_KEY`
3. 重新执行：

```bash
./.venv/bin/python -m backend.api.minimal_api --llm-smoke --llm-enabled
```

4. 若需要，再启动 API server 并用 `scripts/run_evaluator_v1.py --runner-backend api` 复跑一轮 LLM-on 回归
