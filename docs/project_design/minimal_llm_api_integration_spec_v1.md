# 最小真实 LLM API 接入版实现规格 v1

- 规格日期：2026-04-09
- 输入依据：`docs/project_decision/llm_generation_scope_decision_v1.md`、`docs/project_audit/proposal_vs_actual_gap_audit_v1.md`、`docs/final/PRD_v1.md`、`docs/final/technical_design_v1.md`、`docs/final/system_spec_v1.md`、`docs/evaluation/evaluation_spec_v1.md`
- 文档目标：冻结“最小真实 LLM API 接入版”的实现边界与改动范围，供下一轮直接进入实现

## 1. 目标与非目标

### 1.1 本轮要冻结的目标

本规格只冻结一个最小方案：

1. 保留当前 retrieval / rerank / evidence gating / citations / answer_mode / payload contract。
2. 在当前 `AnswerAssembler` 内增加一个**可选的**真实 LLM 调用步骤。
3. LLM 只参与 `answer_text` 的生成或润色。
4. 所有失败场景都自动回退到当前规则化 `answer_text`。

### 1.2 明确非目标

以下内容不属于本版规格：

1. 不改 retrieval 主链。
2. 不改 rerank。
3. 不改 evidence gating。
4. 不改 `strong / weak_with_review_notice / refuse` 判定逻辑。
5. 不改 `citations`、`primary_evidence`、`secondary_evidence`、`review_materials` 生成逻辑。
6. 不改 payload contract。
7. 不做多步 Prompt。
8. 不重写前端。
9. 不做多 provider 抽象平台。

## 2. 结论先行：最小接入方案

本版冻结的最小方案是：

> **LLM 插在 retrieval 和 gating 之后、在 `AnswerAssembler` 已完成 mode / evidence / citations / deterministic draft answer 之后、在最终 payload 返回之前。**

更具体地说：

1. `strong / weak_with_review_notice / refuse` 先由现有规则层判定。
2. `primary / secondary / review` 三槽位先由现有规则层生成。
3. `citations` 先由现有规则层生成。
4. `disclaimer`、`review_notice`、`refuse_reason`、`suggested_followup_questions` 先由现有规则层生成。
5. 现有规则层先生成一个 deterministic `baseline_answer_text`。
6. 只有在满足条件时，LLM 才把 `baseline_answer_text` 改写为 `final_answer_text`。
7. `display_sections` 仍由现有规则层生成，但基于最终 `answer_text` 计算其 answer summary。

## 3. 接入位置冻结

### 3.1 接入点

最小接入点冻结为：`AnswerAssembler` 内部、`_compose_payload(...)` 之前。

原因：

1. 这时 `answer_mode` 已经稳定。
2. 这时 evidence slots 已经稳定。
3. 这时 citations 已经稳定。
4. 这时已存在 deterministic baseline，可直接作为 fallback。
5. 这时插入不会影响 `Minimal API` 请求合同，也不会影响前端字段消费。

### 3.2 不允许的接入位置

以下位置本版明确不采用：

1. 不插在 retrieval 前。
2. 不插在 rerank 前后去改候选排序。
3. 不插在 gating 前让 LLM 决定证据分层。
4. 不插在 API 层单独拼接“LLM answer + 规则 payload”双轨对象。
5. 不让前端直接请求 LLM。

### 3.3 strong / weak / refuse 的先后顺序

冻结顺序如下：

1. 规则层先判 `refuse`。
2. 若不是 `refuse`，规则层继续完成 comparison / general / standard 路径的 deterministic assembly。
3. 规则层输出 `answer_mode`。
4. 若 `answer_mode in {strong, weak_with_review_notice}` 且 LLM 启用，则执行 LLM answer rendering。
5. 若 `answer_mode == refuse`，直接跳过 LLM，使用现有 deterministic refuse `answer_text`。

### 3.4 question path 覆盖范围

本版默认覆盖：

1. standard path
2. general question path
3. comparison path

但覆盖方式统一为：

- **只改写最终 `answer_text`，不改任何 path-specific evidence / citation / mode 逻辑。**

这样可以避免为了不同题型再开一套 LLM orchestration。

## 4. 字段职责边界冻结

### 4.1 继续由规则层负责的字段

下列字段必须继续完全由现有规则层生成：

