# eval_diagnostic_loop_policy_integrated_summary_v1

## 本轮目标
把 `secondary_review_citation_policy_v1` 的结果纳入最终诊断总览，只更新 summary 和 next queue。这不是系统全通过；本轮不修 runtime、不改 prompt、不改 API、不改前端。本轮也不改 retrieval、trace、existing evaluator 或 dataset。

## 输入 artifacts
| name | path |
| --- | --- |
| loop_summary | artifacts/eval/eval_diagnostic_loop_v1/eval_diagnostic_loop_summary_v1.json |
| reclassified_report | artifacts/eval/failure_report_reclassified_after_citation_audit_v1/failure_cases_reclassified_v1.json |
| secondary_policy | artifacts/eval/secondary_review_citation_policy_v1/secondary_review_citation_policy_v1.json |
| next_queue_after_citation_audit | artifacts/eval/failure_report_reclassified_after_citation_audit_v1/next_repair_queue_after_citation_audit_v1.json |
| secondary_policy_cases | artifacts/eval/secondary_review_citation_policy_v1/secondary_review_policy_cases_v1.json |

## 旧 reclassified summary
| field | value |
| --- | --- |
| total_examples | 36 |
| failure_report_v1 formal_fail_count | 17 |
| reclassified_formal_fail_count_before_policy | 7 |
| retrieval_eval_v1 Hit@5 | 0.84 |
| answer_eval_v1 citation_from_top_k_rate | 0.44 |

## secondary_review_citation_policy_v1 结果
| field | value |
| --- | --- |
| secondary_review_policy_decision_count | 9 |
| secondary_review_policy_accepted_count | 9 |
| secondary_review_policy_violation_count | 0 |
| secondary_review_policy_needs_trace_improvement_count | 0 |
| policy_integrated_policy_blocking_count | 0 |

9 条 secondary/review policy warning 已被 policy 接受。它们不再进入 runtime repair queue。

## policy-integrated 后的真实待办队列
| queue | count | ids |
| --- | --- | --- |
| runtime_citation_scope_repairs | 3 | eval_023, eval_025, eval_027 |
| trace_or_evaluator_repairs | 2 | eval_002, eval_009 |
| retrieval_or_chunking_repairs | 4 | eval_007, eval_026, eval_027, eval_029 |
| policy_accepted_no_runtime_repair | 9 | eval_006, eval_010, eval_016, eval_017, eval_018, eval_022, eval_024, eval_026, eval_030 |
| p2_manual_audit | 5 | eval_011, eval_012, eval_013, eval_014, eval_015 |
| deferred_observations | 15 | eval_006, eval_008, eval_009, eval_010, eval_016, eval_017, eval_018, eval_020, eval_022, eval_024, eval_026, eval_027, eval_028, eval_029, eval_030 |

policy accepted 不等于所有相关样本都没有别的问题。eval_026 policy accepted，但仍保留 retrieval/chunking repair 观察。

## 9 条 policy accepted 列表
| id | category | question | next_action | notes |
| --- | --- | --- | --- | --- |
| eval_006 | 原文定位 | 太阳之为病的原文是什么？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |
| eval_010 | 术语解释 | 两阳是什么意思？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |
| eval_016 | 方剂关联 | 太阳中风鼻鸣乾呕用什么方？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |
| eval_017 | 方剂关联 | 太阳病项背强几几无汗恶风用什么方？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |
| eval_018 | 方剂关联 | 伤寒脉浮紧无汗身疼痛用什么方？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |
| eval_022 | 症候检索 | 头项强痛而恶寒对应哪段原文？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |
| eval_024 | 症候检索 | 发热无汗反恶寒名为什么？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | none | weak answer cites secondary/review material with conservative language and traceable slots. policy accepted 只解决 secondary/review citation policy，不代表 retrieval/chunking 已修。 |
| eval_030 | 注文理解 | 注文如何解释奔豚从何而发？ | none | weak answer cites secondary/review material with conservative language and traceable slots. |

## 3 条 runtime citation bug 列表
| id | category | question | next_action | notes |
| --- | --- | --- | --- | --- |
| eval_023 | 症候检索 | 发热汗出恶风脉缓名为什么？ | fix_answer_assembly_citation_scope | citation audit root_cause=real_citation_assembly_issue reclassifies the original citation_not_from_top_k signal. |
| eval_025 | 症候检索 | 发热汗出不恶寒名为什么？ | fix_answer_assembly_citation_scope | citation audit root_cause=real_citation_assembly_issue reclassifies the original citation_not_from_top_k signal. |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | fix_answer_assembly_citation_scope | citation audit root_cause=real_citation_assembly_issue reclassifies the original citation_not_from_top_k signal. |

