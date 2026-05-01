# failure_report_v1

本报告只合并既有 eval 产物做失败归因，不运行问答链路，也不做系统修复。当前 answer_eval_v1 已暴露 citation_from_top_k_rate、scope_qualified_rate 等诊断信号，因此报告按样本列出问题来源。

## 总览
| field | value |
| --- | --- |
| total_examples | 36 |
| answerable_metric_examples | 25 |
| diagnostic_only_examples | 5 |
| unanswerable_examples | 6 |
| formal_fail_count | 17 |
| warning_count | 2 |
| diagnostic_count | 5 |
| ok_count | 12 |

## retrieval_eval_v1 指标摘要
| metric | value |
| --- | --- |
| total_examples | 36 |
| answerable_metric_examples | 25 |
| diagnostic_only_examples | 5 |
| unanswerable_examples | 6 |
| hit_at_1 | 0.8 |
| hit_at_3 | 0.84 |
| hit_at_5 | 0.84 |
| mrr | 0.813333 |
| recall_at_5 | 0.84 |

## answer_eval_v1 指标摘要
| metric | value |
| --- | --- |
| total_examples | 36 |
| answerable_metric_examples | 25 |
| diagnostic_only_examples | 5 |
| unanswerable_examples | 6 |
| has_citation_rate | 1.0 |
| citation_from_top_k_rate | 0.44 |
| gold_cited_rate | 0.8 |
| refuse_when_should_not_answer_rate | 1.0 |
| scope_qualified_rate | 0.612903 |
| answer_keyword_hit_rate | 1.0 |
| expected_answer_mode_match_rate | 0.677419 |

## failure_type_counts
| key | count |
| --- | --- |
| citation_not_from_top_k | 14 |
| correct_chunk_not_retrieved | 4 |
| expected_answer_mode_mismatch | 10 |
| gold_not_cited | 5 |
| manual_audit_required | 5 |
| scope_qualifier_missing | 12 |

## recommended_next_action_counts
| key | count |
| --- | --- |
| consider_answer_template_scope_phrase | 1 |
| fix_citation_mapping_or_answer_assembly | 1 |
| fix_retrieval_or_chunking | 4 |
| inspect_answer_mode_calibration | 1 |
| inspect_trace_or_citation_mapping | 12 |
| manual_audit_required | 5 |
| none | 12 |

## 正式 fail 样本列表
| id | category | question | primary | all_failure_types | action |
| --- | --- | --- | --- | --- | --- |
| eval_002 | 原文定位 | 麻黄汤方的条文是什么？ | citation_not_from_top_k | citation_not_from_top_k | inspect_trace_or_citation_mapping |
| eval_006 | 原文定位 | 太阳之为病的原文是什么？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_007 | 术语解释 | 干呕是什么意思？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved | fix_retrieval_or_chunking |
| eval_009 | 术语解释 | 反是什么意思？ | citation_not_from_top_k | citation_not_from_top_k, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_010 | 术语解释 | 两阳是什么意思？ | citation_not_from_top_k | citation_not_from_top_k, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_016 | 方剂关联 | 太阳中风鼻鸣乾呕用什么方？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_017 | 方剂关联 | 太阳病项背强几几无汗恶风用什么方？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_018 | 方剂关联 | 伤寒脉浮紧无汗身疼痛用什么方？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_022 | 症候检索 | 头项强痛而恶寒对应哪段原文？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_023 | 症候检索 | 发热汗出恶风脉缓名为什么？ | citation_not_from_top_k | citation_not_from_top_k | inspect_trace_or_citation_mapping |
| eval_024 | 症候检索 | 发热无汗反恶寒名为什么？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_025 | 症候检索 | 发热汗出不恶寒名为什么？ | citation_not_from_top_k | citation_not_from_top_k, gold_not_cited | inspect_trace_or_citation_mapping |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, citation_not_from_top_k, gold_not_cited, scope_qualifier_missing | fix_retrieval_or_chunking |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, citation_not_from_top_k, gold_not_cited, expected_answer_mode_mismatch | fix_retrieval_or_chunking |
| eval_028 | 注文理解 | 注文怎样解释清邪中上？ | gold_not_cited | gold_not_cited, expected_answer_mode_mismatch | fix_citation_mapping_or_answer_assembly |
| eval_029 | 注文理解 | 注文对桂枝汤不可误用有什么提醒？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, gold_not_cited, expected_answer_mode_mismatch | fix_retrieval_or_chunking |
| eval_030 | 注文理解 | 注文如何解释奔豚从何而发？ | citation_not_from_top_k | citation_not_from_top_k, scope_qualifier_missing | inspect_trace_or_citation_mapping |

