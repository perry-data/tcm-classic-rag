# 开题报告 vs 当前项目实际成果缺口审计 v1

- 审计日期：2026-04-08
- 开题报告来源：`docs/proposal/221030147张前_开题报告.docx`
- 当前成果来源：`docs/final/PRD_v1.md`、`docs/final/technical_design_v1.md`、`docs/final/system_spec_v1.md`、`docs/evaluation/evaluation_spec_v1.md`、`docs/evaluation/evaluation_plan_v1.md`、`artifacts/evaluation/goldset_v2_working_150.json`、`artifacts/evaluation/goldset_v2_batchC_eval_report.json`、`docs/patch_notes/goldset_v2_batchC_patch_note.md` 及相关 smoke / build artifacts。
- 审计范围：只做范围对齐与证据核查，不改系统、不扩功能、不写论文正文。

## 1. 审计结论总览

当前项目可以支撑一个“《伤寒论》单书、证据驱动、可溯源、带拒答边界的 RAG 研读支持 MVP”。数据底座、SQLite/FTS5/BM25、FAISS、Hybrid/RRF/rerank、evidence gating、answer assembler、最小 API、原生前端 MVP、150 条 goldset evaluator v1 已有实物或正式文档支撑。

但不能按开题报告原始口径直接宣称“《伤寒论》+《金匮要略》双书、React + Tailwind、外接 LLM API 生成、分步 Prompt、200-250 条金标准集、用户满意度测试和响应速度测试全部完成”。这些是当前最大风险点，必须在论文和答辩口径中拆成两类处理：

1. 必须补做：不需要重写系统，但论文若要保留相应测试或章节，必须补足可审计证据。
2. 可改口径：实现成本高、会扩大冻结范围，建议在论文中如实收缩为当前项目已完成的单书 MVP 口径。

| 分类 | 数量 | 结论 |
| --- | ---: | --- |
| 已完成 | 10 | 可作为论文第 2/3/4 章的主要实物基础。 |
| 未完成且必须补做 | 5 | 响应速度、用户满意度、正式图件、部署运行支撑、论文阶段性成稿/第 4 章结果整理需要补证据。 |
| 未完成但可通过缩范围/改论文表述解决 | 9 | 双书、React + Tailwind、真实 LLM API、分步 Prompt、200-250 测试集等不建议本轮扩功能，应统一改口径。 |

完整逐项矩阵见 `docs/project_audit/proposal_vs_actual_gap_matrix_v1.json`。

## 2. 已完成项

