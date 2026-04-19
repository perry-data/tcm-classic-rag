# commentarial handoff bundle README

这是 commentarial layer 的第三轮 handoff 版本。

## 本 bundle 的定位
- 只服务于 **下一轮 coding agent 的安全接入准备**。
- 不代表 commentarial layer 已经可以进入默认 `primary_evidence`。
- 不代表可以绕过 canonical layer。

## 你会拿到什么
1. 已补丁的数据文件：`commentarial_units.jsonl` / `commentarial_anchor_links.jsonl` / `manual_review_queue.json`
2. 已有的标签、用例、审计与验收文件
3. 接入约束说明与下一步建议
4. 更新后的测试器
5. 一个 manifest 与 zip 打包件

## 本轮新增的关键结构
- `multi`：新增 `primary_anchor_candidates` / `supporting_anchor_candidates` / `anchor_priority_mode`
- `theme`：新增 `theme_display_tier`
- `links`：为 multi 补充 `anchor_role` / `anchor_priority_rank`

## 使用提醒
- `PASSAGE_NO:*` / `THEME:*` 仍然是 provisional anchors，尚未回填真实 canonical `passage_id`。
- `unresolved_multi` 不能在接入层被强行当作单主锚使用。
- `tier_4_do_not_default_display` 不能默认展示到回答正文。
