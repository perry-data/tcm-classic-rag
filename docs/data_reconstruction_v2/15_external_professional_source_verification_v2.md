# External Professional Source Verification v2

## Purpose

This Phase 1.4.2 packet verifies and plans external professional-source confirmation for four `needs_external_source_check` findings carried from Phase 1.4.1:

- 浓朴 / 厚朴
- 杏子 / 杏仁 / 杏人
- 桃人 / 桃仁
- 乾 / 干

The purpose is narrow: external sources may support alias, textual-variant, canonical naming, and search-normalization policy. They are not new 《注解伤寒论》 evidence and must not be used as RAG primary evidence for book-internal answers.

## Scope and Source Boundary

Allowed output scope:

- `docs/data_reconstruction_v2/15_external_professional_source_verification_v2.md`
- `artifacts/data_reconstruction_v2/spec_landing_phase1_4_2/`

Out of scope:

- no Phase 2.6 execution
- no Batch-1 anchor application
- no annotation-anchor application
- no relation patch
- no new snapshot
- no runtime connection
- no shadow retrieval
- no v1 DB / FAISS / dense meta / config mutation
- no backend / frontend / runtime / eval mutation

External professional sources are only policy support. They must not rewrite `display_text`, and they must not be promoted into primary evidence slots. In particular, `display_text` must not be globally rewritten.

## Verification Mode

verification_mode: `mixed`

Internet access was available. Official or authoritative sources were consulted, but the external sources only confirm modern canonical names or orthographic relationships. They do not fully settle source-specific textual questions inside the raw 《注解伤寒论》 witness, so all four findings remain partially confirmed and require human or textual review before broad policy application.

## Sources Consulted

Source bibliography is recorded in:

`artifacts/data_reconstruction_v2/spec_landing_phase1_4_2/professional_source_bibliography.jsonl`

Consulted source groups:

- Hong Kong Chinese Materia Medica Standards, Chinese Medicine Regulatory Office, Department of Health, Hong Kong SAR.
- Chinese Medicine Regulatory Office public-health materia-medica page for 苦杏仁.
- PRC Ministry of Education page for 《通用规范汉字表》.
- Taiwan Ministry of Education Variant Dictionary entry for 乾.

## Summary Matrix

| finding | verification_status | external confirmation | still open | policy result |
|---|---|---|---|---|
| 浓朴 / 厚朴 | partially_confirmed | Modern standard source supports 厚樸 / Houpo / Cortex Magnoliae Officinalis as a materia-medica name. | It does not prove that raw `浓朴` is a historical variant rather than OCR or source-specific form. | Preserve `浓朴`; allow cautious canonical/search mapping to `厚朴`; no display rewrite. |
| 杏子 / 杏仁 / 杏人 | partially_confirmed | Official source supports 苦杏仁 / Armeniacae Semen Amarum as a modern materia-medica name and mature seed source. | It does not prove formula-name `杏子` should be rewritten or that `杏人` is always OCR. | Preserve formula display `杏子` and raw `杏人`; ingredient canonical may map to `苦杏仁` / `杏仁` for search. |
| 桃人 / 桃仁 | partially_confirmed | HKCMMS supports 桃仁 / Persicae Semen as a modern materia-medica name and seed source. | It does not classify raw `桃人` as variant, OCR, or edition-specific form. | Preserve `桃人`; allow source-specific cautious search expansion to `桃仁`; no broad alias without human review. |
| 乾 / 干 | partially_confirmed | Official language sources support `乾` as an orthographic/lexical character and include `干` in the variant relation context. | Source choice is linguistic, not TCM-specific; it does not authorize global simplification of raw display text. | Preserve `乾`; optional normalized/search expansion to `干`; no global display rewrite. |

## Finding 1: 浓朴 / 厚朴

- project_artifact_fact:
  - Phase 2.0 dry-run and Pilot QA preserve raw/display `浓朴`.
  - Pilot QA records that canonical retrieval/comparison can use `厚朴`.
  - Raw zip read-only count in this pass: `浓朴=22`, `厚朴=2`.
- external_source_evidence:
  - `SRC_HKCMMS_HOUPO_VOL2` lists `厚樸 (Cortex Magnoliae Officinalis)` in HKCMMS Volume 2.
  - The English HKCMMS monograph records official name `Cortex Magnoliae Officinalis`, phonetic `Houpo`, and source from Magnolia stem bark.
- verification_status: `partially_confirmed`
- policy_recommendation:
  - Keep raw `display_text` as `浓朴`.
  - Use `厚朴` as canonical herb name only in a separate canonical/search field.
  - Prefer `alias_kind=source_specific_textual_variant_candidate` until an edition or philological source confirms `浓朴` as a stable historical/textual variant.
- confidence: `medium`
- limitations:
  - HKCMMS confirms modern Houpo standard naming but does not mention `浓朴`.
  - It cannot prove OCR error, scribal variant, or edition-specific reading.
