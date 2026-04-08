# q004 Reannotation Report v1

- 报告日期：2026-04-08
- 范围：仅 `question_id = eval_seed_q004`
- 题面：`少阴病应该怎么办？`
- 最终状态：`manual_independent`
- 记录文件：`artifacts/evaluation/q004_reannotation_record_v1.json`

## 1. 旧问题

q004 原状态为 `needs_reannotation`。旧问题不在于少阴病章缺少稳定条文，而在于 provenance 和口径混在一起：

1. `source_refs` 指向 `artifacts/general_question_examples.json:shaoyin_management_strong`，不是正文独立来源。
2. gold 曾因当前正式系统 actual citations 扩展，容易把“当前系统 strong 响应的可接受 citation 集”误当成“人工定义的评估口径”。
3. 旧 evidence rationale 中有“当前正式系统稳定选入”之类说明，不能作为正式独立 gold 的理由。

## 2. 新口径

q004 本轮定义为：

> “少阴病应该怎么办？” = 少阴病的最小稳定治法分支整理；不是当前系统 strong 回答 citation 集，也不是少阴病章全量穷举。

该口径要求回答保持 general_overview strong 的多分支特征：少阴病不能按单一治法处理，应按少阴病章中直接、稳定、可核对的方证分支分情况整理。

## 3. 新 gold

本轮保留 6 条经人工复核后可独立成立的少阴病章 main_passages 分支，并重写 source refs、rationale 与 annotation notes：

1. `ZJSHL-CH-014-P-0062`：少阴病始得之，反发热，脉沉，麻黄附子细辛汤主之。
2. `ZJSHL-CH-014-P-0072`：少阴病二三日以上，心中烦，不得卧，黄连阿胶汤主之。
3. `ZJSHL-CH-014-P-0078`：少阴病一二日，口中和，背恶寒，当灸之，附子汤主之。
4. `ZJSHL-CH-014-P-0093`：少阴病二三日至四五日，腹痛，小便不利，下利不止便脓血，桃花汤主之。
5. `ZJSHL-CH-014-P-0112`：少阴病咽中伤生疮，不能语言，声不出，苦酒汤主之。
6. `ZJSHL-CH-014-P-0162`：少阴病四逆及或咳、悸、小便不利、腹中痛、泄利下重，四逆散主之。

不再保留为 q004 gold 定义依据的内容：

1. `artifacts/general_question_examples.json:shaoyin_management_strong`。
2. 当前系统 replay citations。
3. `full:passages:*` 或 `full:ambiguous_passages:*` record。
4. 公式条、死证/预后条、欲解时条、非少阴病主题条文。

## 4. 状态判断

q004 现在可以转为 `manual_independent`。

理由：

1. 题面范围已明确为“少阴病最小稳定治法分支整理”。
2. 新 source refs 全部指向 `data/processed/zjshl_dataset_v2/main_passages.json`。
3. 6 条 gold 均为少阴病章内直接方证条文。
4. evidence 全部为 `primary`，符合 strong 总括题多分支支撑规则。
5. 不再依赖系统样例或 replay 作为唯一来源。

## 5. 验证结果

本轮已用更新后的 72 条总集重跑 evaluator v1：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json artifacts/evaluation/q004_reannotation_eval_report.json --report-md artifacts/evaluation/q004_reannotation_eval_report.md --fail-on-evaluation-failure
```

结果：

1. 总题量：72。
2. `answer_mode` 匹配：72 / 72。
3. `citation_check_required` 基础通过：58 / 58。
4. q004：expected `strong`，actual `strong`，gold citation check passed。
5. q004 matched citations：`ZJSHL-CH-014-P-0078`, `ZJSHL-CH-014-P-0112`, `ZJSHL-CH-014-P-0062`。
6. `failure_count`：0。
7. `all_checks_passed`：true。

本轮后，72 条总集的 `gold_source_type` 计数为：`manual_independent = 72`。
