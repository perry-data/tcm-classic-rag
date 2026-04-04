# Hybrid Retrieval Smoke Checks

## 运行命令

`python run_hybrid_retrieval.py`

## 结论

- `黄连汤方的条文是什么？` -> mode=`strong`, primary=3, secondary=3, review=2
- `烧针益阳而损阴是什么意思？` -> mode=`weak_with_review_notice`, primary=0, secondary=3, review=2
- `书中有没有提到量子纠缠？` -> mode=`refuse`, primary=0, secondary=0, review=0

## Validation

- strong_precision_patch_preserved: `True`
- evidence_gating_preserved: `True`
- annotation_links_disabled: `True`

## Query: 黄连汤方的条文是什么？

- mode: `strong`
- mode_reason: 基于主证据回答，并附带辅助说明
- runtime_risk_flags: `[]`

### Sparse Top Candidates

[
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0049",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "sparse_score": 158.5,
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 上热..."
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "sparse_score": 157.5,
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-010-P-0145",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-010",
    "topic_consistency": "exact_formula_anchor",
    "sparse_score": 154.5,
    "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。"
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0009",
    "source_object": "chunks",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "sparse_score": 116.5,
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易 葛根半斤 甘草二两，炙。味甘平 黄芩二，赵本作「三」两。味苦寒 黄连三两。味苦寒 上四味，以水八升，先煮葛根，减二升，内诸药，..."
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0016",
    "source_object": "main_passages",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "sparse_score": 114.5,
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0016",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-009",
    "topic_consistency": "expanded_formula_anchor",
    "sparse_score": 112.5,
    "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易"
  }
]

### Dense Top Candidates

{
  "dense_chunks": [
    {
      "record_id": "safe:chunks:ZJSHL-CK-F-0049",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "exact_formula_anchor",
      "dense_score": 0.686211,
      "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 上热..."
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-F-0009",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-009",
      "topic_consistency": "expanded_formula_anchor",
      "dense_score": 0.610976,
      "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易 葛根半斤 甘草二两，炙。味甘平 黄芩二，赵本作「三」两。味苦寒 黄连三两。味苦寒 上四味，以水八升，先煮葛根，减二升，内诸药，..."
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0493",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "formula_query_off_topic",
      "dense_score": 0.564709,
      "text_preview": "苦以泄之，辛以散之；黄连栝蒌实医统本有「之」字苦寒以泄热，半夏之辛以散结。"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-F-0064",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-014",
      "topic_consistency": "different_formula_anchor",
      "dense_score": 0.643123,
      "text_preview": "黄连阿胶汤方：黄连四两。苦寒 黄芩一。赵本作二，两。苦寒 芍药二两。酸平 鸡子黄二枚。甘温 阿胶三两。赵本注：一云三挺。甘温"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-F-0080",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-015",
      "topic_consistency": "different_formula_anchor",
      "dense_score": 0.636104,
      "text_preview": "乾姜黄连黄芩赵本作「黄芩黄连」人参汤方：乾姜辛热 黄连苦寒 黄芩苦寒 人参各三两。甘温"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-F-0043",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "different_formula_anchor",
      "dense_score": 0.625284,
      "text_preview": "大黄黄连泻心汤方：大黄二两。味苦寒 黄连一两。味苦寒 《内经》曰：火热受邪，心病生焉。苦入心，寒除热。大黄、黄连之苦寒，以导泻心下之虚热。但以麻沸汤渍服者，取其..."
    }
  ],
  "dense_main_passages": [
    {
      "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "exact_formula_anchor",
      "dense_score": 0.701662,
      "text_preview": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-009-P-0016",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-009",
      "topic_consistency": "expanded_formula_anchor",
      "dense_score": 0.632304,
      "text_preview": "葛根黄芩黄连汤方：赵本芩、连互易"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-014-P-0074",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-014",
      "topic_consistency": "different_formula_anchor",
      "dense_score": 0.655395,
      "text_preview": "黄连阿胶汤方：黄连四两。苦寒 黄芩一。赵本作二，两。苦寒 芍药二两。酸平 鸡子黄二枚。甘温"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-010-P-0085",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "different_formula_anchor",
      "dense_score": 0.646392,
      "text_preview": "大黄黄连泻心汤方：大黄二两。味苦寒 黄连一两。味苦寒"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-015-P-0278",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-015",
      "topic_consistency": "different_formula_anchor",
      "dense_score": 0.636104,
      "text_preview": "乾姜黄连黄芩赵本作「黄芩黄连」人参汤方：乾姜辛热 黄连苦寒 黄芩苦寒 人参各三两。甘温"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-009-P-0022",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-009",
      "topic_consistency": "different_formula_anchor",
      "dense_score": 0.626937,
      "text_preview": "麻黄汤方：麻黄三两，去节。味甘温 桂枝二，医统本作三两，去皮。味辛热 甘草一两，炙。味甘平"
    }
  ]
}

