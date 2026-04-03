# MVP 安全版数据底座补丁说明

## 1. 本轮修复了什么

- 修正了 `chapters.json.role_breakdown`，现已与 `chapter_stats.json.role_breakdown_v2` 和当前 `passages.json` 口径一致。
- 生成了新的 safe 数据包：`dist/zjshl_dataset_v2_mvp_safe.zip`。
- `main_passages.json` 已从 1212 条收缩为 777 条，其中 `retrieval_primary = true` 的主条为 666 条。
- `chunks.json` 已从 1119 条收缩为 583 条，默认仅保留适合 MVP 主检索层的切片。

## 2. 本轮隔离了什么

- `annotation_links.json` 已在 safe 版中默认停用，文件内容置空。
- `annotations.json` 与 `passages.json` 中注解类记录的 `anchor_passage_id` 已清空，避免未复核挂接关系被下游误用。
- `ambiguous_passages.json` 对应的高风险主条不再进入 `main_passages.json`，对应高风险切片也不再进入 `chunks.json`。
- 过短 chunk（长度小于 20）已从 safe 版 `chunks.json` 中移除。
- 过短但非高风险的主条未直接删除，而是保留在 `main_passages.json` 中并降为 `retrieval_primary = false`，仅作次级回查，不作默认主证据。

## 3. 哪些问题仍然保留到后续版本

- 注解挂接层没有在本轮恢复启用。原因不是缺文件，而是可靠性仍不足；后续需要人工复核或重跑更稳妥的 link 生成逻辑。
- `passages.json` 仍保留全量文本总账，其中包括低置信度与过短条目。这是有意保留的底账，不代表这些记录在 MVP 中应直接参与检索。
- `aliases.json` 规模仍然较小，本轮未扩充术语映射表。
- 低置信度条目清单 `ambiguous_passages.json` 仍需后续人工校对，但本轮已将其从 MVP 主检索层隔离。

## 4. annotation_links 策略

- MVP 默认不启用 annotation_links 参与证据展示。
- 已确认错挂的 6 条 link 仍以补丁说明为准记录修正目标，但不在 safe 包中启用。
- 这样做的原因是：当前 link 层不是“少量脏点”，而是存在批量疑似风险；在未完成系统性复核前，整体停用比局部带病启用更安全。

## 5. ambiguous_passages 策略

- `ambiguous_passages.json` 保留原清单，用于后续人工复核。
- 这些高风险 passage 默认不进入 safe 版 `main_passages.json`。
- 任何引用到这些 passage 的 chunk 也不进入 safe 版 `chunks.json`。

## 6. 短文本策略

- `chunks.json`：采用“过滤”策略，长度小于 20 的切片不进入 safe 版主检索层。
- `main_passages.json`：采用“保留但降级”策略，长度小于 20 且非 ambiguous 的主条保留，但 `retrieval_primary = false`。
- 这样做是为了兼顾两点：一方面降低检索噪声，另一方面不直接丢失简短而可能有价值的原文证据。

## 7. 为什么这份 safe 版适合 MVP 使用

- 它保留了全量文本底账，因此后续数据库阶段仍有完整源数据可导入和核对。
- 它默认屏蔽了最危险的证据风险，即错误注解挂接。
- 它把低置信度主条和相关切片从 MVP 默认主检索层中剥离，避免把未验明的内容直接送入系统。
- 它对短 chunk 做了直接过滤，使第一版检索输入更稳定；同时对短主条采用降级而非删除，避免证据层过度收缩。

## 8. 最终判断

**这份 safe 数据包可以进入数据库实现阶段。**

前提是后续数据库实现应以 safe 包中的策略为准：

1. 默认不启用 `annotation_links.json`。
2. 主检索层优先使用 safe 版 `chunks.json`。
3. 主证据层优先使用 safe 版 `main_passages.json` 中 `retrieval_primary = true` 的记录。
4. `ambiguous_passages.json` 仅作复核清单，不作默认主证据来源。
