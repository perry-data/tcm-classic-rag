# Full Chain P0 Boundary Repairs v1

## Scope

本轮只处理 full-chain 暴露的 4 个 P0：清邪中上、反、两阳、白虎。未新增 AHV3，未改 prompt、前端、API payload 顶层 contract 或 answer_mode 定义，也未重新放开 raw full passages 进入 primary。

## Root Cause

- 清邪中上 / 反 / 两阳：对象层未升格为 safe primary，但解释型 runtime 仍允许 main_passages 在无安全定义对象时形成 strong。
- 白虎：单问“白虎是什么意思”没有明确方名后缀，却被含“白虎汤 / 白虎加人参汤”的方剂片段吸附成 strong。
- failure metrics：JSON 内部一致，失败记录、failure_count、failure_type_counts 都是 37；旧报告缺少显式合计字段，容易被误读。

## Repair

- 新增 exact meaning guard：review-only/not-ready topic 只走 weak_with_review_notice，原 primary 候选降为 secondary/review。
- 新增 exact negative guard：白虎 / 白虎星 / 反证 / 反复不触发方剂或正文 primary。
- full-chain 报告指标补充 failure_record_count、failure_type_count_total、missing_failure_type_count、failure_metrics_consistent。

## Results

- before_p0_failure_count: `10`
- after_p0_failure_count: `0`
- regression_fail_count: `0`
- p0_failure_count: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`
- failure_metrics_consistent: `True`

## Artifact Index

- `artifacts/full_chain_p0_repairs/p0_boundary_before_after_v1.json`
- `artifacts/full_chain_p0_repairs/p0_boundary_regression_v1.json`
- `artifacts/full_chain_p0_repairs/failure_metrics_consistency_check_v1.json`
