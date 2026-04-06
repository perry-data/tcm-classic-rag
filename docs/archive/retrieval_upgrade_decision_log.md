# Retrieval Upgrade Decision Log

## Decision 1

- topic: dense retrieval 技术路线
- decision: 采用本地 embedding + 本地 `faiss-cpu` + 本地 Cross-Encoder rerank
- reason: 成本可控，和当前 SQLite 底座兼容，不依赖长期 API 费用

## Decision 2

- topic: dense index 对象
- decision: 只对 `records_chunks` 和 `records_main_passages` 建索引
- reason: 让 dense 重点服务主证据召回，同时避免辅助 / 风险对象被过度抬升

## Decision 3

- topic: fusion 方式
- decision: 优先使用 RRF
- reason: sparse / dense 分数不需要统一标定，工程稳定性更高

## Decision 4

- topic: rerank 接入位置
- decision: rerank 放在 fusion 之后，只 rerank top-N
- reason: 控制推理成本，同时让 rerank 聚焦已融合后的高价值候选

## Decision 5

- topic: 主证据门控
- decision: 保留现有 `primary_allowed` 与 `topic_consistency` 规则，不允许 dense / rerank 绕过
- reason: 防止 semantic match 把相近但不对应的问题材料抬进 `primary_evidence`

## Decision 6

- topic: Apple Silicon 利用方式
- decision: FAISS 默认仍走 CPU；Cross-Encoder 若依赖 PyTorch，则优先尝试 `mps`
- reason: macOS 上常规 FAISS GPU 不现实，但 rerank 可能部分利用 Apple GPU
