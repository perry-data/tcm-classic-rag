# FTS5 / BM25 Sparse Smoke Checks

## 运行命令

`python -m backend.retrieval.hybrid`

## 结论

- sparse backend: `sqlite_fts5_bm25`
- fts table: `retrieval_sparse_fts`
- tokenizer: `trigram`

- `黄连汤方的条文是什么？` -> mode=`strong`, legacy_top=6, fts5_top=6, primary=3
- `烧针益阳而损阴是什么意思？` -> mode=`weak_with_review_notice`, legacy_top=3, fts5_top=3, primary=0
- `书中有没有提到量子纠缠？` -> mode=`refuse`, legacy_top=0, fts5_top=0, primary=0
- `桂枝汤方的条文是什么？` -> mode=`strong`, legacy_top=6, fts5_top=6, primary=2

## Query: 黄连汤方的条文是什么？

- query_focus: `黄连汤方`
- sparse_backend: `sqlite_fts5_bm25`
- fts_match_expression: `"黄连汤方" OR "连汤方" OR "黄连汤"`

### Legacy Sparse Top Candidates

[
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0049",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 158.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 上热..."
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 157.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-010-P-0145",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 154.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0009",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 116.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易 葛根半斤 甘草二两，炙。味甘平 黄芩二，赵本作「三」两。味苦寒 黄连三两。味苦寒 上四味，以水八升，先煮葛根，减二升，内诸药，..."
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0016",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 114.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0016",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 112.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易"
  }
]

### FTS5 Sparse Top Candidates

[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 176.792991,
    "sparse_bm25_raw": -21.520433,
    "sparse_bm25_score": 21.520433,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-010-P-0145",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 173.792991,
    "sparse_bm25_raw": -21.520433,
    "sparse_bm25_score": 21.520433,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0049",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 168.33827,
    "sparse_bm25_raw": -10.974132,
    "sparse_bm25_score": 10.974132,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 上热..."
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0016",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 138.5,
    "sparse_bm25_raw": -26.770883,
    "sparse_bm25_score": 26.770883,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0016",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 136.5,
    "sparse_bm25_raw": -26.770883,
    "sparse_bm25_score": 26.770883,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0009",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 130.656543,
    "sparse_bm25_raw": -15.790965,
    "sparse_bm25_score": 15.790965,
    "matched_terms": [
      "黄连汤方",
      "连汤方",
      "黄连汤",
      "汤方",
      "连汤",
      "黄连"
    ],
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易 葛根半斤 甘草二两，炙。味甘平 黄芩二，赵本作「三」两。味苦寒 黄连三两。味苦寒 上四味，以水八升，先煮葛根，减二升，内诸药，..."
  }
]

### Final Hybrid Summary

{
  "mode": "strong",
  "mode_reason": "基于主证据回答，并附带辅助说明",
  "primary_evidence": [
    "safe:main_passages:ZJSHL-CH-010-P-0145",
    "safe:main_passages:ZJSHL-CH-010-P-0146",
    "safe:main_passages:ZJSHL-CH-010-P-0147"
  ],
  "secondary_evidence": [
    "safe:main_passages:ZJSHL-CH-009-P-0016",
    "safe:main_passages:ZJSHL-CH-009-P-0017",
    "safe:main_passages:ZJSHL-CH-009-P-0019"
  ],
  "review_materials": [
    "full:passages:ZJSHL-CH-010-P-0145",
    "full:passages:ZJSHL-CH-009-P-0016"
  ]
}

## Query: 烧针益阳而损阴是什么意思？

- query_focus: `烧针益阳而损阴`
- sparse_backend: `sqlite_fts5_bm25`
- fts_match_expression: `"烧针益阳而损阴" OR "烧针益阳" OR "益阳而损" OR "针益阳而" OR "阳而损阴" OR "烧针益" OR "益阳而" OR "而损阴" OR "针益阳" OR "阳而损"`

### Legacy Sparse Top Candidates

[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "source_object": "annotations",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "text_match_score": 189.0,
    "sparse_score": 192.0,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "烧针益阳而损阴",
      "烧针益阳",
      "益阳而损",
      "针益阳而",
      "阳而损阴",
      "烧针益",
      "益阳而",
      "而损阴",
      "针益阳",
      "阳而损",
      "损阴",
      "烧针"
    ],
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "text_match_score": 189.0,
    "sparse_score": 191.0,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "烧针益阳而损阴",
      "烧针益阳",
      "益阳而损",
      "针益阳而",
      "阳而损阴",
      "烧针益",
      "益阳而",
      "而损阴",
      "针益阳",
      "阳而损",
      "损阴",
      "烧针"
    ],
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
    "source_object": "ambiguous_passages",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "text_match_score": 189.0,
    "sparse_score": 190.0,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "烧针益阳而损阴",
      "烧针益阳",
      "益阳而损",
      "针益阳而",
      "阳而损阴",
      "烧针益",
      "益阳而",
      "而损阴",
      "针益阳",
      "阳而损",
      "损阴",
      "烧针"
    ],
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  }
]

### FTS5 Sparse Top Candidates

