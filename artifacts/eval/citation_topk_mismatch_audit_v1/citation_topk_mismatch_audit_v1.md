# citation_topk_mismatch_audit_v1

本报告只审计 failure_report_v1 中包含 citation_not_from_top_k 的样本。本轮不重新运行检索、不重新生成答案、不使用 LLM judge，也不修改系统。

## 总览
| field | value |
| --- | --- |
| source_failure_report | artifacts/eval/failure_report_v1/failure_cases_v1.json |
| total_citation_not_from_topk | 14 |
| runtime_bug_count | 3 |
| evaluator_or_trace_issue_count | 2 |
| manual_audit_required_count | 0 |
| runs_retrieval | False |
| runs_answer_generation | False |
| llm_judge | False |

## root_cause_counts
| key | count |
| --- | --- |
| answer_uses_secondary_or_review_not_in_topk | 9 |
| real_citation_assembly_issue | 3 |
| trace_topk_missing_equivalence | 2 |

## 审计发现
| key | count |
| --- | --- |
| answer_uses_secondary_or_review_not_in_topk_rows | 9 |
| formula_or_definition_source_expansion_rows | 10 |
| primary_citation_not_in_topk_rows | 3 |
| real_runtime_bug_rows | 3 |
| retrieval_but_not_existing_equivalence_citation_count | 2 |
| trace_top_k_chunks_record_id_mismatch_rows | 1 |
| trace_topk_missing_equivalence_rows | 2 |

## recommended_next_action_counts
| key | count |
| --- | --- |
| fix_answer_assembly_citation_scope | 3 |
| fix_trace_logging | 2 |
| inspect_secondary_review_citation_policy | 9 |

## 每条 citation_not_from_top_k 审计表
| id | category | question | answer_mode | root_cause | runtime_bug | next_action | existing match | retrieval match | unmatched after retrieval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eval_002 | 原文定位 | 麻黄汤方的条文是什么？ | strong | trace_topk_missing_equivalence | False | fix_trace_logging | 2/3 | 3/3 | 0 |
| eval_006 | 原文定位 | 太阳之为病的原文是什么？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 3/6 | 3/6 | 3 |
| eval_009 | 术语解释 | 反是什么意思？ | weak_with_review_notice | trace_topk_missing_equivalence | False | fix_trace_logging | 7/8 | 8/8 | 0 |
| eval_010 | 术语解释 | 两阳是什么意思？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 4/7 | 4/7 | 3 |
| eval_016 | 方剂关联 | 太阳中风鼻鸣乾呕用什么方？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 6/7 | 6/7 | 1 |
| eval_017 | 方剂关联 | 太阳病项背强几几无汗恶风用什么方？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 2/7 | 2/7 | 5 |
| eval_018 | 方剂关联 | 伤寒脉浮紧无汗身疼痛用什么方？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 6/7 | 6/7 | 1 |
| eval_022 | 症候检索 | 头项强痛而恶寒对应哪段原文？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 4/8 | 4/8 | 4 |
| eval_023 | 症候检索 | 发热汗出恶风脉缓名为什么？ | strong | real_citation_assembly_issue | True | fix_answer_assembly_citation_scope | 1/3 | 1/3 | 2 |
| eval_024 | 症候检索 | 发热无汗反恶寒名为什么？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 4/12 | 4/12 | 8 |
| eval_025 | 症候检索 | 发热汗出不恶寒名为什么？ | strong | real_citation_assembly_issue | True | fix_answer_assembly_citation_scope | 1/3 | 1/3 | 2 |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 5/13 | 5/13 | 8 |
| eval_027 | 注文理解 | 成无己如何解释卫气衰？ | strong | real_citation_assembly_issue | True | fix_answer_assembly_citation_scope | 0/1 | 0/1 | 1 |
| eval_030 | 注文理解 | 注文如何解释奔豚从何而发？ | weak_with_review_notice | answer_uses_secondary_or_review_not_in_topk | False | inspect_secondary_review_citation_policy | 4/10 | 4/10 | 6 |

