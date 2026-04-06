# Evaluation Seed Smoke Checks

## 运行命令

### 1. 基础结构与覆盖检查

```bash
jq -e '(.schema_version == "goldset_schema_v1") and (.dataset_stage == "seed") and ((.items | length) == 9) and (([.items[].question_type] | unique | length) == 5)' artifacts/evaluation/goldset_v1_seed.json
```

结果：`true`

### 2. 结构化手工校验

```bash
python3 -c 'import json, pathlib; data=json.loads(pathlib.Path("artifacts/evaluation/goldset_v1_seed.json").read_text(encoding="utf-8")); required_top={"schema_version","dataset_name","dataset_stage","dataset_scope","items"}; assert required_top <= set(data); allowed_types={"source_lookup","meaning_explanation","general_overview","comparison","refusal"}; allowed_modes={"strong","weak_with_review_notice","refuse"}; item_ids=set(); required_item={"question_id","query","question_type","question_type_label","expected_mode","gold_record_ids","gold_passage_ids","gold_evidence_spans","annotation_notes","citation_check_required","evaluation_targets","retrieval_assertions","answer_assertions","source_refs"}; base=pathlib.Path(".");\nfor item in data["items"]:\n    assert required_item <= set(item)\n    assert item["question_id"] not in item_ids\n    item_ids.add(item["question_id"])\n    assert item["question_type"] in allowed_types\n    assert item["expected_mode"] in allowed_modes\n    assert item["source_refs"]\n    for ref in item["source_refs"]:\n        assert (base / ref["artifact_path"]).exists()\n    gold_passages=set(item["gold_passage_ids"])\n    gold_records=set(item["gold_record_ids"])\n    for span in item["gold_evidence_spans"]:\n        assert span["passage_id"] in gold_passages\n        assert span["record_id"] in gold_records\nprint("manual_structure_ok")'
```

结果：`manual_structure_ok`

### 3. 覆盖统计

```bash
jq '{item_count: (.items | length), type_counts: (.items | group_by(.question_type) | map({question_type: .[0].question_type, count: length})), citation_checks_required: ([.items[] | select(.citation_check_required == true)] | length), source_refs_present: ([.items[] | select((.source_refs | length) > 0)] | length)}' artifacts/evaluation/goldset_v1_seed.json
```

结果：

```json
{
  "item_count": 9,
  "type_counts": [
    {
      "question_type": "comparison",
      "count": 2
    },
    {
      "question_type": "general_overview",
      "count": 3
    },
    {
      "question_type": "meaning_explanation",
      "count": 1
    },
    {
      "question_type": "refusal",
      "count": 2
    },
    {
      "question_type": "source_lookup",
      "count": 1
    }
  ],
  "citation_checks_required": 7,
  "source_refs_present": 9
}
```

## 结论

### 1. 当前 seed goldset 是否可被系统消费

可以，但要准确描述“消费”的边界：

1. 当前正式系统并没有单独的 evaluator runner，因此不会直接整包读取 `goldset_v1_seed.json`。
2. 当前正式系统实际消费的是每条样本的 `query` 字段，这一点与现有 `POST /api/v1/answers` contract 一致。
3. 当前 seed 的 9 条样本都带有 `source_refs`，且都能追溯到现有 examples，说明这些 query 已经是当前系统可消费、可回放的真实样例。

因此，v1 的正确表述应是：

- seed goldset 已具备被当前正式系统“按 query 重放”的消费条件；
- 尚未具备“被独立 evaluator 直接整包执行”的自动化能力；
- 这属于本轮刻意保留的边界，而不是遗漏。

### 2. 样例覆盖情况

当前 seed 共 9 条，覆盖 5 个主问题类型：

1. 条文/出处类：1 条
2. 含义解释类：1 条
3. 泛问/总括类：3 条
4. 比较类：2 条
5. 无证据拒答类：2 条

其中：

1. 7 条要求执行 citation check；
2. 2 条是拒答基线；
3. 9 条全部可追溯到当前已有 example artifacts。

### 3. 这批题能支撑哪些后续评估

这批 seed 题已经可以支撑四类正式评估：

1. retrieval 命中评估
   - 通过 `gold_passage_ids` 做 Hit@K / Recall@K 的后续扩展。
2. citation 正确性评估
   - 通过 `gold_record_ids` 与 `gold_evidence_spans` 做人工核对。
3. `answer_mode` 合理性评估
   - 通过 `expected_mode` 检查 `strong / weak / refuse` 是否符合当前系统边界。
4. 无证据强答评估
   - 通过拒答题和弱答题识别越级结论、错引强答和无证据断言。

## 附记

本次验证未使用第三方 `jsonschema` 包，因为当前环境未安装该依赖。  
本轮改用 `jq` + Python 标准库完成结构与覆盖检查，这不影响 v1 基线成立。
