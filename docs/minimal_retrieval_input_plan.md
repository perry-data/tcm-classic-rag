# 最小检索输入结构方案

## 1. 目标

本文件定义后续“最小检索实现”在数据库层应接收什么输入、如何组织阶段性结果、以及如何把结果分发到：

- `primary_evidence`
- `secondary_evidence`
- `risk_materials`

它不是 API 设计，而是检索模块内部的数据结构约定。

## 2. 最小检索请求结构

建议检索模块内部至少接收以下结构：

```json
{
  "query_text": "用户原始问题",
  "query_text_normalized": "规范化后的查询文本",
  "target_mode": "strong_first",
  "allow_levels": ["A", "B", "C"],
  "blocked_sources": ["annotation_links"],
  "source_priority": [
    "safe_chunks",
    "safe_main_passages_primary",
    "safe_main_passages_secondary",
    "full_annotations_raw",
    "full_passages_ledger",
    "ambiguous_related_material"
  ],
  "candidate_budget": {
    "total_limit": 24,
    "per_source_soft_limit": {
      "safe_chunks": 8,
      "safe_main_passages_primary": 6,
      "safe_main_passages_secondary": 4,
      "full_annotations_raw": 3,
      "full_passages_ledger": 2,
      "ambiguous_related_material": 1
    }
  },
  "scope_filters": {
    "book_id": "ZJSHL",
    "chapter_id": null
  }
}
```

说明：

- `query_text` 是唯一必填业务输入。
- `query_text_normalized` 是检索实现的内部字段，不是新接口要求。
- `target_mode` 建议先固定成 `strong_first`，即优先尝试产出 Strong 结果，再自动退到 Weak + Review。
- `blocked_sources` 必须显式包含 `annotation_links`。

## 3. 第一阶段检索优先查哪些对象

优先顺序固定为：

1. `records_chunks`
2. `records_main_passages` 中 Level A
3. `records_main_passages` 中 Level B
4. `records_annotations`
5. `records_passages`
6. `risk_registry_ambiguous`

实现上可通过 `vw_retrieval_records_unified` 一次查出候选，再按 `default_weight_tier` 和文本匹配分数重排。

## 4. 第一阶段候选结果结构

建议统一收敛成如下结构：

```json
{
  "query_text": "用户原始问题",
  "raw_candidates": [
    {
      "retrieval_entry_id": "safe:chunks:ZJSHL-CK-F-0087",
      "record_table": "records_chunks",
      "record_id": "safe:chunks:ZJSHL-CK-F-0087",
      "source_object": "chunks",
      "dataset_variant": "safe",
      "evidence_level": "C",
      "display_allowed": "preview_only",
      "default_weight_tier": "highest",
      "risk_flag": [],
      "backref_target_type": "main_passages",
      "backref_target_ids": ["ZJSHL-CH-025-P-0002"],
      "score": 0.91
    }
  ]
}
```

这里的 `raw_candidates` 还不是回答输入，只是检索命中集合。

## 5. `chunks` 命中后的回指结构

`chunks` 必须先回指，再进入证据筛选。

建议内部追加一个回指解析层：

```json
{
  "chunk_hits": [
    {
      "chunk_record_id": "safe:chunks:ZJSHL-CK-F-0087",
      "chunk_score": 0.91,
      "linked_main_passages": [
        {
          "main_passage_record_id": "safe:main_passages:ZJSHL-CH-025-P-0002",
          "passage_id": "ZJSHL-CH-025-P-0002",
          "evidence_level": "A"
        }
      ]
    }
  ]
}
```

规则：

- 命中 `chunks` 后，必须查 `record_chunk_passage_links`。
- 取回的对象必须是 `records_main_passages`。
- 若一个 chunk 对应多个 `main_passages`，全部保留；后续优先选 A，再选 B。
- `chunks` 本身只保留在 `chunk_hits` 或 `retrieval_trace`，不直接写入 `primary_evidence`。

## 6. `annotations` 如何进入结果集

`records_annotations` 的进入方式应是“直接命中，直接进入辅助池”：