## warning 样本列表
| id | category | question | primary | all_failure_types | action |
| --- | --- | --- | --- | --- | --- |
| eval_008 | 术语解释 | 清邪中上是什么意思？ | scope_qualifier_missing | scope_qualifier_missing | consider_answer_template_scope_phrase |
| eval_020 | 方剂关联 | 霍乱热多欲饮水用什么方？ | expected_answer_mode_mismatch | expected_answer_mode_mismatch, scope_qualifier_missing | inspect_answer_mode_calibration |

## P2 diagnostic-only 样本列表
| id | category | question | primary | all_failure_types | action |
| --- | --- | --- | --- | --- | --- |
| eval_011 | 术语解释 | 少阴病是什么意思 | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_012 | 术语解释 | 半表半里证和过经有什么不同 | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_013 | 术语解释 | 荣气微和卫气衰有什么区别 | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_014 | 术语解释 | 霍乱和伤寒有什么区别 | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_015 | 术语解释 | 痓病和太阳病有什么不同 | manual_audit_required | manual_audit_required | manual_audit_required |

## citation_not_from_top_k 样本列表
| id | category | question | primary | all_failure_types | action |
| --- | --- | --- | --- | --- | --- |
| eval_002 | 原文定位 | 麻黄汤方的条文是什么？ | citation_not_from_top_k | citation_not_from_top_k | inspect_trace_or_citation_mapping |
| eval_006 | 原文定位 | 太阳之为病的原文是什么？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_009 | 术语解释 | 反是什么意思？ | citation_not_from_top_k | citation_not_from_top_k, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_010 | 术语解释 | 两阳是什么意思？ | citation_not_from_top_k | citation_not_from_top_k, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_016 | 方剂关联 | 太阳中风鼻鸣乾呕用什么方？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_017 | 方剂关联 | 太阳病项背强几几无汗恶风用什么方？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_018 | 方剂关联 | 伤寒脉浮紧无汗身疼痛用什么方？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_022 | 症候检索 | 头项强痛而恶寒对应哪段原文？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_023 | 症候检索 | 发热汗出恶风脉缓名为什么？ | citation_not_from_top_k | citation_not_from_top_k | inspect_trace_or_citation_mapping |
| eval_024 | 症候检索 | 发热无汗反恶寒名为什么？ | citation_not_from_top_k | citation_not_from_top_k, expected_answer_mode_mismatch, scope_qualifier_missing | inspect_trace_or_citation_mapping |
| eval_025 | 症候检索 | 发热汗出不恶寒名为什么？ | citation_not_from_top_k | citation_not_from_top_k, gold_not_cited | inspect_trace_or_citation_mapping |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, citation_not_from_top_k, gold_not_cited, scope_qualifier_missing | fix_retrieval_or_chunking |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, citation_not_from_top_k, gold_not_cited, expected_answer_mode_mismatch | fix_retrieval_or_chunking |
| eval_030 | 注文理解 | 注文如何解释奔豚从何而发？ | citation_not_from_top_k | citation_not_from_top_k, scope_qualifier_missing | inspect_trace_or_citation_mapping |

## gold_not_cited 样本列表
| id | category | question | primary | all_failure_types | action |
| --- | --- | --- | --- | --- | --- |
| eval_025 | 症候检索 | 发热汗出不恶寒名为什么？ | citation_not_from_top_k | citation_not_from_top_k, gold_not_cited | inspect_trace_or_citation_mapping |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, citation_not_from_top_k, gold_not_cited, scope_qualifier_missing | fix_retrieval_or_chunking |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, citation_not_from_top_k, gold_not_cited, expected_answer_mode_mismatch | fix_retrieval_or_chunking |
| eval_028 | 注文理解 | 注文怎样解释清邪中上？ | gold_not_cited | gold_not_cited, expected_answer_mode_mismatch | fix_citation_mapping_or_answer_assembly |
| eval_029 | 注文理解 | 注文对桂枝汤不可误用有什么提醒？ | correct_chunk_not_retrieved | correct_chunk_not_retrieved, gold_not_cited, expected_answer_mode_mismatch | fix_retrieval_or_chunking |

## 下一轮建议
| recommended_next_action | count |
| --- | --- |
| consider_answer_template_scope_phrase | 1 |
| fix_citation_mapping_or_answer_assembly | 1 |
| fix_retrieval_or_chunking | 4 |
| inspect_answer_mode_calibration | 1 |
| inspect_trace_or_citation_mapping | 12 |
| manual_audit_required | 5 |