| 项目 | 开题报告原承诺 | 当前实际做到什么 | 差距 | 建议动作 | 判定理由 |
| --- | --- | --- | --- | --- | --- |
| 单书知识库与数据底座 | 构建中医经典知识库，建立可检索结构化内容。 | 已形成《伤寒论》 safe/full 数据底座、SQLite 数据库和统一检索视图；`records_main_passages=777`、`records_chunks=583`、`records_annotations=629`、`vw_retrieval_records_unified=4280`。 | 双书范围另列为可改口径项；当前单书底座已完成。 | 论文中写成“以《伤寒论》为研究对象的知识库构建”。 | `database_build_report.md`、`technical_design_v1.md` 与 `system_spec_v1.md` 都有实物证据。 |
| SQLite FTS5 / BM25 | 使用 SQLite FTS5 与 BM25 做稀疏检索。 | 已启用 `retrieval_sparse_fts` 和 SQLite `bm25()` sparse layer。 | 当前 score / tokenizer 只按单书校准。 | 保留为已完成，但不要写成多书通用调优完成。 | 技术设计明确 FTS5/BM25 已落地。 |
| FAISS 稠密索引 | 使用预训练向量模型与 FAISS 建立语义索引。 | 已用 `BAAI/bge-small-zh-v1.5` 建 `dense_chunks.faiss` 与 `dense_main_passages.faiss`。 | 未对所有 full 注解/风险材料建 dense index。 | 写清只索引 chunks 与 main_passages，是风险控制策略。 | 技术设计说明 FAISS 已实际使用。 |
| Hybrid/RRF/rerank | 采用 BM25 + 向量检索、RRF、重排序优化结果。 | 当前链路为 sparse recall、dense recall、RRF fusion、Cross-Encoder rerank。 | 不是训练式排序，也不是 LLM scoring rerank。 | 论文写 RRF + Cross-Encoder 的最小可靠方案。 | `technical_design_v1.md`、`hybrid_retrieval_smoke_checks.md` 可支撑。 |
| 引用与证据分层 | 答案附带原文依据，支持出处核验。 | 已有 `primary_evidence`、`secondary_evidence`、`review_materials`、`citations`、`display_sections`。 | 注解片段联动高亮不是完整论文级图示。 | 保留证据分层和 citation 口径，不夸大为复杂前端联动。 | API smoke、frontend smoke 和 system spec 都有字段与展示证据。 |
| 拒答与幻觉控制 | 避免模型杜撰，确保答案基于证据。 | 通过 evidence gating 和 `strong / weak_with_review_notice / refuse` 三模式控制无证据强答。 | 未实现生成后 LLM verifier。 | 写成“门控式证据一致性控制”，不要写“LLM 生成后校验器”。 | `system_spec_v1.md` 和 evaluator v1 覆盖 refusal。 |
| 最小 API | 设计接口与调用流程。 | `POST /api/v1/answers` 已冻结，请求体仅 `query`，三模式返回 `200` 业务结果。 | 非插件化 LLM API。 | 第 3 章按当前 Minimal API 写。 | `api_smoke_checks.md` 有三条冻结样例。 |
| 前端 MVP 闭环 | Web 前端支持输入问题并返回答案和出处。 | 已有同源原生 SPA：`frontend/index.html`、`frontend/styles.css`、`frontend/app.js`，可消费 `/api/v1/answers`。 | 框架不是 React + Tailwind，另列为可改口径项。 | 写成“原生 HTML/CSS/JS 同源前端 MVP”。 | `frontend_v1_smoke_checks.md` 证明页面、静态资源、fetch 和渲染规则。 |
| 功能 smoke / 案例验证 | 对核心流程进行功能测试和案例测试。 | 已有 API smoke、frontend smoke、hybrid retrieval / answer smoke、数据库构建报告。 | 不等同于响应速度、满意度和 200-250 goldset。 | 第 4 章拆分为“已完成功能验证”和“未覆盖指标”。 | 多个 `artifacts/*smoke_checks.md` 可支撑。 |
| 150 条 evaluator v1 | 自建 goldset 并人工核对引用。 | `goldset_v2_working_150.json` 已生成；evaluator v1 报告 `total_questions=150`、`mode_match=150/150`、`citation_basic_pass=120/120`、`failure_count=0`。 | 尚未达到开题报告 200-250 条。 | 论文改为“150 条阶段性评估集”，不要写 200-250 已完成。 | Batch C patch note 与 eval report 是直接证据。 |

## 3. 必须补做项

