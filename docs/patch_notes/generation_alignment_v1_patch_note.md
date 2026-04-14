# Generation Alignment v1 Patch Note

## 1. 本轮目标

本轮仅处理“生成式回答对齐开题写法 v1”：

- 把当前 `规则组织 + LLM 润色` 的 answer_text 生成方式，升级为 `Evidence Pack -> LLM 解释型生成 -> validator 对齐校验`。
- 保持既有 `answer_mode`、三槽位（`primary_evidence / secondary_evidence / review_materials`）、`citations` 与 payload contract 不变。
- 增加 LLM 输出失败时的 strict retry 与 guardrail fallback，避免因为生成异常导致接口失败或乱强答。

## 2. 变更范围

本轮实际修改文件：

- `backend/answers/assembler.py`
- `backend/llm/client.py`
- `backend/llm/prompt_builder.py`
- `backend/llm/validator.py`
- `backend/checks/generation_alignment_v1_checks.py`
- `artifacts/generation_alignment_v1/generation_alignment_v1_report.md`
- `artifacts/generation_alignment_v1/generation_alignment_v1_examples.json`

新增说明文档：

- `docs/patch_notes/generation_alignment_v1_patch_note.md`

## 3. 核心实现

### 3.1 Evidence Pack（内部结构）

在 `AnswerAssembler` 内部新增了面向 LLM 的 `Evidence Pack` 组装逻辑：

- 将当前已裁决出的 `primary / secondary / review` 证据重新编号为内部 `E1 / E2 / ...`
- 每条证据传给 LLM 的字段包括：
  - `evidence_id`
  - `source_type`
  - `section_label`
  - `title`
  - `content`
- `content` 做了长度裁剪，避免 prompt 过长
- 该结构只用于内部 prompt，不对外暴露，也不影响 payload contract

### 3.2 Prompt 从“改写器”升级为“证据解释器”

`backend/llm/prompt_builder.py` 已改为：

- 输入 `Evidence Pack`，不再以 baseline 文本为主输入
- 明确要求 LLM 先输出 `evidence_outline` 再输出 `answer_text`
- 强制 `answer_text` 结构为：
  - 第 1 行一句结论
  - 第 2 行起 2-4 条编号要点
  - 每一行都要带 `[E#]`
- 强制 `strong` 只能引用 primary evidence 的 `[E#]`
- 强制 `weak_with_review_notice` 保留不确定性表达
- 增加 strict retry 模式，用于第一次生成越界或格式不稳时重新压缩表述

### 3.3 Validator 升级

`backend/llm/validator.py` 新增了 answer_text 级别的边界校验：

- 检查 JSON 结构与长度范围
- 检查每一行是否都带合法 `[E#]`
- 检查 `[E#]` 是否都来自当前 Evidence Pack
- 检查 `strong` 是否错误引用了 secondary/review evidence
- 检查关键句与其引用证据之间是否存在基本词面重合，降低无证据断言风险
- `weak_with_review_notice` 继续强制保留“需核对 / 证据不足 / 暂不能视为确定答案”等不确定提示

### 3.4 自动重试与降级

`backend/answers/assembler.py` 中的 LLM 调用策略已变为：

- `strong`：若 LLM enabled，必须尝试 LLM 生成
- `weak_with_review_notice`：若 LLM enabled，尝试生成保守解释
- `refuse`：仍然跳过 LLM
- 非拒答模式下：
  1. 首次生成
  2. validator 不通过时，进入 strict retry
  3. 若仍失败，则返回 guardrail fallback

guardrail fallback 的特点：

- 不改 `answer_mode`
- 不改 evidence slots
- 不改 `citations`
- answer_text 改为保守、可核验、带 `[E#]` 的整理文本
- 不会导致接口失败

### 3.5 LLM 配置微调

为了适配新的 Evidence Pack + JSON 输出：

- `DEFAULT_LLM_MAX_OUTPUT_TOKENS` 从 `480` 调整为 `900`
- `DEFAULT_LLM_TIMEOUT_SECONDS` 从 `12.0` 调整为 `20.0`

目的：

- 避免解释型 JSON 在长回答时被截断
- 给 strict retry 和弱解释题更稳定的回包时间

## 4. 明确保留不变的内容

本轮未改：

- payload 顶层字段名与结构
- `answer_mode` 决策逻辑
- 三槽位裁决逻辑
- `citations` 生成方式
- API contract
- 前端
- 检索 / rerank / evaluator 主链

## 5. 回归命令

本轮新增回归脚本：

```bash
python -m backend.checks.generation_alignment_v1_checks
```

该脚本会同时跑：

- required
  - `黄连汤方的条文是什么？`
  - `烧针益阳而损阴是什么意思？`
  - `书中有没有提到量子纠缠？`
- explainer
  - `太阳病应该怎么办？`
  - `黄连汤方由什么组成？`
  - `桂枝加附子汤方由什么组成？`

并自动校验：

- payload contract 未漂移
- `answer_mode` 未漂移
- 三槽位 record_id 未漂移
- `citations` 未漂移
- 非拒答 answer_text 是否满足“结论 + 2-4 条编号要点 + 每行 `[E#]`”
- `refuse` 是否继续跳过 LLM

## 6. 产物

本轮产物：

- `artifacts/generation_alignment_v1/generation_alignment_v1_report.md`
- `artifacts/generation_alignment_v1/generation_alignment_v1_examples.json`

回归结论（对应当前产物）：

- 6/6 用例 mode 保持不变
- 6/6 用例 evidence slots 保持不变
- 6/6 用例 citations 保持不变
- 5/5 非拒答用例 answer_text 均满足 `[E#]` 对齐与解释型结构
- refuse 继续跳过 LLM
- required + explainer 共 5 条非拒答样例均成功使用真实 LLM 输出

## 7. 对论文 / 答辩口径的意义

本轮之后，仓库中的 answer_text 生成方式更贴近开题报告中的描述：

- 检索证据先进入生成链，而不是只作为改写背景
- 回答正文具备逐点可核验的证据编号
- 通过 prompt + validator + retry/fallback 共同降低幻觉与错引
- 保持了现有 RAG 主链的稳定合同，不引入主行为漂移
