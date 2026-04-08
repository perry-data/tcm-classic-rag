# Proposal vs Actual Gap Audit v1 Patch Note

- 日期：2026-04-08
- 范围：开题报告 vs 当前项目实际成果缺口审计
- 任务性质：只新增审计文档，不改系统、不扩功能、不写论文正文

## 变更

1. 新增 `docs/project_audit/proposal_vs_actual_gap_audit_v1.md`。
   - 汇总审计结论。
   - 按“已完成 / 未完成且必须补做 / 未完成但可通过缩范围或改论文表述解决”分类。
   - 明确对论文第 2/3/4 章的影响。
   - 给出建议收尾顺序。
2. 新增 `docs/project_audit/proposal_vs_actual_gap_matrix_v1.json`。
   - 逐项记录开题报告承诺、当前状态、差距类型、证据文件、建议动作和优先级。
   - 覆盖研究目标、论文基本框架、研究重点与难点、研究方法中的测试评估承诺、创新点和阶段性产物。

## 审计结论摘要

当前项目已具备一个可交付的《伤寒论》单书、证据驱动、可溯源、带拒答边界的 RAG 研读支持 MVP。

已完成的核心支撑包括：

- 《伤寒论》单书 safe/full 数据底座与 SQLite 运行库
- SQLite FTS5 / BM25 sparse retrieval
- FAISS dense index
- Hybrid retrieval、RRF fusion、Cross-Encoder rerank
- evidence gating、三模式 answer mode、citations 和证据分层
- `POST /api/v1/answers` minimal API
- 原生 HTML/CSS/JS 同源 frontend MVP
- 功能 smoke / 案例验证
- 150 条 goldset evaluator v1 阶段性评估

必须补做的关键证据包括：

- 响应速度 / 性能测试
- 用户满意度测试或明确删除相关结果宣称
- 图 1 / 图 2 / UML / 架构图正式版
- 第 3 章“系统部署与运行”的正式支撑材料
- 论文阶段性成稿与第 4 章结果整理

建议通过缩范围或改论文表述解决的关键差距包括：

- 双书《伤寒论》+《金匮要略》收缩为《伤寒论》单书
- CTEXT / 四部丛刊双书底本口径改为当前结构化《注解伤寒论》数据源口径
- 外接 LLM API / 可插拔模型改为 evidence-driven answer assembler
- 分步 Prompt Engineering 改为规则化回答编排与 evidence gating
- React + Tailwind 改为原生 HTML/CSS/JS 同源前端
- 200-250 条 goldset 改为 150 条阶段性评估集
- 生产级部署改为本地演示运行

## 边界说明

本轮没有：

- 改 retrieval / rerank / gating / answer assembler
- 改 API / frontend
- 扩到 200-250
- 接入《金匮要略》或其他多书
- 接入真实 LLM API
- 重写 React + Tailwind 前端
- 写论文正文或答辩讲稿

## 后续建议

下一步建议先统一论文范围口径，再补图件、部署运行支撑、响应速度测试和用户满意度最小证据。第 4 章只引用已经存在或后续补做的结果，未覆盖项放入限制与展望。
