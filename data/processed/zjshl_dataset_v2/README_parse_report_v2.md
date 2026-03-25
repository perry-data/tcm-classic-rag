# 注解伤寒论数据集 v2 解析说明

## 本次改进
- 在 v1 基础上，将 mixed passage 进一步细分为：`main_text`、`commentary`、`formula_heading`、`formula_ingredients`、`formula_method`、`formula_commentary`、`appendix_*` 等角色。
- 新增 `main_passages.json`：更适合后续 RAG 主库。
- 新增 `annotations.json` 与 `annotation_links.json`：保存注解，并尽量挂接到对应正文/方剂。
- `chunks.json` 采用“双策略”：正文单条 chunk；方剂按标题+组成+煎服法合并成 `formula_bundle`。

## 注意
- 由于原始 md 为“正文 + 成无己注解 + 校勘夹注”混排，v2 仍然是**规则解析版**，不是百分之百人工校勘版。
- 共生成 passages 1841 条，其中 main_passages 1212 条，annotations 629 条，annotation_links 619 条，chunks 1119 条。
- 低置信度条目 450 条，已单独输出到 `ambiguous_passages.json`，建议优先人工复核。

## 角色统计
- appendix_formula_heading: 24
- appendix_formula_material: 6
- appendix_formula_method: 8
- appendix_intro: 1
- appendix_text: 1
- commentary: 581
- formula_commentary: 38
- formula_heading: 86
- formula_ingredients: 42
- formula_method: 38
- front_matter: 2
- main_text: 1008
- preface_paragraph: 6

## 建议用法
- 做检索主库：优先使用 `main_passages.json` + `chunks.json`。
- 做证据展示：回答时展示 `main_passages.json` 中的正文/方剂；需要解释时再回查 `annotations.json`。
- 做人工校对：优先审查 `ambiguous_passages.json`。
