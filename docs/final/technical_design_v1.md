# 基于检索增强生成的中医经典研读支持系统技术设计文档 v1

- 文档版本：v1
- 文档日期：2026-04-06
- 约束来源：`docs/proposal/221030147张前_开题报告.docx` + 当前仓库真实实现状态
- 文档定位：解释当前真实技术方案如何承接开题报告的方法路线

## 1. 设计目标

当前技术设计的目标不是实现一个“大而全”的古籍智能系统，而是在本科毕设可控范围内，完成以下三件事：

1. 让《伤寒论》单书场景的检索增强问答闭环真正可运行。
2. 让回答建立在证据分层和出处展示之上，而不是自由生成。
3. 让开题报告中的方法路线能够在当前实现中找到对应落点，并对未完成部分给出明确解释。

## 2. 总体架构

当前系统可以分为离线构建链路与在线运行链路两部分。

### 2.1 离线构建链路

```text
原始回查底本
  -> 数据验收
  -> safe 数据底座构建
  -> SQLite 数据库构建
  -> FAISS 向量索引构建
```

对应主要脚本：

- `scripts/check_dataset_acceptance.py`
- `scripts/build_mvp_safe_dataset.py`
- `scripts/build_mvp_database.py`
- `scripts/build_dense_index.py`

### 2.2 在线运行链路

```text
用户 query
  -> AnswerAssembler
     -> 问题类型分流
        -> standard
        -> general question
        -> comparison
     -> HybridRetrievalEngine
        -> SQLite FTS5/BM25 sparse recall
        -> dense FAISS recall
        -> RRF fusion
        -> Cross-Encoder rerank
        -> evidence gating
     -> answer payload 组装
  -> POST /api/v1/answers
  -> 同源前端单页渲染
```

当前正式主链路已经稳定为：

`query -> hybrid retrieval -> evidence gating -> answer assembler -> POST /api/v1/answers -> frontend`

## 3. 数据输入边界

### 3.1 当前输入源

当前系统的离线数据输入边界如下：

1. 原始回查底本：`data/raw/《注解伤寒论》.zip`
2. full 结构化数据：`data/processed/zjshl_dataset_v2/`
3. safe 数据包：`dist/zjshl_dataset_v2_mvp_safe.zip`

### 3.2 当前内容边界

- 当前只处理《伤寒论》。
- 数据验收统计中 `books = 1`，因此运行期不存在双书调度。
- 外部网页、教材、现代指南、其他典籍均不在当前检索范围内。

### 3.3 safe / full 双层输入策略

当前数据设计不是“全量直接上”，而是：

1. safe 数据承担主证据和主检索骨架。
2. full 数据承担注解、总账和风险回退层。
3. `annotation_links` 默认禁用，不进入运行链路。

这与开题报告强调的“证据溯源优先”一致，但实现上比原始设想更保守。

## 4. 数据层与索引层设计

### 4.1 SQLite 运行底座

当前 SQLite 数据库 `artifacts/zjshl_mvp.db` 已落成，并包含：

| 对象 | 数量 | 作用 |
| --- | --- | --- |
| `records_main_passages` | 777 | 主证据与次级主条 |
| `records_chunks` | 583 | 检索骨架切片 |
| `records_annotations` | 629 | 注解辅助材料 |
| `records_passages` | 1841 | 全量文本总账 |
| `risk_registry_ambiguous` | 450 | 低置信度风险清单 |
| `record_chunk_passage_links` | 676 | `chunks -> main_passages` 回指关系 |
| `vw_retrieval_records_unified` | 4280 | 统一检索入口视图 |

### 4.2 证据层级

当前运行时实际采用 A/B/C/D 四层思路：

| 层级 | 运行对象 | 当前作用 |
| --- | --- | --- |
| A | safe `main_passages(retrieval_primary=true)` | 可进入 `primary_evidence` |
| B | safe 降级主条 + full `annotations` | 只进入 `secondary_evidence` |
| C | safe `chunks` + full `passages` + `ambiguous_passages` | 召回与风险材料 |
| D | `annotation_links` | 默认禁用 |

### 4.3 索引层设计

