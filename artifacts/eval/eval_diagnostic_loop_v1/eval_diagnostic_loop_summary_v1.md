# eval_diagnostic_loop_summary_v1

## 本轮目标
这是诊断闭环总览；这不是系统全通过。本轮只一键复跑既有诊断链路并汇总产物，不修系统、不改规则、不隐藏失败。

## 运行配置
| field | value |
| --- | --- |
| dataset_path | data/eval/eval_dataset_v1.csv |
| run_mode | B_retrieval_rerank_no_llm |
| PERF_DISABLE_LLM | 1 |
| PERF_DISABLE_RERANK | 0 |
| PERF_RETRIEVAL_MODE | hybrid |
| all_steps_passed | True |
| llm_judge | False |

## 各步骤运行状态
| step | status | returncode | stdout excerpt | stderr excerpt |
| --- | --- | --- | --- | --- |
| validate_eval_dataset_v1 | pass | 0 |  |  |
| retrieval_eval_v1 | pass | 0 | [1/36] retrieval: eval_001 桂枝汤方的条文是什么？ [2/36] retrieval: eval_002 麻黄汤方的条文是什么？ [3/36] retrieval: eval_003 白虎汤方的条文是什么？ [4/36] retrieval: eval_004 小柴胡汤方的条文是什么？ [5/36] retrieval: eval_005 乌梅丸方的条文是什么？ [6/36] retrieval: eval_006 太阳之为病的原文是什么？ [7/36] retrieval: eval_007 干呕是什么意思？ [8/36] retrieval: eval_008 清邪中上是什么意思？ [9/36] retrieval: eval_009 反是什么意思？ [10/36] retrieval: eval_010 两阳是什么意思？ [11/36] retrieval: eval_011 少阴病是什么意思 [12/36] retrieval: eval_012 半表半里证和过经有什么不同 [13/36] retrieval: eval_013 荣气微和卫气衰有什么区别 [14/36] retrieval: eval_014 霍乱和伤寒有什么区别 [15/36] retrieval: eval_015 痓病和太阳病有什么不同 [16/36] retrieval: eval_016 太阳中风鼻鸣乾呕用什么方？ [17/36] retrieval: eval_017 太阳病项背强几几无汗恶风用什么方？ [18/36] retrieval: eval_018 伤寒脉浮紧无汗身疼痛用什么方？ [19/36] retrieval: eval_019 小结胸病正在心下按之痛用什么方？ [20/36] retrieval: eval_020 霍乱热多欲饮水用什么方？ [21/36] retrieval: eval_021 呕吐而利在书中叫什么？ [22/36] retrieval: eval_022 头项强痛而恶寒对应哪段原文？ [23/36] retrieval: eval_023 发热汗出恶风脉缓名为什么？ [24/36] retrieval: eval_024 发热无汗反恶寒名为什么？ [25/36] retrieval: eval_025 发热汗出不恶寒名为什么？ [26/36] retrieval: eval_026 成无己如何解释荣气微？ [27/36] retrieval: eval_027 成无己如何解释卫气衰？ [28/36] retrieval: eval_028 注文怎样解释清邪中上？ [29/36] retrieval: eval_029 注文对桂枝汤不可误用有什么提醒？ [30/36] retrieval: eval_030 注文如何解释奔豚从何而发？ [31/36] retrieval: eval_031 白虎是什么意思？ [32/36] retrieval: eval_032 太阳能是什么意思？ [33/36] retrieval: eval_033 霍乱疫苗是什么？ [34/36] retrieval: eval_034 劳动合同是什么？ [35/36] retrieval: eval_035 量子纠缠在书中怎么解释？ [36/36] retrieval: eval_036 Python 怎么写爬虫？ Wrote artifacts/eval/retrieval_eval_v1/retrieval_eval_v1.json Wrote artifacts/eval/retrieval_eval_v1/retrieval_eval_v1.md | Loading weights: 0%\| \| 0/71 [00:00<?, ?it/s] Loading weights: 100%\|██████████\| 71/71 [00:00<00:00, 9521.23it/s] [1mBertModel LOAD REPORT[0m from: /Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/hf_cache/models--BAAI--bge-small-zh-v1.5/snapshots/7999e1d3359715c523056ef9478215996d62a620 Key \| Status \| \| ------------------------+------------+--+- embeddings.position_ids \| UNEXPECTED \| \| Notes: - UNEXPECTED: can be ignored when loading from different task/architecture; not ok if you expect identical arch. Loading weights: 0%\| \| 0/201 [00:00<?, ?it/s] Loading weights: 100%\|██████████\| 201/201 [00:00<00:00, 9739.77it/s] [1mXLMRobertaForSequenceClassification LOAD REPORT[0m from: /Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/hf_cache/models--BAAI--bge-reranker-base/snapshots/2cfc18c9415c912f9d8155881c133215df768a70 Key \| Status \| \| --------------------------------+------------+--+- roberta.embeddings.position_ids \| UNEXPECTED \| \| Notes: - UNEXPECTED: can be ignored when loading from different task/architecture; not ok if you expect identical arch. |
| answer_eval_v1 | pass | 0 | [1/36] answer_eval: eval_001 桂枝汤方的条文是什么？ [2/36] answer_eval: eval_002 麻黄汤方的条文是什么？ [3/36] answer_eval: eval_003 白虎汤方的条文是什么？ [4/36] answer_eval: eval_004 小柴胡汤方的条文是什么？ [5/36] answer_eval: eval_005 乌梅丸方的条文是什么？ [6/36] answer_eval: eval_006 太阳之为病的原文是什么？ [7/36] answer_eval: eval_007 干呕是什么意思？ [8/36] answer_eval: eval_008 清邪中上是什么意思？ [9/36] answer_eval: eval_009 反是什么意思？ [10/36] answer_eval: eval_010 两阳是什么意思？ [11/36] answer_eval: eval_011 少阴病是什么意思 [12/36] answer_eval: eval_012 半表半里证和过经有什么不同 [13/36] answer_eval: eval_013 荣气微和卫气衰有什么区别 [14/36] answer_eval: eval_014 霍乱和伤寒有什么区别 [15/36] answer_eval: eval_015 痓病和太阳病有什么不同 [16/36] answer_eval: eval_016 太阳中风鼻鸣乾呕用什么方？ [17/36] answer_eval: eval_017 太阳病项背强几几无汗恶风用什么方？ [18/36] answer_eval: eval_018 伤寒脉浮紧无汗身疼痛用什么方？ [19/36] answer_eval: eval_019 小结胸病正在心下按之痛用什么方？ [20/36] answer_eval: eval_020 霍乱热多欲饮水用什么方？ [21/36] answer_eval: eval_021 呕吐而利在书中叫什么？ [22/36] answer_eval: eval_022 头项强痛而恶寒对应哪段原文？ [23/36] answer_eval: eval_023 发热汗出恶风脉缓名为什么？ [24/36] answer_eval: eval_024 发热无汗反恶寒名为什么？ [25/36] answer_eval: eval_025 发热汗出不恶寒名为什么？ [26/36] answer_eval: eval_026 成无己如何解释荣气微？ [27/36] answer_eval: eval_027 成无己如何解释卫气衰？ [28/36] answer_eval: eval_028 注文怎样解释清邪中上？ [29/36] answer_eval: eval_029 注文对桂枝汤不可误用有什么提醒？ [30/36] answer_eval: eval_030 注文如何解释奔豚从何而发？ [31/36] answer_eval: eval_031 白虎是什么意思？ [32/36] answer_eval: eval_032 太阳能是什么意思？ [33/36] answer_eval: eval_033 霍乱疫苗是什么？ [34/36] answer_eval: eval_034 劳动合同是什么？ [35/36] answer_eval: eval_035 量子纠缠在书中怎么解释？ [36/36] answer_eval: eval_036 Python 怎么写爬虫？ Wrote artifacts/eval/answer_eval_v1/qa_trace_answer_eval_v1.jsonl Wrote artifacts/eval/answer_eval_v1/answer_eval_v1.json Wrote artifacts/eval/answer_eval_v1/answer_eval_v1.md | Loading weights: 0%\| \| 0/71 [00:00<?, ?it/s] Loading weights: 100%\|██████████\| 71/71 [00:00<00:00, 16928.86it/s] [1mBertModel LOAD REPORT[0m from: /Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/hf_cache/models--BAAI--bge-small-zh-v1.5/snapshots/7999e1d3359715c523056ef9478215996d62a620 Key \| Status \| \| ------------------------+------------+--+- embeddings.position_ids \| UNEXPECTED \| \| Notes: - UNEXPECTED: can be ignored when loading from different task/architecture; not ok if you expect identical arch. Loading weights: 0%\| \| 0/201 [00:00<?, ?it/s] Loading weights: 100%\|██████████\| 201/201 [00:00<00:00, 10144.82it/s] [1mXLMRobertaForSequenceClassification LOAD REPORT[0m from: /Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/hf_cache/models--BAAI--bge-reranker-base/snapshots/2cfc18c9415c912f9d8155881c133215df768a70 Key \| Status \| \| --------------------------------+------------+--+- roberta.embeddings.position_ids \| UNEXPECTED \| \| Notes: - UNEXPECTED: can be ignored when loading from different task/architecture; not ok if you expect identical arch. |
| failure_report_v1 | pass | 0 | {"diagnostic_count": 5, "formal_fail_count": 17, "ok_count": 12, "run_id": "failure_report_v1", "total_examples": 36, "warning_count": 2} |  |
| citation_topk_mismatch_audit_v1 | pass | 0 | Wrote artifacts/eval/citation_topk_mismatch_audit_v1/citation_topk_mismatch_audit_v1.json Wrote artifacts/eval/citation_topk_mismatch_audit_v1/citation_topk_mismatch_audit_v1.md Audited 14 citation_not_from_top_k examples. |  |
| failure_report_reclassified_after_citation_audit_v1 | pass | 0 | Wrote artifacts/eval/failure_report_reclassified_after_citation_audit_v1/failure_cases_reclassified_v1.json Wrote artifacts/eval/failure_report_reclassified_after_citation_audit_v1/failure_cases_reclassified_v1.md Wrote artifacts/eval/failure_report_reclassified_after_citation_audit_v1/next_repair_queue_after_citation_audit_v1.json Reclassified 36 examples; runtime citation repairs=3, trace/evaluator repairs=2, policy decisions=9. |  |

## dataset 概况
| metric | value |
| --- | --- |
| total_examples | 36 |
| category_counts | {'原文定位': 6, '方剂关联': 5, '术语解释': 9, '注文理解': 5, '症候检索': 5, '超范围拒答': 6} |
| dataset_valid | True |

### category_counts
| key | count |
| --- | --- |
| 原文定位 | 6 |
| 方剂关联 | 5 |
| 术语解释 | 9 |
| 注文理解 | 5 |
| 症候检索 | 5 |
| 超范围拒答 | 6 |

## retrieval 指标
| metric | value |
| --- | --- |
| answerable_metric_examples | 25 |
| diagnostic_only_examples | 5 |
| unanswerable_examples | 6 |
| hit_at_1 | 0.8 |
| hit_at_3 | 0.84 |
| hit_at_5 | 0.84 |
| mrr | 0.813333 |
| recall_at_5 | 0.84 |

## answer 指标
| metric | value |
| --- | --- |
| has_citation_rate | 1.0 |
| citation_from_top_k_rate | 0.44 |
| gold_cited_rate | 0.8 |
| refuse_when_should_not_answer_rate | 1.0 |
| scope_qualified_rate | 0.612903 |
| answer_keyword_hit_rate | 1.0 |
| expected_answer_mode_match_rate | 0.677419 |
| llm_used | False |

answer_eval_v1 使用 rules-only 评估；summary 记录 no_llm=true，且 answer.llm_used=false。

## failure_report 原始归因
| metric | value |
| --- | --- |
| formal_fail_count | 17 |
| warning_count | 2 |
| diagnostic_count | 5 |
| ok_count | 12 |

### failure_type_counts
| key | count |
| --- | --- |
| citation_not_from_top_k | 14 |
| correct_chunk_not_retrieved | 4 |
| expected_answer_mode_mismatch | 10 |
| gold_not_cited | 5 |
| manual_audit_required | 5 |
| scope_qualifier_missing | 12 |

## citation audit 结论
| metric | value |
| --- | --- |
| total_citation_not_from_topk | 14 |
| runtime_bug_count | 3 |
| evaluator_or_trace_issue_count | 2 |
| manual_audit_required_count | 0 |

### root_cause_counts
| key | count |
| --- | --- |
| answer_uses_secondary_or_review_not_in_topk | 9 |
| real_citation_assembly_issue | 3 |
| trace_topk_missing_equivalence | 2 |

## reclassified 归因
| metric | value |
| --- | --- |
| original_formal_fail_count | 17 |
| reclassified_formal_fail_count | 7 |
| runtime_bug_count | 3 |
| tooling_count | 2 |
| policy_warning_count | 9 |
| diagnostic_count | 5 |
| ok_count | 12 |

## next repair queue
| queue | count | ids |
| --- | --- | --- |
| runtime_citation_scope_repairs | 3 | eval_023, eval_025, eval_027 |
| trace_or_evaluator_repairs | 2 | eval_002, eval_009 |
| secondary_review_policy_decisions | 9 | eval_006, eval_010, eval_016, eval_017, eval_018, eval_022, eval_024, eval_026, eval_030 |
| retrieval_or_chunking_repairs | 4 | eval_007, eval_026, eval_027, eval_029 |
| p2_manual_audit | 5 | eval_011, eval_012, eval_013, eval_014, eval_015 |

## 下一步建议
- reclassified formal fail 仍为 7。
- 3 条是真 runtime citation bug：eval_023, eval_025, eval_027。
- 2 条是 trace/evaluator 工具问题：eval_002, eval_009。
- 9 条是 secondary/review citation policy decision：eval_006, eval_010, eval_016, eval_017, eval_018, eval_022, eval_024, eval_026, eval_030。
- 5 条 P2 仍是 diagnostic：eval_011, eval_012, eval_013, eval_014, eval_015。
- 下一轮若进入修复，应先按 queue 分流；policy warning 先定政策，不作为 runtime bug 直接修。
