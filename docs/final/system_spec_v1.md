# 基于检索增强生成的中医经典研读支持系统系统规格说明 v1

- 文档版本：v1
- 文档日期：2026-04-06
- 文档定位：当前正式系统定义、合同冻结与后续变更约束
- 使用方式：后续开发、审查、论文映射、答辩口径均应以本文件为正式依据

## 1. 系统范围说明

当前正式系统定义为：一个面向《伤寒论》单书场景的研读支持系统，其正式运行边界是：

`query -> hybrid retrieval -> evidence gating -> answer assembler -> POST /api/v1/answers -> 同源前端单页展示`

系统只负责：

1. 接收问题
2. 检索书内证据
3. 按证据层级组织结果
4. 输出回答、引用和改问建议

系统不负责：

1. 诊疗推断
2. 处方建议
3. 书外知识整合
4. 多轮对话管理

## 2. 当前正式模块清单

当前正式模块分为离线构建模块与在线运行模块。

### 2.1 离线构建模块

| 模块 ID | 模块名 | 责任 |
| --- | --- | --- |
| B1 | 数据验收模块 | 验证结构化数据、错挂风险和可回溯性 |
| B2 | safe 数据底座构建模块 | 生成当前 MVP 使用的安全数据包 |
| B3 | 数据库构建模块 | 构建 SQLite 表、关系表和统一视图 |
| B4 | 向量索引构建模块 | 构建 `chunks` 与 `main_passages` 的 FAISS 索引 |

### 2.2 在线运行模块

| 模块 ID | 模块名 | 责任 |
| --- | --- | --- |
| R1 | Hybrid Retrieval Engine | 执行 sparse recall、dense recall、RRF、rerank |
| R2 | Evidence Gating | 将候选分入 `primary / secondary / review` |
| R3 | Answer Assembler | 负责问题分流、回答编排、引用生成 |
| R4 | Minimal API | 暴露 `POST /api/v1/answers` 并返回稳定 payload |
| R5 | Frontend SPA | 展示回答、证据、引用与改问建议 |

说明：

- `backend/` 目录中的空骨架文件当前不是正式运行模块。
- `annotation_links` 当前不是正式系统的一部分。

## 3. 模块职责定义

### 3.1 B1 数据验收模块

职责：

1. 检查数据包结构完整性
2. 检查引用闭合性
3. 识别 `annotation_links` 错挂风险
4. 输出是否适合进入开发的结论

不负责：

- 运行期检索
- 在线回答

### 3.2 B2 safe 数据底座构建模块

职责：

1. 生成 safe `main_passages`
2. 生成 safe `chunks`
3. 隔离 ambiguous 风险主条
4. 默认停用 `annotation_links`

### 3.3 B3 数据库构建模块

职责：

1. 建立运行时事实表
2. 建立 `record_chunk_passage_links`
3. 建立 `vw_retrieval_records_unified`
4. 把分层策略翻译为数据库字段和约束

### 3.4 B4 向量索引构建模块

职责：

1. 对 `records_chunks` 建立 dense index
2. 对 `records_main_passages` 建立 dense index
3. 输出索引 meta 和构建报告

### 3.5 R1 Hybrid Retrieval Engine

职责：

1. 执行 SQLite FTS5/BM25 sparse recall
2. 执行 FAISS dense recall
3. 执行 RRF fusion
4. 执行 Cross-Encoder rerank
5. 对 `chunks` 命中进行回指

### 3.6 R2 Evidence Gating

职责：

1. 根据对象类型和层级，把结果分入三槽位
2. 执行 `strong / weak_with_review_notice / refuse` 裁决

### 3.7 R3 Answer Assembler

职责：

1. 识别标准问、总括问、比较问
2. 生成模板化回答文本
3. 生成 citations
4. 生成 `display_sections`

### 3.8 R4 Minimal API

职责：

1. 接收 HTTP 请求
2. 校验请求体
3. 返回稳定 answer payload
4. 提供同源静态资源

### 3.9 R5 Frontend SPA

职责：

1. 发送 `POST /api/v1/answers`
2. 根据 `answer_mode` 选择展示分支
3. 独立显示主依据、补充依据、核对材料、引用和改问建议

## 4. 模块间调用关系

### 4.1 离线调用关系

```text
B1 数据验收
  -> B2 safe 数据底座构建
  -> B3 SQLite 数据库构建
  -> B4 FAISS 索引构建
```

### 4.2 在线调用关系

```text
R5 Frontend SPA
  -> R4 Minimal API
     -> R3 Answer Assembler
        -> R1 Hybrid Retrieval Engine
           -> R2 Evidence Gating
```

