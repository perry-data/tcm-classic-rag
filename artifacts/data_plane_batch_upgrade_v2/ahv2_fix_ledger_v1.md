# AHV2 Fix Ledger v1

- run_id: `ahv2_adversarial_fixes_v1`
- changed_learner_surface_count: `0`
- deactivated_alias_count: `0`
- downgraded_object_count: `0`

## Runtime Safety

- `backend/retrieval/minimal.py` treats AHV v1 and AHV2 promotion layers as exact-match layers.
- AHV definition objects are skipped from raw text-match collection unless exact term normalization already selected that concept.
- `backend/answers/assembler.py` keeps definition-outline payload metadata intact and prefers the exact definition object when one was selected by term normalization.

## Learner Surface Fixes

- none

## Alias Fixes

- none
