# Paused Phase 2.6 Decision Note

## Decision
Phase 2.6 prompt/plan may exist, but execution is paused by this checkpoint.

## Evidence From Phase 2.5.1
- apply_ready_count: `7`
- deferred_count: `2`
- anchors_applied: `False`
- phase2_6_output_snapshot_path: `artifacts/data_reconstruction_v2/full_build_annotation_batch1_formula_text_anchor_pass2/`

## Apply-ready Rows
- ZJSHL-V02-FULL-REVIEW-00434
- ZJSHL-V02-FULL-REVIEW-00408
- ZJSHL-V02-FULL-REVIEW-00418
- ZJSHL-V02-FULL-REVIEW-00400
- ZJSHL-V02-FULL-REVIEW-00371
- ZJSHL-V02-FULL-REVIEW-00546
- ZJSHL-V02-FULL-REVIEW-00480

## Deferred Rows
- ZJSHL-V02-FULL-REVIEW-00594
- ZJSHL-V02-FULL-REVIEW-00465

## Resume Conditions
- Phase 2.6 can be resumed only after explicit user approval after this roadmap/spec landing checkpoint.
- If resumed, it must apply only the 7 audited rows listed in the Phase 2.5.1 minimal apply plan.
- It must exclude 00594 and 00465 until source spans are repaired.
- It still does not allow Macro Phase 2.2, shadow retrieval, runtime connection, v1 DB modification, FAISS rebuild, config change, backend/frontend change, or eval expansion.
