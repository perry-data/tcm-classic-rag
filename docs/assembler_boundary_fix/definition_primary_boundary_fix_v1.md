# Definition Primary Boundary Fix v1

## 本轮目标

本轮只修复 definition priority 分支中 `full:passages:*` 越权进入 `primary_evidence` 的问题。冻结边界保持不变：不改 prompt、不改前端、不改 API payload 字段名、不改 answer_mode 定义、不重开 formula object 主线、不改 commentarial 主逻辑。

## 越权路径核查

触发 query 主要来自 definition priority 的四类 family：

- `what_is`：如 `什么是发汗药`、`阳结是什么`、`坏病是什么`
- `what_means`：如 `发汗药是什么意思`、`阳结是什么意思`
- `category_membership_yesno`：如 `承气汤是下药吗`
- `category_membership_open`：如 `桂枝汤是什么药`

旧配置的问题在 `config/controlled_replay/definition_query_priority_rules_v1.json`：每个 family 的 `primary_source_allowlist` 同时允许了 `main_passages` 和 `passages`。这使 `records_passages` 里的 `full:passages:*` 可以参与 definition priority 的 primary 竞争。

retrieval 层本身没有把 `records_passages` 放进 primary。`backend/retrieval/minimal.py` 的 slot assembly 会把 `records_main_passages` 放入 primary/secondary pool，把 `records_passages` 与 `risk_registry_ambiguous` 放入 risk pool；`backend/retrieval/hybrid.py` 只是沿用这个 gating 结果返回 `primary_evidence`、`secondary_evidence`、`risk_materials`。

payload 最终越界发生在 `backend/answers/assembler.py` 的 definition priority 分支。该分支从 `retrieval["raw_candidates"]` 重新收集候选、打分、排序，然后用优先候选重建 payload 的 primary/secondary/review。因为旧 allowlist 允许 `passages`，`full:passages:ZJSHL-CH-006-P-0120` 这类 raw candidate 会绕过 retrieval slot 结果，被重新构造成 `primary_evidence`。

因此根因不是 suspected pool、不是 retrieval gate，而是 definition priority 的配置与 assembler 槽位重选规则共同放宽了 primary 边界。

## 修复内容

配置修复：

- `primary_source_allowlist` 只保留 `main_passages`
- 新增 `secondary_source_allowlist` 保留 `passages`，仅允许其作为补充材料参与 definition priority，不再参与 primary 竞争
- 未改 family、pattern、evidence type 权重、block hints 或其它 query 策略

assembler 修复：

- definition priority primary 现在必须同时满足：
  - `source_object == "main_passages"`
  - `record_id` 以 `safe:main_passages:` 开头
  - raw candidate 来自 `records_main_passages`
  - `evidence_level == "A"`
  - 当前 candidate 没有被 topic gate 标为 `primary_allowed=false`
- `full:passages:*`、`ambiguous_passages`、annotation/ledger/risk-only 对象即使被 raw retrieval 命中，也只能进入 `secondary_evidence` 或 `review_materials`
- 当 definition priority 只有 support-only 候选、没有合格 primary 时，payload 降为 `weak_with_review_notice`，不再为了保持 strong 而把 full passage 塞进 primary
- 保留原有 formula object / comparison / formula_effect / definition_outline / commentarial 的分支顺序和主逻辑

## 回归产物

- JSON 回归：`artifacts/assembler_boundary_fix/definition_primary_regression_v1.json`
- Markdown 回归：`artifacts/assembler_boundary_fix/definition_primary_regression_v1.md`
- 集成测试：`tests/test_definition_primary_boundary.py`
- 回归脚本：`scripts/run_definition_primary_boundary_regression_v1.py`

## 验收口径

- definition 类 payload 的 `primary_evidence` 不得出现 `full:passages:*`
- risk-only / ledger-only 对象不得进入 `primary_evidence`
- `passages` 若被保留，只能出现在 `secondary_evidence` 或 `review_materials`
- formula object 命中的方剂题 primary 仍应为 `safe:main_passages:*`
- 典型 exact formula lookup 保持 strong
