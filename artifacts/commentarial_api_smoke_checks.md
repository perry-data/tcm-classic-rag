# Commentarial API Smoke Checks

## 运行方式

`python -m backend.api.minimal_api`

## Endpoint

- base_url: `http://127.0.0.1:51302`
- method: `POST`
- path: `/api/v1/answers`

## Validation

- all_status_200: `True`
- payload_fields_stable: `True`
- query_echo_kept: `True`
- named_route_kept: `True`
- comparison_dual_sections: `True`
- meta_contains_learning_sections: `True`
- assistive_canonical_primary_present: `True`
- assistive_commentarial_collapsed: `True`
- commentarial_out_of_primary: `True`
- commentarial_out_of_confidence_gate: `True`

## named_view: 刘渡舟怎么看第141条？

- request_body: `{"query": "刘渡舟怎么看第141条？"}`
- response_status: `200`
- response_keys: `["query", "answer_mode", "answer_text", "primary_evidence", "secondary_evidence", "review_materials", "disclaimer", "review_notice", "refuse_reason", "suggested_followup_questions", "citations", "commentarial", "display_sections"]`
- response_body.query: `刘渡舟怎么看第141条？`
- answer_mode: `weak_with_review_notice`
- commentarial.route: `named_view`
- commentarial.sections: `[{"section_id": "commentarial_named_view_刘渡舟_main", "commentator": "刘渡舟", "collapsed_by_default": false, "item_count": 1}]`
- primary_evidence: `[]`
- display_sections: `[{"section_id": "answer", "field": "answer_text", "visible": true}, {"section_id": "review_notice", "field": "review_notice", "visible": true}, {"section_id": "primary_evidence", "field": "primary_evidence", "visible": false}, {"section_id": "secondary_evidence", "field": "secondary_evidence", "visible": true}, {"section_id": "review_materials", "field": "review_materials", "visible": true}, {"section_id": "citations", "field": "citations", "visible": true}, {"section_id": "refusal_guidance", "field": "suggested_followup_questions", "visible": false}, {"section_id": "commentarial", "field": "commentarial", "visible": true}]`
- review_notice: 正文强证据不足，以下内容需核对，不应视为确定答案。
- commentarial_lead_note: 以下为点名名家视角；原典主依据与 canonical citation 仍保持独立。

## comparison_view: 两家如何解释少阳病？

- request_body: `{"query": "两家如何解释少阳病？"}`
- response_status: `200`
- response_keys: `["query", "answer_mode", "answer_text", "primary_evidence", "secondary_evidence", "review_materials", "disclaimer", "review_notice", "refuse_reason", "suggested_followup_questions", "citations", "commentarial", "display_sections"]`
- response_body.query: `两家如何解释少阳病？`
- answer_mode: `strong`
- commentarial.route: `comparison_view`
- commentarial.sections: `[{"section_id": "commentarial_comparison_view_刘渡舟_main", "commentator": "刘渡舟", "collapsed_by_default": false, "item_count": 3}, {"section_id": "commentarial_comparison_view_郝万山_main", "commentator": "郝万山", "collapsed_by_default": false, "item_count": 3}]`
- primary_evidence: `[{"record_id": "safe:main_passages:ZJSHL-CH-006-P-0076", "record_type": "main_passages", "title": "其不两感于寒更不传经不加异气者至七日太阳病衰头痛少愈也八日阳明病衰身热少歇也九日少阳病衰耳聋微闻也十日太阴病衰腹减如故则思饮食十一日少阴病衰渴止舌乾已而嚏也十二日厥阴病衰囊纵少腹微下大气皆去病患精神爽慧也"}]`
- display_sections: `[{"section_id": "answer", "field": "answer_text", "visible": true}, {"section_id": "review_notice", "field": "review_notice", "visible": true}, {"section_id": "primary_evidence", "field": "primary_evidence", "visible": true}, {"section_id": "secondary_evidence", "field": "secondary_evidence", "visible": true}, {"section_id": "review_materials", "field": "review_materials", "visible": true}, {"section_id": "citations", "field": "citations", "visible": true}, {"section_id": "refusal_guidance", "field": "suggested_followup_questions", "visible": false}, {"section_id": "commentarial", "field": "commentarial", "visible": true}]`
- review_notice: 以下补充依据与核对材料仅作说明，不作为主依据。
- commentarial_lead_note: 以下为名家比较视角；原典 citation 与主证据层仍保持 canonical 优先。

