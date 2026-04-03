# zjshl_dataset_v2 开发前验收报告

## 1. 验收范围

- 结构化数据包：`/Users/man_ray/大四毕业论文/数据/zjshl_dataset_v2.zip`
- 原始回查来源：`/Users/man_ray/Projects/Python/tcm-classic-rag/data/raw/《注解伤寒论》.zip`
- 验收对象限定为：books / chapters / passages / main_passages / annotations / annotation_links / chunks / aliases / ambiguous_passages / chapter_stats / README_parse_report_v2.md
- 本轮只做开发前验收，不改写任何原始数据文件。

## 2. 核查方法

1. 对数据包中的 11 个核心文件做存在性、可读性和 JSON / Markdown 合法性检查。
2. 对各 JSON 文件做结构检查：记录数、必要字段、空值、主键唯一性。
3. 对引用关系做一致性检查：book / chapter / passage / annotation / chunk 的引用闭合情况。
4. 将 `passages.json` 的每条记录回指到原始 `《注解伤寒论》.zip` 中对应 `source_file + source_item_no`，核验文本是否一致。
5. 对 `main_passages`、`annotations`、`chunks` 各做 10 条等距抽样，并结合上下文复核注解挂接是否合理。
6. 做检索前预验收：主检索语料、chunk 粒度、别名表覆盖度、低置信度占比。

## 3. 文件级完整性结果

| 文件 | 结果 | 说明 |
| --- | --- | --- |
| books.json | 通过 | 记录数 1 |
| chapters.json | 通过 | 记录数 29 |
| passages.json | 通过 | 记录数 1841 |
| main_passages.json | 通过 | 记录数 1212 |
| annotations.json | 通过 | 记录数 629 |
| annotation_links.json | 通过 | 记录数 619 |
| chunks.json | 通过 | 记录数 1119 |
| aliases.json | 通过 | 记录数 46 |
| ambiguous_passages.json | 通过 | 记录数 450 |
| chapter_stats.json | 通过 | 记录数 29 |
| README_parse_report_v2.md | 通过 | Markdown 可读取 |

说明：所有核心文件均存在，且能从 `zjshl_dataset_v2.zip` 中直接读取；JSON 语法合法，README 可正常解析为 Markdown 文本。

## 4. 各核心文件检查结果

### 4.1 books.json

- 记录数：1
- `source_file_count` = 15，与原始 zip 内 15 个 md 文件一致。
- 结构完整，无空值、无重复主键。

### 4.2 chapters.json

- 记录数：29
- `book_id` 引用闭合：True
- `passage_count` 与 passages 实际统计一致：True
- 发现问题：`role_breakdown` 与 v2 实际 `text_role` 分布不一致的章节数为 27 / 29。
- 结论：章节主键和范围边界可用，但章节角色统计字段仍带有旧口径，不应直接作为 v2 的事实来源。

### 4.3 passages.json

- 记录数：1841
- 主键唯一：True
- 原始 md 精确回查：1841 / 1841 条完全一致。
- 缺失原始来源映射：0
- 结论：作为总表，文本回溯性良好，可作为后续核验基线。

### 4.4 main_passages.json

- 记录数：1212
- 均为 `passages.json` 子集：True
- `retrieval_primary = true` 全量成立：True
- 短文本（<20 字）数量：142 / 1212（11.72%）
- 低置信度主条：435 / 1212（35.89%）
- 结论：可作为主检索语料的基础，但需要先处理低置信度条目和过短条目。

### 4.5 annotations.json

- 记录数：629
- 均为 `passages.json` 子集：True
- 未挂接主条的记录：10 条，均为前言 / 卷首 / 附录类记录。
- 结论：注解文本本身可回溯、可读取，但是否正确挂接到正文需要结合 `annotation_links.json` 进一步判断。

### 4.6 annotation_links.json