```json
{
  "secondary_candidates": [
    {
      "record_id": "full:annotations:ZJSHL-CH-003-P-0003",
      "source_object": "annotations",
      "evidence_level": "B",
      "display_allowed": "secondary",
      "risk_flag": ["annotation_unlinked"],
      "requires_disclaimer": true
    }
  ]
}
```

硬规则：

- 不读取 `annotation_links`
- 不自动把 `annotations` 拼回正文
- 即使 `source_anchor_passage_id` 非空，也只作为审计字段

## 7. `passages` 与 `ambiguous_passages` 如何只做兜底

建议把这两类统一塞入 `risk_candidates`，而不是 `primary_evidence`：

```json
{
  "risk_candidates": [
    {
      "record_id": "full:passages:ZJSHL-CH-003-P-0016",
      "source_object": "passages",
      "evidence_level": "C",
      "display_allowed": "risk_only",
      "risk_flag": ["ledger_mixed_roles", "ambiguous_source"]
    },
    {
      "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
      "source_object": "ambiguous_passages",
      "evidence_level": "C",
      "display_allowed": "risk_only",
      "risk_flag": ["ambiguous_source"]
    }
  ]
}
```

硬规则：

- 二者都不能直接变成 `primary_evidence`
- `records_passages` 默认只在没有足够 A/B 时提供回查文本
- `risk_registry_ambiguous` 只承担风险提示和最低优先级召回

## 8. 回答前的最小结果槽位结构

数据库检索完成后，建议交给回答模块的最小结构如下：

```json
{
  "query_text": "用户原始问题",
  "primary_evidence": [],
  "secondary_evidence": [],
  "risk_materials": [],
  "retrieval_trace": {
    "chunk_hits": [],
    "blocked_sources": ["annotation_links"],
    "used_sources": [
      "records_chunks",
      "records_main_passages",
      "records_annotations"
    ]
  }
}
```

三类槽位的填充规则：

- `primary_evidence`
  - 只允许 `records_main_passages` 且 `evidence_level = A`
- `secondary_evidence`
  - 允许 `records_main_passages` 且 `evidence_level = B`
  - 允许 `records_annotations`
- `risk_materials`
  - 允许 `records_passages`
  - 允许 `risk_registry_ambiguous`
  - 不建议把 `records_chunks` 直接放进该槽位；chunk 更适合待在 `retrieval_trace`

## 9. Strong / Weak + Review / Refuse 的数据库判定

### 9.1 Strong

最小条件：

```json
{
  "primary_evidence_count": ">= 1"
}
```

解释：

- 只要存在至少一条 Level A `records_main_passages`，即可进入 Strong。
- 该 Level A 可以是直接命中 `records_main_passages`，也可以是 `chunks` 回指得到。

### 9.2 Weak + Review

最小条件：

```json
{
  "primary_evidence_count": 0,
  "secondary_evidence_count_or_risk_material_count": ">= 1",
  "required_runtime_risk_flag": ["strong_evidence_insufficient"]
}
```

解释：

- 没有 A，但有 B 或 C。
- 如果命中的是 `annotations`，同时保留 `annotation_unlinked`。
- 如果命中的是 `passages/ambiguous_passages`，保留对应风险标签。

### 9.3 Refuse

最小条件：

```json
{
  "primary_evidence_count": 0,
  "secondary_evidence_count": 0,
  "risk_material_count": 0
}
```

解释：

- 数据库结果层没有任何可进入三个槽位的记录。
- `annotation_links` 不应影响这个判定，因为它从头到尾都被阻断。

## 10. `annotation_links` 在输入层如何保持禁用

最小要求：

- 请求结构里显式写入 `blocked_sources = ["annotation_links"]`
- 统一检索视图不包含 `annotation_links`
- 回指阶段只允许 `record_chunk_passage_links`
- 证据筛选阶段只认 `records_main_passages / records_annotations / records_passages / risk_registry_ambiguous`

这意味着：

- `annotation_links` 不是“低权重启用”
- 而是“数据库层完全不进入运行输入”

## 11. 下一轮实现时可直接照此拆分

下一轮只要完成三件事即可：

1. 按本文件的请求结构驱动 `vw_retrieval_records_unified`
2. 对 `records_chunks` 实现强制回指
3. 按三个结果槽位做模式判定

做到这三点，就已经满足最小检索实现需要的数据库输入结构。
