# failure_report_reclassified_after_citation_audit_v1

本报告只基于 citation_topk_mismatch_audit_v1 对 failure_report_v1 做诊断归因重分类。它不重新生成答案、不重新跑检索，也不修改原始评测产物或系统实现。

## 总览
| field | value |
| --- | --- |
| total_examples | 36 |
| original_formal_fail_count | 17 |
| reclassified_formal_fail_count | 7 |
| runtime_bug_count | 3 |
| tooling_count | 2 |
| policy_warning_count | 9 |
| policy_warning_only_count | 8 |
| warning_count | 2 |
| diagnostic_count | 5 |
| ok_count | 12 |

## 原 failure_report_v1 计数
| field | value |
| --- | --- |
| formal_fail_count | 17 |
| warning_count | 2 |
| diagnostic_count | 5 |
| ok_count | 12 |
| citation_not_from_top_k | 14 |

## citation audit 计数
| field | value |
| --- | --- |
| total_citation_not_from_topk | 14 |
| runtime_bug_count | 3 |
| evaluator_or_trace_issue_count | 2 |
| manual_audit_required_count | 0 |

| key | count |
| --- | --- |
| answer_uses_secondary_or_review_not_in_topk | 9 |
| real_citation_assembly_issue | 3 |
| trace_topk_missing_equivalence | 2 |

## 重分类后的计数
| key | count |
| --- | --- |
| diagnostic | 5 |
| fail | 7 |
| ok | 12 |
| policy_warning | 8 |
| tooling | 2 |
| warning | 2 |

| key | count |
| --- | --- |
| correct_chunk_not_retrieved | 4 |
| expected_answer_mode_mismatch | 10 |
| gold_not_cited | 5 |
| manual_audit_required | 5 |
| real_citation_assembly_issue | 3 |
| scope_qualifier_missing | 12 |
| secondary_review_citation_policy_needs_decision | 9 |
| trace_or_evaluator_equivalence_gap | 2 |

## 真 runtime citation bug 列表
| id | category | question | severity | primary | types | action |
| --- | --- | --- | --- | --- | --- | --- |
| eval_023 | 症候检索 | 发热汗出恶风脉缓名为什么？ | fail | real_citation_assembly_issue | real_citation_assembly_issue | fix_answer_assembly_citation_scope |
| eval_025 | 症候检索 | 发热汗出不恶寒名为什么？ | fail | real_citation_assembly_issue | real_citation_assembly_issue, gold_not_cited | fix_answer_assembly_citation_scope |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | fail | real_citation_assembly_issue | correct_chunk_not_retrieved, real_citation_assembly_issue, gold_not_cited, expected_answer_mode_mismatch | fix_answer_assembly_citation_scope |

## trace / evaluator 问题列表
| id | category | question | severity | primary | types | action |
| --- | --- | --- | --- | --- | --- | --- |
| eval_002 | 原文定位 | 麻黄汤方的条文是什么？ | tooling | trace_or_evaluator_equivalence_gap | trace_or_evaluator_equivalence_gap | fix_trace_logging_or_eval_equivalence |
| eval_009 | 术语解释 | 反是什么意思？ | tooling | trace_or_evaluator_equivalence_gap | trace_or_evaluator_equivalence_gap, scope_qualifier_missing | fix_trace_logging_or_eval_equivalence |

## secondary / review citation policy 问题列表
| id | category | question | severity | primary | types | action |
| --- | --- | --- | --- | --- | --- | --- |
| eval_006 | 原文定位 | 太阳之为病的原文是什么？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, expected_answer_mode_mismatch, scope_qualifier_missing | define_secondary_review_citation_policy |
| eval_010 | 术语解释 | 两阳是什么意思？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, scope_qualifier_missing | define_secondary_review_citation_policy |
| eval_016 | 方剂关联 | 太阳中风鼻鸣乾呕用什么方？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, expected_answer_mode_mismatch, scope_qualifier_missing | define_secondary_review_citation_policy |
| eval_017 | 方剂关联 | 太阳病项背强几几无汗恶风用什么方？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, expected_answer_mode_mismatch, scope_qualifier_missing | define_secondary_review_citation_policy |
| eval_018 | 方剂关联 | 伤寒脉浮紧无汗身疼痛用什么方？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, expected_answer_mode_mismatch, scope_qualifier_missing | define_secondary_review_citation_policy |
| eval_022 | 症候检索 | 头项强痛而恶寒对应哪段原文？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, expected_answer_mode_mismatch, scope_qualifier_missing | define_secondary_review_citation_policy |
| eval_024 | 症候检索 | 发热无汗反恶寒名为什么？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, expected_answer_mode_mismatch, scope_qualifier_missing | define_secondary_review_citation_policy |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | fail | correct_chunk_not_retrieved | correct_chunk_not_retrieved, secondary_review_citation_policy_needs_decision, gold_not_cited, scope_qualifier_missing | fix_retrieval_or_chunking |
| eval_030 | 注文理解 | 注文如何解释奔豚从何而发？ | policy_warning | secondary_review_citation_policy_needs_decision | secondary_review_citation_policy_needs_decision, scope_qualifier_missing | define_secondary_review_citation_policy |

## retrieval / chunking 仍需修复的问题列表
| id | category | question | severity | primary | types | action |
| --- | --- | --- | --- | --- | --- | --- |
| eval_007 | 术语解释 | 干呕是什么意思？ | fail | correct_chunk_not_retrieved | correct_chunk_not_retrieved | fix_retrieval_or_chunking |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | fail | correct_chunk_not_retrieved | correct_chunk_not_retrieved, secondary_review_citation_policy_needs_decision, gold_not_cited, scope_qualifier_missing | fix_retrieval_or_chunking |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | fail | real_citation_assembly_issue | correct_chunk_not_retrieved, real_citation_assembly_issue, gold_not_cited, expected_answer_mode_mismatch | fix_answer_assembly_citation_scope |
| eval_029 | 注文理解 | 注文对桂枝汤不可误用有什么提醒？ | fail | correct_chunk_not_retrieved | correct_chunk_not_retrieved, gold_not_cited, expected_answer_mode_mismatch | fix_retrieval_or_chunking |

## P2 diagnostic-only 列表
| id | category | question | severity | primary | types | action |
| --- | --- | --- | --- | --- | --- | --- |
| eval_011 | 术语解释 | 少阴病是什么意思 | diagnostic | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_012 | 术语解释 | 半表半里证和过经有什么不同 | diagnostic | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_013 | 术语解释 | 荣气微和卫气衰有什么区别 | diagnostic | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_014 | 术语解释 | 霍乱和伤寒有什么区别 | diagnostic | manual_audit_required | manual_audit_required | manual_audit_required |
| eval_015 | 术语解释 | 痓病和太阳病有什么不同 | diagnostic | manual_audit_required | manual_audit_required | manual_audit_required |

## 下一步建议
| queue | count | next_action |
| --- | --- | --- |
| runtime_citation_scope_repairs | 3 | fix_answer_assembly_citation_scope |
| retrieval_or_chunking_repairs | 4 | fix_retrieval_or_chunking |
| trace_or_evaluator_repairs | 2 | fix_trace_logging_or_eval_equivalence |
| secondary_review_policy_decisions | 9 | define_secondary_review_citation_policy |
| p2_manual_audit | 5 | manual_audit_required |
