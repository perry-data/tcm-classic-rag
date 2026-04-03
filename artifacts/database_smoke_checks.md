# 数据库 Smoke Checks

## 结论

- unified view 可查询：`vw_retrieval_records_unified` 行数大于 0，当前为 21 条示例行已提取。
- chunk 回指关系已落地：`record_chunk_passage_links` 行数为 676，大于多 passage chunk 数 67。
- `annotations / passages / ambiguous_passages` 均按 B/C 层分开导入，未发生越级。

## Query 1: unified view 基础查询

```sql
SELECT record_id, source_object, dataset_variant, evidence_level, display_allowed,
       default_weight_tier, backref_target_type, backref_target_ids_json
FROM vw_retrieval_records_unified
ORDER BY CASE default_weight_tier
    WHEN 'highest' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'medium_low' THEN 4
    WHEN 'low' THEN 5
    WHEN 'lowest' THEN 6
    ELSE 7 END, record_id
LIMIT 6;
```

| record_id | source_object | dataset_variant | evidence_level | display_allowed | default_weight_tier | backref_target_type | backref_target_ids_json |
| --- | --- | --- | --- | --- | --- | --- | --- |
| safe:chunks:ZJSHL-CK-F-0001 | chunks | safe | C | preview_only | highest | main_passages | ["ZJSHL-CH-008-P-0217","ZJSHL-CH-008-P-0219"] |
| safe:chunks:ZJSHL-CK-F-0002 | chunks | safe | C | preview_only | highest | main_passages | ["ZJSHL-CH-008-P-0251","ZJSHL-CH-008-P-0253"] |
| safe:chunks:ZJSHL-CK-F-0003 | chunks | safe | C | preview_only | highest | main_passages | ["ZJSHL-CH-008-P-0258","ZJSHL-CH-008-P-0259","ZJSHL-CH-008-P-0260"] |
| safe:chunks:ZJSHL-CK-F-0004 | chunks | safe | C | preview_only | highest | main_passages | ["ZJSHL-CH-008-P-0261","ZJSHL-CH-008-P-0262","ZJSHL-CH-008-P-0263"] |
| safe:chunks:ZJSHL-CK-F-0005 | chunks | safe | C | preview_only | highest | main_passages | ["ZJSHL-CH-008-P-0264","ZJSHL-CH-008-P-0266"] |
| safe:chunks:ZJSHL-CK-F-0006 | chunks | safe | C | preview_only | highest | main_passages | ["ZJSHL-CH-008-P-0267","ZJSHL-CH-008-P-0268","ZJSHL-CH-008-P-0269"] |

## Query 2: chunk 回指 main_passages

```sql
SELECT c.record_id AS chunk_record_id, c.chunk_id, c.source_passage_ids_json,
       l.link_order, l.main_passage_id, m.evidence_level AS main_passage_evidence_level,
       substr(m.text, 1, 60) AS main_passage_text_preview
FROM records_chunks AS c
JOIN record_chunk_passage_links AS l ON l.chunk_record_id = c.record_id
JOIN records_main_passages AS m ON m.record_id = l.main_passage_record_id
WHERE c.source_passage_count > 1
ORDER BY c.source_passage_count DESC, c.record_id, l.link_order
LIMIT 6;
```

