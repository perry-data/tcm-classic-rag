# Goldset v2 Batch A Patch Note

- 日期：2026-04-08
- 范围：评估集扩容 Batch A，72 -> 102
- 基线：`artifacts/evaluation/goldset_v1_seed.json` 保持冻结，未覆盖

## 变更

1. 新增 `artifacts/evaluation/goldset_v2_batchA_new_items.json`，只包含本轮新增的 30 条样本。
2. 新增 `artifacts/evaluation/goldset_v2_working_102.json`，由原 72 条基线加本轮 30 条组成。
3. 新增 `artifacts/evaluation/goldset_v2_batchA_log.json`，逐题记录 query、题型、来源、rationale、answer mode bucket 和设计备注。
4. 新增 `docs/evaluation/goldset_expansion_to_150_plan_v1.md`，记录 72 -> 150 的总体策略、Batch A 范围和剩余配额。
5. 新增 `artifacts/evaluation/goldset_v2_batchA_eval_report.json` 和 `artifacts/evaluation/goldset_v2_batchA_eval_report.md`，记录 evaluator v1 在 102 条 working set 上的回放结果。

## 新增数量

- source_lookup: 10
- comparison: 8
- meaning_explanation: 4
- general_overview: 2
- refusal: 6
- total: 30

## 当前总量

当前 working set 从 72 条增加到 102 条；question_id 新增范围为 `eval_seed_q073` 到 `eval_seed_q102`。到 150 条目标还差 48 条。

## 边界说明

本轮只新增样本，不修旧题，不继续独立性审查，不改系统链路，不改 evaluator v1。新增样本全部为 `manual_independent`，非拒答题的 gold evidence 均来自 `main_passages.json` 或 `annotations.json`；拒答题 gold evidence 为空，source_refs 只记录结构化语料边界，不使用 evaluator report、系统 replay 或旧示例答案。

## 验证摘要

- `jq empty`：新增 JSON、working set、batch log、eval report 均通过。
- `evaluator v1`：已在 `goldset_v2_working_102.json` 上运行，总题量 102，failure_count 13。
- `jsonschema`：环境缺少 `jsonschema`，未执行 jsonschema 校验。
