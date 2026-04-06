# Proposal Alignment Note

## 一、本轮实现与开题报告“方法”的对应关系

### 1. 继续复用了 hybrid retrieval

本轮没有新起一套 retriever。

总括类问题仍然建立在现有链路之上：

- sparse lexical retrieval
- dense vector retrieval
- RRF 融合
- rerank
- evidence gating

具体做法不是推翻原链路，而是：

1. 先识别这是“总括类问题”
2. 仍先跑现有 `HybridRetrievalEngine.retrieve(...)`
3. 再用提取出的 topic 做一次更贴近主题的补充召回
4. 在 safe `main_passages` 中做最小 branch organization

所以本轮属于“在既有 hybrid retrieval 之上补一层问题类型处理”，而不是重写方法。

### 2. 继续保留了向量检索 / 稀疏检索 / 融合 / 证据驱动生成

本轮没有删掉或绕过：

- 向量检索
- 稀疏检索
- 融合排序
- rerank

总括类回答中的 branch 选择，仍然参考已有 hybrid retrieval 的结果，而不是只做静态文本匹配。

同时，回答文本不是自由总结，而是基于当前可核对的条文线索做整理，因此仍属于“证据驱动生成”。

### 3. 继续保留引用依据与风险控制

本轮没有破坏现有 evidence gating 约束：

- `chunks` 不直接进入 `primary_evidence`
- `annotations` 不进入 `primary_evidence`
- `passages / ambiguous_passages` 不越级进入 `primary_evidence`
- `annotation_links` 继续禁用

对应到总括类问题：

- strong：只把可作为主依据的 `main_passages` 放进 `primary_evidence`
- weak：不输出 `primary_evidence`，只给 `secondary_evidence / review_materials`
- refuse：不输出概括性答案

因此，本轮没有为了“让泛问看起来更聪明”而牺牲风险控制。

### 4. 本轮新增的方法补丁是什么

本轮新增的是一条最小策略，而不是新方法栈：

- 问题类型识别
- topic 抽取
- topic 定向补充召回
- branch heuristic organization
- strong / weak / refuse 降级

这与开题报告的方法承诺并不冲突。它只是把“检索到证据后如何组织成更像研读支持的答案”补得更完整。

### 5. FAISS 核对

#### 5.1 当前系统是否已经实际使用 FAISS

是，已经实际使用。

#### 5.2 如果已经使用，用在什么模块、通过哪些脚本 / 流程落地

当前落地点很明确：

1. 索引构建

- [build_dense_index.py](/Users/man_ray/Projects/Python/tcm-classic-rag/scripts/build_dense_index.py)
- 该脚本用 `SentenceTransformer` 生成 embedding
- 再用 `faiss.IndexFlatIP(...)` 建两个本地向量索引：
  - [dense_chunks.faiss](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_chunks.faiss)
  - [dense_main_passages.faiss](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_main_passages.faiss)

2. 检索使用

- [hybrid.py](/Users/man_ray/Projects/Python/tcm-classic-rag/backend/retrieval/hybrid.py)
- 在 `HybridRetrievalEngine.__post_init__()` 中直接 `import faiss`
- 然后通过 `faiss.read_index(...)` 读取上述两个索引文件
- dense recall 再与 sparse 结果一起进入 fusion + rerank

3. 现有产物

- [dense_index_build_report.md](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_index_build_report.md) 已记录当前索引构建结果
- 当前报告显示：
  - `chunks` 索引 583 条
  - `main_passages` 索引 777 条

#### 5.3 如果没有实际启用，原因是什么，当前替代方案是什么

不适用，因为当前并不是“未启用”状态。

当前系统不是只有 SQLite FTS 或纯稀疏检索，而是已经有：

- SQLite / lexical 召回
- FAISS dense recall
- rerank

#### 5.4 这一点与开题报告“FAISS 向量索引”承诺之间是否一致

总体一致。

准确说：

- “是否已经用了 FAISS”这一点：一致，已经用了
- “是否已经做成更复杂的大规模索引系统”这一点：本轮没有扩展，但不影响“已落地 FAISS 向量索引”这个承诺本身