### Fusion Top Candidates

[
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0049",
    "source_object": "chunks",
    "topic_consistency": "exact_formula_anchor",
    "rrf_score": 0.032787,
    "stage_sources": [
      "sparse",
      "dense_chunks"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
    "source_object": "main_passages",
    "topic_consistency": "exact_formula_anchor",
    "rrf_score": 0.032522,
    "stage_sources": [
      "sparse",
      "dense_main_passages"
    ]
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0009",
    "source_object": "chunks",
    "topic_consistency": "expanded_formula_anchor",
    "rrf_score": 0.031754,
    "stage_sources": [
      "sparse",
      "dense_chunks"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0016",
    "source_object": "main_passages",
    "topic_consistency": "expanded_formula_anchor",
    "rrf_score": 0.031514,
    "stage_sources": [
      "sparse",
      "dense_main_passages"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-010-P-0145",
    "source_object": "passages",
    "topic_consistency": "exact_formula_anchor",
    "rrf_score": 0.015873,
    "stage_sources": [
      "sparse"
    ]
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0493",
    "source_object": "chunks",
    "topic_consistency": "formula_query_off_topic",
    "rrf_score": 0.015873,
    "stage_sources": [
      "dense_chunks"
    ]
  }
]

### Rerank Top Candidates

[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0085",
    "source_object": "main_passages",
    "topic_consistency": "different_formula_anchor",
    "rerank_score": 0.729054,
    "combined_score": 739.28042
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-014-P-0074",
    "source_object": "main_passages",
    "topic_consistency": "different_formula_anchor",
    "rerank_score": 0.728709,
    "combined_score": 739.050252
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0064",
    "source_object": "chunks",
    "topic_consistency": "different_formula_anchor",
    "rerank_score": 0.728164,
    "combined_score": 739.35773
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0016",
    "source_object": "main_passages",
    "topic_consistency": "expanded_formula_anchor",
    "rerank_score": 0.728036,
    "combined_score": 854.210405
  },
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0016",
    "source_object": "passages",
    "topic_consistency": "expanded_formula_anchor",
    "rerank_score": 0.728036,
    "combined_score": 844.051152
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-F-0037",
    "source_object": "chunks",
    "topic_consistency": "different_formula_anchor",
    "rerank_score": 0.728004,
    "combined_score": 738.804748
  }
]

### Final Evidence Summary

{
  "primary_evidence": [
    "safe:main_passages:ZJSHL-CH-010-P-0145",
    "safe:main_passages:ZJSHL-CH-010-P-0146",
    "safe:main_passages:ZJSHL-CH-010-P-0147"
  ],
  "secondary_evidence": [
    "safe:main_passages:ZJSHL-CH-009-P-0017",
    "safe:main_passages:ZJSHL-CH-009-P-0019",
    "safe:main_passages:ZJSHL-CH-009-P-0016"
  ],
  "review_materials": [
    "full:passages:ZJSHL-CH-010-P-0145",
    "full:passages:ZJSHL-CH-009-P-0016"
  ]
}

## Query: 烧针益阳而损阴是什么意思？

