# Batch A general_overview finish fix v1

## 目标范围

本轮只修 `eval_seed_q095` 与 `eval_seed_q096` 两条 Batch A general_overview 失败样本，不修改 `goldset_v2_working_102.json`，不修改旧 72 条，不继续 Batch B，也不处理其他题型或其他 question_id。

## 修复前状态

上一轮 `meaning_explanation_boundary_fix_v1` 后，完整 102 题只剩 `eval_seed_q095` 与 `eval_seed_q096` 失败：

| question_id | query | expected | 修复前 actual | primary | total_evidence | citations | gold_citation_check | failed_checks |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `eval_seed_q095` | `少阳病有哪些核心表现和处理边界？` | `strong` | `weak_with_review_notice` | 0 | 5 | 5 | FAIL | `mode_match, gold_citation_check` |
| `eval_seed_q096` | `伤寒瘥后有哪些处理分支？` | `strong` | `weak_with_review_notice` | 0 | 8 | 8 | PASS | `mode_match` |

## 失败根因

两题有一个共同入口问题：general question detector 未识别 `有哪些核心表现和处理边界` 与 `有哪些处理分支` 这两种总括问法，导致它们没有进入 general_overview 的主题分支整理路径，而是落回标准检索/弱回答路径。

`eval_seed_q095` 还有额外的 citation scope 问题。题面主题是 `少阳病`，gold scope 位于 `辨少阳病脉证并治` 章节中的少阳纲领、禁忌与小柴胡汤相关条文。修复前系统引用了跨章节的弱相关记录，没有稳定覆盖 gold。进入 general_overview 路径后，还需要允许 `少阳病` 在章节约束下匹配正文中的 `少阳`，并从 `与小柴胡汤` 这类句式提取方剂分支，否则可晋级的 strong 分支不足。

`eval_seed_q096` 与 q095 不是完全同根因。q096 的主题 `伤寒瘥后` 在正文中常以 `伤寒瘥以后`、`大病瘥后`、`伤寒解后` 等形态出现，并集中在瘥后/劳复相关章节。修复前虽能碰到部分 gold citation，但没有按主题分支组织成 strong；因此需要在章节约束下为 `伤寒瘥后` 增加文本别名匹配，而不是放宽到全库泛匹配。

## 修复策略

本轮代码修改保持窄口径：

- 在 `backend/strategies/general_question.py` 中补充总括触发短语：`有哪些核心表现和处理边界`、`有哪些处理分支`、`有哪些核心表现`。
- 在 `backend/answers/assembler.py` 的 general_overview candidate 收集阶段增加主题别名配置，并要求别名命中受章节别名约束，避免跨章节泛化。
- 为 `少阳病` 增加章节内 `少阳` 别名匹配；为 `伤寒瘥后` 增加 `伤寒瘥`、`大病瘥后`、`伤寒解后` 等章节内文本别名匹配。
- 在 general branch analyzer 中补充 `与X汤` 方剂分支句式，使 q095 的 `与小柴胡汤` 能作为稳定分支进入 primary_evidence。

本轮没有修改 evaluator、goldset 或 expected_mode，也没有触碰 source_lookup、comparison、meaning_explanation 或 refusal 逻辑。

## 修复后结果

完整重跑 `goldset_v2_working_102.json` 后：

| question_id | 修复后 actual | primary | total_evidence | citations | gold_citation_check | failed_checks | primary_evidence |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `eval_seed_q095` | `strong` | 2 | 9 | 2 | PASS | 无 | `ZJSHL-CH-012-P-0219`, `ZJSHL-CH-012-P-0215` |
| `eval_seed_q096` | `strong` | 4 | 12 | 4 | PASS | 无 | `ZJSHL-CH-017-P-0063`, `ZJSHL-CH-017-P-0048`, `ZJSHL-CH-017-P-0056`, `ZJSHL-CH-017-P-0061` |

完整 102 题 evaluator 汇总：

- total_questions: `102`
- mode_match_count: `102/102`
- citation_basic_pass: `82/82`
- failure_count: `0`
- all_checks_passed: `true`
- general_overview 题型：`14/14` mode match，`14/14` citation basic pass，`failure_count = 0`

旧 72 条 general_overview 样本检查：旧 general_overview 共 12 条，修复后 `12/12` 仍通过。

## 未处理项

Batch A working set 当前已全通过。本轮不继续 Batch B，不扩容到 150，也不写论文正文。
