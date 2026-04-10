# Goldset v2 Batch C Patch Note

- 日期：2026-04-08
- 范围：评估集扩容 Batch C，126 -> 150
- 基线：`artifacts/evaluation/goldset_v2_working_126.json` 保持冻结，未覆盖

## 变更

1. 新增 `artifacts/evaluation/goldset_v2_batchC_new_items.json`，只包含本轮新增的 24 条样本。
2. 新增 `artifacts/evaluation/goldset_v2_working_150.json`，由 working 126 加本轮 24 条组成。
3. 新增 `artifacts/evaluation/goldset_v2_batchC_log.json`，逐题记录 query、题型、来源、rationale、answer mode bucket 和设计备注。
4. 新增 `docs/evaluation/goldset_v2_batchC_plan_v1.md`，记录 Batch C 的新增策略、配额和 150 左右目标完成状态。
5. 新增 `artifacts/evaluation/goldset_v2_batchC_eval_report.json` 和 `artifacts/evaluation/goldset_v2_batchC_eval_report.md`，记录 evaluator v1 在 150 条 working set 上的回放结果。

## 新增数量

- source_lookup: 5
- comparison: 5
- meaning_explanation: 6
- general_overview: 3
- refusal: 5
- total: 24

## 当前总量

当前 working set 从 126 条增加到 150 条；question_id 新增范围为 `eval_seed_q127` 到 `eval_seed_q150`。

Batch C 后的题型分布：

- source_lookup: 40
- comparison: 30
- meaning_explanation: 30
- general_overview: 20
- refusal: 30

当前阶段“扩到 150 左右”的目标已完成。

## 边界说明

本轮只新增样本，不修旧题，不改旧 126 条，不改 retrieval / rerank / gating / answer assembler，不改 API / frontend，不重写 evaluator v1，不扩到 200-250。

新增样本全部为 `manual_independent`。非 refusal 样本的 gold evidence 均来自 `main_passages.json` 或 `annotations.json`；refusal 样本 gold evidence 为空，source_refs 只记录结构化语料边界，不使用 evaluator report、系统 replay 或旧示例答案。

## 验证摘要

- `jq empty`：新增 JSON、working set、batch log、eval report 均通过。
- `evaluator v1`：已在 `goldset_v2_working_150.json` 上运行，总题量 150，`failure_count = 0`，`all_checks_passed = true`。
- 题型统计：source_lookup 40、comparison 30、meaning_explanation 30、general_overview 20、refusal 30。
- mode match: `150/150`。
- citation basic pass: `120/120`。
- `jsonschema`：当前环境缺少 `jsonschema`，未执行 jsonschema 校验。
