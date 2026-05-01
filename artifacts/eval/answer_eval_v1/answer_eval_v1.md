# answer_eval_v1

## Summary

- Dataset: `data/eval/eval_dataset_v1.csv`
- Retrieval eval source: `artifacts/eval/retrieval_eval_v1/retrieval_eval_v1.json`
- Trace log: `artifacts/eval/answer_eval_v1/qa_trace_answer_eval_v1.jsonl`
- Run mode: `B_retrieval_rerank_no_llm`
- LLM used: `false`
- Total examples: 36
- Answerable metric examples: 25
- Diagnostic-only examples: 5
- Unanswerable examples: 6
- has_citation_rate: 1.000000
- citation_from_top_k_rate: 0.440000
- gold_cited_rate: 0.800000
- refuse_when_should_not_answer_rate: 1.000000
- scope_qualified_rate: 0.612903
- answer_keyword_hit_rate: 1.000000
- expected_answer_mode_match_rate: 0.677419

## Per Category

| category | examples | answerable | diagnostic | unanswerable | has citation | citation in top-k | gold cited | refuse ok | scope qualified | keyword hit | mode match |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 原文定位 | 6 | 6 | 0 | 0 | 1.000000 | 0.666667 | 1.000000 | 0.000000 | 0.833333 | 1.000000 | 0.833333 |
| 方剂关联 | 5 | 5 | 0 | 0 | 1.000000 | 0.400000 | 1.000000 | 0.000000 | 0.200000 | 1.000000 | 0.200000 |
| 术语解释 | 9 | 4 | 5 | 0 | 1.000000 | 0.500000 | 1.000000 | 0.000000 | 0.250000 | 1.000000 | 1.000000 |
| 注文理解 | 5 | 5 | 0 | 0 | 1.000000 | 0.400000 | 0.200000 | 0.000000 | 0.600000 | 1.000000 | 0.400000 |
| 症候检索 | 5 | 5 | 0 | 0 | 1.000000 | 0.200000 | 0.800000 | 0.000000 | 0.600000 | 1.000000 | 0.600000 |
| 超范围拒答 | 6 | 0 | 0 | 6 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 1.000000 | 0.000000 | 1.000000 |

## Citation Missing

- none

## Citation Not From Top-K

