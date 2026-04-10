# Evaluator Runner v1 Patch Note

## 1. 本轮新增了什么

本轮新增最小 evaluator runner v1，用于把 `artifacts/evaluation/goldset_v1_seed.json` 自动 replay 成结构化评估报告。

新增文件：

1. `scripts/run_evaluator_v1.py`
   - 读取 seed goldset。
   - 默认通过本地 `backend.answers.assembler.AnswerAssembler` replay 当前正式主链。
   - 支持可选 `--runner-backend api`，用于对已启动的 `POST /api/v1/answers` 端点 replay。
   - 输出 JSON 与 Markdown 两份报告。
2. `artifacts/evaluation/evaluator_v1_report.json`
   - 结构化保存每题 expected vs actual、基础 citation / evidence 检查、最小无证据断言检查和汇总统计。
3. `artifacts/evaluation/evaluator_v1_report.md`
   - 保存面向人工审查的首份 evaluator v1 评估摘要。
4. `docs/patch_notes/evaluator_v1_patch_note.md`
   - 记录本轮 runner 范围、执行入口、校验规则和结果。

## 2. 本轮使用的 replay 入口

本轮默认使用本地 answer assembler，而不是启动 HTTP API：

`query -> hybrid retrieval -> evidence gating -> answer assembler`

这样做的原因是：

1. 不要求评估前手动启动本地 HTTP 服务。
2. 不修改 `POST /api/v1/answers`。
3. 不修改 answer payload contract。
4. 不修改 retrieval 主链或 answer assembler 业务逻辑。

脚本仍保留 `--runner-backend api`，后续如果需要覆盖完整 HTTP transport adapter，可以直接对正式 API endpoint 执行同一套 goldset replay。

## 3. 自动检查规则

每题当前至少输出以下字段：

1. `question_id`
2. `query`
3. `expected_mode`
4. `actual_mode`
5. `mode_match`
6. `citations_present`
7. `primary_empty_check`
8. `zero_evidence_check`
9. `zero_citations_check`
10. `gold_citation_check`
11. `unsupported_assertion_check`

其中 `gold_citation_check` 使用最小规则：

1. citation 的 `record_id` 命中 `gold_record_ids`，记为通过；
2. 或 citation 的 record_id 中可解析出的 canonical passage id 命中 `gold_passage_ids`，也记为通过。

`unsupported_assertion_check` 当前是最小规则版，主要拦截：

1. 应拒答但未拒答；
2. 应弱答但返回 strong；
3. 应保持 `primary_evidence` 为空但出现主证据；
4. 应零证据或零引用但出现证据 / 引用；
5. strong 回答没有 evidence、`primary_evidence`、citations 或 gold citation。

## 4. 本次运行结果

运行命令：

```bash
python scripts/run_evaluator_v1.py
```

本次 replay 结果：

1. 总题数：9
2. `answer_mode` 匹配：9 / 9
3. `citation_check_required` 基础通过：6 / 7
4. 失败样本：1 条

失败样本：

1. `eval_seed_q004`
   - query：`少阴病应该怎么办？`
   - expected_mode：`strong`
   - actual_mode：`strong`
   - failed_checks：`gold_citation_check`, `unsupported_assertion_check`
   - 说明：当前 strong citations 指向另一组少阴病分支；goldset 中的三条少阴病 gold 依据出现在 `secondary_evidence`，但没有进入 citations，因此按 v1 citation gold 命中规则记为失败。

## 5. 本轮未做什么

本轮明确没有做以下事情：

1. 没有扩写 seed goldset 题量。
2. 没有接 Prompt / LLM。
3. 没有修改 API。
4. 没有修改 answer payload contract。
5. 没有修改 retrieval 主链。
6. 没有修改 answer assembler 业务逻辑。

本轮重点只是把评估执行链跑通，并产出首份可审查的 evaluator v1 报告。
