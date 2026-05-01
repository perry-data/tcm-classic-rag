# Manual Review Resolution and Spec Freeze v2

## Purpose
This document backfills the Phase 1.4 manual-review/spec-freeze narrative from the validated v2 reconstruction artifacts.
It freezes only project-policy decisions already supported by Phase 1.2 through Phase 2.5.1 outputs and keeps the unresolved review families open.

## Scope
- In scope: documentation/spec gap backfill for manual-review resolution, frozen policies, open blockers, and runtime gate posture.
- Out of scope: Phase 2.6 execution, applying Batch-1 anchors, applying annotation anchors, relation patch generation, data snapshot mutation, runtime connection, shadow retrieval, index rebuilds, backend/frontend/config/eval changes.
- may_enter_shadow_retrieval=false
- may_connect_runtime=false
- Phase 2.6 paused unless user explicitly approves

## Review Resolution Timeline
- Phase 1.2 applied pilot review-resolution/spec-freeze decisions inside `pilot_build/` only.
- Phase 1.3 ran object-level QA from retrieval-ready views and passed 10/10 checks.
- Phase 2.0 produced a full-book dry-run sidecar with 1,154 review rows and 493 blocking rows; runtime stayed disconnected.
- Phase 2.1 emitted a review-resolution matrix; 491 rows stayed blocking, with 481 `annotation_anchor_uncertain` rows.
- Phase 2.2 created an isolated review-resolved pass from only the auto-safe subset: 2 review rows and 12 patch items.
- Phase 2.3.2 regenerated the annotation-anchor workbench and separated 102 `batch_007_parser_reclassification_required` rows.
- Phase 2.3.3 audited repaired calibration decisions and identified 10 minimal schema-test candidates.
- Phase 2.4 applied 10 audited formula_text annotation anchors in isolated snapshot.
- Phase 2.5.1 audited 9 Batch-1 candidates: 7 apply-ready, 2 deferred.
- Phase 2.6 remains paused until user explicitly approves after roadmap/spec checkpoint.
- Macro Phase 2.2 shadow-ready sidecar freeze is not started.
- Phase 3 shadow retrieval is not started.
- Phase 4 runtime adapter is not started.

## Frozen Decisions

### Formula text vs formula usage
Formula composition/comparison questions use `retrieval_ready_formula_texts`; usage questions use `retrieval_ready_formula_usage`.
Formula wording must not be substituted for formula usage context, and usage context must not replace formula composition evidence.

### Main text vs annotation
Main text, annotation, formula_text, and formula_usage_context are distinct object lanes.
Annotations remain auxiliary by default and cannot replace main_text primary evidence unless a specific audited relation and retrieval-ready policy allow that use case.

### Appendix carrier vs extracted formula_text
Appendix carriers remain non-primary source carriers.
Extracted formula_text objects may become retrieval-ready formula-text records only when the source span and object split are explicit enough to validate.

### Prohibition / misuse vs positive usage
`不可与` and `反与...此误也` style prohibition/misuse contexts are excluded from positive formula_usage primary evidence.
They may remain as exclusions, review-only materials, or `must_not_use_records`, but not as positive indications.

### Alias display preservation vs canonical retrieval
Raw display variants such as `浓朴`, `杏子`, `杏人`, and `乾` are preserved in display/source fields.
Canonical/search forms are separate and must not erase attested source wording.

### Annotation primary boundary
Uncertain annotation anchors remain review-gated.
Broad annotation auto-promotion is forbidden; Phase 2.1 produced 0 automatic annotation-anchor promotions.

### Formula_text annotation anchors
Human-approved formula_text annotation anchors may create explicit annotation-to-formula_text relations in isolated sidecar snapshots.
Phase 2.4 proved the minimal schema on 10 audited formula_text annotation anchors; it did not authorize full annotation-anchor apply or runtime connection.

## Decisions Still Open

### Annotation-anchor remaining blockers
After Phase 2.4, residual blockers still include 471 `annotation_anchor_uncertain` rows, plus other review families.
Manual review is not finished.

### Source-span repair for 00594 / 00465
Phase 2.5.1 deferred:
- `ZJSHL-V02-FULL-REVIEW-00594`: 竹叶石膏汤 parent formula_text span is incomplete; raw item 66 contains 甘草、粳米、麦门冬 but the parent ingredient lines do not include them.
- `ZJSHL-V02-FULL-REVIEW-00465`: 柴胡桂枝乾姜汤 parent formula_text span is incomplete; raw item 61 contains 黄芩、牡蛎、甘草 but the parent ingredient lines do not include them.

