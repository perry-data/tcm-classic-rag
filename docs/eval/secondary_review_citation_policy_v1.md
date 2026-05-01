# secondary_review_citation_policy_v1

本轮目标是只定义 secondary/review citation policy，处理 `next_repair_queue_after_citation_audit_v1.json` 中的 `secondary_review_policy_decisions`。本轮不修 runtime，不修 retrieval，不改已有 evaluator，不改 dataset，不改 prompt，不改前端，不改 API。

## 本轮目标
| field | value |
| --- | --- |
| run_id | secondary_review_citation_policy_v1 |
| policy_version | v1 |
| total_policy_decision_cases | 9 |
| policy_accepted_count | 9 |
| policy_needs_trace_improvement_count | 0 |
| policy_violation_count | 0 |
| manual_audit_required_count | 0 |
| strong_secondary_review_violation_count | 0 |
| policy_cases_also_in_retrieval_or_chunking_repairs | eval_026 |

## 为什么要定义 secondary/review citation policy
citation_topk_mismatch_audit_v1 将 9 条弱答 citation warning 归因为 `answer_uses_secondary_or_review_not_in_topk`。这些样本不是 P2 manual audit，也不属于已确认的 runtime citation bug。必须先明确弱答是否允许引用 secondary/review 材料，才能避免把政策空白误判成 answer assembly 缺陷。

## answer_mode citation 规则
| answer_mode | policy |
| --- | --- |
| strong | strong answer 不允许引用 secondary/review 作为主引用；citations 必须来自 primary evidence。若 strong 引用 secondary/review，标记 policy_violation，下一步是 fix_answer_assembly_citation_scope。 |
| weak_with_review_notice | weak answer 可以引用 secondary/review，但必须带保守语气和可追踪证据槽；final answer 要说明目前不作为稳定定义、只能作为核对线索、建议回到原文核对、证据不足以强答等；citation source slot 或 trace/evidence slots 必须能追踪到 secondary/review；raw full:passages、full:ambiguous_passages、review-only、risk-only 不能进入 primary。 |
| refuse | refuse answer 通常不要求 citation；若有 citation，只能作为范围说明或检索线索，不应写成实质回答依据。本轮只记录政策，不修回答。 |

## 9 条 policy decision 逐条表格
| id | category | question | answer_mode | citation_source_slots | conservative | source_traceable | primary_forbidden_full | policy_status | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eval_006 | 原文定位 | 太阳之为病的原文是什么？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, review | True | True | False | policy_accepted | none |
| eval_010 | 术语解释 | 两阳是什么意思？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, secondary, secondary | True | True | False | policy_accepted | none |
| eval_016 | 方剂关联 | 太阳中风鼻鸣乾呕用什么方？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, review, review | True | True | False | policy_accepted | none |
| eval_017 | 方剂关联 | 太阳病项背强几几无汗恶风用什么方？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, review, review | True | True | False | policy_accepted | none |
| eval_018 | 方剂关联 | 伤寒脉浮紧无汗身疼痛用什么方？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, review, review | True | True | False | policy_accepted | none |
| eval_022 | 症候检索 | 头项强痛而恶寒对应哪段原文？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, review, review, review | True | True | False | policy_accepted | none |
| eval_024 | 症候检索 | 发热无汗反恶寒名为什么？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, review | True | True | False | policy_accepted | none |
| eval_026 | 注文理解 | 成无己如何解释荣气微？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, review, review | True | True | False | policy_accepted | none |
| eval_030 | 注文理解 | 注文如何解释奔豚从何而发？ | weak_with_review_notice | secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary, secondary | True | True | False | policy_accepted | none |

## 队列边界
本轮 cases 的唯一入口是 `secondary_review_policy_decisions`。`runtime_citation_scope_repairs`、`trace_or_evaluator_repairs`、`p2_manual_audit` 不进入本轮 cases。若某个 id 同时带有 retrieval/chunking 失败类型，本轮也只裁定它的 secondary/review citation policy 状态，不修 retrieval/chunking。

## policy_accepted
Accepted ids: eval_006, eval_010, eval_016, eval_017, eval_018, eval_022, eval_024, eval_026, eval_030.

这些 case 都是 `weak_with_review_notice`，最终回答包含保守语气，citation source slots 明确落在 secondary/review，trace 中 primary_evidence_ids 未放入 raw full passage 或 ambiguous passage。

## policy_needs_trace_improvement
Trace-improvement ids: none.

若后续出现弱答语气合格但 source slot 或 trace/evidence slot 不清楚的样本，应归到这里，下一步只改 trace 可见性，不直接修 answer assembly。

## policy_violation
Violation ids: none.

若 strong answer 引用 secondary/review、weak answer 没有保守语气却引用 secondary/review，或 forbidden full/review-risk 材料进入 primary，才进入 violation。

## manual_audit_required
Manual-audit ids: none.

无法从 answer_eval、citation audit、trace slots 自动判断时才进入 manual_audit_required。P2 manual audit 不进入本轮 cases。

## 为什么本轮不修 runtime
本轮产物只是 policy 分类：`runtime_changed=false`，`prompt_changed=false`，`api_changed=false`，`frontend_changed=false`，`dataset_changed=false`。这不是系统全通过；这不是修 P2；这不是 prompt 修改。

## 下一步建议
| bucket | count | next_action |
| --- | --- | --- |
| policy_accepted | 9 | none |
| policy_needs_trace_improvement | 0 | improve_trace_evidence_slot_visibility |
| policy_violation | 0 | repair in a later runtime task |
| manual_audit_required | 0 | manual_audit_required |