- 记录数：619
- `from_passage_id` 全部可回指 annotation：True
- `to_passage_id` 全部可回指 main passage：True
- `anchor_passage_id` 与 link 一致：True
- 已人工确认错挂：6 条。
- 启发式疑似错挂：105 条。
- 结论：ID 级引用是闭合的，但语义级挂接不可靠，不能直接把该文件当作“已验明正确”的注解关联层。

### 4.7 chunks.json

- 记录数：1119
- `source_passage_ids` 全部可回指 passages：True
- chunk 与来源 passage 拼接精确一致：1119 / 1119
- 短 chunk（<20 字）数量：132 / 1119（11.80%）
- 受低置信度 passage 影响的 chunk：435 / 1119（38.87%）
- 结论：chunk 可追溯性良好，但直接入检索前仍应过滤或标记高风险数据。

### 4.8 aliases.json

- 记录数：46
- canonical_term 出现在主语料中的数量：45 / 46
- alias 文面直接出现在主语料中的数量：22 / 46
- 结论：可作为 MVP 的基础术语辅助层，但规模偏小，只能视为补充，不足以支撑完整术语归一。

### 4.9 ambiguous_passages.json

- 记录数：450 / 1841（24.44%）
- 其中进入 `main_passages` 的数量：435
- 结论：低置信度规模偏高，会直接影响第一版检索与证据展示的可信度。

### 4.10 chapter_stats.json

- 记录数：29
- 与 passages 实际角色统计一致：True
- 结论：chapter_stats.json 比 chapters.json.role_breakdown 更可信，应优先作为 v2 章节统计依据。

## 5. 引用关系一致性

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| chapters -> books | 通过 | 未发现悬空 book 引用 |
| passages -> chapters | 通过 | 未发现悬空 chapter 引用 |
| main_passages / annotations -> passages | 通过 | 二者均为 passages 子集 |
| annotation_links -> annotations / main_passages | 部分通过 | ID 级闭合，但存在语义错挂 |
| chunks -> passages | 通过 | 未发现孤儿 source_passage_ids |
| anchor_passage_id -> annotation_links | 通过 | 当前 link 与 anchor 字段一致 |

判断：数据包的“引用闭合”没有断裂，但“语义挂接正确性”未通过正式验收，主要问题集中在 annotation link 层。

## 6. 内容抽样核验

- 正文主条抽样：10 条，文本精确一致 10 / 10
- 注解条目抽样：10 条，文本精确一致 10 / 10
- 检索切片抽样：10 条，chunk 与来源拼接一致 10 / 10
- 补充定向复核：对疑似错挂的 annotation link 做上下文核验，确认至少 6 条链接存在正文挂接错误。

### 6.1 抽样摘要

| 类别 | 样本数 | 通过数 | 说明 |
| --- | --- | --- | --- |
| main_passages | 10 | 10 | source_file + source_item_no 可精确回查 |
| annotations | 10 | 10 | 注解文本本身与原始 md 一致 |
| chunks | 10 | 10 | chunk_text 等于来源 passage 串接结果 |

### 6.2 已确认的错挂样本

| link_id | 源条目 | 当前目标 | 应指向 | 说明 |
| --- | --- | --- | --- | --- |
| LINK-00033 | 1《卷一》.md#73 | ZJSHL-CH-003-P-0072 | ZJSHL-CH-003-P-0074 | 条 73 的注解内容解释“属腑/溲数/便难”，应对应条 74，不应挂到条 72。 |
| LINK-00034 | 1《卷一》.md#77 | ZJSHL-CH-003-P-0076 | ZJSHL-CH-003-P-0078 | 条 77 的“肺先绝也”摘要语应引向条 78 的肺绝解释，不应挂到条 76。 |
| LINK-00036 | 1《卷一》.md#81 | ZJSHL-CH-003-P-0080 | ZJSHL-CH-003-P-0082 | 条 81 的“肝绝也”摘要语应引向条 82 的肝绝解释，不应挂到条 80。 |
| LINK-00037 | 1《卷一》.md#83 | ZJSHL-CH-003-P-0082 | ZJSHL-CH-003-P-0084 | 条 83 的“脾绝也”摘要语应引向条 84 的脾绝解释，不应挂到条 82。 |
| LINK-00038 | 1《卷一》.md#85 | ZJSHL-CH-003-P-0084 | ZJSHL-CH-003-P-0086 | 条 85 的“肾绝也”摘要语应引向条 86 的肾绝解释，不应挂到条 84。 |
| LINK-00039 | 1《卷一》.md#87 | ZJSHL-CH-003-P-0086 | ZJSHL-CH-003-P-0088 | 条 87 的阴阳先绝摘要语应引向条 88 的解释，不应挂到条 86。 |