- mode: `weak_with_review_notice`
- mode_reason: 仅命中辅助或风险材料，以下内容需核对
- runtime_risk_flags: `["strong_evidence_insufficient", "annotation_unlinked", "topic_mismatch_demoted", "ledger_mixed_roles", "ambiguous_source"]`

### Sparse Top Candidates

[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "source_object": "annotations",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "sparse_score": 192.0,
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "source_object": "passages",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "sparse_score": 191.0,
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
    "source_object": "ambiguous_passages",
    "chapter_id": "ZJSHL-CH-003",
    "topic_consistency": "neutral",
    "sparse_score": 190.0,
    "text_preview": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也..."
  }
]

### Dense Top Candidates

{
  "dense_chunks": [
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0461",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-009",
      "topic_consistency": "neutral",
      "dense_score": 0.615967,
      "text_preview": "烧针发汗，则损阴血，而惊动心气。针处被寒，气聚而成核。心气因惊而虚，肾气乘寒气而动，发为奔豚。《金匮要略》曰：病有奔豚，从惊发得之。肾气欲上乘心，故其气从少腹上..."
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0761",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-014",
      "topic_consistency": "neutral",
      "dense_score": 0.61335,
      "text_preview": "阳有馀，以苦除之，黄芩、黄连之苦，以除热；阴不足，以甘补之，鸡黄、阿胶之甘，以补血；酸，收也，泄也，芍药之酸，收阴气而泄邪热。"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0916",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-017",
      "topic_consistency": "neutral",
      "dense_score": 0.606447,
      "text_preview": "伤寒，阴阳易之为病，其人身体重，少气，少腹里急，或引阴中拘挛，热上冲胸，头重不欲举，眼中生花，赵本注：「一作眵」膝胫拘急者，烧 散主之。"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0048",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-003",
      "topic_consistency": "neutral",
      "dense_score": 0.590702,
      "text_preview": "阳主热而色赤，阴主寒而色青。其人死也，身色青，则阴未离乎体，故曰阴气后竭。身色赤，腋下温，心下热，则阳未离乎体，故曰阳气后竭。《针经》云：医统本作「曰」人有两死..."
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0522",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "neutral",
      "dense_score": 0.588892,
      "text_preview": "太阳病，医发汗，遂发热恶寒，因复下之，心下痞，表里俱虚，阴阳气并竭，无阳则阴独，复加烧针，因胸烦，面色青黄，肤 者，难治；今色微黄，手足温者，易愈。"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0015",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-003",
      "topic_consistency": "neutral",
      "dense_score": 0.583675,
      "text_preview": "阴阳相搏，名曰动。阳动则汗出，阴动则发热。形冷、恶寒者，此三焦伤也。"
    }
  ],
  "dense_main_passages": [
    {
      "record_id": "safe:main_passages:ZJSHL-CH-009-P-0301",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-009",
      "topic_consistency": "neutral",
      "dense_score": 0.629719,
      "text_preview": "太阳伤寒者，加温针，必惊也。"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-009-P-0295",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-009",
      "topic_consistency": "neutral",
      "dense_score": 0.615967,
      "text_preview": "烧针发汗，则损阴血，而惊动心气。针处被寒，气聚而成核。心气因惊而虚，肾气乘寒气而动，发为奔豚。《金匮要略》曰：病有奔豚，从惊发得之。肾气欲上乘心，故其气从少腹上..."
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-014-P-0076",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-014",
      "topic_consistency": "neutral",
      "dense_score": 0.61335,
      "text_preview": "阳有馀，以苦除之，黄芩、黄连之苦，以除热；阴不足，以甘补之，鸡黄、阿胶之甘，以补血；酸，收也，泄也，芍药之酸，收阴气而泄邪热。"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-017-P-0045",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-017",
      "topic_consistency": "neutral",
      "dense_score": 0.606447,
      "text_preview": "伤寒，阴阳易之为病，其人身体重，少气，少腹里急，或引阴中拘挛，热上冲胸，头重不欲举，眼中生花，赵本注：「一作眵」膝胫拘急者，烧 散主之。"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-003-P-0088",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-003",
      "topic_consistency": "neutral",
      "dense_score": 0.590702,
      "text_preview": "阳主热而色赤，阴主寒而色青。其人死也，身色青，则阴未离乎体，故曰阴气后竭。身色赤，腋下温，心下热，则阳未离乎体，故曰阳气后竭。《针经》云：医统本作「曰」人有两死..."
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-010-P-0080",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "neutral",
      "dense_score": 0.588892,
      "text_preview": "太阳病，医发汗，遂发热恶寒，因复下之，心下痞，表里俱虚，阴阳气并竭，无阳则阴独，复加烧针，因胸烦，面色青黄，肤 者，难治；今色微黄，手足温者，易愈。"
    }
  ]
}