## 哪些应修 trace
| id | question | root_cause | notes |
| --- | --- | --- | --- |
| eval_002 | 麻黄汤方的条文是什么？ | trace_topk_missing_equivalence | retrieval_eval top5 matchable ids cover the citation, but answer_eval trace-topk equivalence does not. \| trace_top_k_record_ids_match_retrieval_eval=true \| existing_equivalence_match=2/3 \| retrieval_equivalence_match=3/3 \| object_source_expansion_ids=safe:main_passages:ZJSHL-CH-009-P-0022,safe:main_passages:ZJSHL-CH-009-P-0025 \| answer_eval_notes=at least one citation was not found in trace top_k_chunks |
| eval_009 | 反是什么意思？ | trace_topk_missing_equivalence | retrieval_eval top5 matchable ids cover the citation, but answer_eval trace-topk equivalence does not. \| trace_top_k_record_ids_match_retrieval_eval=true \| existing_equivalence_match=7/8 \| retrieval_equivalence_match=8/8 \| object_source_expansion_ids=safe:main_passages:ZJSHL-CH-025-P-0007,safe:main_passages:ZJSHL-CH-009-P-0159,safe:main_passages:ZJSHL-CH-014-P-0107,safe:main_passages:ZJSHL-CH-014-P-0108,safe:main_passages:ZJSHL-CH-014-P-0105,safe:main_passages:ZJSHL-CH-014-P-0069,safe:main_passages:ZJSHL-CH-015-P-0265 \| answer_eval_notes=at least one citation was not found in trace top_k_chunks |

## 哪些应修 evaluator id equivalence
_None._

## 哪些可能是真 answer assembly bug
| id | question | root_cause | notes |
| --- | --- | --- | --- |
| eval_023 | 发热汗出恶风脉缓名为什么？ | real_citation_assembly_issue | Primary citation ids are outside retrieval_eval top5 equivalence; this is the strongest runtime citation-scope signal. \| trace_top_k_record_ids_match_retrieval_eval=true \| existing_equivalence_match=1/3 \| retrieval_equivalence_match=1/3 \| primary_outside_top5_ids=safe:main_passages:ZJSHL-CH-008-P-0229,safe:main_passages:ZJSHL-CH-008-P-0220 \| answer_eval_notes=at least one citation was not found in trace top_k_chunks |
| eval_025 | 发热汗出不恶寒名为什么？ | real_citation_assembly_issue | Primary citation ids are outside retrieval_eval top5 equivalence; this is the strongest runtime citation-scope signal. \| trace_top_k_record_ids_match_retrieval_eval=true \| existing_equivalence_match=1/3 \| retrieval_equivalence_match=1/3 \| primary_outside_top5_ids=safe:main_passages:ZJSHL-CH-011-P-0101,safe:main_passages:ZJSHL-CH-009-P-0159 \| answer_eval_notes=at least one citation was not found in trace top_k_chunks; no citation matched gold_chunk_ids under evaluator equivalence |
| eval_027 | 成无己如何解释卫气衰？ | real_citation_assembly_issue | Primary citation ids are outside retrieval_eval top5 equivalence; this is the strongest runtime citation-scope signal. \| trace_top_k_record_ids_match_retrieval_eval=false \| existing_equivalence_match=0/1 \| retrieval_equivalence_match=0/1 \| primary_outside_top5_ids=safe:main_passages:ZJSHL-CH-004-P-0255 \| answer_eval_notes=at least one citation was not found in trace top_k_chunks; no citation matched gold_chunk_ids under evaluator equivalence |

## 下一轮建议
| recommended_next_action | count | scope |
| --- | --- | --- |
| fix_trace_logging | 2 | 只改 trace/evidence logging 时再做 |
| fix_evaluator_id_equivalence | 0 | 只改 evaluator 等价映射时再做 |
| allow_formula_source_expansion_in_eval | 0 | 只改 citation_from_top_k 评估口径时再做 |
| inspect_secondary_review_citation_policy | 9 | 先定 weak/review citation 政策，再决定是否修 |
| fix_answer_assembly_citation_scope | 3 | 下一轮若修系统，只针对真实 citation scope 问题 |
