# 标注规范 v1

- 文档版本：v1
- 文档日期：2026-04-06
- 文档定位：定义 goldset 的人工标注规则与引用核对口径

## 1. 标注对象

每条标注对象是一条“问题样本”，目标是为后续 retrieval 评估、citation 核对和 `answer_mode` 判断提供统一依据。

每条样本至少填写：

1. `question_id`
2. `query`
3. `question_type`
4. `expected_mode`
5. `gold_record_ids`
6. `gold_passage_ids`
7. `gold_evidence_spans`
8. `annotation_notes`
9. `citation_check_required`

## 2. question_type 标注规则

按当前正式系统边界，统一使用以下五类：

| question_type | 何时使用 |
| --- | --- |
| `source_lookup` | 问原文、出处、方文、条文位置 |
| `meaning_explanation` | 问某句、某术语、某条文表达的含义 |
| `general_overview` | 问总体情况、处理思路、有哪些分支 |
| `comparison` | 明确比较两个方名或两条证据对象 |
| `refusal` | 书外问题、超边界问题、当前明确不支持的问题 |

若问题同时包含多个意图，优先按最终判分目标选择主类型；不要一题多标。

## 3. expected_mode 标注规则

### 3.1 `strong`

当问题存在稳定主证据，且当前系统按正式边界可以直接回答时，标为 `strong`。

典型特征：

1. 至少有 1 条可作主依据的 `main_passages`。
2. 结论可以直接回指条文或方文。
3. 不需要依赖纯注解或风险材料才能成立。

### 3.2 `weak_with_review_notice`

当问题可部分回答，但强证据不足时，标为 `weak_with_review_notice`。

典型特征：

1. 只能依赖 `secondary_evidence` 或 `review_materials`。
2. 主题过宽、分支不完整，不能强答。
3. 当前系统应显式提示“需核对”。

### 3.3 `refuse`

当问题无书内依据、超出功能边界，或当前比较请求不受支持时，标为 `refuse`。

典型特征：

1. 问题不在《伤寒论》范围内。
2. 问题要求系统进行优劣判断、诊疗判断等边界外能力。
3. 当前系统即使能检索到相关词面，也不应组织成正式答案。

## 4. 标准依据怎么写

### 4.1 `gold_record_ids`

`gold_record_ids` 填“允许视为正确命中或正确引用的具体记录 ID”。

填写规则：

1. 优先填当前正式链路真实会返回的记录 ID。
2. 若同一 canonical passage 在 safe/full 中都存在，只把当前评估要接受的对象层写进去。
3. 对 `strong` 题，优先写主引用应落到的 `main_passages`。
4. 对 `weak` 题，可写辅助条文、注解和必要的 review 材料。
5. 对 `refuse` 题，留空数组。

### 4.2 `gold_passage_ids`

`gold_passage_ids` 填 canonical passage ID，例如 `ZJSHL-CH-010-P-0145`。

填写规则：

1. 用于把 safe/full 等对象层折叠到同一条底层 passage。
2. 用于后续做 `Hit@K`、`Recall@K` 一类 retrieval 统计。
3. 对 `refuse` 题留空。

## 5. 证据片段怎么写

`gold_evidence_spans` 用来记录 1-3 段最核心证据片段，原则上直接摘录原文，不做改写。

填写规则：

1. `quote` 必须来自实际条文或注解文本，尽量保持原始表述。
2. `record_id` 对应当前引用对象；`passage_id` 对应 canonical passage。
3. `evidence_role` 按 `primary / secondary / review` 填写。
4. `rationale` 要说明这段证据为什么构成 gold。
5. 对 `strong` 题优先写主证据；对 `weak` 题写促成弱回答的辅助证据；对 `refuse` 题留空。

## 6. 什么算“引用正确”

满足以下条件时，记为“引用正确”：

1. citation 对应的 `record_id` 落在 `gold_record_ids` 中；或
2. citation 不同于 `gold_record_ids`，但能稳定映射到同一 `gold_passage_ids`，且其引用角色没有越级；并且
3. 该 citation 确实支持当前答案中的对应结论。

## 7. 什么算“错引”

出现以下任一情形，记为“错引”：

1. citation 不在 `gold_record_ids`，也不对应任何 `gold_passage_ids`。
2. citation 文本与答案主张不匹配。
3. 只能作 `secondary` 或 `review` 的材料被当作 `primary` 使用。
4. 比较题里只引用了其中一方，却写成双方差异已被证实。

## 8. 什么算“无证据断言”

出现以下任一情形，记为“无证据断言”：

1. 没有 gold 证据却给出确定性答案。
2. 证据只支持“可疑/需核对”，系统却输出 `strong`。
3. `refusal` 边界内的问题被系统改写成看似合理的强回答。

## 9. 推荐标注流程

1. 先判断问题属于哪一类 `question_type`。
2. 再判断当前正式系统最合理的 `expected_mode`。
3. 回填 `gold_record_ids` 与 `gold_passage_ids`。
4. 从原文中摘录 `gold_evidence_spans`。
5. 决定 `citation_check_required` 是否为 `true`。
6. 在 `annotation_notes` 中写清楚该题最关键的判分点。

## 10. 分歧处理原则

若两位标注者对某题存在分歧，按以下顺序处理：

1. 先看当前正式系统边界，而不是按理想功能判断。
2. 先看条文能否直接支持结论，再看注解是否只能作辅助。
3. 对存在明显争议的题，优先保守标为 `weak_with_review_notice` 或暂不收入种子集。

该原则的核心是：seed goldset 先追求口径稳定，再追求题量扩张。
