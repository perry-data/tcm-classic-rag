# Professional Source Findings v2

## Purpose
This document backfills the remaining Phase 1.4 professional-source gap for the ZJSHL v2 reconstruction spec.
It records what the project artifacts already prove, what policy has been frozen from those artifacts, and what still needs external professional confirmation.

## Source Boundary
- confirmed_from_project_artifacts: yes
- professional_source_needed: yes, for the variant/alias judgments listed below
- external_source_not_verified_by_coding_agent: true
- do_not_use_as_final_authoritative_source: true
- no external professional source was queried or verified in this Phase 1.4.1 pass
- may_enter_shadow_retrieval=false
- may_connect_runtime=false
- Phase 2.6 paused unless user explicitly approves

## Confirmed From Project Artifacts
- Phase 2.0 dry-run summary preserves raw/display variants such as `浓朴`, `杏子`, `杏人`, and `乾`, with canonical/search forms kept separate.
- Phase 2.0 validation passed alias preservation checks for `浓朴` and `杏人`.
- Pilot QA confirms formula-text comparison for 桂枝加浓朴/厚朴杏子汤 preserves display `浓朴` / `杏人` while canonical retrieval/comparison can use `厚朴` / `杏仁`.
- Phase 2.1 records frozen mappings for `浓朴/厚朴` and `杏子/杏仁/杏人`, while other textual variants are not newly canonicalized.
- Phase 2.1 records `啬啬恶寒` and `干呕` as supported term definitions, while bare `白虎` and common `反` remain review-only.
- Pilot QA confirms `啬啬恶寒` and `干呕` are local annotation-supported definition candidates in `retrieval_ready_terms`.
- Phase 2.5.1 surfaces `桃人/桃仁` in the 桃核承气汤-related Batch-1 review context, but does not provide an external authority for final canonical policy.

## Findings Matrix
| finding | confirmed_project_fact | professional_source_finding | policy_decision | current_status | needs_human_confirmation |
|---|---|---|---|---|---|
| 浓朴 / 厚朴 | display variant preserved; canonical herb can map to 厚朴 | needs_external_source_check | preserve raw display; use canonical/search form separately | needs_external_source_check | true |
| 杏子 / 杏仁 / 杏人 | display variants preserved; canonical ingredient can map to 杏仁 | needs_external_source_check | formula name/display may retain 杏子; ingredient canonical may use 杏仁; 杏人 remains textual/OCR candidate | needs_external_source_check | true |
| 桃人 / 桃仁 | surfaced in Phase 2.5.1 Batch-1 context | needs_external_source_check | do not finalize broad canonical policy in this pass | needs_external_source_check | true |
| 乾 / 干 | `乾` is preserved as raw/display variant in dry-run policy | needs_external_source_check | preserve raw display; do not globally rewrite to 干 | needs_external_source_check | true |
| 啬啬恶寒 | local annotation-supported definition candidate exists | project_artifact_only | allow local definition candidate with annotation support | project_only | true |
| 干呕 | local annotation-supported definition candidate exists | project_artifact_only | allow local definition candidate with annotation support | project_only | true |
| 反 | project policy keeps common `反` review-only | project_artifact_only | do not promote as global term definition | project_only | true |
| 白虎 bare term | project policy keeps bare `白虎` review-only | project_artifact_only | do not infer a term definition from 白虎汤 | project_only | true |

## Variant / Alias Findings

### 浓朴 / 厚朴