| field | 责任方 | 说明 |
| --- | --- | --- |
| `query` | 规则层 | 原样回显 |
| `answer_mode` | 规则层 | 不允许 LLM 决策 |
| `primary_evidence` | 规则层 | 不允许 LLM 升降级 |
| `secondary_evidence` | 规则层 | 不允许 LLM 改写结构 |
| `review_materials` | 规则层 | 不允许 LLM 改写结构 |
| `disclaimer` | 规则层 | 保持当前三模式语义 |
| `review_notice` | 规则层 | 保持 weak 语义 |
| `refuse_reason` | 规则层 | refuse 继续 deterministic |
| `suggested_followup_questions` | 规则层 | refuse 继续 deterministic |
| `citations` | 规则层 | 不允许 LLM 生成或改写 |
| `display_sections` | 规则层 | 结构不变，只基于最终 answer_text 更新 summary |

### 4.2 允许 LLM 参与的字段

本版只允许 LLM 参与一个字段：

| field | 责任方 | 说明 |
| --- | --- | --- |
| `answer_text` | 规则层先生成 baseline；LLM 可选改写 | 失败时必须回退 baseline |

### 4.3 为什么这是最优最小方案

这是最优最小方案，原因有五点：

1. **contract 最小变动**：前端和 API 合同完全不变。
2. **评估可继承**：evaluator v1 依赖的 mode / citations / evidence 仍可直接复跑。
3. **回退容易**：已有 deterministic baseline，不需要为 LLM 失败额外造结构。
4. **风险可控**：LLM 不碰 evidence 分层和 refusal policy，最危险的部分继续 deterministic。
5. **论文收益最大化**：题目中的“生成”真正进入链路，但不推翻当前 MVP。

### 4.4 明确否决的替代方案

| 方案 | 本版结论 | 否决原因 |
| --- | --- | --- |
| LLM 决定 `answer_mode` | 否 | 会破坏 evaluator v1 和当前 gating 语义 |
| LLM 决定 citations | 否 | 最容易引入错引与漂移 |
| LLM 决定 evidence slots | 否 | 会推翻当前分层与风险控制 |
| LLM 生成整个 payload | 否 | 合同风险和 debug 成本过高 |
| LLM 只做前端文案装饰 | 否 | 不能证明“生成”进入正式链路 |

## 5. 运行条件冻结

### 5.1 LLM 调用条件

只有同时满足以下条件时，才调用 LLM：

1. `llm_enabled = true`
2. 已显式配置 model
3. 已注入 API key
4. 当前 `answer_mode in {strong, weak_with_review_notice}`
5. 当前存在 `baseline_answer_text`

### 5.2 明确跳过 LLM 的条件

以下情况直接跳过 LLM：

1. `answer_mode == refuse`
2. `llm_enabled = false`
3. 启动时未配置 key / model
4. 本次请求在规则层已经生成空 answer_text 或非正常状态

## 6. 最小 Prompt 组装方案

本版只允许**单步 Prompt**。

### 6.1 Prompt 输入总结构

Prompt 由四块组成：

1. `system instruction`
2. `mode + query + draft answer`
3. `primary / secondary / review` 三类证据
4. `hard constraints + output format`

### 6.2 System Instruction

冻结要求：

1. 明确模型是“研读支持答案重写器”，不是自由问答器。
2. 明确只能基于提供证据与 draft answer 输出。
3. 明确不能新增书外知识、不能给诊疗建议、不能补造出处。
4. 明确不能改变当前 mode 的语气边界。
5. 明确若证据不足，不得把 weak 写成 strong。

推荐模板：

```text
你是一个中医经典研读支持系统中的答案改写器。你的任务不是自由回答，而是在不改变既有证据边界、题型边界和回答模式的前提下，把给定的草稿答案整理成更自然、更清晰的中文表达。你只能使用提供的 query、draft answer 和 evidence。你不能新增外部知识，不能给出诊疗、剂量、现代病名疗效判断，不能补造出处、章节、条号、引用编号，不能改变 strong / weak_with_review_notice / refuse 的语气边界。
```

### 6.3 User Prompt 结构

冻结结构如下：

```text
[answer_mode]
strong | weak_with_review_notice

[user_query]
{原始 query}

[draft_answer]
{当前规则层生成的 baseline_answer_text}

[primary_evidence]
- {title} | {chapter_title} | {snippet}
- ...

[secondary_evidence]
- {title} | {chapter_title} | {snippet}
- ...

[review_materials]
- {title} | {chapter_title} | {snippet}
- ...

[hard_constraints]
1. 只能依据上述材料表达，不得补充书外知识。
2. 不得输出诊疗建议、剂量建议、现代病名疗效判断。
3. 不得新增或臆造 citation、record_id、条号、章节号、书名对比。
4. strong 模式可做清晰归纳，但不得超出 primary evidence。
5. weak_with_review_notice 模式必须保留不确定性，且明确“需核对”。
6. 如果 draft 已包含编号分支，输出时保留编号结构，不得压扁成一句话。
7. 输出必须是 JSON：{\"answer_text\": \"...\"}
```