## 二、本轮实现与开题报告“功能”的对应关系

### 1. 更接近“研读支持系统”，而不是“检索展示器”

本轮之前：

- 系统对 `太阳病应该怎么办？` 这类问题容易退化成“召回几条相关主条然后拼上去”
- 更像检索展示

本轮之后：

- 系统会先明确告诉用户：这是总括性问题，书中并非只有一个固定答案
- 会按“分情况 / 分支”组织 2～4 条典型线索
- 仍然给出处与 citations
- 证据不足时主动降级

因此它更像“帮助用户研读、分辨、继续追问”的系统，而不是只把检索结果摊开。

### 2. 更好支持现代汉语提问

开题报告强调的是现代汉语问法下的书内检索与问答支持。

本轮新增能力直接对齐这一点：

- 用户可以用现代汉语问：`太阳病应该怎么办？`
- 系统不再要求用户先学会问成“第几条怎么说”
- 系统会把这种现代汉语总括问法转成书内证据组织问题

这比只支持“某条原文是什么 / 某句什么意思”更接近真实使用场景。

### 3. 更接近“典型问题案例验证”

本轮新增后，系统覆盖的典型问题类型更完整：

- 方名原文追问
- 弱证据解释追问
- 无依据拒答
- 总括 / 泛问 / 分情况问题

尤其是当前重点样例：

- `太阳病应该怎么办？`

现在已经能明显比原来更接近“研读支持回答”。

## 三、本轮补齐了什么

本轮补齐的是：

1. “总括类 / 泛问类问题”的最小识别
2. 总括类问题的最小 branch organization
3. strong / weak / refuse 的总括类降级逻辑
4. 总括类样例、smoke checks、patch note
5. 与开题报告方法 / 功能承诺的专门对齐说明

## 四、尚未补齐什么

当前还没有补齐的内容包括：

- 对某一主题的穷尽式专题整理
- 更稳定的 topic 语义解析
- 更完整的 branch dedupe / coverage 控制
- 多书扩展
- 更结构化的前端专题展示
- 多对象复杂比较之外的更复杂专题问答

## 五、当前不继续扩展的理由

原因很明确：

1. 本轮目标是“最小实现”，不是系统重写
2. 当前最关键差距是：系统要先从“会检索”提升到“能给最小分情况整理”
3. 若继续扩展到多书、知识图谱、复杂前端，会直接冲掉本轮冻结边界
4. 现有 API、payload、数据底座都已冻结，本轮应优先做最小高价值补丁

## 六、对你最关心的三个问题的直接回答

### 1. 这轮完成后，系统面对“太阳病应该怎么办？”这类问题，是否比以前更像一个研读支持系统？

是。

现在它至少会：

- 识别这不是单条直答问题
- 明说书中并非只有一个固定答案
- 给出若干典型分支
- 保留 citations 与 evidence 分层
- 在证据不足时降级

所以它已经明显比此前“拼几条主条”更像研读支持系统。

### 2. 当前系统是否已经真正落实了开题报告里提到的 FAISS 向量索引？

是，已经真正落实。

它不是停留在计划或文档里，而是已经通过：

- [build_dense_index.py](/Users/man_ray/Projects/Python/tcm-classic-rag/scripts/build_dense_index.py)
- [dense_chunks.faiss](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_chunks.faiss)
- [dense_main_passages.faiss](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_main_passages.faiss)
- [hybrid.py](/Users/man_ray/Projects/Python/tcm-classic-rag/backend/retrieval/hybrid.py)

这条实际流程落地了。

### 3. 本轮实现与开题报告的方法和功能承诺，具体对应关系是什么？

可以压缩成三句话：

1. 方法上：

- 继续复用 hybrid retrieval、dense/sparse、fusion、rerank、evidence gating

2. 功能上：

- 把系统从“检索展示”往“分情况研读支持”推进了一步

3. 差距上：

- 本轮补齐了总括类问题的最小能力
- 还没有扩成完整专题系统
- 之所以不继续扩，是为了守住当前冻结边界和最小实现原则