- confirmed_project_fact: Phase 2.0 and Pilot QA preserve raw display `浓朴`; Pilot QA states canonical retrieval/comparison can map the herb to `厚朴`.
- professional_source_finding: needs_external_source_check; no external authoritative source is verified in this repository pass.
- policy_decision: preserve raw display text in formula_text records; use canonical/search forms separately for retrieval and comparison; do not rewrite the source wording.
- current_status: needs_external_source_check
- affects_files: `artifacts/data_reconstruction_v2/spec/alias_policy_v2.json`; `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- risk_if_wrong: an over-broad rewrite could erase source display form or create a false herb equivalence.
- needs_human_confirmation: true

### 杏子 / 杏仁 / 杏人

- confirmed_project_fact: Phase 2.0 and Pilot QA preserve `杏子` and `杏人` display forms; Pilot QA records canonical retrieval/comparison against `杏仁`.
- professional_source_finding: needs_external_source_check; no external authoritative source is verified in this repository pass.
- policy_decision: formula display/name may retain `杏子`; ingredient canonical/search may map to `杏仁`; `杏人` remains a textual/OCR variant candidate unless human review freezes a broader rule.
- current_status: needs_external_source_check
- affects_files: `artifacts/data_reconstruction_v2/spec/alias_policy_v2.json`; `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- risk_if_wrong: treating all occurrences as one form could lose formula-title fidelity or incorrectly normalize OCR/textual variants.
- needs_human_confirmation: true

### 桃人 / 桃仁

- confirmed_project_fact: Phase 2.5.1 surfaces a Batch-1 review context where `桃人/桃仁` requires source-span and professional-policy care.
- professional_source_finding: needs_external_source_check; no external authoritative source is verified in this repository pass.
- policy_decision: keep any raw display variant as attested text; do not finalize an external canonical policy until a human reviewer supplies source-backed confirmation.
- current_status: needs_external_source_check
- affects_files: `docs/data_reconstruction_v2/08_professional_source_findings_v2.md`; future alias-policy review only
- risk_if_wrong: a false canonical mapping could affect 桃核承气汤 formula_text or annotation anchors.
- needs_human_confirmation: true

### 乾 / 干

- confirmed_project_fact: Phase 2.0 dry-run summary lists `乾` among raw/display variants to preserve.
- professional_source_finding: needs_external_source_check; no external authoritative source is verified in this repository pass.
- policy_decision: preserve `乾` in display/source text; do not globally rewrite to `干`; retrieval may use a separate normalized/search form only after explicit policy.
- current_status: needs_external_source_check
- affects_files: `artifacts/data_reconstruction_v2/spec/alias_policy_v2.json`; `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- risk_if_wrong: global simplification could damage formula names, ingredient names, or source quotation fidelity.
- needs_human_confirmation: true

## Term Definition Findings

### 啬啬恶寒

- confirmed_project_fact: Pilot QA uses `ZJSHL-V02-RR-DEF-SESE-EHAN-0001` and an anchored annotation as local support; Phase 2.1 records `啬啬恶寒` as supported.
- professional_source_finding: project_artifact_only; external_source_not_verified_by_coding_agent.
- policy_decision: allow as a local annotation-supported definition candidate in `retrieval_ready_terms`; do not claim a general dictionary or medical-authority definition.
- current_status: project_only
- affects_files: `artifacts/data_reconstruction_v2/spec/term_definition_policy_v2.json`; `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- risk_if_wrong: an answer could overstate a local annotation gloss as a universal definition.
- needs_human_confirmation: true

### 干呕

- confirmed_project_fact: Pilot QA uses `ZJSHL-V02-RR-DEF-GANOU-0004` and an anchored annotation as local support; Phase 2.1 records `干呕` as supported.
- professional_source_finding: project_artifact_only; external_source_not_verified_by_coding_agent.
- policy_decision: allow as a local annotation-supported definition candidate in `retrieval_ready_terms`; keep the scope as book-local annotation support.
- current_status: project_only
- affects_files: `artifacts/data_reconstruction_v2/spec/term_definition_policy_v2.json`; `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- risk_if_wrong: an answer could conflate occurrence-only evidence with a definition; current policy requires the definition candidate and annotation support.
- needs_human_confirmation: true

### 反

- confirmed_project_fact: Phase 2.0 and Phase 2.1 keep common `反` review-only unless a safe local definition exists; prohibition/misuse uses such as `反与...此误也` are excluded from positive formula usage.
- professional_source_finding: project_artifact_only; external_source_not_verified_by_coding_agent.
- policy_decision: do not promote `反` as a global term definition; keep contextual/misuse evidence outside positive usage lanes.
- current_status: project_only
- affects_files: `artifacts/data_reconstruction_v2/spec/evidence_promotion_rules_v2.json`; `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- risk_if_wrong: misuse/prohibition evidence could be interpreted as positive usage or a general term definition.
- needs_human_confirmation: true