### 6.4 证据组织规则

为控制 token 和漂移，本版 prompt 只放：

1. `draft_answer`
2. 最多 3 条 `primary_evidence`
3. 最多 3 条 `secondary_evidence`
4. 最多 2 条 `review_materials`

每条证据只给：

- `title`
- `chapter_title`
- `snippet`

本版不放：

1. retrieval score
2. rerank score
3. record_id
4. raw trace
5. hidden debug 信息

### 6.5 模式相关硬约束

#### `strong`

必须满足：

1. 不得写成“推测”“可能只是”这类明显弱化表达，除非 baseline 本身如此。
2. 不得超出 `primary_evidence` 的主结论边界。
3. 若 draft 有编号条目，输出应保留 1-3 条的结构化整理。

#### `weak_with_review_notice`

必须满足：

1. 必须保留弱化语气。
2. 必须显式表达“需核对”或等价意思。
3. 不得把 `secondary_evidence` / `review_materials` 写成已确认主结论。

#### `refuse`

本版不调用 LLM，因此无 prompt。

## 7. 输出校验与自动回退机制

### 7.1 启动期配置错误

启动期规则冻结如下：

1. `llm_enabled = false`：正常启动，完全走 baseline。
2. `llm_enabled = true` 但缺少 `api_key` 或 `model`：启动失败，直接报配置错误。

理由：

- 显式开启 LLM 却静默退回 baseline，会让实验结果不透明。

### 7.2 运行期失败回退

运行期以下情况统一回退 baseline `answer_text`：

1. 网络错误
2. provider 返回非 2xx
3. 超时
4. 解析失败
5. 返回空文本
6. 返回 JSON 格式不合法
7. 输出越界校验失败

回退后：

1. payload 继续按当前规则层返回
2. HTTP 状态码仍按原业务逻辑处理
3. 不向前端暴露新的错误字段
4. 只在服务日志和 smoke artifact 中记录 fallback reason

### 7.3 输出越界判定

本版最小校验器至少做以下检查：

1. 输出必须可解析为 JSON 对象。
2. 必须存在非空 `answer_text`。
3. `answer_text` 长度必须在合理范围内，例如 20-800 字符。
4. 不得出现明显越界内容：
   - 个体化处方/服药建议
   - 剂量换算
   - 现代病名疗效断言
   - 跨书价值判断
   - 杜撰 citation / record_id / 条号 / 章节号
5. `weak_with_review_notice` 模式必须包含弱化或核对提示语。
6. 若 baseline answer 含编号结构，则输出必须保留编号结构。

### 7.4 为什么回退到 baseline 而不是报错

因为本版目标是“最小真实 LLM 接入”，不是“把 LLM 变成单点依赖”。

回退到 baseline 的好处：

1. 不破坏当前演示稳定性。
2. 不破坏当前 evaluator v1 回放。
3. 不要求前端新增错误分支。
4. 便于逐步比较“LLM answer vs deterministic answer”。

## 8. 对 evaluator / smoke 的影响

### 8.1 evaluator v1 仍然有效的部分

接入后，下列检查仍应保持有效：

1. `answer_mode` 是否匹配
2. `primary_evidence` / `secondary_evidence` / `review_materials` 是否保持分层
3. `citations` 是否保持基本正确
4. refusal 是否仍为空 evidence / citations
5. payload contract 是否不变

原因：

- 本版不让 LLM 改这些字段。

### 8.2 受 nondeterminism 影响的部分

受影响的只有 `answer_text` 文本表面表达。

因此：

1. 不应新增“answer_text 必须与固定字符串完全一致”的回归断言。
2. `display_sections.answer.summary` 会随着最终 `answer_text` 变化。
3. 现有 evaluator v1 若只记录 `answer_text_excerpt`，可以继续记录，但不应用于严格字符串比较。

### 8.3 接入后必须新增的最小 smoke / regression

需要新增一个最小 LLM smoke/regression 方案，建议覆盖以下 5 条：

1. `黄连汤方的条文是什么？`：standard strong
2. `烧针益阳而损阴是什么意思？`：standard weak
3. `太阳病应该怎么办？`：general strong
4. `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`：comparison strong
5. `书中有没有提到量子纠缠？`：refuse

最小断言：

1. `answer_mode` 与 baseline 一致
2. evidence slots 的 record_id 集合与 baseline 一致
3. citations 的 record_id / role 与 baseline 一致
4. `refuse` 不触发 LLM，payload 与 baseline refusal 语义一致
5. strong / weak 若调用 LLM，则 `answer_text` 非空且通过 validator；若失败则明确记录 fallback

建议产物：

