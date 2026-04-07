# Goldset Independence Review v1

- 审查日期：2026-04-07
- 审查对象：`artifacts/evaluation/goldset_v1_seed.json`
- 当前题量：72
- 审查产物：`artifacts/evaluation/goldset_independence_audit_v1.json`

## 1. 结论

本轮确认当前 72 条 goldset 可以继续作为开发回归集使用，但不能把 evaluator v1 的 `72/72` 通过率直接写成论文第 4 章的强评估结论。核心原因是扩写 patch note 已明示：q010-q060 的非拒答题 gold citation 主要来自当前正式系统 replay 后的 `citations`，再回填 `gold_record_ids` 与 `gold_passage_ids`。

独立性收紧后的口径如下：

1. `formal_core`：14 条，均为拒答边界题，可独立于系统 citation 判断。
2. `formal_candidate_with_provenance_note`：6 条，为原 seed 中带人工说明但参考过系统样例的题，可作为候选或附表，正文需披露来源。
3. `exclude_until_reannotation`：52 条，其中 51 条为系统 replay 回填 gold，1 条为 q004，曾按当前系统实际 citations 扩展 gold 集合，需人工重标。

## 2. 来源标记

本轮给每条样本新增 `gold_source_type`：

| gold_source_type | 数量 | 说明 |
| --- | --- | --- |
| `manual_independent` | 14 | 本轮可基于题目边界或人工先验判断，不需要当前系统 citation 回填定义 gold。拒答题若虽经 replay 筛选但 gold 为空且边界可独立判断，也归入此类。 |
| `manual_with_system_reference` | 6 | 有人工标注理由与证据片段，但 source_refs 或历史修订仍引用当前系统样例；可作为候选集，但论文中应披露来源。 |
| `system_bootstrapped` | 51 | gold_record_ids / gold_passage_ids 主要来自当前正式系统 replay 后 citations 回填，存在明显自举污染风险。 |
| `needs_reannotation` | 1 | 已经发现 gold 集合直接受当前系统输出修正影响，或需要先人工重标后再纳入正式主评估。 |

按题型分布如下：

| question_type | label | manual_independent | manual_with_system_reference | system_bootstrapped | needs_reannotation |
| --- | --- | --- | --- | --- | --- |
| `source_lookup` | 条文/出处类 | 0 | 1 | 19 | 0 |
| `meaning_explanation` | 含义解释类 | 0 | 1 | 13 | 0 |
| `general_overview` | 泛问/总括类 | 0 | 2 | 9 | 1 |
| `comparison` | 比较类 | 0 | 2 | 10 | 0 |
| `refusal` | 无证据拒答类 | 14 | 0 | 0 | 0 |

## 3. 抽样复核

本轮按题型做分层抽样，共复核 40 条，达到本轮要求的最低抽样数：

| question_type | 抽样数 | question_ids | 样本内来源分布 |
| --- | --- | --- | --- |
| `source_lookup` | 10 | `eval_seed_q001`, `eval_seed_q010`, `eval_seed_q011`, `eval_seed_q012`, `eval_seed_q013`, `eval_seed_q014`, `eval_seed_q015`, `eval_seed_q016`, `eval_seed_q017`, `eval_seed_q018` | manual_with_system_reference=1, system_bootstrapped=9 |
| `meaning_explanation` | 8 | `eval_seed_q002`, `eval_seed_q029`, `eval_seed_q030`, `eval_seed_q031`, `eval_seed_q032`, `eval_seed_q033`, `eval_seed_q034`, `eval_seed_q035` | manual_with_system_reference=1, system_bootstrapped=7 |
| `general_overview` | 8 | `eval_seed_q003`, `eval_seed_q004`, `eval_seed_q005`, `eval_seed_q042`, `eval_seed_q043`, `eval_seed_q044`, `eval_seed_q045`, `eval_seed_q046` | manual_with_system_reference=2, needs_reannotation=1, system_bootstrapped=5 |
| `comparison` | 8 | `eval_seed_q006`, `eval_seed_q007`, `eval_seed_q051`, `eval_seed_q052`, `eval_seed_q053`, `eval_seed_q054`, `eval_seed_q055`, `eval_seed_q056` | manual_with_system_reference=2, system_bootstrapped=6 |
| `refusal` | 6 | `eval_seed_q008`, `eval_seed_q009`, `eval_seed_q061`, `eval_seed_q062`, `eval_seed_q063`, `eval_seed_q064` | manual_independent=6 |

抽样观察：