- should_update_alias_policy: `recommendation_only`
- should_update_retrieval_ready_contract: `recommendation_only`
- should_block_phase2_6: `false`

## Finding 2: 杏子 / 杏仁 / 杏人

- project_artifact_fact:
  - Phase 2.0 and Pilot QA preserve `杏子` and `杏人` display forms.
  - Pilot QA records canonical retrieval/comparison against `杏仁`.
  - Raw zip read-only count in this pass: `杏子=7`, `杏仁=10`, `杏人=12`.
- external_source_evidence:
  - `SRC_HKCMMS_KUXINGREN_VOL12_LIST` lists `苦杏仁 (Armeniacae Semen Amarum)` in HKCMMS Volume 12.
  - `SRC_CMRO_KUXINGREN_AE17` describes 苦杏仁 as mature seed from listed Prunus species and records aliases `苦杏` and `北杏`.
- verification_status: `partially_confirmed`
- policy_recommendation:
  - Keep formula canonical/display for `桂枝加厚朴杏子汤` with `杏子` where attested.
  - Use `苦杏仁` as the externally preferred materia-medica canonical name for ingredient standardization; retain `杏仁` as a project search/canonical short form only if the alias policy records that distinction.
  - Treat `杏人` as `textual_or_ocr_variant_candidate`, not a canonical herb.
  - Split formula-name canonical/display policy from ingredient canonical policy.
- confidence: `medium`
- limitations:
  - External sources do not adjudicate the book's formula-title form `杏子`.
  - External sources do not decide whether `杏人` is OCR, edition variant, or note-layer text.
- should_update_alias_policy: `recommendation_only`
- should_update_retrieval_ready_contract: `recommendation_only`
- should_block_phase2_6: `false`

## Finding 3: 桃人 / 桃仁

- project_artifact_fact:
  - Phase 2.5.1 surfaces `桃人/桃仁` in a 桃核承气汤-related Batch-1 review context.
  - Raw zip read-only count in this pass: `桃人=6`, `桃仁=0`.
  - Raw contexts include `桃人人赵本作仁` and `桃人赵本作仁`.
  - Phase 2.5.1 apply-ready row `ZJSHL-V02-FULL-REVIEW-00418` states: preserve `桃人/桃仁` textual variant and it does not block that anchor.
- external_source_evidence:
  - `SRC_HKCMMS_TAOREN_VOL5` records `Chinese Name: 桃仁`, official name `Persicae Semen`, phonetic `Taoren`, and seed source.
- verification_status: `partially_confirmed`
- policy_recommendation:
  - Keep raw `display_text` as `桃人` where attested.
  - Permit `桃仁` as canonical ingredient candidate for search only when paired with source-span evidence and the row-specific review note.
  - Use `alias_kind=source_specific_textual_variant` or `textual_variant_candidate`; do not create a broad alias until human textual review confirms scope.
- confidence: `medium`
- limitations:
  - HKCMMS confirms modern `桃仁` but does not classify `桃人`.
  - The raw source itself suggests edition variation, but Phase 1.4.2 does not perform philological adjudication.
- should_update_alias_policy: `recommendation_only`
- should_update_retrieval_ready_contract: `recommendation_only`
- should_block_phase2_6: `false`, provided Phase 2.6 only applies the already audited anchor and preserves display text.

## Finding 4: 乾 / 干

- project_artifact_fact:
  - Phase 2.0 dry-run lists `乾` as a raw/display variant to preserve.
  - Raw zip read-only count in this pass: `乾=153`, `干=16`.
  - `乾` appears in formula names and symptom text such as `乾姜`, `乾呕`, and `乾燥`.
- external_source_evidence:
  - `SRC_MOE_TONGYONG_GUANFAN_2013` is an official PRC Ministry of Education page for 《通用规范汉字表》.
  - `SRC_TW_MOE_VARIANTS_QIAN_2024` records `乾` as a正字 entry, gives `gān` reading and dry/lack-of-moisture meanings, and includes `干` in the variant list.
- verification_status: `partially_confirmed`
- policy_recommendation:
  - Treat `乾/干` as orthographic/search-normalization policy, not an herb alias.
  - Keep raw `display_text` as `乾`.
  - Allow optional normalized/search expansion from `乾` to `干` only in a separate search field.
  - Prohibit global display rewrite.
- confidence: `medium`
- limitations:
  - Taiwan MOE variant data supports the orthographic relation but is not a PRC simplified-character policy source.
  - The PRC general standard page confirms the official standard artifact but was not used to assert a row-level herb or formula policy.
- should_update_alias_policy: `recommendation_only`
- should_update_retrieval_ready_contract: `recommendation_only`
- should_block_phase2_6: `false`

## Policy Implications

- External sources support modern canonical materia-medica names for `厚朴`, `苦杏仁`, and `桃仁`.
- External sources do not authorize changing raw book display forms.
- `浓朴`, `杏人`, and `桃人` remain source-specific textual or OCR candidates until human textual review or an authoritative edition confirms scope.
- `乾/干` belongs to orthographic normalization, not herb alias policy.
- External sources are not RAG primary evidence.

