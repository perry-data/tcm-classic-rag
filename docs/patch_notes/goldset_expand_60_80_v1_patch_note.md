# Goldset 60-80 Expansion v1 Patch Note

## 1. 本轮目标

本轮将 evaluation goldset 从 9 条 seed 扩写到 72 条，用作论文第 4 章与后续 200-250 条完整 goldset 扩容前的中间版本。

本轮只扩题，不改系统：

1. 不改 API。
2. 不改 answer payload contract。
3. 不改 retrieval 主链。
4. 不改 answer assembler 业务逻辑。
5. 不接 Prompt / LLM。

## 2. 文件命名说明

本轮继续更新：

`artifacts/evaluation/goldset_v1_seed.json`

原因是 evaluator v1 默认读取这个路径，继续沿用可以避免新增 runner 参数或改动运行入口。

为避免语义误解，本轮已将 `dataset_name` 更新为：

`evaluation_goldset_v1_seed_expanded_72`

`dataset_stage` 仍保留为 `seed`，因为当前 schema 只定义 `seed / full` 两档；本轮 72 条属于从 seed 到 full 之间的中间扩展集，尚不是最终 full goldset。

## 3. 扩写策略

扩写遵守现有三份规则文档：

1. `docs/evaluation/evaluation_spec_v1.md`
2. `docs/evaluation/evaluation_plan_v1.md`
3. `docs/evaluation/annotation_guideline_v1.md`

具体策略：

1. 优先扩写当前系统已有稳定处理基础的问题类型。
2. 非拒答题的 gold citation 直接来自当前正式系统 replay 后的 `citations`，并回填 `gold_record_ids` 与 `gold_passage_ids`。
3. 每条非拒答题保留 1-3 条 `gold_evidence_spans`，作为人工核对入口。
4. 拒答题只选择当前正式系统返回 `refuse` 且证据槽位与 citations 全空的样本。
5. 比较类严格保持 pairwise comparison，不扩展到三方比较或优劣判断。
6. 总括类只按当前“最小分支整理”口径扩写，不要求穷尽专题。

## 4. 题型分布

扩写后总题量为 72 条。

| question_type | 数量 |
| --- | ---: |
| `source_lookup` | 20 |
| `meaning_explanation` | 14 |
| `general_overview` | 12 |
| `comparison` | 12 |
| `refusal` | 14 |

该分布落在本轮要求的推荐区间内：

1. 条文/出处类：18-22，本轮 20。
2. 含义解释类：12-16，本轮 14。
3. 泛问/总括类：10-14，本轮 12。
4. 比较类：8-12，本轮 12。
5. 拒答类：10-14，本轮 14。

## 5. 样本来源与边界

新增样本覆盖：

1. 更多方名与条文出处查询，例如桂枝汤方、葛根汤方、麻黄汤方、大承气汤方等。
2. 注解依赖或短语释义类问题，例如“一阴一阳谓之道是什么意思？”、“阳为气，阴为血是什么意思？”等。
3. 总括类问题，例如阳明病、太阴病、厥阴病、伤寒、中风、霍乱病等。
4. pairwise 比较问题，例如桂枝汤方 vs 葛根汤方、大承气汤方 vs 小承气汤方等。
5. 拒答问题，覆盖书外问题、优劣判断和当前正式系统不支持的诊疗类请求。

本轮没有加入无法明确回指 gold 依据或明确拒答边界的问题。

## 6. 验证结果

运行命令：

```bash
python scripts/run_evaluator_v1.py --fail-on-evaluation-failure
```

结果：

1. 总题量：72
2. `answer_mode` 匹配：72 / 72
3. `citation_check_required`：58
4. `citation_check_required` 基础通过：58 / 58
5. 失败题列表：空
6. `all_checks_passed`：true

本轮没有需要归因的失败题，因此没有进一步区分 goldset 问题或系统问题。

## 7. 本轮更新文件

1. `artifacts/evaluation/goldset_v1_seed.json`
2. `artifacts/evaluation/evaluator_v1_report.json`
3. `artifacts/evaluation/evaluator_v1_report.md`
4. `docs/patch_notes/goldset_expand_60_80_v1_patch_note.md`
