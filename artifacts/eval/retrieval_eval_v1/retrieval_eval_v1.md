# retrieval_eval_v1

## Summary

- Dataset: `data/eval/eval_dataset_v1.csv`
- Run mode: `B_retrieval_rerank`
- Total examples: 36
- Answerable metric examples: 25
- Diagnostic-only examples: 5
- Unanswerable examples: 6
- Hit@1: 0.800000
- Hit@3: 0.840000
- Hit@5: 0.840000
- MRR: 0.813333
- Recall@5: 0.840000

## Per Category

| category | examples | Hit@1 | Hit@3 | Hit@5 | MRR | Recall@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 原文定位 | 6 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| 方剂关联 | 5 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| 术语解释 | 4 | 0.750000 | 0.750000 | 0.750000 | 0.750000 | 0.750000 |
| 注文理解 | 5 | 0.200000 | 0.400000 | 0.400000 | 0.266667 | 0.400000 |
| 症候检索 | 5 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |

## Top5 Misses

- `eval_007` (术语解释) 干呕是什么意思？ | gold=["safe:main_passages:ZJSHL-CH-014-P-0188", "safe:main_passages:ZJSHL-CH-015-P-0324"] | top5=[]
- `eval_026` (注文理解) 成无己如何解释荣气微？ | gold=["full:annotations:ZJSHL-CH-003-P-0011", "full:annotations:ZJSHL-CH-003-P-0016"] | top5=["safe:definition_terms:AHV2-850318ee8950", "safe:main_passages:ZJSHL-CH-003-P-0010", "full:passages:ZJSHL-CH-003-P-0010", "safe:main_passages:ZJSHL-CH-004-P-0216", "full:annotations:ZJSHL-CH-003-P-0015"]
- `eval_027` (注文理解) 成无己如何解释卫气衰？ | gold=["full:annotations:ZJSHL-CH-003-P-0013"] | top5=["safe:definition_terms:AHV2-81a12b6da994", "safe:main_passages:ZJSHL-CH-003-P-0012", "safe:main_passages:ZJSHL-CH-004-P-0214", "safe:chunks:ZJSHL-CK-M-0007", "safe:main_passages:ZJSHL-CH-003-P-0014"]
- `eval_029` (注文理解) 注文对桂枝汤不可误用有什么提醒？ | gold=["full:annotations:ZJSHL-CH-008-P-0228"] | top5=["safe:chunks:ZJSHL-CK-M-0292", "formula:FML-1b00cf16ce52", "safe:chunks:ZJSHL-CK-F-0001", "safe:main_passages:ZJSHL-CH-008-P-0217", "safe:chunks:ZJSHL-CK-F-0002"]

## Gold Appears Below Top5

- none

## P2 Residual Diagnostic Top5

- `eval_011` 少阴病是什么意思 | included_in_metrics=false | top5=["safe:definition_terms:AHV2-9f641a6ecc7d", "safe:chunks:ZJSHL-CK-M-0777", "safe:main_passages:ZJSHL-CH-014-P-0029", "safe:chunks:ZJSHL-CK-M-0756", "safe:chunks:ZJSHL-CK-M-0776"]
- `eval_012` 半表半里证和过经有什么不同 | included_in_metrics=false | top5=["full:passages:ZJSHL-CH-009-P-0210", "safe:definition_terms:AHV2-aa28a21f86c8", "full:annotations:ZJSHL-CH-010-P-0136", "full:passages:ZJSHL-CH-010-P-0136", "safe:chunks:ZJSHL-CK-M-0480"]
- `eval_013` 荣气微和卫气衰有什么区别 | included_in_metrics=false | top5=["safe:chunks:ZJSHL-CK-M-0007", "safe:main_passages:ZJSHL-CH-003-P-0014", "full:annotations:ZJSHL-CH-004-P-0252", "full:passages:ZJSHL-CH-004-P-0252", "safe:definition_terms:AHV2-81a12b6da994"]
- `eval_014` 霍乱和伤寒有什么区别 | included_in_metrics=false | top5=["safe:chunks:ZJSHL-CK-M-0897", "safe:main_passages:ZJSHL-CH-016-P-0006", "safe:chunks:ZJSHL-CK-M-0902", "safe:main_passages:ZJSHL-CH-016-P-0014", "full:passages:ZJSHL-CH-009-P-0321"]
- `eval_015` 痓病和太阳病有什么不同 | included_in_metrics=false | top5=["safe:definition_terms:AHV-87d3ca263c08", "safe:main_passages:ZJSHL-CH-007-P-0157", "safe:definition_terms:DPO-0159fa8c7c2c", "safe:chunks:ZJSHL-CK-M-0451", "safe:main_passages:ZJSHL-CH-009-P-0275"]

## Unanswerable Top5

- `eval_031` 白虎是什么意思？ | included_in_metrics=false | top5=["safe:chunks:ZJSHL-CK-M-0638", "safe:main_passages:ZJSHL-CH-011-P-0104", "formula:FML-47765c7ee78a", "safe:chunks:ZJSHL-CK-M-0546", "safe:main_passages:ZJSHL-CH-010-P-0128"]
- `eval_032` 太阳能是什么意思？ | included_in_metrics=false | top5=[]
- `eval_033` 霍乱疫苗是什么？ | included_in_metrics=false | top5=[]
- `eval_034` 劳动合同是什么？ | included_in_metrics=false | top5=[]
- `eval_035` 量子纠缠在书中怎么解释？ | included_in_metrics=false | top5=[]
- `eval_036` Python 怎么写爬虫？ | included_in_metrics=false | top5=[]
