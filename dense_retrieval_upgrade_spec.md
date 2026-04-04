# Dense Retrieval Upgrade Spec

## 1. 当前基础现状

当前系统已经具备以下稳定基础：

- SQLite 检索底座：[artifacts/zjshl_mvp.db](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_mvp.db)
- 最小检索闭环：[run_minimal_retrieval.py](/Users/man_ray/Projects/Python/tcm-classic-rag/run_minimal_retrieval.py)
- 三模式输出：`strong` / `weak_with_review_notice` / `refuse`
- 主证据污染首轮修复：[retrieval_precision_patch_note.md](/Users/man_ray/Projects/Python/tcm-classic-rag/retrieval_precision_patch_note.md)
- answer assembler 已完成：[run_answer_assembler.py](/Users/man_ray/Projects/Python/tcm-classic-rag/run_answer_assembler.py)

本轮升级不是从零重做检索，而是在现有稳定链路上增加：

- dense retrieval
- sparse + dense fusion
- Cross-Encoder rerank

同时保持既有 evidence gating 不失效。

## 2. 升级目标

最终最小链路固定为：

`query -> sparse recall -> dense recall -> RRF fusion -> Cross-Encoder rerank -> evidence gating -> strong/weak/refuse`

本轮只做检索增强，不改 answer payload 合同，不扩展前端 / API / 多书。

## 3. Embedding 选型原则

选型必须同时满足：

- 当前可获得：优先本地可跑，次选外部 API
- 成本可控：建库成本、调试成本、查询成本都不能失控
- 中文语义检索可用：能覆盖“现代问法 -> 古文条文”
- 工程复杂度适中：适合当前本科毕设规模
- 与现有 gating 兼容：dense 只能增强召回，不能越级决定主证据

## 4. 推荐方案

推荐方案：

- Embedding：`BAAI/bge-small-zh-v1.5`
- Dense index：`faiss-cpu`
- Cross-Encoder：`BAAI/bge-reranker-base`
- 运行方式：本地虚拟环境；FAISS 走 CPU；rerank 优先尝试 `mps`，否则回退 CPU

推荐原因：

- 中文检索能力相对稳
- 模型体量适中，适合当前单书规模
- 没有持续 API 调用成本
- 当前数据量只有几千条，建库和调试都可控
- 与 `chunks -> main_passages` 回指结构兼容

## 5. 备选方案

备选方案 A：

- Embedding：`BAAI/bge-base-zh-v1.5`
- Cross-Encoder：`BAAI/bge-reranker-base`

特点：

- 语义效果可能略好
- 模型更重，建库和查询延迟更高
- 更依赖本地内存与推理时间

备选方案 B：

- Embedding：外部 API 向量模型
- Dense index：本地 `faiss-cpu`
- Cross-Encoder：仍用本地 reranker

特点：

- 工程实现简单
- 需要 API key
- 后续 query 成本持续发生
- 对毕设演示可用，但长期成本不如本地方案

## 6. 不推荐方向

- 直接上超大 embedding 模型或超大 reranker
- 在本阶段训练自定义 reranker
- 让 dense 直接覆盖现有 evidence gating
- 一开始把所有 source object 都做 dense index

原因：

- 成本高
- 依赖重
- 容易让 strong 证据门控失效
- 超出当前最小闭环所需复杂度

## 7. 成本口径

### 7.1 本地低成本方案

- 一次性成本：模型下载 + 本地建索引
- 持续成本：几乎只有本地算力和电量
- 优点：没有 API 计费
- 风险：首次安装与模型下载较重，对本机环境有要求

### 7.2 API 方案

- 一次性成本：低
- 持续成本：每次建库和查询都产生 API 费用
- 优点：部署简单，模型效果稳定
- 风险：调试时成本持续上升，离线演示不友好

### 7.3 混合方案

- Embedding 用 API，rerank 本地
- 优点：dense 建设快，rerank 可控
- 风险：仍有长期 embedding 成本

当前推荐成本结构：

- 优先本地方案
- 若本地依赖难以稳定安装，再降级到 API embedding + 本地 reranker

## 8. Chunk 策略与索引管理

### 8.1 索引对象

本轮采用双索引：