当前索引层不是单一索引，而是“SQLite 事实表 + 统一视图 + FAISS 双索引”的组合：

1. SQLite 保存真值记录与分层字段。
2. `vw_retrieval_records_unified` 暴露统一检索接口。
3. FAISS 仅对 `chunks` 与 `main_passages` 建立 dense index。

## 5. 稀疏检索设计

### 5.1 开题报告中的原始承诺

开题报告把“SQLite FTS5 / BM25”作为稀疏检索主路线。

### 5.2 当前真实落地

当前系统已经在正式运行链路中实际启用 SQLite FTS5 虚表 `retrieval_sparse_fts` 与 SQLite `bm25()`。

当前稀疏检索的真实实现是：

1. 建库脚本创建 `retrieval_sparse_fts`，运行时若缺失会自动补建并回填。
2. 对 query 做噪音词清洗与 focus 提取。
3. 基于 focus 文本构造 3 字及以上的 FTS `MATCH` 表达式，tokenizer 使用 `trigram`。
4. 使用 SQLite `bm25()` 作为稀疏召回排序基线，并保留 `text_match_score` 用于后续 topic/gating 收口。
5. 结合 `default_weight_tier`、主题一致性和 source budget 做候选裁剪，再进入 hybrid retrieval 主链。

### 5.3 当前结论

因此，“SQLite FTS5 / BM25”在当前版本中的状态应表述为：

- SQLite 底座：已实现
- 稀疏检索能力：已实现
- FTS5/BM25 物理索引：已正式落地
- 当前正式方案：SQLite FTS5 trigram 虚表 + `bm25()` sparse retrieval

### 5.4 当前实现边界

1. 本轮只替换 sparse 层，不改 API、answer payload 和 evidence gating。
2. 当前 tokenizer 选择为 `trigram`，目的是与中文词面召回需求保持一致。
3. 对不足 3 字的极短 focus query，仍保留 lexical fallback 作为兜底。

## 6. 稠密检索设计

### 6.1 开题报告中的原始承诺

开题报告承诺：

1. 使用预训练向量模型
2. 构建 FAISS 向量索引
3. 用于弥补现代问法与古文表述之间的语义鸿沟

### 6.2 当前模型与索引

当前系统已实际使用：

- embedding model：`BAAI/bge-small-zh-v1.5`
- rerank model：`BAAI/bge-reranker-base`
- vector index：`faiss-cpu`

当前已构建两个向量索引：

| 索引 | 对象数 | 作用 |
| --- | --- | --- |
| `dense_chunks.faiss` | 583 | 语义召回主入口 |
| `dense_main_passages.faiss` | 777 | 补足短标题/方名/主条直接命中 |

### 6.3 FAISS 专项说明

#### 6.3.1 开题报告为什么提 FAISS

开题报告提 FAISS，是因为它是当前最直接、最适合小到中等规模本地向量检索的实现方式，尤其适合：

1. 将经典文本嵌入后建立本地可检索索引
2. 在现代汉语问法下补足词面匹配不足
3. 避免把整个语义检索能力外包给在线服务

#### 6.3.2 当前系统是否已经实际使用

是，已经实际使用，不是停留在计划层。

#### 6.3.3 当前用在什么模块

FAISS 当前用在两个模块：

1. `scripts/build_dense_index.py`
   - 用 `SentenceTransformer` 编码文本
   - 用 `faiss.IndexFlatIP` 建立两个索引
2. `backend/retrieval/hybrid.py`
   - 运行时 `faiss.read_index(...)`
   - 读取 `chunks` 与 `main_passages` 两套索引进行 dense recall

#### 6.3.4 如果没有完整落地，原因是什么

FAISS 本身已落地。  
未完整扩展的部分是：当前没有对 `annotations`、`passages`、`ambiguous_passages` 建 dense index。

这是有意收口，原因是：

1. 这些对象不允许进入主证据。
2. 直接 dense 化会抬高风险材料排序，破坏证据门控。
3. 当前单书 MVP 优先保证主证据精度，而不是最大化语义覆盖。

## 7. 融合与重排序设计

### 7.1 Hybrid 检索结构

当前 hybrid retrieval 固定为：