| 项目 | 开题报告原承诺 | 当前实际做到什么 | 差距 | 建议动作 | 判定理由 |
| --- | --- | --- | --- | --- | --- |
| 响应速度 / 性能测试 | 对检索模块响应速度、核心流程响应时间做测试。 | 目前只有功能 smoke 和 evaluator 结果，未发现正式 latency / response time 报告。 | 第 2 章有性能测试方案，第 4 章有测试结果，但缺可引用数据。 | 补一个最小性能测试 artifact：API 三类/五类问题各跑多次，记录 p50/p95/均值、环境、命令和结论。 | 这是测试证据缺口，不需要扩功能，但不能靠改口径说已完成。 |
| 用户满意度测试 | 初步评价包含用户满意度，需求分析还提到与中医专业学习者交流。 | 当前没有问卷、访谈记录、用户评分或任务完成反馈 artifact。 | 若论文保留“用户满意度”，没有证据会是硬伤。 | 补最小 3-5 人任务反馈或删除满意度结果宣称；最稳妥是补轻量问卷记录。 | 满意度属于人为评价证据，不能由 evaluator 替代。 |
| 图 1 / 图 2 / UML / 架构图正式版 | 开题报告列出系统功能结构图、系统框架结构图，并要求 UML/流程图/架构图。 | 仓库内未发现 `.png/.svg/.drawio/.mmd/.puml` 等正式图件。 | 论文第 2/3 章缺可直接进入正文的图。 | 补正式图件或至少补 Mermaid/Drawio 源文件：功能结构图、系统架构图、调用流程图。 | 文档中有文本架构，但没有正式图件文件。 |
| 第 3 章系统部署与运行支撑 | 论文框架包含“系统部署与运行”。 | 目前有启动命令、API/frontend smoke，但没有单独的部署运行说明或论文可引用运行截图包。 | 第 3.4 若直接写，需要运行环境、启动步骤、页面/API 验证记录。 | 补最小 runbook 或部署运行记录，关联 `backend/api/minimal_api.py --host 127.0.0.1 --port ...`、页面入口和 smoke 结论。 | 运行链路已存在，但支撑材料分散，需收束成章节证据。 |
| 论文阶段性成稿与第 4 章结果整理 | 计划进度要求初稿、修改、最终论文；框架包含第 4 章测试与结果分析。 | 仓库当前是工程与评估文档，不是论文正文；Batch C 报告可作为第 4 章素材。 | 论文正文不能自动等同于工程 artifacts。 | 在后续论文写作轮次补第 4 章结果表和失败分析，明确 150 条范围与未覆盖项。 | 这是毕业论文交付物缺口，但本轮只审计，不写正文。 |

## 4. 可改口径项

| 项目 | 开题报告原承诺 | 当前实际做到什么 | 差距 | 建议动作 | 判定理由 |
| --- | --- | --- | --- | --- | --- |
| 双书：《伤寒论》+《金匮要略》 | 目标是提升研读两部经典的效率和质量。 | 当前正式系统、数据库、goldset 均为《伤寒论》单书。 | 《金匮要略》未入库、未索引、未评估。 | 不建议本轮补多书；论文统一改成“以《伤寒论》为对象的研读支持系统”，展望写多书扩展。 | 多书会牵动数据、检索、引用、评估，不符合冻结范围。 |
| CTEXT / 四部丛刊底本 | 数据底本采用 CTEXT 收录《四部丛刊初编》。 | 当前输入源为 `data/raw/《注解伤寒论》.zip`、`data/processed/zjshl_dataset_v2/`、safe zip。 | 底本来源和范围与开题表述不完全一致。 | 论文按当前结构化数据源如实写，不再声称 CTEXT 双书底本已完整处理。 | 底本口径可通过论文说明收束，不必为补原承诺扩数据。 |
| 外接 LLM API / 可插拔 LLM | 调用 ChatGPT 或本地 ChatGLM 生成答案，并设计可插拔接口。 | 当前是 `AnswerAssembler` 规则化证据编排，不外接 LLM。 | 真实生成式 API 和模型切换未实现。 | 改写为“检索增强的证据驱动回答编排”，展望中说明可接入 LLM。 | 接 LLM 会改变测试口径和风险控制，不建议当前补。 |
| 分步 Prompt Engineering | 分步 Prompt：证据释义/要点抽取、基于证据生成、条文依据输出。 | 当前以模板、三模式裁决和 evidence gating 替代真实 prompt 栈。 | 没有真实 prompt 模板调用链。 | 创新点改为“规则化证据编排与门控”，不要写已完成分步 Prompt。 | 控制意图已实现，但技术形态不同，适合改表述。 |
| React + Tailwind | 使用 React + Tailwind CSS 实现友好 Web 前端。 | 当前为原生 HTML/CSS/JS 同源 SPA。 | 无 `package.json`、React、Tailwind、Vite 等工程证据。 | 论文改写技术选型，说明为降低演示与部署复杂度采用原生前端。 | 当前前端已可用，重写框架不提升核心研究目标。 |
| 出处文本高亮 / 联动展示 | 前端实时返回回答并附带出处文本高亮显示。 | 当前可展示 evidence slots、citations、record_id 和章节信息。 | 未形成复杂文本高亮联动功能。 | 写成“出处与证据分区展示”，不要写“全文高亮联动已完成”。 | UI 展示目的已部分满足，功能形态可收缩。 |
| 200-250 条 goldset | 自建 200-250 条测试问题并人工标注标准依据。 | 当前已完成 150 条 working set 和 evaluator v1 报告。 | 数量未达 200-250。 | 不建议本轮扩到 200-250；论文写“150 条阶段性评估集”，把 200-250 放展望或限制。 | Batch C 明确只完成 150 左右，且本轮约束不扩样本。 |
| 古今对照能力 | 研读需求包含“溯源求证”和“古今对照”。 | 当前支持现代汉语提问到古文证据定位，但没有成体系古今对照翻译模块。 | 不能宣称完整古今对照。 | 写成“现代问法到书内证据的映射与解释支持”。 | 现有系统满足部分研读需求，完整对照是扩展方向。 |
| 生产级部署/复杂运维 | 开题背景提到实际部署挑战，论文框架有部署运行。 | 当前定位为本地同源 MVP，PRD 明确不做生产级高并发和复杂部署。 | 没有生产部署、容器化、高并发或运维体系。 | 第 3.4 只写本地运行/演示部署，不写生产级部署。 | 生产部署不属于当前毕设核心闭环，可改口径。 |

