# coding agent 接入约束说明

## 不可突破的边界
1. canonical layer 仍是默认主证据层。
2. commentarial layer 默认不得进入 `primary_evidence`。
3. commentarial layer 默认不参与 confidence gate。
4. `multi` 必须按 `primary_anchor_candidates` / `supporting_anchor_candidates` 处理。
5. `theme` 必须按 `theme_display_tier` 控制默认展示。
6. 默认问法下，commentarial 只允许做 assistive retrieval，并建议折叠显示。

## 接入优先顺序
1. **named view**：例如“刘渡舟怎么看第141条”“郝万山怎么看桂枝汤”。
2. **comparison view**：例如“两家如何解释少阳病”“某个方证两家有什么不同”。
3. **meta learning view**：例如“怎么学《伤寒论》”。
4. **assistive retrieval**：默认问法下可做补充，但必须是保守、折叠、非主证据。

## multi 的接法
- resolved multi：先取 `primary_anchor_candidates` 作为主挂接点，再把 `supporting_anchor_candidates` 作为补充展开。
- `unresolved_multi`：不要强行只挂一个主锚；应优先进入人工复核或只用于折叠展示。

## theme 的接法
- `tier_1_named_view_ok`：可用于 named view / comparison view。
- `tier_2_fold_only`：只用于折叠展示。
- `tier_3_meta_learning_only`：仅用于 meta learning view。
- `tier_4_do_not_default_display`：默认不展示到回答正文。

## 默认问法下的要求
- commentarial 不得覆盖 canonical answer。
- commentarial 不得替代 canonical citation。
- commentarial 如被显示，应在视觉上弱于 canonical layer。
