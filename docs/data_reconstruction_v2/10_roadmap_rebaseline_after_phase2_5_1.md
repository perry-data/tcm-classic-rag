# Roadmap Rebaseline After Phase 2.5.1

## Purpose
This checkpoint pauses the proposed Phase 2.6 apply step and realigns the macro roadmap with the fine-grained work that has already happened.

## Original Macro Roadmap
- Phase 1.3 pilot object QA
- Phase 1.4 docs/spec landing
- Phase 2.0 full_build_dry_run
- Phase 2.1 review queue 分批处理
- Phase 2.2 full v2 sidecar DB
- Phase 3.0 shadow retrieval comparison
- Phase 4.0 runtime adapter / feature flag 接入

## Rebaseline Decision
- Actual Phase 2.3 / 2.4 / 2.5 / proposed 2.6 are all sub-work under original Macro Phase 2.1 review queue 分批处理.
- The artifact named `full_build_review_resolved_pass1` was an auto-safe review-queue snapshot. It is not Macro Phase 2.2 shadow-ready sidecar freeze.
- Macro Phase 2.2 full v2 sidecar DB freeze has not started.
- Phase 3.0 shadow retrieval comparison has not started.
- Phase 4.0 runtime adapter / feature flag has not started.
- Phase 2.6 remains paused until this rebaseline and Phase 1.4 spec landing checkpoint is reviewed and the user explicitly approves resumption.
- All data snapshots remain isolated. The runtime gate remains closed.

## Evidence
- Phase 2.0 manifest: `spec_files_used=[]` and `spec_note=spec files missing; pilot_build and prompt rules used as working spec`.
- Phase 2.5.1 manifest: `anchors_applied=False`, `apply_ready_count=7`, `deferred_count=2`.
- Phase 2.6 output directory exists: `False`.

## Mapping Matrix
| Macro phase | Actual phase name | Actual substep | Status | Rebased under | Notes |
|---|---|---|---|---|---|
| Macro Phase 1.3 | Phase 1.3 | pilot object QA | completed | Macro Phase 1.3 | pilot sidecar QA only |
| Macro Phase 1.4 | Phase 1.4 | docs/spec landing | partial_backfilled_now | Macro Phase 1.4 | Phase 2.0/2.1 manifests showed spec_files_used=[] |
| Macro Phase 2.0 | Phase 2.0 | full build dry-run | completed | Macro Phase 2.0 | dry-run sidecar only |
| Macro Phase 2.1 | Phase 2.1 | full review resolution matrix | completed | Macro Phase 2.1 | matrix and patch plan |
| Macro Phase 2.1 | executed as Phase 2.2 review_resolved_pass1 | auto-safe patch snapshot | completed | Macro Phase 2.1 | name looked like macro 2.2 but is review-queue substep, not sidecar freeze |
| Macro Phase 2.1 | Phase 2.3 | annotation workbench | completed | Macro Phase 2.1 | human review package |
| Macro Phase 2.1 | Phase 2.3.1 | calibration repair | completed | Macro Phase 2.1 | no anchor application |
| Macro Phase 2.1 | Phase 2.3.2 | repaired annotation workbench | completed | Macro Phase 2.1 | batch_007 parser reclassification introduced |
| Macro Phase 2.1 | Phase 2.3.3 | repaired calibration audit | completed | Macro Phase 2.1 | eligible minimal schema test rows |
| Macro Phase 2.1 | Phase 2.4 | minimal formula_text anchor schema test | completed | Macro Phase 2.1 | 10 audited anchors in isolated snapshot |
| Macro Phase 2.1 | Phase 2.5 | batch1 human review package | completed | Macro Phase 2.1 | 9 selected formula_text candidates |
| Macro Phase 2.1 | Phase 2.5.1 | batch1 decision audit | completed | Macro Phase 2.1 | 7 apply-ready, 2 deferred |
| Macro Phase 2.1 | proposed Phase 2.6 | batch1 apply 7 anchors | paused_not_executed | Macro Phase 2.1 | requires explicit user approval after this checkpoint |
| Macro Phase 2.2 | not started | shadow-ready full v2 sidecar DB freeze | not_started | Macro Phase 2.2 | existing sidecars are validation/review snapshots |
| Macro Phase 3.0 | not started | v1/v2 evidence comparison and isolated v2 index build | not_started | Macro Phase 3 | no shadow retrieval was run |
| Macro Phase 4.0 | not started | feature-flag adapter and staged runtime smoke | not_started | Macro Phase 4 | runtime connection is forbidden |

## Runtime Boundary
- may_enter_macro_phase2_2_sidecar_freeze: false
- may_enter_shadow_retrieval: false
- may_connect_runtime: false
- may_modify_zjshl_v1_db: false
- may_modify_existing_faiss: false
- may_modify_runtime_prompt_frontend_eval: false