## 2 条 trace/evaluator issue 列表
| id | category | question | next_action | notes |
| --- | --- | --- | --- | --- |
| eval_002 | 原文定位 | 麻黄汤方的条文是什么？ | fix_trace_logging_or_eval_equivalence | citation audit root_cause=trace_topk_missing_equivalence reclassifies the original citation_not_from_top_k signal. |
| eval_009 | 术语解释 | 反是什么意思？ | fix_trace_logging_or_eval_equivalence | citation audit root_cause=trace_topk_missing_equivalence reclassifies the original citation_not_from_top_k signal. |

## retrieval/chunking repair 列表
| id | category | question | next_action | notes |
| --- | --- | --- | --- | --- |
| eval_007 | 术语解释 | 干呕是什么意思？ | fix_retrieval_or_chunking |  |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | fix_retrieval_or_chunking | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. policy warning coexists with a still-valid formal retrieval or gold-citation failure. policy accepted 只解决 secondary/review citation policy，不代表 retrieval/chunking 已修。 |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | fix_answer_assembly_citation_scope | citation audit root_cause=real_citation_assembly_issue reclassifies the original citation_not_from_top_k signal. |
| eval_029 | 注文理解 | 注文对桂枝汤不可误用有什么提醒？ | fix_retrieval_or_chunking |  |

## 5 条 P2 manual audit 列表
| id | category | question | next_action | notes |
| --- | --- | --- | --- | --- |
| eval_011 | 术语解释 | 少阴病是什么意思 | manual_audit_required | P2 residual remains diagnostic-only and is excluded from runtime repair queues. |
| eval_012 | 术语解释 | 半表半里证和过经有什么不同 | manual_audit_required | P2 residual remains diagnostic-only and is excluded from runtime repair queues. |
| eval_013 | 术语解释 | 荣气微和卫气衰有什么区别 | manual_audit_required | P2 residual remains diagnostic-only and is excluded from runtime repair queues. |
| eval_014 | 术语解释 | 霍乱和伤寒有什么区别 | manual_audit_required | P2 residual remains diagnostic-only and is excluded from runtime repair queues. |
| eval_015 | 术语解释 | 痓病和太阳病有什么不同 | manual_audit_required | P2 residual remains diagnostic-only and is excluded from runtime repair queues. |

## deferred observations
| id | category | question | next_action | notes |
| --- | --- | --- | --- | --- |
| eval_006 | 原文定位 | 太阳之为病的原文是什么？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |
| eval_008 | 术语解释 | 清邪中上是什么意思？ | consider_answer_template_scope_phrase |  |
| eval_009 | 术语解释 | 反是什么意思？ | fix_trace_logging_or_eval_equivalence | citation audit root_cause=trace_topk_missing_equivalence reclassifies the original citation_not_from_top_k signal. |
| eval_010 | 术语解释 | 两阳是什么意思？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |
| eval_016 | 方剂关联 | 太阳中风鼻鸣乾呕用什么方？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |
| eval_017 | 方剂关联 | 太阳病项背强几几无汗恶风用什么方？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |
| eval_018 | 方剂关联 | 伤寒脉浮紧无汗身疼痛用什么方？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |
| eval_020 | 方剂关联 | 霍乱热多欲饮水用什么方？ | inspect_answer_mode_calibration |  |
| eval_022 | 症候检索 | 头项强痛而恶寒对应哪段原文？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |
| eval_024 | 症候检索 | 发热无汗反恶寒名为什么？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | fix_retrieval_or_chunking | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. policy warning coexists with a still-valid formal retrieval or gold-citation failure. |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | fix_answer_assembly_citation_scope | citation audit root_cause=real_citation_assembly_issue reclassifies the original citation_not_from_top_k signal. |
| eval_028 | 注文理解 | 注文怎样解释清邪中上？ | fix_citation_mapping_or_answer_assembly |  |
| eval_029 | 注文理解 | 注文对桂枝汤不可误用有什么提醒？ | fix_retrieval_or_chunking |  |
| eval_030 | 注文理解 | 注文如何解释奔豚从何而发？ | define_secondary_review_citation_policy | weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair. |

这些 observation 不改变本轮 runtime citation repair、tooling repair、policy accepted 或 P2 diagnostic 的分流。

## 下一步建议
- runtime citation repair 仍只处理 eval_023 / eval_025 / eval_027。
- trace/evaluator tooling repair 仍只处理 eval_002 / eval_009。
- retrieval/chunking repair 队列继续保留，不因 policy accepted 被吞掉。
- P2 manual audit 仍是 diagnostic，不进入 formal runtime repair。
- 保持 `system_all_passed=false`；下一轮若修复，应按 queue 分流单独开任务。