1. `source_lookup`：q010-q018 的题面方名与 evidence span 中的方文能对应，但 record / passage id 仍来自 replay citations；建议人工从原文或索引目录重新确认后再纳入正式主评估。
2. `meaning_explanation`：q029-q035 多数依赖注解或弱回答证据，当前 gold 很容易固化系统选取的注解顺序；需人工先验重标核心注解与正文补充。
3. `general_overview`：q004 和 q042-q046 暴露总括题的核心风险：系统选择了若干“最小分支”，gold 随之接受这些分支；后续必须先定义人工覆盖口径。
4. `comparison`：q051-q056 的双方方文基本可核对，但比较语境和补充 evidence 仍由系统 replay 选取；建议收紧到人工可解释的双方最小证据集合。
5. `refusal`：q008、q009、q061-q064 可由边界规则独立判断，gold citation 为空，当前污染风险低。

## 4. 进入论文评估集的建议

可作为正式主评估 `formal_core` 的题：

`eval_seed_q008`, `eval_seed_q009`, `eval_seed_q061`, `eval_seed_q062`, `eval_seed_q063`, `eval_seed_q064`, `eval_seed_q065`, `eval_seed_q066`, `eval_seed_q067`, `eval_seed_q068`, `eval_seed_q069`, `eval_seed_q070`, `eval_seed_q071`, `eval_seed_q072`

可作为候选或附表、但需披露“参考过系统样例”的题：

`eval_seed_q001`, `eval_seed_q002`, `eval_seed_q003`, `eval_seed_q005`, `eval_seed_q006`, `eval_seed_q007`

暂不纳入论文正式主评估、需人工重标或收紧 gold 的题：

`eval_seed_q004`, `eval_seed_q010`, `eval_seed_q011`, `eval_seed_q012`, `eval_seed_q013`, `eval_seed_q014`, `eval_seed_q015`, `eval_seed_q016`, `eval_seed_q017`, `eval_seed_q018`, `eval_seed_q019`, `eval_seed_q020`, `eval_seed_q021`, `eval_seed_q022`, `eval_seed_q023`, `eval_seed_q024`, `eval_seed_q025`, `eval_seed_q026`, `eval_seed_q027`, `eval_seed_q028`, `eval_seed_q029`, `eval_seed_q030`, `eval_seed_q031`, `eval_seed_q032`, `eval_seed_q033`, `eval_seed_q034`, `eval_seed_q035`, `eval_seed_q036`, `eval_seed_q037`, `eval_seed_q038`, `eval_seed_q039`, `eval_seed_q040`, `eval_seed_q041`, `eval_seed_q042`, `eval_seed_q043`, `eval_seed_q044`, `eval_seed_q045`, `eval_seed_q046`, `eval_seed_q047`, `eval_seed_q048`, `eval_seed_q049`, `eval_seed_q050`, `eval_seed_q051`, `eval_seed_q052`, `eval_seed_q053`, `eval_seed_q054`, `eval_seed_q055`, `eval_seed_q056`, `eval_seed_q057`, `eval_seed_q058`, `eval_seed_q059`, `eval_seed_q060`

## 5. 后续处理建议

| recommended_action | 数量 |
| --- | --- |
| `keep` | 20 |
| `reannotate` | 23 |
| `tighten_gold` | 29 |

具体建议：

1. q010-q028：先做 source_lookup 人工先验重标，确认方名、方文起止段和是否接受方义说明段，完成后可从 `system_bootstrapped` 升级为 `manual_independent` 或 `manual_with_system_reference`。
2. q029-q041：解释题需人工确定核心注解、正文补充和 weak / strong 判定，不宜只按系统 citations 保留。
3. q004、q042-q050：总括题需先定义“最小分支整理”的人工覆盖规则；q004 当前 gold 集合尤其需要去除“按系统实际 citation 扩展”的影响。
4. q051-q060：比较题需人工确认双方方文和语境证据至少各有命中，并去掉只为适配当前 replay 的补充 citation。
5. q008-q009、q061-q072：拒答题可保留为低风险正式样本，但论文中应说明它们主要评估边界控制，不代表 citation 能力。

## 6. 验证

本轮执行了最小结构和 evaluator 验证：

1. `jq empty config/evaluation/goldset_schema_v1.json artifacts/evaluation/goldset_v1_seed.json artifacts/evaluation/goldset_independence_audit_v1.json`：通过。
2. `./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json /tmp/goldset_independence_eval.json --report-md /tmp/goldset_independence_eval.md --fail-on-evaluation-failure`：通过。
3. evaluator v1 结果：总题量 72，`answer_mode` 匹配 72 / 72，`citation_check_required` 基础通过 58 / 58，`failure_count` 为 0。

## 7. 本轮未改动范围

本轮没有修改 API、payload contract、retrieval 主链或 answer assembler，也没有扩题量。新增内容只用于评估集来源审查和论文评估口径收紧。
