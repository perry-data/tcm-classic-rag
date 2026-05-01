# Macro Roadmap v2 After Rebaseline

## Pilot + Spec
- id: `macro_phase_1`
- status: `partial_complete`
- 1.1 pilot build: `completed`
- 1.2 pilot fix/review/spec freeze: `completed_by_phase_artifacts`
- 1.3 pilot object QA: `completed`
- 1.4 docs/spec landing: `partial_backfilled_now`

## Full dry-run + review queue resolution
- id: `macro_phase_2`
- status: `in_progress`
- 2.0 full build dry-run: `completed`
- 2.1 review queue resolution and batched human review: `in_progress`
  - 2.1-a review resolution matrix: `completed`
  - 2.1-b auto-safe patch snapshot: `completed`
  - 2.1-c annotation workbench: `completed`
  - 2.1-d repaired annotation workbench: `completed`
  - 2.1-e minimal formula_text anchor schema test: `completed`
  - 2.1-f batch1 review package: `completed`
  - 2.1-g batch1 decision audit: `completed`
  - 2.1-h optional batch1 apply, paused until user approves: `paused_not_executed`
  - 2.1-i source-span repair package for 00594/00465: `not_started`
  - 2.1-j parser reclassification planning for batch_007: `not_started`
- 2.2 shadow-ready full v2 sidecar DB freeze: `not_started`

## Shadow retrieval
- id: `macro_phase_3`
- status: `not_started`
- 3.0 v1/v2 evidence comparison: `not_started`
- 3.1 isolated v2 index build: `not_started`

## Runtime adapter
- id: `macro_phase_4`
- status: `not_started`
- 4.0 feature-flag adapter: `not_started`
- 4.1 staged runtime smoke: `not_started`
- 4.2 controlled rollout: `not_started`

## Gate
- Macro Phase 2.1 remains in progress.
- Macro Phase 2.2 shadow-ready full v2 sidecar DB freeze is not started.
- Phase 3 shadow retrieval is not started.
- Phase 4 runtime adapter is not started.
- Runtime remains disconnected.