## 5. 对论文第 2/3/4 章的影响

### 第 2 章：需求分析与总体设计

第 2 章必须先完成口径收缩：研究对象从“双书”改为“《伤寒论》单书”，前端技术从 React + Tailwind 改为原生同源 SPA，生成模块从外接 LLM 改为 evidence-driven answer assembler。性能测试方案可以保留，但必须把“将要测什么”和“已经测出什么”分开，不能把尚未执行的响应速度、用户满意度写成结果。

### 第 3 章：系统实现与关键技术

第 3 章可以重点写当前真实实现：safe/full 数据层、SQLite FTS5/BM25、FAISS 双索引、Hybrid/RRF/Cross-Encoder rerank、evidence gating、AnswerAssembler、Minimal API、原生前端 MVP。需要补的不是新功能，而是正式图件和“系统部署与运行”证据收束，否则第 3.4 会缺少可复核支撑。

### 第 4 章：系统测试与结果分析

第 4 章可以使用 150 条 evaluator v1 作为当前最强证据：题量 150，五类题型分布为 source_lookup 40、comparison 30、meaning_explanation 30、general_overview 20、refusal 30；`mode_match=150/150`，`citation_basic_pass=120/120`，`failure_count=0`。但第 4 章不能写 200-250 条已完成，不能写用户满意度已完成，也不能写响应速度测试已完成。若保留这些小节，必须先补最小测试 artifact。

## 6. 建议的收尾顺序

1. 先统一论文口径：单书《伤寒论》、原生前端、规则化 answer assembler、150 条阶段性评估集，不再沿用双书/React+Tailwind/LLM API/200-250 已完成的旧说法。
2. 补正式图件：功能结构图、系统框架结构图、在线调用流程图。优先用 Mermaid 或 Drawio，确保能直接进入论文。
3. 补第 3.4 运行支撑：整理本地启动命令、页面入口、API 入口、smoke 结果和运行环境说明。
4. 补响应速度测试：围绕 `/api/v1/answers` 对五类代表问题做最小多轮测量，记录统计口径。
5. 补用户满意度或删除该指标：若保留满意度，做轻量问卷/访谈记录；若导师允许删除，则在论文中只保留功能与证据评估。
6. 写第 4 章时只引用已存在或已补做的结果：150 条 evaluator v1、smoke checks、性能测试、满意度反馈，未覆盖项放限制与展望。

## 7. 不建议本轮补做的扩展

以下事项不建议在当前阶段直接实现：

1. 扩到《金匮要略》或其他多书。
2. 把原生前端重写为 React + Tailwind。
3. 接入真实 LLM API 并重写生成链路。
4. 把 goldset 从 150 扩到 200-250。
5. 做生产级部署、高并发或复杂运维。

这些事项更适合写入“研究限制与后续展望”，而不是在收尾阶段引入新的系统风险。
