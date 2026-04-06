# Comparison Answer Spec

## 1. 支持的问题类型

当前只补齐最小的“比较类研读问答”能力，支持以下问法：

- `A 和 B 的区别是什么`
- `A 与 B 有何不同`
- `A 和 B 有什么异同`
- `A 比 B 多了什么 / 少了什么`
- 包含 `区别 / 不同 / 异同 / 比较 / 相比 / 何异 / 差别 / 多了什么 / 少了什么` 的同类问法

明确不支持：

- `哪个好 / 谁更好 / 更适合 / 优劣` 这类优劣判断
- 三个及以上对象同时比较
- 非 pairwise comparison

## 2. 当前支持的实体范围

- 当前优先支持 `方名 vs 方名`
- 识别方式以现有 safe `main_passages` 中可稳定抽出的方名标题为主
- 允许极小量别名归一：
  - `厚朴 -> 浓朴`
  - `杏仁 / 杏人 -> 杏子`
  - `方` 后缀有无不影响识别

当前不做：

- 多书比较
- 非方名对象的大范围泛化
- 同时比较方名、概念、注解对象的混合场景

## 3. 比较流程说明

1. 先识别比较意图。
2. 在 query 中抽取两个候选方名，并归一到当前系统内的 canonical formula title。
3. 对 A、B 分别单独调用现有 `HybridRetrievalEngine.retrieve(...)`。
4. 每一侧优先找：
   - 该方对应的 `main_passages` 方文标题，作为 strong 候选主依据
   - 若能找到 safe `main_passages` 中点名该方的相关条文，则作为 `secondary_evidence`
   - 若只有 `passages / ambiguous_passages` 能提供相关条文，则只进入 `review_materials`
5. 在 answer assembler 内部做差异整理，输出一句总述 + 2~4 条结构化差异。
6. 外部接口保持不变，仍然只返回既有 answer payload。

## 4. 比较维度说明

本轮最小先整理以下维度：

- 条文/出处线索
  - 方文位于哪里
  - 若有相关条文，条文位于哪一章
- 方名中的加减关系
  - 是否都写明“于某方内，加 / 去 …”
  - 是否共享同一基础方
- 药味层面的显式差异
  - 只整理方文里明写的加味 / 去味
- 文本上可见的证候 / 语境关键词差异
  - 只使用可回指到相关条文的可见文本
  - 若只能从 review 层看到，只能作为核对线索，不能伪装成强证据

## 5. strong / weak_with_review_notice / refuse 判定逻辑

### 5.1 `strong`

同时满足以下条件时：

- 两个对象都能稳定识别为方名
- 两侧都能稳定找到对应方文的 `main_passages`
- 至少能整理出 2 条结构化差异
- 若 query 只是泛问“区别 / 不同 / 异同 / 多了什么 / 少了什么”，允许主结论主要建立在两侧方文上
- 若某一侧语境只在 review 层可见，仍可作为补充线索写入答案，但必须保留 review_notice 与 citations

### 5.2 `weak_with_review_notice`

出现以下任一情况时降级：

- 两个对象虽然识别成功，但用户明确追问 `证候 / 主治 / 条文语境`，而两侧都没有 safe 正文条文可稳定支撑
- 两侧方文能比，但语境差异只能部分依赖 review 层
- 比较结论无法被包装成确定性 strong 答案

弱答时继续遵守原合同：

- `primary_evidence` 为空
- 方文降级后进入 `secondary_evidence`
- `passages / ambiguous_passages` 继续只进 `review_materials`

### 5.3 `refuse`

出现以下情况时拒答：

- 两个对象无法稳定识别
- 一次出现两个以上对象
- 问法超出本轮支持范围，例如 `哪个好`
- 无法形成可靠的 pairwise comparison

## 6. 分层与合同约束

本轮继续保持既有 evidence gating：

- `chunks` 不直接进入 `primary_evidence`
- `annotations` 不进入 `primary_evidence`
- `passages / ambiguous_passages` 不越级进入 `primary_evidence`
- `annotation_links` 继续禁用
- `POST /api/v1/answers` 不变
- 请求体仍然只接收 `query`
- answer payload 顶层字段不变

## 7. 已知限制

- 仍然只支持两个对象的最小比较，不支持三方或多方比较
- 当前优先解决“方名 vs 方名”，没有泛化到概念、人物、条文主题等实体
- 方名别名归一只做了极小映射，不是完整别名系统
- 语境差异仍然严重依赖现有 safe / full 分层；若某一侧只有 review 材料，答案必须降级或显式保留核对提示
- 仍然没有复杂结构化表格前端，只是沿用现有 payload + 单页展示