- `eval_002` (原文定位) 麻黄汤方的条文是什么？ | mode=strong | citations=["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0023", "safe:main_passages:ZJSHL-CH-009-P-0025"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_006` (原文定位) 太阳之为病的原文是什么？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-008-P-0191", "safe:main_passages:ZJSHL-CH-009-P-0202", "safe:main_passages:ZJSHL-CH-008-P-0195", "safe:main_passages:ZJSHL-CH-009-P-0318", "safe:main_passages:ZJSHL-CH-007-P-0157", "full:passages:ZJSHL-CH-008-P-0191"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_009` (术语解释) 反是什么意思？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-003-P-0090", "safe:main_passages:ZJSHL-CH-025-P-0007", "safe:main_passages:ZJSHL-CH-009-P-0159", "safe:main_passages:ZJSHL-CH-014-P-0107", "safe:main_passages:ZJSHL-CH-014-P-0108", "safe:main_passages:ZJSHL-CH-014-P-0105", "safe:main_passages:ZJSHL-CH-014-P-0069", "safe:main_passages:ZJSHL-CH-015-P-0265"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_010` (术语解释) 两阳是什么意思？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-009-P-0275", "safe:main_passages:ZJSHL-CH-017-P-0049", "safe:main_passages:ZJSHL-CH-017-P-0050", "safe:main_passages:ZJSHL-CH-017-P-0053", "safe:main_passages:ZJSHL-CH-009-P-0161", "safe:main_passages:ZJSHL-CH-009-P-0160", "safe:main_passages:ZJSHL-CH-009-P-0164"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_016` (方剂关联) 太阳中风鼻鸣乾呕用什么方？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-008-P-0215", "safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-008-P-0219", "safe:main_passages:ZJSHL-CH-008-P-0220", "safe:main_passages:ZJSHL-CH-008-P-0229", "full:passages:ZJSHL-CH-008-P-0215", "full:passages:ZJSHL-CH-007-P-0167"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_017` (方剂关联) 太阳病项背强几几无汗恶风用什么方？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-009-P-0002", "safe:main_passages:ZJSHL-CH-009-P-0004", "safe:main_passages:ZJSHL-CH-009-P-0006", "safe:main_passages:ZJSHL-CH-009-P-0011", "safe:main_passages:ZJSHL-CH-026-P-0001", "full:passages:ZJSHL-CH-009-P-0002", "full:passages:ZJSHL-CH-009-P-0003"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_018` (方剂关联) 伤寒脉浮紧无汗身疼痛用什么方？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0025", "safe:main_passages:ZJSHL-CH-009-P-0026", "safe:main_passages:ZJSHL-CH-009-P-0030", "safe:main_passages:ZJSHL-CH-009-P-0059", "full:passages:ZJSHL-CH-009-P-0077", "full:passages:ZJSHL-CH-009-P-0078"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_022` (症候检索) 头项强痛而恶寒对应哪段原文？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-008-P-0191", "full:annotations:ZJSHL-CH-008-P-0192", "full:annotations:ZJSHL-CH-008-P-0255", "safe:main_passages:ZJSHL-CH-016-P-0006", "safe:main_passages:ZJSHL-CH-007-P-0188", "full:passages:ZJSHL-CH-008-P-0191", "full:passages:ZJSHL-CH-008-P-0192", "full:ambiguous_passages:ZJSHL-CH-010-P-0048"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_023` (症候检索) 发热汗出恶风脉缓名为什么？ | mode=strong | citations=["safe:main_passages:ZJSHL-CH-008-P-0193", "safe:main_passages:ZJSHL-CH-008-P-0229", "safe:main_passages:ZJSHL-CH-008-P-0220"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_024` (症候检索) 发热无汗反恶寒名为什么？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-007-P-0157", "full:annotations:ZJSHL-CH-007-P-0158", "full:annotations:ZJSHL-CH-008-P-0194", "safe:main_passages:ZJSHL-CH-009-P-0303", "safe:main_passages:ZJSHL-CH-007-P-0159", "full:passages:ZJSHL-CH-007-P-0159", "full:passages:ZJSHL-CH-007-P-0158", "full:passages:ZJSHL-CH-007-P-0157", "full:passages:ZJSHL-CH-007-P-0160", "full:passages:ZJSHL-CH-008-P-0193", "full:passages:ZJSHL-CH-008-P-0195", "full:ambiguous_passages:ZJSHL-CH-011-P-0020"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_025` (症候检索) 发热汗出不恶寒名为什么？ | mode=strong | citations=["safe:main_passages:ZJSHL-CH-011-P-0101", "safe:main_passages:ZJSHL-CH-009-P-0159", "safe:main_passages:ZJSHL-CH-009-P-0135"] | notes=at least one citation was not found in trace top_k_chunks; no citation matched gold_chunk_ids under evaluator equivalence
- `eval_026` (注文理解) 成无己如何解释荣气微？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-003-P-0010", "full:annotations:ZJSHL-CH-003-P-0015", "safe:main_passages:ZJSHL-CH-004-P-0216", "full:annotations:ZJSHL-CH-009-P-0302", "safe:main_passages:ZJSHL-CH-003-P-0014", "full:passages:ZJSHL-CH-003-P-0015", "full:passages:ZJSHL-CH-003-P-0014", "full:passages:ZJSHL-CH-003-P-0016", "full:passages:ZJSHL-CH-003-P-0011", "full:passages:ZJSHL-CH-009-P-0303", "full:passages:ZJSHL-CH-003-P-0009", "full:passages:ZJSHL-CH-003-P-0010", "full:passages:ZJSHL-CH-005-P-0002"] | notes=at least one citation was not found in trace top_k_chunks; no citation matched gold_chunk_ids under evaluator equivalence
- `eval_027` (注文理解) 成无己如何解释卫气衰？ | mode=strong | citations=["safe:main_passages:ZJSHL-CH-004-P-0255"] | notes=at least one citation was not found in trace top_k_chunks; no citation matched gold_chunk_ids under evaluator equivalence
- `eval_030` (注文理解) 注文如何解释奔豚从何而发？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-009-P-0295", "full:annotations:ZJSHL-CH-009-P-0109", "full:annotations:ZJSHL-CH-009-P-0111", "full:passages:ZJSHL-CH-009-P-0294", "full:passages:ZJSHL-CH-009-P-0108", "full:passages:ZJSHL-CH-026-P-0005", "full:passages:ZJSHL-CH-009-P-0296", "full:passages:ZJSHL-CH-009-P-0110", "safe:main_passages:ZJSHL-CH-026-P-0006", "full:passages:ZJSHL-CH-009-P-0109"] | notes=at least one citation was not found in trace top_k_chunks

## Should Answer False But Not Refused

- none

## Expected Answer Mode Mismatch

- `eval_006` (原文定位) 太阳之为病的原文是什么？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-008-P-0191", "safe:main_passages:ZJSHL-CH-009-P-0202", "safe:main_passages:ZJSHL-CH-008-P-0195", "safe:main_passages:ZJSHL-CH-009-P-0318", "safe:main_passages:ZJSHL-CH-007-P-0157", "full:passages:ZJSHL-CH-008-P-0191"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_016` (方剂关联) 太阳中风鼻鸣乾呕用什么方？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-008-P-0215", "safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-008-P-0219", "safe:main_passages:ZJSHL-CH-008-P-0220", "safe:main_passages:ZJSHL-CH-008-P-0229", "full:passages:ZJSHL-CH-008-P-0215", "full:passages:ZJSHL-CH-007-P-0167"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_017` (方剂关联) 太阳病项背强几几无汗恶风用什么方？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-009-P-0002", "safe:main_passages:ZJSHL-CH-009-P-0004", "safe:main_passages:ZJSHL-CH-009-P-0006", "safe:main_passages:ZJSHL-CH-009-P-0011", "safe:main_passages:ZJSHL-CH-026-P-0001", "full:passages:ZJSHL-CH-009-P-0002", "full:passages:ZJSHL-CH-009-P-0003"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_018` (方剂关联) 伤寒脉浮紧无汗身疼痛用什么方？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0025", "safe:main_passages:ZJSHL-CH-009-P-0026", "safe:main_passages:ZJSHL-CH-009-P-0030", "safe:main_passages:ZJSHL-CH-009-P-0059", "full:passages:ZJSHL-CH-009-P-0077", "full:passages:ZJSHL-CH-009-P-0078"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_020` (方剂关联) 霍乱热多欲饮水用什么方？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-016-P-0014", "safe:main_passages:ZJSHL-CH-016-P-0016", "safe:main_passages:ZJSHL-CH-016-P-0018", "safe:main_passages:ZJSHL-CH-017-P-0061", "full:annotations:ZJSHL-CH-016-P-0015", "full:passages:ZJSHL-CH-016-P-0014", "full:passages:ZJSHL-CH-016-P-0015"] | notes=
- `eval_022` (症候检索) 头项强痛而恶寒对应哪段原文？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-008-P-0191", "full:annotations:ZJSHL-CH-008-P-0192", "full:annotations:ZJSHL-CH-008-P-0255", "safe:main_passages:ZJSHL-CH-016-P-0006", "safe:main_passages:ZJSHL-CH-007-P-0188", "full:passages:ZJSHL-CH-008-P-0191", "full:passages:ZJSHL-CH-008-P-0192", "full:ambiguous_passages:ZJSHL-CH-010-P-0048"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_024` (症候检索) 发热无汗反恶寒名为什么？ | mode=weak_with_review_notice | citations=["safe:main_passages:ZJSHL-CH-007-P-0157", "full:annotations:ZJSHL-CH-007-P-0158", "full:annotations:ZJSHL-CH-008-P-0194", "safe:main_passages:ZJSHL-CH-009-P-0303", "safe:main_passages:ZJSHL-CH-007-P-0159", "full:passages:ZJSHL-CH-007-P-0159", "full:passages:ZJSHL-CH-007-P-0158", "full:passages:ZJSHL-CH-007-P-0157", "full:passages:ZJSHL-CH-007-P-0160", "full:passages:ZJSHL-CH-008-P-0193", "full:passages:ZJSHL-CH-008-P-0195", "full:ambiguous_passages:ZJSHL-CH-011-P-0020"] | notes=at least one citation was not found in trace top_k_chunks
- `eval_027` (注文理解) 成无己如何解释卫气衰？ | mode=strong | citations=["safe:main_passages:ZJSHL-CH-004-P-0255"] | notes=at least one citation was not found in trace top_k_chunks; no citation matched gold_chunk_ids under evaluator equivalence
- `eval_028` (注文理解) 注文怎样解释清邪中上？ | mode=strong | citations=["safe:main_passages:ZJSHL-CH-023-P-0046"] | notes=no citation matched gold_chunk_ids under evaluator equivalence
- `eval_029` (注文理解) 注文对桂枝汤不可误用有什么提醒？ | mode=strong | citations=["safe:main_passages:ZJSHL-CH-008-P-0217"] | notes=no citation matched gold_chunk_ids under evaluator equivalence

## P2 Residual Diagnostics

These rows are diagnostic-only and are not included in gold_cited or keyword-hit aggregate denominators.

| id | question | answer_mode | citations | final_answer_excerpt |
| --- | --- | --- | --- | --- |
| eval_011 | 少阴病是什么意思 | strong | `["safe:main_passages:ZJSHL-CH-014-P-0112", "safe:main_passages:ZJSHL-CH-014-P-0072", "safe:main_passages:ZJSHL-CH-014-P-0105"]` | 和这个问题直接相关的主条，当前主要落在这些命中片段里。 少阴病，咽中伤生疮，不能语言，声不出者，苦酒汤主之。 少阴病，得之二三日以上，心中烦，不得卧，黄连阿胶汤主之。 少阴病，二三日咽痛者，可与甘草汤；不瘥者，赵本无「者」字与桔梗汤。 可以先据此理解原文意思，具体字句再结合引用继续回看。 |
| eval_012 | 半表半里证和过经有什么不同 | strong | `["safe:main_passages:ZJSHL-CH-010-P-0005"]` | 和这个问题直接相关的主条，当前主要落在这些命中片段里。 脏结于法当下，无阳证，为表无热；不往来寒热，为半表半里无热；其人反静，为里无热。经曰：舌上如苔者，以丹田有热，胸中有寒，医统本有「邪气」二字以表里皆寒，故不可攻。 可以先据此理解原文意思，具体字句再结合引用继续回看。 |
| eval_013 | 荣气微和卫气衰有什么区别 | strong | `["safe:main_passages:ZJSHL-CH-004-P-0255"]` | 和这个问题直接相关的主条，当前主要落在这些命中片段里。 趺阳脉浮而芤，浮者卫气衰，赵本作「虚」芤者荣气伤，其身体瘦，肌肉甲错，浮芤相搏，宗气衰微，赵本作「微衰」四属断绝。 可以先据此理解原文意思，具体字句再结合引用继续回看。 |
| eval_014 | 霍乱和伤寒有什么区别 | strong | `["safe:main_passages:ZJSHL-CH-009-P-0320", "safe:main_passages:ZJSHL-CH-009-P-0322"]` | 和这个问题直接相关的主条，当前主要落在这些命中片段里。 伤寒有热，少腹满，应小便不利；今反利者，为有血也，当下之，不可馀药，宜抵当丸。 抵当丸方：水蛭二十个，赵本有「熬」字。味苦寒 虻虫二十五个，赵本作二十个，去翅足，熬。味苦，微寒 桃人人赵本作仁，二十个，赵本有「五」字，去皮尖 大黄三两 可以先据此理解原文意思，具体字句再结合引用继续回看。 |
| eval_015 | 痓病和太阳病有什么不同 | strong | `["safe:main_passages:ZJSHL-CH-007-P-0159", "safe:main_passages:ZJSHL-CH-009-P-0002", "safe:main_passages:ZJSHL-CH-008-P-0220"]` | 和这个问题直接相关的主条，当前主要落在这些命中片段里。 太阳病，发热汗出，赵本有「而」字不恶寒者，赵本无「者」字名曰柔痓。 太阳病，项背强几几，无汗，恶风，葛根汤主之。 太阳病，头痛发热，汗出恶风者，赵本无「者」字桂枝汤主之。 可以先据此理解原文意思，具体字句再结合引用继续回看。 |