### 4.3 问题类型分流关系

```text
query
  -> comparison detect
     -> comparison path
  -> general detect
     -> general path
  -> fallback
     -> standard path
```

## 5. 当前关键合同

### 5.1 API Contract

当前 API 合同已冻结为：

- Method：`POST`
- Path：`/api/v1/answers`
- Request Body：

```json
{
  "query": "..."
}
```

冻结要求：

1. 请求体当前只允许依赖 `query`
2. 前端不得发送内部检索参数
3. `refuse` 仍返回 `200`

### 5.2 Answer Payload Contract

当前顶层字段已冻结为：

1. `query`
2. `answer_mode`
3. `answer_text`
4. `primary_evidence`
5. `secondary_evidence`
6. `review_materials`
7. `disclaimer`
8. `review_notice`
9. `refuse_reason`
10. `suggested_followup_questions`
11. `citations`
12. `display_sections`

冻结要求：

1. 不得擅自增删或重命名这些字段
2. 前端展示语义必须继续依赖这些字段
3. `display_sections` 的 section 语义必须稳定

### 5.3 Evidence 分层规则

当前 evidence 分层规则已冻结为：

| 槽位 | 允许对象 | 禁止对象 |
| --- | --- | --- |
| `primary_evidence` | 合规 `main_passages` | `chunks`、`annotations`、`passages`、`ambiguous_passages` |
| `secondary_evidence` | 降级主条、`annotations` | `chunks` 直接进入 |
| `review_materials` | `passages`、`ambiguous_passages` | 升格为主依据 |

同时继续冻结：

1. `annotation_links` 禁用
2. `chunks` 只能召回与回指
3. `weak_with_review_notice` 模式下 `primary_evidence` 必须为空
4. `refuse` 模式下三槽位都应为空

## 6. 当前问题类型分层

### 6.1 条文/出处类

定义：

- 用户直接问某条、某方、某出处、某原文

当前行为：

- 优先走标准路径
- 若主条稳定命中，则返回 `strong`

当前状态：处理较好

### 6.2 含义解释类

定义：

- 用户问某句、某术语、某条文表达“是什么意思”

当前行为：

- 若只有注解或风险材料，则返回 `weak_with_review_notice`
- 不允许把注解包装成主依据

当前状态：部分处理

### 6.3 泛问/总括类

定义：

- 用户问“X 应该怎么办”“X 有哪些情况”

当前行为：

1. 识别 general question trigger
2. 做 topic 级检索
3. 组织 2-4 条最小分支
4. 分支不足则降级

当前状态：最小可用

### 6.4 比较类

定义：

- 用户问两个对象的区别、不同、异同、多了什么、少了什么

当前行为：

1. 只支持两个对象
2. 当前优先支持方名 vs 方名
3. 优劣判断类直接拒答

当前状态：最小可用

### 6.5 无证据拒答类

定义：

- 查询超出书内证据范围，或证据槽位均为空

当前行为：

- 返回 `refuse`
- 给出 `refuse_reason`
- 给出改问建议

当前状态：处理较好

## 7. 当前系统行为规则

以下规则视为正式系统行为，不得随意改变：

1. 系统定位始终是研读支持，不是诊疗。
2. 回答强度由 `answer_mode` 决定，不由 HTTP 状态码决定。
3. `strong` 必须建立在主证据上。
4. `weak_with_review_notice` 必须显式提醒用户核对。
5. `refuse` 必须给出拒答原因和改问建议。
6. `primary_evidence`、`secondary_evidence`、`review_materials` 必须分区展示。
7. `chunks` 不得越级成主证据。
8. `annotation_links` 未复核前不得恢复。
9. 问题过宽时，降级优先于强答。
10. 当前所有输出都应可解释为“书内证据整理”，而不是“模型自主判断”。

## 8. 当前冻结样例与回归基线

### 8.1 一级冻结基线

以下三条是当前必须长期保留的一级回归基线：

| Query | 期望模式 | 必查项 |
| --- | --- | --- |
| `黄连汤方的条文是什么？` | `strong` | 主证据精度、主条 ID、引用稳定 |
| `烧针益阳而损阴是什么意思？` | `weak_with_review_notice` | 主依据为空、核对提示存在 |
| `书中有没有提到量子纠缠？` | `refuse` | 统一拒答结构、证据槽位全空 |

### 8.2 二级扩展基线

以下能力已进入当前版本，建议作为长期保留的二级回归基线：