### Fusion Top Candidates

[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "source_object": "annotations",
    "topic_consistency": "neutral",
    "rrf_score": 0.016393,
    "stage_sources": [
      "sparse"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0301",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rrf_score": 0.016393,
    "stage_sources": [
      "dense_main_passages"
    ]
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0461",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rrf_score": 0.016393,
    "stage_sources": [
      "dense_chunks"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "source_object": "passages",
    "topic_consistency": "neutral",
    "rrf_score": 0.016129,
    "stage_sources": [
      "sparse"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0295",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rrf_score": 0.016129,
    "stage_sources": [
      "dense_main_passages"
    ]
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0761",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rrf_score": 0.016129,
    "stage_sources": [
      "dense_chunks"
    ]
  }
]

### Rerank Top Candidates

[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "source_object": "annotations",
    "topic_consistency": "neutral",
    "rerank_score": 0.730734,
    "combined_score": 927.373344
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "source_object": "passages",
    "topic_consistency": "neutral",
    "rerank_score": 0.730734,
    "combined_score": 925.346903
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
    "source_object": "ambiguous_passages",
    "topic_consistency": "neutral",
    "rerank_score": 0.730734,
    "combined_score": 923.321302
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0461",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rerank_score": 0.727494,
    "combined_score": 741.293014
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0295",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rerank_score": 0.727494,
    "combined_score": 740.266573
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0522",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rerank_score": 0.624184,
    "combined_score": 637.611382
  }
]

### Final Evidence Summary

{
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

- mode: `refuse`
- mode_reason: 未找到足以支撑回答的依据，建议缩小问题范围或改问具体条文
- runtime_risk_flags: `[]`

### Sparse Top Candidates

_no rows_

### Dense Top Candidates

{
  "dense_chunks": [
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0193",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-006",
      "topic_consistency": "neutral",
      "dense_score": 0.462217,
      "text_preview": "腠理者，津液腠泄之所，文理缝会之中也。《金匮要略》曰：腠者，是三焦通会元真之处，为血气所注；理者，是皮肤脏腑之文理也。邪客于皮肤，则邪气浮浅，易为散发，若以时治..."
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0566",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "neutral",
      "dense_score": 0.459727,
      "text_preview": "脉按之来缓，而赵本无「而」字时一止复来者，名曰结。又脉来动而中止，更来小数，中有还者反动，名曰结阴也；脉来动而中止，不能自还，因而复动，赵本有「者」字 名曰代阴..."
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0927",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-018",
      "topic_consistency": "neutral",
      "dense_score": 0.450991,
      "text_preview": "夫以为疾病至急，仓卒寻按，要者难得，故重集诸可与不可方治，比之三阴三阳篇中，此易见也。又时有不止是三阴三阳，出在诸可与不可中也。"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0284",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-008",
      "topic_consistency": "neutral",
      "dense_score": 0.449266,
      "text_preview": "太阳病，发汗，遂漏不止，其人恶风，小便难，四支微急，难以屈伸者，桂枝加附子汤主之。赵本有「桂枝加附子汤方」详见本书卷十"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0563",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "neutral",
      "dense_score": 0.446959,
      "text_preview": "复烦者，赵本有「将」字服五合，恐一升多者，宜服六七合为妙。赵本医统本并作「始」"
    },
    {
      "record_id": "safe:chunks:ZJSHL-CK-M-0019",
      "source_object": "chunks",
      "chapter_id": "ZJSHL-CH-003",
      "topic_consistency": "neutral",
      "dense_score": 0.445682,
      "text_preview": "经曰：弦则为减，以紧为实，是切之如转索无常而不散。《金匮要略》曰：脉紧如转索无常者，有宿食也。"
    }
  ],
  "dense_main_passages": [
    {
      "record_id": "safe:main_passages:ZJSHL-CH-006-P-0093",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-006",
      "topic_consistency": "neutral",
      "dense_score": 0.462217,
      "text_preview": "腠理者，津液腠泄之所，文理缝会之中也。《金匮要略》曰：腠者，是三焦通会元真之处，为血气所注；理者，是皮肤脏腑之文理也。邪客于皮肤，则邪气浮浅，易为散发，若以时治..."
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-010-P-0174",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "neutral",
      "dense_score": 0.459727,
      "text_preview": "脉按之来缓，而赵本无「而」字时一止复来者，名曰结。又脉来动而中止，更来小数，中有还者反动，名曰结阴也；脉来动而中止，不能自还，因而复动，赵本有「者」字 名曰代阴..."
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-021-P-0006",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-021",
      "topic_consistency": "neutral",
      "dense_score": 0.457425,
      "text_preview": "合四证，已具太阳篇中。"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-018-P-0072",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-018",
      "topic_consistency": "neutral",
      "dense_score": 0.450991,
      "text_preview": "夫以为疾病至急，仓卒寻按，要者难得，故重集诸可与不可方治，比之三阴三阳篇中，此易见也。又时有不止是三阴三阳，出在诸可与不可中也。"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-008-P-0236",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-008",
      "topic_consistency": "neutral",
      "dense_score": 0.449266,
      "text_preview": "太阳病，发汗，遂漏不止，其人恶风，小便难，四支微急，难以屈伸者，桂枝加附子汤主之。赵本有「桂枝加附子汤方」详见本书卷十"
    },
    {
      "record_id": "safe:main_passages:ZJSHL-CH-010-P-0162",
      "source_object": "main_passages",
      "chapter_id": "ZJSHL-CH-010",
      "topic_consistency": "neutral",
      "dense_score": 0.446959,
      "text_preview": "复烦者，赵本有「将」字服五合，恐一升多者，宜服六七合为妙。赵本医统本并作「始」"
    }
  ]
}

### Fusion Top Candidates

[
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0193",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rrf_score": 0.016393,
    "stage_sources": [
      "dense_chunks"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-006-P-0093",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rrf_score": 0.016393,
    "stage_sources": [
      "dense_main_passages"
    ]
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0566",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rrf_score": 0.016129,
    "stage_sources": [
      "dense_chunks"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0174",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rrf_score": 0.016129,
    "stage_sources": [
      "dense_main_passages"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-021-P-0006",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rrf_score": 0.015873,
    "stage_sources": [
      "dense_main_passages"
    ]
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0927",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rrf_score": 0.015873,
    "stage_sources": [
      "dense_chunks"
    ]
  }
]

### Rerank Top Candidates

[
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0284",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rerank_score": 0.52187,
    "combined_score": 533.92516
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0236",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rerank_score": 0.52187,
    "combined_score": 532.901122
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0563",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rerank_score": 0.510657,
    "combined_score": 522.665052
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0162",
    "source_object": "main_passages",
    "topic_consistency": "neutral",
    "rerank_score": 0.510657,
    "combined_score": 521.641742
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0324",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rerank_score": 0.506412,
    "combined_score": 518.322658
  },
  {
    "record_id": "safe:chunks:ZJSHL-CK-M-0019",
    "source_object": "chunks",
    "topic_consistency": "neutral",
    "rerank_score": 0.505037,
    "combined_score": 517.008972
  }
]

### Final Evidence Summary

{
  "primary_evidence": [],
  "secondary_evidence": [],
  "review_materials": []
}

## Checks

- weak_review_mode_kept: `True`
- refuse_mode_kept: `True`