[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "source_object": "annotations",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "text_match_score": 189.0,
    "sparse_score": 216.0,
    "sparse_bm25_raw": -62.430453,
    "sparse_bm25_score": 62.430453,
    "matched_terms": [
      "烧针益阳而损阴",
      "烧针益阳",
      "益阳而损",
      "针益阳而",
      "阳而损阴",
      "烧针益",
      "益阳而",
      "而损阴",
      "针益阳",
      "阳而损",
      "损阴",
      "烧针"
    ],
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "text_match_score": 189.0,
    "sparse_score": 215.0,
    "sparse_bm25_raw": -62.430453,
    "sparse_bm25_score": 62.430453,
    "matched_terms": [
      "烧针益阳而损阴",
      "烧针益阳",
      "益阳而损",
      "针益阳而",
      "阳而损阴",
      "烧针益",
      "益阳而",
      "而损阴",
      "针益阳",
      "阳而损",
      "损阴",
      "烧针"
    ],
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
    "source_object": "ambiguous_passages",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "text_match_score": 189.0,
    "sparse_score": 214.0,
    "sparse_bm25_raw": -62.430453,
    "sparse_bm25_score": 62.430453,
    "matched_terms": [
      "烧针益阳而损阴",
      "烧针益阳",
      "益阳而损",
      "针益阳而",
      "阳而损阴",
      "烧针益",
      "益阳而",
      "而损阴",
      "针益阳",
      "阳而损",
      "损阴",
      "烧针"
    ],
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  }
]

### Final Hybrid Summary

{
  "mode": "weak_with_review_notice",
  "mode_reason": "仅命中辅助或风险材料，以下内容需核对",
  "primary_evidence": [],
  "secondary_evidence": [
    "full:annotations:ZJSHL-CH-003-P-0016",
    "safe:main_passages:ZJSHL-CH-009-P-0295",
    "safe:main_passages:ZJSHL-CH-010-P-0080"
  ],
  "review_materials": [
    "full:passages:ZJSHL-CH-003-P-0016",
    "full:ambiguous_passages:ZJSHL-CH-003-P-0016"
  ]
}

## Query: 书中有没有提到量子纠缠？

- query_focus: `量子纠缠`
- sparse_backend: `sqlite_fts5_bm25`
- fts_match_expression: `"量子纠缠" OR "子纠缠" OR "量子纠"`

### Legacy Sparse Top Candidates

_no rows_

### FTS5 Sparse Top Candidates

_no rows_

### Final Hybrid Summary

{
  "mode": "refuse",
  "mode_reason": "未找到足以支撑回答的依据，建议缩小问题范围或改问具体条文",
  "primary_evidence": [],
  "secondary_evidence": [],
  "review_materials": []
}

## Query: 桂枝汤方的条文是什么？

- query_focus: `桂枝汤方`
- sparse_backend: `sqlite_fts5_bm25`
- fts_match_expression: `"桂枝汤方" OR "枝汤方" OR "桂枝汤"`

### Legacy Sparse Top Candidates

[
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0001",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-008",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 158.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温 右伍..."
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0217",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-008",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 157.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-008-P-0217",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-008",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 154.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0102",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-027",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 116.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "柴胡桂枝汤方：桂枝去皮 黄芩 人参各一两半 甘草一两，炙 半夏二合半 芍药一两半 大枣六枚，擘 生姜一两半，切 柴胡四两 上九味，以水七升，煮取三升，去滓，温服..."
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0321",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 116.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "太阳赵本有「桂枝汤方」详见本书卷二病，外证未解，脉浮弱者，当以汗解，宜桂枝汤。"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0720",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-013",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 116.5,
    "sparse_bm25_raw": null,
    "sparse_bm25_score": null,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "太阴病脉浮者，可发汗，宜桂枝汤。赵本有「桂枝汤方」详见卷二"
  }
]

### FTS5 Sparse Top Candidates

[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0217",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-008",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 173.929077,
    "sparse_bm25_raw": -11.115284,
    "sparse_bm25_score": 11.115284,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-008-P-0217",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-008",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 170.929077,
    "sparse_bm25_raw": -11.115284,
    "sparse_bm25_score": 11.115284,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0001",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-008",
    "topic_consistency": "exact_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 165.422513,
    "sparse_bm25_raw": -4.683507,
    "sparse_bm25_score": 4.683507,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温 右伍..."
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0720",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-013",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 140.5,
    "sparse_bm25_raw": -16.23748,
    "sparse_bm25_score": 16.23748,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "太阴病脉浮者，可发汗，宜桂枝汤。赵本有「桂枝汤方」详见卷二"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-013-P-0008",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-013",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 139.5,
    "sparse_bm25_raw": -16.23748,
    "sparse_bm25_score": 16.23748,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "太阴病脉浮者，可发汗，宜桂枝汤。赵本有「桂枝汤方」详见卷二"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0321",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "text_match_score": 128.5,
    "sparse_score": 138.78178,
    "sparse_bm25_raw": -15.074998,
    "sparse_bm25_score": 15.074998,
    "matched_terms": [
      "桂枝汤方",
      "枝汤方",
      "桂枝汤",
      "枝汤",
      "桂枝",
      "汤方"
    ],
    "text_preview": "太阳赵本有「桂枝汤方」详见本书卷二病，外证未解，脉浮弱者，当以汗解，宜桂枝汤。"
  }
]

### Final Hybrid Summary

{
  "mode": "strong",
  "mode_reason": "基于主证据回答，并附带辅助说明",
  "primary_evidence": [
    "safe:main_passages:ZJSHL-CH-008-P-0217",
    "safe:main_passages:ZJSHL-CH-008-P-0219"
  ],
  "secondary_evidence": [
    "safe:main_passages:ZJSHL-CH-013-P-0008",
    "safe:main_passages:ZJSHL-CH-016-P-0034",
    "safe:main_passages:ZJSHL-CH-027-P-0001",
    "safe:main_passages:ZJSHL-CH-027-P-0003",
    "safe:main_passages:ZJSHL-CH-027-P-0002"
  ],
  "review_materials": [
    "full:passages:ZJSHL-CH-008-P-0217"
  ]
}