| chunk_record_id | chunk_id | source_passage_ids_json | link_order | main_passage_id | main_passage_evidence_level | main_passage_text_preview |
| --- | --- | --- | --- | --- | --- | --- |
| safe:chunks:ZJSHL-CK-F-0049 | ZJSHL-CK-F-0049 | ["ZJSHL-CH-010-P-0145","ZJSHL-CH-010-P-0146","ZJSHL-CH-010-P-0147","ZJSHL-CH-010-P-0148"] | 1 | ZJSHL-CH-010-P-0145 | A | 黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 |
| safe:chunks:ZJSHL-CK-F-0049 | ZJSHL-CK-F-0049 | ["ZJSHL-CH-010-P-0145","ZJSHL-CH-010-P-0146","ZJSHL-CH-010-P-0147","ZJSHL-CH-010-P-0148"] | 2 | ZJSHL-CH-010-P-0146 | A | 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 |
| safe:chunks:ZJSHL-CK-F-0049 | ZJSHL-CK-F-0049 | ["ZJSHL-CH-010-P-0145","ZJSHL-CH-010-P-0146","ZJSHL-CH-010-P-0147","ZJSHL-CH-010-P-0148"] | 3 | ZJSHL-CH-010-P-0147 | A | 上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之，人参、甘草、大枣之甘以 |
| safe:chunks:ZJSHL-CK-F-0049 | ZJSHL-CK-F-0049 | ["ZJSHL-CH-010-P-0145","ZJSHL-CH-010-P-0146","ZJSHL-CH-010-P-0147","ZJSHL-CH-010-P-0148"] | 4 | ZJSHL-CH-010-P-0148 | A | 上七味，以水一斗，煮取六升，去滓，温服一升，日三服，夜二服。 |
| safe:chunks:ZJSHL-CK-F-0079 | ZJSHL-CK-F-0079 | ["ZJSHL-CH-015-P-0270","ZJSHL-CH-015-P-0271","ZJSHL-CH-015-P-0272","ZJSHL-CH-015-P-0273"] | 1 | ZJSHL-CH-015-P-0270 | A | 麻黄升麻汤方：麻黄二两半，去节。甘温 升麻一两一分。甘平 当归一两一分。辛温 知母苦寒 赵本作「十八铢」 黄芩苦寒 赵本 |
| safe:chunks:ZJSHL-CK-F-0079 | ZJSHL-CK-F-0079 | ["ZJSHL-CH-015-P-0270","ZJSHL-CH-015-P-0271","ZJSHL-CH-015-P-0272","ZJSHL-CH-015-P-0273"] | 2 | ZJSHL-CH-015-P-0271 | A | 甘寒。赵本作「六铢」 白术甘温 乾姜辛热 赵本作「六铢」 芍药酸平 赵本作「六铢」 天门冬去心。甘平 赵本作「六铢」 桂 |

## Query 3: annotations / passages / ambiguous 分层检查

```sql
SELECT * FROM (
    SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag
    FROM vw_retrieval_records_unified
    WHERE source_object = 'annotations'
    ORDER BY record_id
    LIMIT 3
)
UNION ALL
SELECT * FROM (
    SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag
    FROM vw_retrieval_records_unified
    WHERE source_object = 'passages'
    ORDER BY record_id
    LIMIT 3
)
UNION ALL
SELECT * FROM (
    SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag
    FROM vw_retrieval_records_unified
    WHERE source_object = 'ambiguous_passages'
    ORDER BY record_id
    LIMIT 3
);
```

| record_table | source_object | record_id | evidence_level | display_allowed | risk_flag |
| --- | --- | --- | --- | --- | --- |
| records_annotations | annotations | full:annotations:ZJSHL-CH-001-P-0002 | B | secondary | ["annotation_unlinked"] |
| records_annotations | annotations | full:annotations:ZJSHL-CH-001-P-0003 | B | secondary | ["annotation_unlinked"] |
| records_annotations | annotations | full:annotations:ZJSHL-CH-002-P-0005 | B | secondary | ["annotation_unlinked"] |
| records_passages | passages | full:passages:ZJSHL-CH-001-P-0002 | C | risk_only | ["ledger_mixed_roles"] |
| records_passages | passages | full:passages:ZJSHL-CH-001-P-0003 | C | risk_only | ["ledger_mixed_roles"] |
| records_passages | passages | full:passages:ZJSHL-CH-002-P-0005 | C | risk_only | ["ledger_mixed_roles"] |
| risk_registry_ambiguous | ambiguous_passages | full:ambiguous_passages:ZJSHL-CH-003-P-0016 | C | risk_only | ["ambiguous_source"] |
| risk_registry_ambiguous | ambiguous_passages | full:ambiguous_passages:ZJSHL-CH-003-P-0025 | C | risk_only | ["ambiguous_source"] |
| risk_registry_ambiguous | ambiguous_passages | full:ambiguous_passages:ZJSHL-CH-003-P-0029 | C | risk_only | ["ambiguous_source"] |