### 白虎 bare term

- confirmed_project_fact: Phase 2.0 and Phase 2.1 keep bare `白虎` review-only; Pilot QA uses 白虎汤 formula_usage records for 白虎汤 questions and excludes `不可与白虎汤` as negative evidence.
- professional_source_finding: project_artifact_only; external_source_not_verified_by_coding_agent.
- policy_decision: do not infer a bare-term definition from 白虎汤; keep bare `白虎` review-only until a safe local term object exists.
- current_status: project_only
- affects_files: `artifacts/data_reconstruction_v2/spec/term_definition_policy_v2.json`; `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- risk_if_wrong: formula-name evidence could be misused as a term-definition record.
- needs_human_confirmation: true

## Decisions That Need External Professional Confirmation
- `浓朴 / 厚朴`: confirm the exact professional/canonical herb relationship before broad policy use.
- `杏子 / 杏仁 / 杏人`: confirm formula-name display, ingredient canonicalization, and OCR/textual-variant handling.
- `桃人 / 桃仁`: confirm before any broad alias-policy rule or Batch-1 anchor application that depends on the variant.
- `乾 / 干`: confirm before any global simplification or canonical normalization.
- The project-only term decisions for `啬啬恶寒`, `干呕`, `反`, and bare `白虎` should still be reviewed by a human before they are treated as final professional statements.

## How These Findings Affect Alias Policy
- Alias/display policy is conservative: preserve attested source display in `display_text` and keep canonical/search fields separate.
- Locally frozen project mappings cover `浓朴/厚朴` and `杏子/杏仁/杏人` for retrieval/comparison behavior, but this pass does not claim external professional authority.
- Non-frozen variants, including `桃人/桃仁`, remain review-gated.

## How These Findings Affect Retrieval-ready Views
- `retrieval_ready_formula_texts` must preserve raw display variants and separate display from canonical/search forms.
- `retrieval_ready_terms` may include local annotation-supported definition candidates for `啬啬恶寒` and `干呕`.
- Bare `白虎` and common `反` must not enter primary term-definition lanes without an audited safe object.
- Formula-name evidence must not be used as a bare-term definition.

## Runtime Boundary
- may_enter_shadow_retrieval=false
- may_connect_runtime=false
- may_modify_zjshl_v1_db=false
- may_modify_existing_faiss=false
- may_modify_config=false
- may_modify_backend_frontend_runtime_eval=false
- Phase 2.6 paused unless user explicitly approves

## Source Artifacts Used
- `artifacts/data_reconstruction_v2/pilot_build/PILOT_OBJECT_QA_REPORT.md`
- `artifacts/data_reconstruction_v2/full_build_dry_run/FULL_BUILD_DRY_RUN_SUMMARY.md`
- `artifacts/data_reconstruction_v2/full_build_dry_run/VALIDATION_REPORT.md`
- `artifacts/data_reconstruction_v2/full_review_resolution_phase2_1/PHASE2_1_REVIEW_RESOLUTION_SUMMARY.md`
- `artifacts/data_reconstruction_v2/human_annotation_anchor_batch1_decision_audit_phase2_5_1/PHASE2_5_1_BATCH1_DECISION_AUDIT_SUMMARY.md`
- `artifacts/data_reconstruction_v2/spec/alias_policy_v2.json`
- `artifacts/data_reconstruction_v2/spec/evidence_promotion_rules_v2.json`
- `artifacts/data_reconstruction_v2/spec/term_definition_policy_v2.json`

## Needs Human Confirmation
- external professional source confirmation remains open for `浓朴/厚朴`, `杏子/杏仁/杏人`, `桃人/桃仁`, and `乾/干`.
- project-only local term decisions should be reviewed before being quoted as professional authority.
- This document is a Phase 1.4.1 project-artifact backfill, not a final professional-source bibliography.
