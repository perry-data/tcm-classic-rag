# Model Studio Qwen Plus Switch Patch Note

## 本轮目标

在不改 retrieval / rerank / gating / payload contract / frontend 的前提下，把最小真实 LLM 接入从 OpenRouter 切换到 Alibaba Cloud Model Studio：

- provider: `Alibaba Cloud Model Studio`
- interface: `OpenAI-compatible Chat Completions`
- model: `qwen-plus`
- mode: `non-thinking`

## 本轮改动

1. `backend/llm/client.py`
   - 固定默认 provider 为 Alibaba Cloud Model Studio。
   - 默认模型固定为 `qwen-plus`。
   - 默认 `base_url` 切为 Singapore endpoint：`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
   - 请求体显式加入 `enable_thinking=false`，按 non-thinking 使用。
   - 若本地配置仍指向 OpenRouter，或模型不是 `qwen-plus`，启动时显式报配置错误。

2. `backend/llm/__init__.py`
   - 导出切换后的 Model Studio config / client / error / defaults。

3. `backend/llm/prompt_builder.py`
   - 继续沿用现有单步 prompt、JSON 输出、validator 约束。
   - 未放宽 citations / record_id / chapter_id 等越界限制。

4. `backend/answers/assembler.py`
   - LLM hook 仍只参与 `answer_text`。
   - `answer_mode`、evidence slots、citations、payload contract 继续由规则层决定。
   - `refuse` 仍不调用 LLM。
   - provider 调用失败或 validator 失败时，继续 fallback 到 baseline `answer_text`。

5. `backend/api/minimal_api.py`
   - provider 文案改为 Model Studio。
   - 默认 LLM smoke 产物改为：
     - `artifacts/llm_api_examples_modelstudio.json`
     - `artifacts/llm_api_smoke_checks_modelstudio.md`
   - smoke 增加非 `refuse` 样例必须实际尝试 LLM 的断言，并显式记录 `fallback_used`。

6. `.env.example`
   - 改为 Model Studio 模板，不包含真实 key。
   - 默认写明 Singapore endpoint。
   - 补充 China (Beijing) endpoint 示例，便于手动切换区域。

## 配置方式

支持以下环境变量：

- `TCM_RAG_LLM_API_KEY`
- `TCM_RAG_LLM_MODEL=qwen-plus`
- `TCM_RAG_LLM_BASE_URL`
- `TCM_RAG_LLM_ENABLED=true`

模板文件：`/Users/man_ray/Projects/Python/tcm-classic-rag/.env.example`

默认配置：

```env
TCM_RAG_LLM_API_KEY=your_model_studio_api_key_here
TCM_RAG_LLM_MODEL=qwen-plus
TCM_RAG_LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
TCM_RAG_LLM_ENABLED=true
```

可选区域 endpoint 示例：

```env
# China (Beijing)
TCM_RAG_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

说明：

- 本轮没有改写或提交真实 `.env`。
- 当前工作区本地 `.env` 仍保留旧的 OpenRouter model / base_url；因此本轮 smoke 使用 CLI 显式覆盖 `--llm-model qwen-plus --llm-base-url https://dashscope-intl.aliyuncs.com/compatible-mode/v1` 进行验证。
- 若直接在当前旧 `.env` 下执行 `--llm-enabled`，系统会显式报错并阻止误连旧 provider：

```text
[llm:config_error] LLM provider is fixed to Alibaba Cloud Model Studio. Replace TCM_RAG_LLM_BASE_URL with a DashScope OpenAI-compatible endpoint such as https://dashscope-intl.aliyuncs.com/compatible-mode/v1.
```

## 主链边界确认

以下边界本轮保持不变：

- `answer_mode` 由规则层决定
- evidence slots 由规则层决定
- citations 由规则层决定
- payload contract 不变
- LLM 只参与 `answer_text`
- `refuse` 路径不调用 LLM
- fallback 机制保留

## 最小 LLM smoke

命令：

```bash
./.venv/bin/python -m backend.api.minimal_api \
  --llm-smoke \
  --llm-enabled \
  --llm-model qwen-plus \
  --llm-base-url https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

产物：

- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/llm_api_examples_modelstudio.json`
- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/llm_api_smoke_checks_modelstudio.md`

覆盖查询：

1. `黄连汤方的条文是什么？`
2. `烧针益阳而损阴是什么意思？`
3. `太阳病应该怎么办？`
4. `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
5. `书中有没有提到量子纠缠？`

smoke 结果：

- `answer_mode` 与 baseline 一致
- evidence slots 不变
- citations 不变
- `refuse` 明确跳过 LLM
- 非 `refuse` 样例都实际尝试了 Model Studio client
- 当前环境下 strong / weak 均因 provider 返回 `HTTP 401 invalid_api_key` 而触发 fallback
- fallback 后 `answer_text` 仍非空，payload contract 保持稳定

结论摘要：

- `mode_match_kept`: `True`
- `evidence_unchanged`: `True`
- `citations_unchanged`: `True`
- `refuse_skips_llm`: `True`
- `llm_attempted_for_non_refuse`: `True`
- `answer_text_non_empty`: `True`

说明：

- 这证明请求已经实际到达 Alibaba Cloud Model Studio 路径。
- 当前没有留下 live generation 成功样例，是因为本地现存 key 不是可用于 Model Studio 的 key；provider 返回的是显式 `invalid_api_key`，不是本地假启用。
- fallback 仍按设计生效，没有污染 rule-layer 字段。

## 150 条 evaluator v1 回归

命令：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py \
  --goldset artifacts/evaluation/goldset_v2_working_150.json \
  --report-json artifacts/evaluation/modelstudio_qwen_plus_regression_report.json \
  --report-md artifacts/evaluation/modelstudio_qwen_plus_regression_report.md \
  --fail-on-evaluation-failure
```

产物：

- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/modelstudio_qwen_plus_regression_report.json`
- `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/modelstudio_qwen_plus_regression_report.md`

结果：

- `total_questions`: `150`
- `mode_match_count`: `150/150`
- `citation_check_required_basic_pass`: `120/120`
- `failure_count`: `0`
- `all_checks_passed`: `True`

与已有 `minimal_llm_api_regression_report.json` 对比：

- `mode_match` 未下降
- `citation_basic_pass` 未下降
- `failure_count` 未上升

说明：

- 本轮回归使用 `local_assembler` 路径，验证 retrieval / rerank / gating / assembler 主链未因 provider 切换而回退。
- LLM provider 本身的接入边界则由上面的 Model Studio smoke 负责验证。

## 当前已知边界

1. 代码已切到 Alibaba Cloud Model Studio `qwen-plus` non-thinking。
2. 当前工作区真实 `.env` 仍是旧 OpenRouter 配置，未在本轮被改写。
3. 因此本轮验证已经证明：
   - provider/model/base_url 切换完成
   - non-thinking 参数已接入
   - `refuse` 不调用 LLM
   - fallback 可触发
   - 主链职责边界未破坏
4. 若需补 live generation 成功证据，只需把本地 `.env` 的 key / model / base_url 换成可用的 Model Studio 配置后重新执行同一条 `--llm-smoke` 命令，无需继续改代码。