1. sparse recall
2. dense chunks recall
3. dense main_passages recall
4. RRF fusion
5. Cross-Encoder rerank

### 7.2 RRF 对齐说明

开题报告明确提出采用 RRF 融合。当前实现已正式落地：

- RRF 常数：`60`
- fused pool：`24`

当前选择 RRF 的原因与开题报告一致：

1. sparse 与 dense 分数不共尺度
2. 小规模项目更适合排名融合
3. 无需额外标注训练数据

### 7.3 重排序对齐说明

开题报告提到“重排序模型”或“交叉编码器”。当前实现已正式落地：

- rerank model：`BAAI/bge-reranker-base`
- rerank top-N：`18`

需要强调的是：

1. rerank 只改变候选顺序
2. rerank 不改变对象层级
3. rerank 不能替代 evidence gating

### 7.4 当前融合与重排序的技术边界

当前实现不是训练式学习排序，也没有加入复杂特征工程，而是保留“RRF + Cross-Encoder”的最小可靠方案。

## 8. 证据门控设计

证据门控是当前系统最关键的风险控制层，也是开题报告“证据一致性校验”承诺在当前版本中的主要落点。

### 8.1 当前门控规则

1. `annotation_links` 禁用
2. `chunks` 只召回并回指，不直接进入 `primary_evidence`
3. `annotations` 只能进入 `secondary_evidence`
4. `passages` / `ambiguous_passages` 只能进入 `review_materials`
5. `primary_evidence` 只允许合规 `main_passages`

### 8.2 三模式裁决

| 模式 | 触发条件 | 技术含义 |
| --- | --- | --- |
| `strong` | 有合规主证据 | 可以给主回答与主引用 |
| `weak_with_review_notice` | 无主证据，但有辅助/风险材料 | 必须弱化表达并提示核对 |
| `refuse` | 三槽位都无法形成稳定结果 | 拒答优先于强答 |

### 8.3 与开题报告的关系

当前没有单独实现“生成后再跑一次 LLM 校验器”，但已经通过门控把“证据不足不强答”真正嵌进了运行链路。这是开题报告“证据一致性校验”的现实收口版本。

## 9. 回答编排设计

### 9.1 当前真实形态

当前 answer 层不是外接 LLM prompt 调用，而是 `backend/answers/assembler.py` 中的证据驱动回答编排器。

它做三件事：

1. 问题类型分流
2. 证据对象格式化
3. answer payload 统一输出

### 9.2 当前支持的回答路径

1. 标准问答路径
   - 直接基于 hybrid retrieval 的三槽位输出模板化答案
2. 总括类路径
   - 先识别 topic
   - 再做 topic 定向 retrieval
   - 最后按 branch heuristic 组织最小分支答案
3. 比较类路径
   - 识别两个方名
   - 分别检索
   - 对方文与相关条文做结构化差异整理

### 9.3 Prompt Engineering 对齐说明

开题报告承诺了 Prompt Engineering。当前状态应如实表述为：

- “严格依证据作答、无证据不强答”的控制意图：已实现
- 通过外部 LLM prompt 模板驱动生成：尚未实现
- 当前替代方式：规则化模板回答 + 三模式裁决 + 引用输出

因此，Prompt Engineering 当前属于“部分实现并收口为规则化回答模板”，而不是“已经接入 LLM prompt 栈”。

### 9.4 引用与证据展示对齐说明

开题报告要求“引用与出处展示”。当前已正式落地：

1. `citations` 数组
2. 章节信息
3. `primary / secondary / review` 分区
4. `display_sections` 稳定编排

这一项属于已实现。

## 10. API 设计

### 10.1 当前接口

当前正式 API 为：

- `POST /api/v1/answers`

请求体只接收：

```json
{
  "query": "..."
}
```

### 10.2 响应特征

1. 直接返回 answer payload
2. 不额外包 `data`
3. 业务分支依赖 `answer_mode`

### 10.3 状态码策略

| 状态码 | 含义 |
| --- | --- |
| `200` | 合法业务结果，包含 strong / weak / refuse |
| `400` | 请求体非法 |
| `500` | 内部错误 |

当前 API 已是正式运行链路的一部分，不是伪接口。