## meta_learning_view: 怎么学《伤寒论》？

- request_body: `{"query": "怎么学《伤寒论》？"}`
- response_status: `200`
- response_keys: `["query", "answer_mode", "answer_text", "primary_evidence", "secondary_evidence", "review_materials", "disclaimer", "review_notice", "refuse_reason", "suggested_followup_questions", "citations", "commentarial", "display_sections"]`
- response_body.query: `怎么学《伤寒论》？`
- answer_mode: `weak_with_review_notice`
- commentarial.route: `meta_learning_view`
- commentarial.sections: `[{"section_id": "commentarial_meta_learning_view_刘渡舟_folded", "commentator": "刘渡舟", "collapsed_by_default": true, "item_count": 2}, {"section_id": "commentarial_meta_learning_view_郝万山_main", "commentator": "郝万山", "collapsed_by_default": false, "item_count": 1}, {"section_id": "commentarial_meta_learning_view_郝万山_folded", "commentator": "郝万山", "collapsed_by_default": true, "item_count": 2}]`
- primary_evidence: `[]`
- display_sections: `[{"section_id": "answer", "field": "answer_text", "visible": true}, {"section_id": "review_notice", "field": "review_notice", "visible": true}, {"section_id": "primary_evidence", "field": "primary_evidence", "visible": false}, {"section_id": "secondary_evidence", "field": "secondary_evidence", "visible": true}, {"section_id": "review_materials", "field": "review_materials", "visible": true}, {"section_id": "citations", "field": "citations", "visible": true}, {"section_id": "refusal_guidance", "field": "suggested_followup_questions", "visible": false}, {"section_id": "commentarial", "field": "commentarial", "visible": true}]`
- review_notice: 正文强证据不足，以下内容需核对，不应视为确定答案。
- commentarial_lead_note: 以下为名家学习方法与教学视角，仍与 canonical 主证据层分离展示。

## assistive_view: 桂枝汤是什么？

- request_body: `{"query": "桂枝汤是什么？"}`
- response_status: `200`
- response_keys: `["query", "answer_mode", "answer_text", "primary_evidence", "secondary_evidence", "review_materials", "disclaimer", "review_notice", "refuse_reason", "suggested_followup_questions", "citations", "commentarial", "display_sections"]`
- response_body.query: `桂枝汤是什么？`
- answer_mode: `strong`
- commentarial.route: `assistive_view`
- commentarial.sections: `[{"section_id": "commentarial_assistive", "commentator": null, "collapsed_by_default": true, "item_count": 2}]`
- primary_evidence: `[{"record_id": "safe:main_passages:ZJSHL-CH-008-P-0217", "record_type": "main_passages", "title": "桂枝汤方"}, {"record_id": "safe:main_passages:ZJSHL-CH-008-P-0219", "record_type": "main_passages", "title": "桂枝汤方"}]`
- display_sections: `[{"section_id": "answer", "field": "answer_text", "visible": true}, {"section_id": "review_notice", "field": "review_notice", "visible": true}, {"section_id": "primary_evidence", "field": "primary_evidence", "visible": true}, {"section_id": "secondary_evidence", "field": "secondary_evidence", "visible": true}, {"section_id": "review_materials", "field": "review_materials", "visible": true}, {"section_id": "citations", "field": "citations", "visible": true}, {"section_id": "refusal_guidance", "field": "suggested_followup_questions", "visible": false}, {"section_id": "commentarial", "field": "commentarial", "visible": true}]`
- review_notice: 以下补充依据与核对材料仅作说明，不作为主依据。
- commentarial_lead_note: 以下名家内容仅作补充解读，默认不进入 primary_evidence，也不参与 confidence gate。
