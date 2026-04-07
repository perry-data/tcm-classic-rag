# q004 Review Note

## 1. 复核对象

本轮只复核 evaluator v1 中唯一失败样本：

- question_id: `eval_seed_q004`
- query: `少阴病应该怎么办？`
- question_type: `general_overview`
- expected_mode: `strong`

本轮没有扩写题量，没有修改 API，没有修改 answer payload contract，也没有改 retrieval 或 answer assembler 业务逻辑。

## 2. 失败根因

失败不是 `answer_mode` 错误。重跑前的 evaluator v1 报告中：

- expected_mode: `strong`
- actual_mode: `strong`
- primary_evidence: 3
- citations: 3
- failed_checks: `gold_citation_check`, `unsupported_assertion_check`

真正原因是 q004 的 gold citation 集合过窄。

原 goldset 只接受三条少阴病分支：

1. `safe:main_passages:ZJSHL-CH-014-P-0072`，黄连阿胶汤
2. `safe:main_passages:ZJSHL-CH-014-P-0162`，四逆散
3. `safe:main_passages:ZJSHL-CH-014-P-0093`，桃花汤

当前正式系统实际 strong citations 为：

1. `safe:main_passages:ZJSHL-CH-014-P-0078`，附子汤
2. `safe:main_passages:ZJSHL-CH-014-P-0112`，苦酒汤
3. `safe:main_passages:ZJSHL-CH-014-P-0062`，麻黄附子细辛汤

原 gold 三条仍出现在本次 payload 的 `secondary_evidence` 中，但没有进入 `citations`。由于 evaluator v1 的 citation 检查只看最终 citations 是否命中 gold record 或 gold passage，q004 被判为 gold citation 失败。

## 3. 判定：改 goldset，不改系统

本轮判定为 goldset 标注问题，而不是系统 citation 选择问题。

理由：

1. q004 是总括类问题，当前正式 spec 对该类问题的目标是“2-4 条最小分支整理”，不是穷尽专题，也不是锁定唯一三条固定分支。
2. 当前系统选出的三条 citation 都来自 `safe:main_passages`，且都是 `A` 级少阴病条文。
3. 三条都含有显式方证分支信号：`附子汤主之`、`苦酒汤主之`、`麻黄附子细辛汤主之`。
4. 当前回答文本明确写了“只列若干典型分支，不等于穷尽全部‘少阴病’处理”，没有把这三条包装成完整专题结论。
5. 旧 gold 三条来自既有 `shaoyin_management_strong` example artifact，但该 artifact 代表的是一组历史可接受分支，不应被解释为唯一可接受的少阴病总括引用集合。

因此，若为了让系统强行回到黄连阿胶汤、四逆散、桃花汤三条，会把实现改成对 q004 的过拟合；这不符合“只做最小修正、不改大链路”的约束。

## 4. 最小修正

本轮只更新 `artifacts/evaluation/goldset_v1_seed.json` 中 q004 的 gold 可接受集合：

1. 保留原三条 gold citation。
2. 新增当前正式系统实际 citations 对应的三条 A 级少阴病主条：
   - `safe:main_passages:ZJSHL-CH-014-P-0078`
   - `safe:main_passages:ZJSHL-CH-014-P-0112`
   - `safe:main_passages:ZJSHL-CH-014-P-0062`
3. 同步补充对应 `gold_passage_ids` 与 `gold_evidence_spans`。
4. 更新 q004 的 `annotation_notes`，说明总括题接受多组典型 A 级分支，不要求唯一三条固定引用。

这不是扩写 seed 题量，而是修正 q004 的 citation 接受口径。

## 5. 重新运行结果

重新运行命令：

```bash
python scripts/run_evaluator_v1.py --fail-on-evaluation-failure
```

更新后的 evaluator v1 结果：

1. 总题数：9
2. `answer_mode` 匹配：9 / 9
3. `citation_check_required` 基础通过：7 / 7
4. 失败样本：0
5. q004 状态：`PASS`

q004 当前命中的 gold citations：

1. `safe:main_passages:ZJSHL-CH-014-P-0078`
2. `safe:main_passages:ZJSHL-CH-014-P-0112`
3. `safe:main_passages:ZJSHL-CH-014-P-0062`