### Parser reclassification batch_007
Phase 2.3.2 identified 102 `batch_007_parser_reclassification_required` rows.
These likely main_text-like or formula_text-like rows must stay out of annotation-anchor apply until parser/reclassification planning is performed.

### Uncertain usage contexts
Nine `uncertain_usage_context` blockers remain open after Phase 2.2 and later checkpoints.
They do not authorize positive primary usage promotion.

### Retrieval-ready view patch v2.1
`retrieval_ready_view_patch_v2_1.json` is backfilled in this Phase 1.4.1 pass to record learned view-contract patches.
It is a spec artifact only, not a runtime connection or data snapshot change.

## Review Queue Status
- Phase 2.0 input review queue count: 1,154
- Phase 2.0 blocking count: 493
- Phase 2.1 still blocking count: 491
- Phase 2.2 output blocking count: 491
- Phase 2.4 output blocking count: 481
- Phase 2.5.1 Batch-1: 7 apply-ready, 2 deferred
- Manual review is still open; this document does not claim completion.

## What Is Allowed Next
- Review this Phase 1.4.1 spec-gap backfill.
- If the user explicitly approves, Phase 2.6 may apply only the 7 audited Batch-1 rows listed in Phase 2.5.1.
- Source-span repair for 00594/00465 may be planned separately before those deferred rows are applied.
- Parser reclassification planning for `batch_007` may be planned separately.

## What Is Still Forbidden
- Execute Phase 2.6 without explicit user approval.
- Apply the 7 Batch-1 anchors during this Phase 1.4.1 pass.
- Apply deferred rows 00594/00465 before source-span repair.
- Apply any broad annotation-anchor batch.
- Generate relation patches as part of this pass.
- Modify pilot/full/review snapshots.
- Modify `artifacts/zjshl_v1.db`, FAISS, dense meta, config, backend, frontend, runtime, or eval runner files.
- Start Macro Phase 2.2, Phase 3 shadow retrieval, or Phase 4 runtime adapter work.

## Source Artifacts Used
- `docs/data_reconstruction_v2/10_roadmap_rebaseline_after_phase2_5_1.md`
- `docs/data_reconstruction_v2/11_spec_landing_checklist_v2.md`
- `docs/data_reconstruction_v2/12_runtime_gate_status_after_phase2_5_1.md`
- `docs/data_reconstruction_v2/13_macro_roadmap_v2_after_rebaseline.md`
- `docs/data_reconstruction_v2/14_paused_phase2_6_decision_note.md`
- `artifacts/data_reconstruction_v2/pilot_build/PILOT_OBJECT_QA_REPORT.md`
- `artifacts/data_reconstruction_v2/full_build_dry_run/FULL_BUILD_DRY_RUN_SUMMARY.md`
- `artifacts/data_reconstruction_v2/full_build_dry_run/VALIDATION_REPORT.md`
- `artifacts/data_reconstruction_v2/full_review_resolution_phase2_1/PHASE2_1_REVIEW_RESOLUTION_SUMMARY.md`
- `artifacts/data_reconstruction_v2/full_build_review_resolved_pass1/PHASE2_2_REVIEW_RESOLVED_PASS1_SUMMARY.md`
- `artifacts/data_reconstruction_v2/human_annotation_anchor_review_phase2_3_2/PHASE2_3_2_REGENERATED_ANNOTATION_WORKBENCH_SUMMARY.md`
- `artifacts/data_reconstruction_v2/human_annotation_anchor_review_phase2_3_3/PHASE2_3_3_REPAIRED_CALIBRATION_DECISION_AUDIT_SUMMARY.md`
- `artifacts/data_reconstruction_v2/full_build_annotation_formula_text_anchor_minimal_pass1/PHASE2_4_MINIMAL_FORMULA_TEXT_ANCHOR_SCHEMA_TEST_SUMMARY.md`
- `artifacts/data_reconstruction_v2/human_annotation_anchor_batch1_decision_audit_phase2_5_1/PHASE2_5_1_BATCH1_DECISION_AUDIT_SUMMARY.md`

## Runtime Gate
- runtime_modified=false
- forbidden_files_touched=[]
- may_execute_phase2_6_batch1_apply=false in this pass
- phase2_6_status=paused
- may_enter_macro_phase2_2=false
- may_enter_shadow_retrieval=false
- may_connect_runtime=false
- may_modify_zjshl_v1_db=false
- may_modify_existing_faiss=false
- may_modify_config=false
- may_modify_backend_frontend_runtime_eval=false
