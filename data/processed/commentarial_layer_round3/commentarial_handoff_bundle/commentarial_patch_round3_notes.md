# commentarial patch round3 notes

本轮只做极小补丁与交接打包。

## 变更点
1. 为 `multi` 增加主锚 / 辅锚结构。
2. 为 `theme` 增加 `theme_display_tier`。
3. 为 `commentarial_anchor_links.jsonl` 增加 `anchor_role` / `anchor_priority_rank` / `anchor_priority_mode`。
4. 更新 `manual_review_queue.json`，加入 `unresolved_multi`。
5. 生成 handoff bundle、manifest、约束说明和下一步建议。

## 未变更内容
- 没有接入真实 canonical 主库。
- 没有伪造真实 `passage_id`。
- 没有改前端 / API / `answer_mode` / `strong-weak-refuse`。
- 没有让 commentarial layer 进入 `primary_evidence`。