- `records_chunks` dense index：主语义召回入口
- `records_main_passages` dense index：补足短标题 / 方名 / 关键条文的直接召回

不对以下对象建立 dense index：

- `records_annotations`
- `records_passages`
- `risk_registry_ambiguous`

原因：

- 这些对象不允许进入 `primary_evidence`
- 若直接 dense 化，容易把语义相近的风险材料抬得过高
- 先用 sparse 保持对辅助 / 风险材料的最低覆盖即可

### 8.2 Chunk 回指

- `chunks` 只承担召回入口
- dense 命中 `chunks` 后，必须走 `record_chunk_passage_links`
- 回指到 `main_passages` 后，再交给现有 gating 判断能否进入 `primary_evidence`

### 8.3 索引文件

建议文件：

- `artifacts/dense_chunks.faiss`
- `artifacts/dense_chunks_meta.json`
- `artifacts/dense_main_passages.faiss`
- `artifacts/dense_main_passages_meta.json`
- `artifacts/dense_index_build_report.md`

### 8.4 重建规则

以下任一情况触发重建：

- dense 模型切换
- 数据库内容变更
- `records_chunks` / `records_main_passages` 条数变更
- embedding 维度或归一化策略变更

## 9. Sparse + Dense 融合策略

### 9.1 为什么优先 RRF

优先使用 Reciprocal Rank Fusion（RRF），原因是：

- 不要求 sparse / dense 分数同尺度
- 对小规模项目足够稳
- 工程实现简单
- 更不容易因单一路径分数失真而污染候选池

### 9.2 建议参数

- sparse top-k：`20`
- dense chunks top-k：`20`
- dense main_passages top-k：`12`
- fusion candidate pool：`24~30`
- RRF 常数：`60`

### 9.3 融合阶段

- 先分别完成 sparse recall 与 dense recall
- 对去重后的候选做 RRF
- RRF 后选取 top-N 进入 rerank 池

## 10. Cross-Encoder Rerank 方案

### 10.1 接入位置

- rerank 固定接在 fusion 后
- 不对全库做 rerank

### 10.2 建议参数

- rerank top-N：`18`

### 10.3 输入输出

输入：

- query
- fusion 后候选的 `retrieval_text`

输出：

- 每个候选的 rerank score

### 10.4 与 evidence gating 的衔接

- rerank 只影响候选排序
- 不改变对象类型
- 不改变 `evidence_level`
- 不改变 `display_allowed`
- 不改变 `primary_allowed`

### 10.5 为什么 rerank 不能替代门控

因为 rerank 只能回答“更像用户问题”，不能回答“是否允许成为主证据”。

因此：

- 语义相近不等于可进 `primary`
- 证据分层必须仍由现有规则控制

## 11. Evidence Gating 保持方案

dense / rerank 升级后，以下规则继续强制成立：

- `chunks` 不能直接进入 `primary_evidence`
- `annotations` 不能进入 `primary_evidence`
- `passages` / `ambiguous_passages` 不能进入 `primary_evidence`
- strong 模式的 `primary_evidence` 仍只能来自合规 `main_passages`
- `annotation_links` 继续完全禁用

为防止“语义相近但不该当主证据”的污染：

- 保留现有 `query_theme` / `topic_consistency` / `primary_allowed` 逻辑
- 对 dense / fusion / rerank 后的候选，仍然执行同一套 gating
- `葛根黄芩黄连汤方` 这类扩展方名，只能降到 `secondary_evidence` 或 `review_materials`

## 12. Phase 2 实现边界

### 要做

- dense index 构建脚本
- dense recall
- sparse + dense Hybrid
- RRF
- Cross-Encoder rerank
- smoke checks

### 不做

- 前端
- HTTP API
- 多书扩展
- answer payload 重构
- LLM 生成增强
- 新一轮数据底座重构
- 自定义模型训练

## 13. 最小实现策略

为了确保本轮能落地，Phase 2 只需要覆盖：

- 3 个冻结 query
- Hybrid retrieval 输出继续兼容 `strong / weak_with_review_notice / refuse`
- smoke check 能展示 sparse / dense / fusion / rerank 摘要
- 主证据精度补丁不回归