## 7. 检索可用性预验收

- `main_passages.json`：文本回溯性和结构完整性足够好，可以作为主检索语料候选。
- `chunks.json`：来源可追溯，方剂类已按 bundle 合并，适合作为检索切片候选。
- `aliases.json`：可作为基础别名辅助，但量级偏小，只适合 MVP 的轻量扩展，不宜过度依赖。
- 明显风险 1：过短检索单元仍较多，主条 142 条、chunk 132 条低于 20 字。
- 明显风险 2：低置信度主条 435 条直接进入主库，影响 435 个 chunk。
- 明显风险 3：若在证据展示链中使用 `annotation_links.json`，会把错挂注解呈现为“有依据”的解释，这是比缺失更危险的问题。

结论：若只看 `main_passages + chunks`，本包已经接近可用；但若要把它作为正式开发底座，并包含注解解释与证据链展示，则必须先做局部修复。

## 8. 低置信度与风险评估

- `ambiguous_passages.json` 规模：450 条，占全部 passages 的 24.44%。
- 其中进入主检索层的比例：435 / 1212（35.89%）。
- 受影响 chunk 占比：435 / 1119（38.87%）。
- 对 MVP 的影响：若不做限制，第一版就会把低置信度内容直接送入检索与证据展示，增加误检和错误引用风险。
- 建议：第一版开发中默认排除或显式标注高风险数据，不把低置信度 passage 当作默认主证据。

## 9. 发现的问题与分级

### 9.1 严重

- `annotation_links.json` 存在已确认的错误挂接，至少 6 条会把注解挂到错误正文。这直接影响“证据溯源”可信度，必须在正式开发前修正或暂时下线注解挂接层。

### 9.2 中等

- `chapters.json.role_breakdown` 在 27 个章节中仍是旧口径统计，容易误导后续开发与论文写作。
- `ambiguous_passages.json` 规模偏高，且有 435 条直接进入主检索层，说明主库中存在较多低置信度内容。
- 启发式检查又标出 105 条疑似错挂 link，说明 annotation link 可能不是个别脏点，而是存在批量风险。

### 9.3 轻微

- 过短主条 / chunk 较多（142 / 132），会拖低检索判别力，但可以通过过滤或合并缓解。
- 10 条前言 / 卷首 / 附录类 annotation 未挂接主条，建议在约定中明确其例外处理。

## 10. 结论

**结论：需局部修复后再开发。**

理由如下：

- 数据包的文本底座本身质量较好。`passages.json` 与原始 md 的逐条回查结果为 1841 / 1841 精确一致，`chunks.json` 也能完整回指来源 passage。
- 但 annotation link 层没有通过正式验收。虽然引用能闭合，但已确认存在错挂，这与项目的“证据溯源”目标直接冲突。
- 因此，不建议把当前整包不加处理地直接作为正式开发底座；建议先做局部修复，再进入后续系统开发。

建议的开发前处置顺序：

1. 修复或临时停用 `annotation_links.json` 中的错挂记录。
2. 修正 `chapters.json.role_breakdown`，统一章节统计口径。
3. 在第一版检索构建时排除或标记 `ambiguous_passages.json` 对应的主条和 chunk。
4. 对过短 chunk 增加过滤或邻近合并规则。