## 11. 前端消费设计

### 11.1 当前前端真实形态

开题报告写的是 React + Tailwind。当前真实实现是：

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

即原生单页前端，而不是 React/Tailwind 工程。

### 11.2 当前为何这样收口

1. 同源部署最稳，演示成本最低
2. 不需要额外构建工具与 CORS 处理
3. 题目重点在“研读支持链路”，不在前端框架本身

### 11.3 前端依赖边界

前端只允许依赖：

1. `POST /api/v1/answers`
2. answer payload 顶层字段
3. `display_sections`

前端不依赖：

1. 检索 trace
2. RRF 分数
3. rerank 分数
4. 内部阈值

## 12. 当前运行链路

### 12.1 标准问题

`query -> HybridRetrievalEngine -> evidence gating -> AnswerAssembler -> payload -> API -> frontend`

### 12.2 总括类问题

`query -> general question detect -> query retrieval + topic retrieval -> branch organization -> payload`

### 12.3 比较类问题

`query -> comparison detect -> entity A retrieval + entity B retrieval -> structured diff -> payload`

## 13. 错误处理与降级策略

当前系统的降级不是异常兜底，而是显式设计的一部分。

1. 请求体不合法
   - 返回 `400`
2. 后端执行异常
   - 返回 `500`
3. 证据不足但仍有辅助材料
   - 返回 `weak_with_review_notice`
4. 完全无可靠证据
   - 返回 `refuse`
5. 总括类问题分支不足
   - strong 降级为 weak 或 refuse
6. 比较类问题识别失败或问题超范围
   - 直接 refuse

## 14. 开题报告方法落地情况说明

| 开题报告方法项 | 当前状态 | 当前实现说明 |
| --- | --- | --- |
| SQLite | 已实现 | 已作为正式数据库底座落地 |
| FTS5 / BM25 | 已实现 | 已启用 SQLite FTS5 `retrieval_sparse_fts` 与 `bm25()` 作为正式 sparse layer |
| 预训练向量模型 | 已实现 | `BAAI/bge-small-zh-v1.5` |
| FAISS 向量索引 | 已实现 | `chunks` 与 `main_passages` 双索引 |
| Hybrid 检索 | 已实现 | sparse + dense + fusion |
| RRF 融合 | 已实现 | 当前正式检索主链的一部分 |
| 重排序 | 已实现 | `BAAI/bge-reranker-base` Cross-Encoder |
| 基于证据的生成式回答 | 部分实现 | 已有证据驱动回答编排；未接入真实 LLM 自由生成 |
| Prompt Engineering | 部分实现 | 当前以规则模板和强约束回答替代真实 prompt 栈 |
| 引用与出处展示 | 已实现 | citations + evidence slots + chapter metadata |
| 功能测试 / 案例测试 / 效果验证 | 部分实现 | 已有 smoke 和案例验证；未形成大规模指标测试集 |
| 证据一致性校验 | 部分实现 | 当前由 evidence gating 主导；未实现生成后验证器 |

## 15. 当前技术风险与限制

1. 当前 FTS5/BM25 使用 `trigram` tokenizer，后续如扩库，仍需重新校准 sparse score 映射与 source budget。
2. 当前回答层未接入真实 LLM，因此不能把系统表述为“完整生成式问答系统”。
3. 总括类与比较类能力目前依赖启发式规则，覆盖范围有限。
4. `annotation_links` 禁用意味着注解自动挂接尚未恢复。
5. 当前测试仍以 smoke 和案例为主，缺少标准化检索指标报告。
6. 前端虽已可演示，但不是开题报告原设的 React/Tailwind 实现。

## 16. 后续扩展原则

1. 若继续优化 FTS5/BM25，应继续在不破坏现有 evidence gating 的前提下只调整 sparse 层，而不是改动 answer contract。
2. 若接入真实 LLM，应继续保留三模式裁决和证据分槽，禁止“直接把检索结果喂给模型后自由输出”。
3. 若扩展多书，必须先重构 scope、索引隔离、引用格式和测试集。
4. 若恢复 `annotation_links`，必须先通过新一轮数据验收和抽样复核。