| Query | 期望模式 | 作用 |
| --- | --- | --- |
| `太阳病应该怎么办？` | `strong` | 验证总括类最小分支整理 |
| `六经病应该怎么办？` | `weak_with_review_notice` | 验证总括类降级 |
| `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？` | `strong` | 验证比较类主链路 |
| `桂枝加附子汤方和桂枝加厚朴杏子汤方哪个好？` | `refuse` | 验证比较类拒答范围 |

## 9. 当前验收标准框架

当前系统验收至少包含四层：

### 9.1 数据层

1. safe / full 输入边界稳定
2. `annotation_links` 未泄漏入运行链路
3. `chunks -> main_passages` 回指稳定

### 9.2 检索层

1. hybrid retrieval 主链路可运行
2. RRF、rerank、dense recall 不破坏证据门控
3. 黄连汤方精度补丁不回归

### 9.3 回答层

1. 三模式语义稳定
2. answer payload 顶层字段稳定
3. citations 生成逻辑稳定

### 9.4 展示层

1. 前端只依赖冻结 API
2. 证据分区显示正确
3. 拒答与弱回答不会被渲染成确定答案

## 10. 后续功能变更时必须更新哪些部分

| 变更类型 | 必须同步更新 |
| --- | --- |
| 改 API 路由或请求体 | `minimal_api_contract.md`、本 spec、前端实现、API smoke |
| 改 answer payload 顶层字段 | `answer_payload_contract.md`、本 spec、前端实现、API smoke |
| 改 evidence 分层规则 | `docs/data/06_layered_enablement_policy.md`、`config/layered_enablement_policy.json`、本 spec、检索/回答 smoke |
| 恢复 `annotation_links` | 数据验收报告、safe 数据策略、本 spec、数据库构建逻辑 |
| 扩展多书 | PRD、本 spec、技术设计、数据/检索/引用合同 |
| 接入真实 LLM | 技术设计、回答规则、风险控制、测试口径 |

## 11. 明确禁止随意推翻的内容

以下内容在当前版本中明确禁止被随意推翻：

1. 单书《伤寒论》边界
2. 非诊疗定位
3. `POST /api/v1/answers` 最小 contract
4. answer payload 顶层字段集合
5. `strong / weak_with_review_notice / refuse` 三模式语义
6. `primary / secondary / review` 三槽位语义
7. `annotation_links` 默认禁用
8. `chunks` 不得进入 `primary_evidence`
9. 一级冻结回归样例的预期结果

## 12. 当前版本已知缺口列表

| 缺口 | 当前状态 | 影响 |
| --- | --- | --- |
| 双书支持 | 未实现 | 不能按开题报告原始双书口径答辩 |
| FTS5/BM25 扩库校准 | 部分实现 | 当前 sparse layer 已落地，但 score 映射仍按单书库调优 |
| 真实 LLM 生成与 Prompt 栈 | 未实现 | 生成式回答目前是规则编排 |
| 大规模测试集与指标评估 | 未实现 | 效果验证仍以 smoke/case 为主 |
| 注解自动挂接 | 未实现 | 不能宣称已完成正文-注解联动证据链 |
| 复杂专题总括 | 部分实现 | 超宽主题常降级为 weak |
| 非双方名比较 | 未实现 | 比较能力范围有限 |

## 13. 与开题报告功能承诺的映射说明

| 开题报告功能/章节承诺 | 当前正式系统映射 | 状态 |
| --- | --- | --- |
| 系统需求分析与总体设计 | 本 spec + PRD + technical design | 已实现 |
| 经典知识库设计 | safe/full 数据底座 + SQLite 运行库 | 已实现 |
| 稀疏检索设计 | SQLite FTS5/BM25 sparse retrieval | 已实现 |
| 稠密向量检索设计 | FAISS 双索引 + embedding model | 已实现 |
| 检索结果融合与重排序 | RRF + Cross-Encoder rerank | 已实现 |
| 答案生成模块设计 | Answer Assembler | 部分实现 |
| 提示模板设计 | 规则化回答模板 | 部分实现 |
| 接口与调用流程 | `POST /api/v1/answers` + same-origin frontend | 已实现 |
| 答案形式与引用机制 | answer payload + citations + display sections | 已实现 |
| 前端界面实现 | 原生单页前端 | 已收口/调整实现 |
| 系统测试与结果分析 | 数据验收、smoke checks、案例回归 | 部分实现 |

本表的正式含义是：

1. 开题报告中的承诺没有被忽略，而是被显式映射进当前系统。
2. 当前凡是未完整落地的项，都必须按“部分实现”或“收口实现”表述。
3. 后续任何扩展都应优先补齐这些差距，而不是改写当前系统已经冻结的合同。
