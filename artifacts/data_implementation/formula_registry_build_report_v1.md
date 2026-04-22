# Formula Registry Build Report v1

- generated_at_utc: `2026-04-22T11:09:37.734853+00:00`
- formula_canonical_registry rows: `106`
- formula_alias_registry rows: `232`
- retrieval_ready_formula_view rows: `106`
- auto_generated_aliases: `110`
- manual_review_aliases: `0`
- skipped aliases.json non-formula rows: `30`
- formulas_without_decoction_segment: `31`
- formulas_without_usage_context_segment: `32`

## Source Confidence

- high: `92`
- medium: `14`

## Alias Types

- canonical: `106`
- orthographic_suffix_variant: `10`
- orthographic_variant: `10`
- source:work_term_variant: `16`
- suffix_variant: `90`

## Notes

- Registry rows are persisted in SQLite and mirrored to JSON artifacts.
- `retrieval_ready_formula_view` is a runtime view with one row per formula_id.
- Core formula text is built from safe `records_main_passages`; risk-only full passages are not used as formula view body text.
- Ambiguous normalized aliases are kept in the alias registry with `needs_manual_review=1` and confidence below runtime threshold.
