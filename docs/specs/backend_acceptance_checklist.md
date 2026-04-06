# Backend Acceptance Checklist

## 1. 文档目标

本文件用于回答一个明确问题：

什么情况下，当前《伤寒论》RAG 后端才算稳定到可以开始前端开发。

## 2. 冻结样例

以下 3 个 query 是当前后端封板的冻结样例，后续每次回归都至少要检查它们：

| query | expected mode | 验收重点 |
| --- | --- | --- |
| `黄连汤方的条文是什么？` | `strong` | 主证据是否精确；黄连汤补丁是否不回归 |
| `烧针益阳而损阴是什么意思？` | `weak_with_review_notice` | 是否保持弱回答与核对提示 |
| `书中有没有提到量子纠缠？` | `refuse` | 是否保持统一拒答结构 |

## 3. 冻结样例验收项

### 3.1 `黄连汤方的条文是什么？`

- [ ] `answer_mode` 为 `strong`
- [ ] `primary_evidence` 非空
- [ ] `primary_evidence` 仅包含 `main_passages`
- [ ] `primary_evidence` 不包含 `chunks`
- [ ] `primary_evidence` 不包含 `annotations`
- [ ] `primary_evidence` 不包含 `passages`
- [ ] `primary_evidence` 不包含 `ambiguous_passages`
- [ ] 黄连汤方主证据精度补丁不回归
- [ ] “葛根黄芩黄连汤方”相关主条未重新混入 `primary_evidence`
- [ ] `secondary_evidence` 与 `review_materials` 如存在，必须保持分层，不得挤占主证据语义
- [ ] `citations` 主要对应 `primary_evidence`

建议同时比对当前冻结主证据 ID：

- `safe:main_passages:ZJSHL-CH-010-P-0145`
- `safe:main_passages:ZJSHL-CH-010-P-0146`
- `safe:main_passages:ZJSHL-CH-010-P-0147`

### 3.2 `烧针益阳而损阴是什么意思？`

- [ ] `answer_mode` 为 `weak_with_review_notice`
- [ ] `primary_evidence` 为空
- [ ] `review_notice` 有值
- [ ] `answer_text` 使用弱表述，不伪装成确定性结论
- [ ] `secondary_evidence` 与 `review_materials` 保持分层展示语义
- [ ] `secondary_evidence` 允许出现 `annotations`
- [ ] `review_materials` 允许出现 `passages` / `ambiguous_passages`
- [ ] `citations` 对应 `secondary_evidence` 与 `review_materials`

### 3.3 `书中有没有提到量子纠缠？`

- [ ] `answer_mode` 为 `refuse`
- [ ] `answer_text` 非空
- [ ] `refuse_reason` 有值
- [ ] `suggested_followup_questions` 非空
- [ ] `primary_evidence` 为空
- [ ] `secondary_evidence` 为空
- [ ] `review_materials` 为空
- [ ] `citations` 为空

## 4. 通用验收项目

除冻结样例外，当前后端还必须同时满足以下通用项目：

- [ ] `mode` 是否正确
- [ ] `primary / secondary / review` 是否分层正确
- [ ] `citations` 是否正确
- [ ] `refuse` 是否正确
- [ ] answer payload 顶层字段是否稳定
- [ ] `annotation_links` 是否继续禁用
- [ ] `chunks` 是否仍只作为召回入口和回指来源，而非主证据
- [ ] `display_sections` 是否继续稳定输出，并与实际字段一致
- [ ] `strong / weak_with_review_notice / refuse` 三模式名称与语义是否稳定
- [ ] 没有擅自改变 `answer_payload_contract.md`

## 5. 运行层验收建议

在工程执行层，建议至少确认以下产物仍可正常生成或已保持一致：

- [ ] `backend/retrieval/hybrid.py` 能产出 `artifacts/hybrid_retrieval_examples.json`
- [ ] `backend/retrieval/hybrid.py` 能产出 `artifacts/hybrid_retrieval_smoke_checks.md`
- [ ] `backend/answers/assembler.py` 能产出 `artifacts/hybrid_answer_examples.json`
- [ ] `backend/answers/assembler.py` 能产出 `artifacts/hybrid_answer_smoke_checks.md`
- [ ] 产物中的三条冻结 query 结果与本清单一致

## 6. 可进入前端的判断标准

只有达到以下条件后，才允许开始前端开发：

- [ ] 三个冻结样例全部通过
- [ ] 三模式行为无回归
- [ ] 主证据分层无回归
- [ ] `annotation_links` 仍然禁用
- [ ] answer payload 顶层字段无漂移
- [ ] 前端将只依赖 `minimal_api_contract.md`，不依赖内部检索细节
- [ ] 本轮没有继续改 Hybrid retrieval / answer assembler 的核心逻辑

判断结论可直接用下面这条规则：

- 只要三条冻结样例、通用验收项、payload 顶层合同三者同时稳定，就可以开始前端开发。
- 如果仍在改 `answer_mode` 语义、证据分层规则或 payload 顶层字段，则不应开始前端开发。

## 7. 本轮 go / no-go 结论口径

本轮的 go / no-go 口径建议固定为：

- `GO`：后端闭环稳定，前端可以按照 `minimal_api_contract.md` 开始联调或先做 mock 接入。
- `NO-GO`：任一冻结样例回归，或 payload 顶层字段发生变更，或证据分层规则被破坏。
