# 当前评测集题型分布快照 v1

生成时间：2026-04-21

原始快照来自 `artifacts/data_diagnostics/query_trace_bundle_v1.json` 中的 `eval_distribution_snapshot`。主数据源为 `artifacts/evaluation/goldset_v2_working_150.json`。

## 1. goldset_v2_working_150 分布

总题数：150。

| question_type | 数量 | 占比 |
| --- | ---: | ---: |
| `source_lookup` | 40 | 26.67% |
| `comparison` | 30 | 20.00% |
| `meaning_explanation` | 30 | 20.00% |
| `refusal` | 30 | 20.00% |
| `general_overview` | 20 | 13.33% |

最少题型：

1. `general_overview`：20
2. `comparison`：30
3. `meaning_explanation`：30

## 2. smoke / benchmark query source

静态抽取到的 smoke/benchmark query：

| 文件 | query_count | 覆盖 |
| --- | ---: | --- |
| `scripts/bench_latency.py` | 6 | source/formula 1、general 2、meaning 1、refusal 2 |
| `backend/api/minimal_api.py` | 5 | source/formula 1、meaning 1、general 1、comparison 1、refusal 1 |
| `backend/retrieval/minimal.py` | 3 | source/formula 1、meaning 1、refusal 1 |
| `backend/answers/assembler.py` | 0 | 常量含展开语法，未做静态 literal 抽取 |

这些 smoke query 用于链路健康检查，不应视为真实用户分布。

## 3. 与普通学习者需求的偏差

当前 goldset 分布对系统边界很有用，但与普通学习者需求仍有偏差：

- `source_lookup` 占比最高，适合验证 citation 和 canonical 定位，但普通学习者不一定总问“条文是什么”。
- `general_overview` 只有 13.33%，但普通学习者常问“太阳病怎么办”“少阴病怎么理解”“初学者先抓什么”。
- 没有单独的 `formula_effect` / `formula_usage_context` 题型，方剂“干什么、治什么、适用什么情况”仍混在别的类型里。
- 没有单独的 `learner_oral_query` 题型，口语改写、简称、异写、别名覆盖不足。
- 没有独立的 `commentarial_view` 评测题型，名家讲稿层当前主要靠 smoke 和人工观察。
- refusal 题有 30 条，但真实边界题常带个人症状、剂量、现代病名、比较优劣，仍需继续扩展。

## 4. 下一轮评测数据建议

不改主链路的前提下，下一轮数据层评测可新增以下诊断桶：

| 新桶 | 目的 |
| --- | --- |
| `formula_effect_oral` | 验证“X方干什么/治什么/有什么用” |
| `formula_alias_lookup` | 验证“桂枝汤/桂枝汤方/异写简称” |
| `symptom_oral_mapping` | 验证“怕冷/拉肚子/胸口堵”等归并 |
| `commentarial_scope` | 验证讲稿材料是专讲、比较、泛论还是顺带提及 |
| `learner_study_question` | 验证“怎么学/先抓什么/怎么看提纲” |

这些建议属于评测和数据层，不要求改 prompt 或前端。
