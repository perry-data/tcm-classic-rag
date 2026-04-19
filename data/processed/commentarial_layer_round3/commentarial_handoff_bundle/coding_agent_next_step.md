# coding agent 下一轮最小任务建议

## 先做什么
1. 接一个 **source-aware named view**：支持按 commentator / anchor_type / theme tier 过滤。
2. 只消费 handoff bundle，不要直接改原始离线构建逻辑。
3. 在接入层尊重 `multi` 主辅锚与 `theme_display_tier`。

## 后做什么
1. 做 provisional anchor 到真实 canonical `passage_id` 的映射表。
2. 再把 named view / comparison view 接到现有回答链的旁路展示区。

## 验收标准
- 不改 `answer_mode`。
- 不改 `strong/weak/refuse`。
- 不让 commentarial 进入默认 `primary_evidence`。
- named view 查询能正确读取 `primary_anchor_candidates` / `supporting_anchor_candidates`。
- theme 单元默认展示遵守 `theme_display_tier`。

## 哪些东西不能动
- canonical layer 的默认主证据地位
- confidence gate
- primary_evidence 默认逻辑
- 真实 canonical 主库以外的数据契约
