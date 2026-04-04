# Minimal API Smoke Checks

## 运行命令

`python app_minimal_api.py --smoke`

## Endpoint

- base_url: `http://127.0.0.1:51819`
- method: `POST`
- path: `/api/v1/answers`

## 结论

- `黄连汤方的条文是什么？` -> status=`200`, mode=`strong`, primary=3, secondary=3, review=2, citations=3
- `烧针益阳而损阴是什么意思？` -> status=`200`, mode=`weak_with_review_notice`, primary=0, secondary=3, review=2, citations=5
- `书中有没有提到量子纠缠？` -> status=`200`, mode=`refuse`, primary=0, secondary=0, review=0, citations=0

## Validation

- route_callable: `True`
- request_body_only_query: `True`
- payload_fields_stable: `True`
- strong_mode_kept: `True`
- weak_review_mode_kept: `True`
- refuse_mode_kept: `True`

## Query: 黄连汤方的条文是什么？

- request_body: `{
  "query": "黄连汤方的条文是什么？"
}`
- response_status: `200`
- response_keys: `[
  "query",
  "answer_mode",
  "answer_text",
  "primary_evidence",
  "secondary_evidence",
  "review_materials",
  "disclaimer",
  "review_notice",
  "refuse_reason",
  "suggested_followup_questions",
  "citations",
  "display_sections"
]`
- answer_mode: `strong`
- disclaimer: 主证据优先；补充依据与核对材料不参与主结论判定。
- review_notice: 以下补充依据与核对材料仅作说明，不作为主依据。
- refuse_reason: None
- evidence_summary: primary=3, secondary=3, review=2
- citations_summary: `[
  "safe:main_passages:ZJSHL-CH-010-P-0145",
  "safe:main_passages:ZJSHL-CH-010-P-0146",
  "safe:main_passages:ZJSHL-CH-010-P-0147"
]`

## Query: 烧针益阳而损阴是什么意思？

- request_body: `{
  "query": "烧针益阳而损阴是什么意思？"
}`
- response_status: `200`
- response_keys: `[
  "query",
  "answer_mode",
  "answer_text",
  "primary_evidence",
  "secondary_evidence",
  "review_materials",
  "disclaimer",
  "review_notice",
  "refuse_reason",
  "suggested_followup_questions",
  "citations",
  "display_sections"
]`
- answer_mode: `weak_with_review_notice`
- disclaimer: 当前只输出弱表述与核对材料，不输出确定性答案。
- review_notice: 正文强证据不足，以下内容需核对，不应视为确定答案。
- refuse_reason: None
- evidence_summary: primary=0, secondary=3, review=2
- citations_summary: `[
  "full:annotations:ZJSHL-CH-003-P-0016",
  "safe:main_passages:ZJSHL-CH-009-P-0295",
  "safe:main_passages:ZJSHL-CH-010-P-0080",
  "full:passages:ZJSHL-CH-003-P-0016",
  "full:ambiguous_passages:ZJSHL-CH-003-P-0016"
]`

## Query: 书中有没有提到量子纠缠？

- request_body: `{
  "query": "书中有没有提到量子纠缠？"
}`
- response_status: `200`
- response_keys: `[
  "query",
  "answer_mode",
  "answer_text",
  "primary_evidence",
  "secondary_evidence",
  "review_materials",
  "disclaimer",
  "review_notice",
  "refuse_reason",
  "suggested_followup_questions",
  "citations",
  "display_sections"
]`
- answer_mode: `refuse`
- disclaimer: 当前为统一拒答结构，不输出推测性答案。
- review_notice: None
- refuse_reason: 未检索到足以支撑回答的主证据、辅助证据或可供核对的风险材料。
- evidence_summary: primary=0, secondary=0, review=0
- citations_summary: `[]`
