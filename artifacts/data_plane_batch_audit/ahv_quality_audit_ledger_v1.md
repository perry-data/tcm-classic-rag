# AHV Quality Audit Ledger v1

- run_id: `batch_upgrade_quality_audit_v1`
- audited_ahv_object_count: `20`
- keep_safe_primary_count: `20`
- adjusted_object_count: `18`
- downgraded_object_count: `0`
- alias_adjusted_count: `5`

| term | verdict | changed_fields | risk_after | fix_action |
| --- | --- | --- | --- | --- |
| 太阳病 | keep_safe_primary_but_needs_notes | notes | low | 补充 audit notes，保留 safe primary 与现有 alias。 |
| 伤寒 | keep_safe_primary_but_needs_notes | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes | low | 把 source 指向同 passage 的 safe main 行，并补充来源边界 notes。 |
| 温病 | adjust_alias | notes, query_aliases_json, learner_surface_forms_json | medium | 保留 canonical 温病 safe primary；停用“春温” learner alias 与 learner normalization。 |
| 暑病 | adjust_alias | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes, query_aliases_json, learner_surface_forms_json | low | 把 source 收窄到 safe main 行；停用“暑病者” alias 与 learner normalization。 |
| 冬温 | keep_safe_primary | - | low | 保留 safe primary；不做 registry 改动。 |
| 时行寒疫 | adjust_alias | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes, query_aliases_json, learner_surface_forms_json | medium | 把 source 指向 safe main 行；停用“寒疫” learner alias 与 learner normalization。 |
| 刚痓 | keep_safe_primary | - | low | 保留 safe primary；不做 registry 改动。 |
| 柔痓 | keep_safe_primary_but_needs_notes | notes | medium | 保留 safe primary，补充 notes 限定为 medium confidence 抽句对象。 |
| 痓病 | adjust_primary_sentence | primary_evidence_text, notes | medium | 将 primary_evidence_text 改为干净句段，并补充 notes。 |
| 结脉 | adjust_primary_sentence | primary_support_passage_id, primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, primary_evidence_type, primary_evidence_text, notes | low | 把 primary 改为 `ZJSHL-CH-003-P-0028` 的“脉来缓，时一止复来者，名曰结”，并指向 safe main source。 |
| 促脉 | keep_safe_primary_but_needs_notes | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes | low | 把 source 指向 safe main 行并补充 notes。 |
| 弦脉 | keep_safe_primary_but_needs_notes | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes | low | 把 source 指向 safe main 行并补充 notes。 |
| 滑脉 | adjust_primary_sentence | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, primary_evidence_text, notes | low | 将 primary 改为“翕奄沉，名曰滑”，并指向 safe main source。 |
| 革脉 | keep_safe_primary_but_needs_notes | notes | medium | 保留 safe primary，补 notes 限定为革脉对象，不启用单字革。 |
| 行尸 | adjust_primary_sentence | primary_evidence_text, notes | medium | 收窄 primary_evidence_text，并补充 source/risk notes。 |
| 内虚 | adjust_primary_sentence | primary_evidence_text, notes | medium | 收窄 primary_evidence_text，并补 notes 限定概念边界。 |
| 血崩 | keep_safe_primary_but_needs_notes | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes | low | 把 source 指向 safe main 行并补充 notes。 |
| 霍乱 | adjust_primary_sentence | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, primary_evidence_text, notes | low | 将 primary 改为“呕吐而利，名曰霍乱”，并指向 safe main source。 |
| 劳复 | adjust_alias | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes, query_aliases_json, learner_surface_forms_json | low | source 指向 safe main；停用“劳动病” alias 与 learner normalization。 |
| 食复 | adjust_alias | primary_source_table, primary_source_object, primary_source_record_id, primary_source_evidence_level, notes, query_aliases_json, learner_surface_forms_json | low | source 指向 safe main；停用“强食复病” alias 与 learner normalization。 |