1. `artifacts/llm_api_smoke_checks.md`
2. `artifacts/llm_api_examples.json`

### 8.4 full regression 建议

接入后仍建议对 `goldset_v2_working_150.json` 复跑 evaluator v1。

预期：

1. mode_match 不应下降
2. citation_basic_pass 不应下降
3. failure_count 不应上升

若下降，优先排查：

1. LLM 是否误改了 rule-layer 字段
2. answer_mode 是否被错误延后到 LLM 之后
3. comparison/general 路径是否绕过了 deterministic gating

## 9. 配置与运行冻结

### 9.1 provider 策略

本版明确选择：

> **先固定单一 provider，不做通用 provider 抽象层。**

理由：

1. 当前目标是最小接入，不是多供应商平台。
2. provider abstraction 会增加配置面、测试矩阵和 debug 成本。
3. 当前最重要的是把“真实 LLM 在链路里”做实，而不是把 provider 做成插件市场。

实现层可以有一个很薄的 client 模块，但它只服务一个 provider。

### 9.2 最小配置项

建议冻结以下配置：

| 配置项 | 作用 | 默认值 |
| --- | --- | --- |
| `llm_enabled` | 是否启用 LLM answer rendering | `false` |
| `llm_model` | 当前使用的单一模型名 | 无，启用时必填 |
| `llm_api_key` | provider 密钥 | 无，启用时必填 |
| `llm_base_url` | 可选 provider base URL | `null` |
| `llm_timeout_seconds` | 单次调用超时 | `8-15` 秒实现时择一固定 |
| `llm_max_output_tokens` | answer_text 生成上限 | 小值，保证受控 |
| `llm_temperature` | 建议低温 | `0` 或低温常量 |
| `llm_max_primary_items` | prompt 中 primary 条数上限 | `3` |
| `llm_max_secondary_items` | prompt 中 secondary 条数上限 | `3` |
| `llm_max_review_items` | prompt 中 review 条数上限 | `2` |

### 9.3 密钥注入

密钥只允许通过环境变量注入，不允许：

1. 写死在代码里
2. 写进仓库 JSON
3. 从前端传入
4. 放进请求 body

建议环境变量名冻结为：

- `TCM_RAG_LLM_API_KEY`
- `TCM_RAG_LLM_MODEL`
- `TCM_RAG_LLM_BASE_URL`（可选）

### 9.4 本地开发运行方式

本地开发继续沿用当前 Minimal API 启动方式，只额外增加 LLM 开关和必要参数。

推荐形态：

```bash
TCM_RAG_LLM_API_KEY=...
TCM_RAG_LLM_MODEL=...
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000 --llm-enabled
```

未启用时：

```bash
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

### 9.5 CLI / 服务层改动边界

本版只允许在 `backend/api/minimal_api.py` 增加最小开关和配置透传，例如：

1. `--llm-enabled`
2. `--llm-timeout-seconds`
3. `--llm-max-output-tokens`
4. 可选 `--llm-base-url`

不允许新增：

1. 面向前端暴露的 provider 参数
2. 请求体中的 LLM 配置字段
3. 多 provider runtime 切换矩阵

## 10. 计划改动文件边界

### 10.1 允许修改 / 新增

最小实现轮次允许动到：

1. `backend/answers/assembler.py`
2. `backend/api/minimal_api.py`
3. 新增 `backend/llm/client.py`
4. 新增 `backend/llm/prompt_builder.py`
5. 新增 `backend/llm/validator.py`
6. 视具体实现决定是否更新 `requirements.txt`
7. 新增 LLM smoke artifacts 输出位置

### 10.2 明确不动

本版明确不动：

1. `backend/retrieval/*`
2. `frontend/*`
3. `config/layered_enablement_policy.json`
4. goldset schema
5. evaluator v1 逻辑主干
6. payload contract 文档结构

## 11. 实现前的最终冻结结论

进入实现轮次前，以下结论视为已冻结：

1. **LLM 接在 `AnswerAssembler` 内部，位于 deterministic assembly 之后、payload 返回之前。**
2. **`answer_mode`、evidence slots、citations、payload contract 全部保持规则层控制。**
3. **LLM 只改 `answer_text`，而且只在 `strong / weak_with_review_notice` 下调用。**
4. **`refuse` 不接 LLM。**
5. **所有 runtime 失败与越界都回退到当前 deterministic `answer_text`。**
6. **只用单步 Prompt，不做多步 Prompt。**
7. **先固定单一 provider，不做通用 provider 抽象层。**

这套规格的目标不是把当前系统重构成“完整生成式平台”，而是在不打碎现有 MVP 与 evaluator 口径的前提下，把真实 LLM 以最小成本放进正式运行链路。