## Alias Policy Patch Recommendation

Write no runtime policy in this phase. Use the generated patch recommendation only:

`artifacts/data_reconstruction_v2/spec_landing_phase1_4_2/alias_policy_external_confirmation_patch.json`

Recommended actions:

- add external-source confirmation notes for modern canonical herb names
- keep `display_rewrite_allowed=false`
- set `search_expand_allowed=true` only for cautious, source-scoped cases
- require human confirmation before broad alias policy
- keep `apply_in_current_phase=false`

## Retrieval-ready View Implications

Retrieval-ready records may later carry separate fields for:

- `display_text`: raw attested form
- `canonical_ingredient_name`: externally supported canonical form where applicable
- `search_expansion_terms`: cautious alias/variant expansion terms
- `alias_kind`: source-specific classification
- `external_source_ids`: bibliography IDs, not primary evidence IDs

No retrieval-ready view is updated in this phase.

## Remaining Uncertainties

Remaining gaps are recorded in:

`artifacts/data_reconstruction_v2/spec_landing_phase1_4_2/source_verification_gaps.csv`

Open items:

- textual authority for `浓朴` as variant of `厚朴`
- formula-title versus ingredient canonical split for `杏子/杏仁/苦杏仁`
- status of `杏人` as OCR, note-layer, or edition-specific form
- source-specific scope for `桃人` before broad alias use
- exact search-normalization scope for `乾/干`

## Runtime Gate

Runtime gate remains closed:

- Phase 2.6 status: paused
- may_resume_phase2_6_after_user_approval: true
- may_enter_macro_phase2_2: false
- may_enter_shadow_retrieval: false
- may_connect_runtime: false

No direct external-source blocker was found for the audited Phase 2.6 Batch-1 apply subset, provided any future Phase 2.6 pass preserves display text and does not apply broad alias rewrites. Explicit user approval is still required before Phase 2.6 resumes.

Macro Phase 2.2 / Phase 3 / Phase 4 remain not allowed in this checkpoint.

## Source Artifacts Used

Project artifacts read:

- `docs/data_reconstruction_v2/08_professional_source_findings_v2.md`
- `docs/data_reconstruction_v2/08_manual_review_resolution_and_spec_freeze_v2.md`
- `docs/data_reconstruction_v2/10_roadmap_rebaseline_after_phase2_5_1.md`
- `docs/data_reconstruction_v2/11_spec_landing_checklist_v2.md`
- `docs/data_reconstruction_v2/12_runtime_gate_status_after_phase2_5_1.md`
- `docs/data_reconstruction_v2/13_macro_roadmap_v2_after_rebaseline.md`
- `docs/data_reconstruction_v2/14_paused_phase2_6_decision_note.md`
- `artifacts/data_reconstruction_v2/spec/retrieval_ready_view_patch_v2_1.json`
- `artifacts/data_reconstruction_v2/spec/alias_policy_v2.json`
- `artifacts/data_reconstruction_v2/spec/evidence_promotion_rules_v2.json`
- `artifacts/data_reconstruction_v2/spec/term_definition_policy_v2.json`
- `artifacts/data_reconstruction_v2/spec_landing_phase1_4_1/spec_gap_backfill_status.json`
- `artifacts/data_reconstruction_v2/spec_landing_phase1_4_1/spec_gap_backfill_matrix.csv`
- `artifacts/data_reconstruction_v2/spec_landing_phase1_4_1/runtime_gate_status_after_gap_backfill.json`
- `artifacts/data_reconstruction_v2/spec_landing_phase1_4_1/manifest.json`
- `artifacts/data_reconstruction_v2/spec_landing_phase1_4_1/VALIDATION_REPORT.md`
- `artifacts/data_reconstruction_v2/pilot_build/PILOT_OBJECT_QA_REPORT.md`
- `artifacts/data_reconstruction_v2/full_build_dry_run/FULL_BUILD_DRY_RUN_SUMMARY.md`
- `artifacts/data_reconstruction_v2/full_build_dry_run/VALIDATION_REPORT.md`
- `artifacts/data_reconstruction_v2/full_review_resolution_phase2_1/PHASE2_1_REVIEW_RESOLUTION_SUMMARY.md`
- `artifacts/data_reconstruction_v2/full_build_review_resolved_pass1/PHASE2_2_REVIEW_RESOLVED_PASS1_SUMMARY.md`
- `artifacts/data_reconstruction_v2/full_build_annotation_formula_text_anchor_minimal_pass1/PHASE2_4_MINIMAL_FORMULA_TEXT_ANCHOR_SCHEMA_TEST_SUMMARY.md`
- `artifacts/data_reconstruction_v2/human_annotation_anchor_batch1_decision_audit_phase2_5_1/PHASE2_5_1_BATCH1_DECISION_AUDIT_SUMMARY.md`
- `data/raw/《注解伤寒论》.zip`
