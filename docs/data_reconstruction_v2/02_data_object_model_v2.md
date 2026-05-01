# Data Object Model v2

The observed object model separates raw_items, chapters, sections, main_texts, annotations, formulas, formula_texts, formula_usage_contexts, definition candidates, editorial notes, and review-only materials.
Formula identity, formula wording, and formula usage context are separate object types.
Annotations are auxiliary unless an audited anchor permits a specific relation to main_text or formula_text.

## source_artifacts_used
- source_artifacts_used: artifacts/data_reconstruction_handoff_v1/DATA_ASSET_INVENTORY.md, artifacts/data_reconstruction_handoff_v1/current_runtime_defaults.txt, artifacts/data_reconstruction_v2/pilot_build/manifest.json, artifacts/data_reconstruction_v2/pilot_build/VALIDATION_REPORT.md, artifacts/data_reconstruction_v2/full_build_dry_run/manifest.json, artifacts/data_reconstruction_v2/full_build_dry_run/FULL_BUILD_DRY_RUN_SUMMARY.md, artifacts/data_reconstruction_v2/full_build_dry_run/VALIDATION_REPORT.md, artifacts/data_reconstruction_v2/full_review_resolution_phase2_1/PHASE2_1_REVIEW_RESOLUTION_SUMMARY.md, artifacts/data_reconstruction_v2/full_build_review_resolved_pass1/manifest.json, artifacts/data_reconstruction_v2/full_build_annotation_formula_text_anchor_minimal_pass1/manifest.json, artifacts/data_reconstruction_v2/human_annotation_anchor_batch1_decision_audit_phase2_5_1/manifest.json


## confirmed_facts
- raw_source_path=data/raw/《注解伤寒论》.zip
- raw_items=1864
- main_texts=735
- annotations=897
- formulas=112
- formula_texts=113
- formula_usage_contexts=292
- full_dry_run_review_queue=1154
- full_dry_run_blocking=493
- phase2_1_still_blocking=491
- phase2_2_output_blocking=491
- phase2_4_output_blocking=481
- phase2_5_1_apply_ready=7
- phase2_5_1_deferred=2


## reasonable_inferences
- Phase 1.4 was not complete before Phase 2.0 because Phase 2.0 manifest recorded spec_files_used=[] and spec_note='spec files missing; pilot_build and prompt rules used as working spec'.
- Existing sidecar DB files are validation/review snapshots, not a shadow-ready full v2 sidecar DB freeze.
- Phase 2.3, 2.4, 2.5, and proposed 2.6 are sub-work under Macro Phase 2.1 review queue resolution.


## needs_human_confirmation
- Human confirmation remains needed for residual annotation_anchor_uncertain rows, uncertain_usage_context rows, source-span repairs, and parser reclassification planning.
- The direct backfill does not replace a later human-authored task-card narrative for docs 06/08/09.


## runtime_boundary
- runtime_boundary: This backfill is documentation/spec only. It does not modify artifacts/zjshl_v1.db, FAISS, dense meta, config, backend, frontend, runtime, eval, or any existing Phase 2.x snapshot.
