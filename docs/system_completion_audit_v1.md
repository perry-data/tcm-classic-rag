# 系统完成度核查 v1

## 1. 核查目的

本次核查用于论文写作、答辩准备与系统封板前收口，不用于重新扩范围，也不用于倒逼当前仓库去补做开题阶段的全部理想目标。

本次核查只回答四件事：

1. 当前主仓库里到底已经有什么。
2. 这些实现与开题报告、正式主文档分别对齐到什么程度。
3. 哪些内容可计入当前完成态，哪些只能算部分完成，哪些不应计入当前答辩范围。
4. 当前系统是否已经具备“可写论文、可演示、可答辩”的基础。

## 2. 核查依据

本次核查实际使用了以下材料：

- 开题报告原件：`docs/proposal/221030147张前_开题报告.docx`
- 正式主文档：
  - `docs/final/PRD_v1.md`
  - `docs/final/technical_design_v1.md`
  - `docs/final/system_spec_v1.md`
- 范围冻结文档：`docs/foundation/01_scope_freeze.md`
- 当前仓库代码与运行工件：
  - 数据与数据库：`data/processed/zjshl_dataset_v2/`、`dist/zjshl_dataset_v2_v1_safe.zip`、`artifacts/zjshl_v1.db`
  - 检索与回答：`backend/retrieval/`、`backend/answers/`
  - API：`backend/api/minimal_api.py`
  - 前端：`frontend/`
  - LLM provider：`backend/llm/`、`.env.example`
  - 评估与 smoke：`artifacts/evaluation/`、`artifacts/*smoke_checks.md`
- 相关设计/patch 文档：
  - `docs/contracts/`
  - `docs/specs/`
  - `docs/project_design/minimal_llm_api_integration_spec_v1.md`
  - `docs/design/chat_history_uiux_v1.md`
  - `docs/patch_notes/`

结构图核查结果：

- 仓库中未核验到正式的系统功能结构图/系统架构结构图源文件或导出图件，如 `.drawio`、`.mmd`、`.puml`、`.png`、`.svg`。
- 仅核验到与 LLM 接入相关的时序图文档：`docs/project_design/minimal_llm_api_sequence_v1.md`。
- 因此，开题报告中的“图 1 / 图 2”目前不能按“仓库已有正式图件”计入完成态。

材料缺失或不一致说明：

- `artifacts/chat_history_v1.db`、`artifacts/chat_history_v1.db-shm`、`artifacts/chat_history_v1.db-wal` 当前存在于工作区，但在本次核查时处于未跟踪状态，不计为版本化交付物。
- 多份旧 artifact 仍引用不存在的 `app_minimal_api.py`，说明运行文档存在口径滞后。

## 3. 当前系统真实范围

当前冻结范围应以 `docs/foundation/01_scope_freeze.md` 与当前主仓库实物为准，而不是以开题报告早期愿景为准。

当前真实范围可明确界定为：

- 单书《伤寒论》研读支持系统
- 基于 RAG 的单体 Web MVP
- 支持现代汉语提问
- 支持检索、回答生成、证据分层、引用溯源
- 支持 `strong / weak_with_review_notice / refuse`
- 支持最小 API、同源前端与答辩可演示闭环

当前主链已经核验到：

`query -> hybrid retrieval -> evidence gating -> answer assembler -> POST /api/v1/answers -> frontend`

当前实际已落地但不应误写为“范围扩大”的附加实现有：

- 最小真实 LLM 接入：`backend/llm/` + `qwen-plus` live smoke artifact
- `POST /api/v1/answers/stream` 流式接口
- `chat history v1` 代码、conversation API 与前端历史会话 UI

以下内容不应被重新拉回为本轮“必须补做”：

- 《金匮要略》双书扩展
- 200–250 条测试集
- React + Tailwind 重写前端
- 更大更全的中医知识平台愿景

## 4. 分模块完成度核查

### 4.0 汇总表

| 模块 | 分类结论 | 核查结论摘要 |
| --- | --- | --- |
| 数据底座 | 已完成 | safe/full 数据、原始底本、safe zip、数据库构建结果均在主仓库可核验。 |
| 检索链路 | 已完成 | SQLite FTS5/BM25、FAISS、hybrid、RRF、rerank 已形成正式主链。 |
| 证据溯源 | 已完成 | evidence gating、三槽位、citations、拒答边界均已实装。 |
| 回答生成 | 已完成 | `AnswerAssembler` 已可完成三模式回答生成；当前正式形态是“规则编排 + 可选 LLM 改写”。 |
| LLM provider 接入 | 已完成 | `qwen-plus` 接入代码、环境变量模板与 live-call artifact 已存在。 |
| API | 已完成 | `/api/v1/answers`、`/api/v1/answers/stream`、conversations 系列接口均在主仓库可核验。 |
| 前端 | 已完成 | 当前前端属于“功能已成型，待封板优化”，未见阻塞性主链 bug 证据。 |
| 会话/history | 不再实现 / 不纳入当前答辩范围 | 代码已回流主仓库并接通，但不属于当前冻结答辩主链。 |
| 评估与测试 | 部分完成 | 评估底座已足够支撑论文/答辩基础说明，但正式结果包装和少数测试口径仍未完全收口。 |
| 运行与部署 | 部分完成 | README、Quickstart、smoke artifact 已有，但存在旧命令残留与材料分散。 |
| 文档完备度 | 部分完成 | 主文档与代码存在多处口径滞后，且缺正式结构图。 |

### 4.1 数据底座

- 当前现状：
  - 主仓库存在原始底本 `data/raw/《注解伤寒论》.zip`。
  - 存在 full 结构化数据目录 `data/processed/zjshl_dataset_v2/`。
  - 存在 safe 数据包 `dist/zjshl_dataset_v2_v1_safe.zip`。
  - 已有数据验收报告与解析说明，能解释为何 `annotation_links` 默认停用。
  - 数据库统计显示当前运行边界确认为单书，非双书。
- 证据文件/代码位置：
  - `docs/data/03_dataset_acceptance_report.md`
  - `data/processed/zjshl_dataset_v2/README_parse_report_v2.md`
  - `scripts/build_v1_safe_dataset.py`
  - `scripts/build_v1_database.py`
  - `artifacts/database_counts.json`
- 分类结论：已完成
- 对论文/答辩的影响：
  - 可直接支撑第 2 章“经典知识库设计”和第 3 章“数据库及预处理”。
  - 论文必须按《伤寒论》单书口径写，不能再把双书说成当前已完成态。

### 4.2 检索链路

- 当前现状：
  - SQLite 主库 `artifacts/zjshl_v1.db` 已存在。
  - 数据库中已核验到 `retrieval_sparse_fts`、`vw_retrieval_records_unified` 等对象。
  - `backend/retrieval/hybrid.py` 已实现 SQLite FTS5/BM25 稀疏召回、FAISS 稠密召回、RRF 融合和 Cross-Encoder rerank。
  - `artifacts/dense_chunks.faiss`、`artifacts/dense_main_passages.faiss` 与 meta 文件已存在。
- 证据文件/代码位置：
  - `backend/retrieval/hybrid.py`
  - `backend/retrieval/minimal.py`
  - `scripts/build_dense_index.py`
  - `scripts/build_v1_database.py`
  - `artifacts/database_counts.json`
  - `artifacts/hybrid_retrieval_smoke_checks.md`
  - `docs/final/technical_design_v1.md`
- 分类结论：已完成
- 对论文/答辩的影响：
  - 可直接支撑第 2.5 节和第 3.2.2 节。
  - 检索部分不需要再重开方案讨论，应按当前 FTS5/BM25 + FAISS + RRF + rerank 口径固定表述。

### 4.3 证据溯源

- 当前现状：
  - `AnswerAssembler` 与 `HybridRetrievalEngine` 已共同落实 `primary_evidence`、`secondary_evidence`、`review_materials` 三槽位。
  - `annotation_links` 仍保持禁用，不会泄漏进正式证据链。
  - `citations`、`display_sections`、`refuse_reason`、`review_notice` 已形成稳定 payload。
  - evaluator 与 smoke 明确检查了 `weak` 模式主证据为空、`refuse` 模式三槽位为空等边界。
- 证据文件/代码位置：
  - `backend/answers/assembler.py`
  - `backend/retrieval/hybrid.py`
  - `config/layered_enablement_policy.json`
  - `docs/contracts/answer_payload_contract.md`
  - `artifacts/api_smoke_checks.md`
  - `artifacts/evaluation/evaluator_v2_report.md`
- 分类结论：已完成
- 对论文/答辩的影响：
  - 可直接支撑第 2.6.3、3.2.3 和答辩中的“证据优先、无证据不强答”表述。
  - 这部分是当前系统最稳定、也最值得答辩强调的主线之一。

### 4.4 回答生成

- 当前现状：
  - `backend/answers/assembler.py` 已负责题型分流、回答文本组织、引用生成与 payload 汇总。
  - `strong / weak_with_review_notice / refuse` 三模式均有明确生成路径。
  - 定义类、总括类、比较类、方剂相关查询均已有独立处理逻辑。
  - 当前真实形态不是“自由生成问答器”，而是“规则化 answer assembler + 可选 LLM answer_text 改写”。
- 证据文件/代码位置：
  - `backend/answers/assembler.py`
  - `backend/strategies/general_question.py`
  - `docs/final/technical_design_v1.md`
  - `artifacts/hybrid_answer_smoke_checks.md`
- 分类结论：已完成
- 对论文/答辩的影响：
  - 可以写“回答生成模块已落地”，但必须说明当前是受证据门控约束的收口实现。
  - 若论文把“生成”写成完全自由的 LLM 生成，会与当前主链不一致。

### 4.5 LLM provider 接入

- 当前现状：
  - 主仓库中存在独立 `backend/llm/` 模块，包含 client、prompt_builder 与 validator。
  - `minimal_api.py` 已提供 `--llm-enabled`、`--llm-smoke` 等参数。
  - `.env.example` 已给出 `TCM_RAG_LLM_API_KEY`、`TCM_RAG_LLM_MODEL=qwen-plus`、`TCM_RAG_LLM_BASE_URL`。
  - `artifacts/llm_api_smoke_checks_modelstudio_live.md` 和 `artifacts/llm_api_examples_modelstudio_live.json` 证明 `qwen-plus` live-call 曾成功跑通，且仅改写 `answer_text`，不改 mode/evidence/citations。
- 证据文件/代码位置：
  - `backend/llm/client.py`
  - `backend/llm/prompt_builder.py`
  - `backend/llm/validator.py`
  - `backend/api/minimal_api.py`
  - `.env.example`
  - `docs/patch_notes/modelstudio_qwen_plus_switch_patch_note.md`
  - `docs/patch_notes/modelstudio_qwen_plus_live_validation_patch_note.md`
  - `artifacts/llm_api_smoke_checks_modelstudio_live.md`
- 分类结论：已完成
- 对论文/答辩的影响：
  - 当前系统不能再写成“LLM 尚未接通”。
  - 真正的缺口不在“有没有 provider 接入”，而在“正式主文档尚未同步这一事实”。

### 4.6 API

- 当前现状：
  - `POST /api/v1/answers` 已稳定存在。
  - `POST /api/v1/answers/stream` 已存在。
  - 主仓库已核验到 conversations 系列接口：
    - `POST /api/v1/conversations`
    - `GET /api/v1/conversations`
    - `GET /api/v1/conversations/{id}`
    - `DELETE /api/v1/conversations/{id}`
    - `POST /api/v1/conversations/{id}/messages`
  - 同时支持前端壳路由 `/`、`/chat/{id}` 和同源静态资源服务。
- 证据文件/代码位置：
  - `backend/api/minimal_api.py`
  - `docs/contracts/minimal_api_contract.md`
  - `artifacts/api_smoke_checks.md`
- 分类结论：已完成
- 对论文/答辩的影响：
  - 可支撑第 2.6.2 与第 3.2.4。
  - 但论文与主文档若只写 `POST /api/v1/answers`，需说明这是答辩主链接口；`stream` 与 `conversations` 属于已存在扩展接口。

### 4.7 前端

- 当前现状：
  - `frontend/index.html`、`frontend/styles.css`、`frontend/app.js` 均存在，且 `node --check frontend/app.js` 已通过。
  - 当前页面已不是单轮极简表单，而是 `history sidebar + current conversation` 的双栏聊天页。
  - 前端实际接的是 conversations API，不是只调用一次 `/api/v1/answers`。
  - 代码层面未发现阻塞性主链 bug 证据；前端目前更接近“功能已成型，待封板优化”。
  - 需要注意：后端虽然有 `/api/v1/answers/stream`，但当前前端未核验到正在消费该流式接口。
- 证据文件/代码位置：
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `backend/api/minimal_api.py`
  - `artifacts/frontend_v1_smoke_checks.md`
  - `docs/notes/frontend_debug_report.md`
- 分类结论：已完成
- 对论文/答辩的影响：
  - 当前前端已足够支撑演示，不需要先补功能才能答辩。
  - 更合适的后续动作应是封板和口径回写，而不是重做 UI 技术栈。

### 4.8 会话 / history

- 当前现状：
  - 当前主仓库真实存在 `backend/chat_history/store.py`。
  - `minimal_api.py` 已接通 conversations 系列接口。
  - `frontend/app.js` 已接入 conversation list、detail、delete、message append 逻辑。
  - 因此，“chat history v1 曾被声称完成，但当前主仓库未核验到，因此不计入当前完成态”这句话不适用于当前仓库。
  - 真实状态应改写为：chat history v1 已回流主仓库代码并接通前后端，但当前冻结答辩主链不依赖它。
  - 另需注意：`artifacts/chat_history_v1.db` 当前为未跟踪工作区文件，不能视为稳定版本化交付物。
- 证据文件/代码位置：
  - `backend/chat_history/store.py`
  - `backend/api/minimal_api.py`
  - `frontend/app.js`
  - `frontend/index.html`
  - `docs/design/chat_history_uiux_v1.md`
  - `docs/patch_notes/chat_history_v1.md`
- 分类结论：不再实现 / 不纳入当前答辩范围
- 对论文/答辩的影响：
  - 不能把它写成“未回流、不可用”。
  - 也不建议把它提升为当前论文主线，否则会冲淡单书 RAG 问答主链。

### 4.9 评估与测试

- 当前现状：
  - 已存在功能 smoke、API smoke、frontend smoke、database smoke、retrieval smoke、answer smoke。
  - 已存在 evaluator v1/v2 脚本与 `goldset_v2_working_150.json`。
  - `artifacts/evaluation/evaluator_v2_report.md` 显示 150 条样本已形成可用评估底座，并包含 retrieval metrics、mode/citation checks 与 failure taxonomy。
  - 已存在 LLM regression 与 live validation artifact。
  - 未核验到正式的响应速度测试报告、用户满意度材料或 200–250 条大样本结果。
- 证据文件/代码位置：
  - `scripts/run_evaluator_v1.py`
  - `scripts/run_evaluator_v2.py`
  - `docs/evaluation/evaluation_spec_v1.md`
  - `artifacts/evaluation/evaluator_v2_report.md`
  - `artifacts/evaluation/goldset_v2_working_150.json`
  - `artifacts/api_smoke_checks.md`
  - `artifacts/frontend_v1_smoke_checks.md`
- 分类结论：部分完成
- 对论文/答辩的影响：
  - 当前评估底座已经足够支撑第 4 章基础写作和答辩效果说明。
  - 但论文中不能再写“200–250 条测试集已完成”或“满意度/响应速度已完成”。

### 4.10 运行与部署

- 当前现状：
  - README 与 Windows Quickstart 已提供最小运行命令。
  - `minimal_api.py`、数据库、FAISS 索引、前端入口均可在仓库中定位。
  - 当前更适合表述为“本地同源 MVP 运行说明已具备”，不应表述为生产级部署完成。
  - 多个 artifact 仍保留了错误启动命令 `app_minimal_api.py`，说明部署材料尚未完全收口。
- 证据文件/代码位置：
  - `README.md`
  - `docs/setup/windows_11_quickstart.md`
  - `backend/api/minimal_api.py`
  - `artifacts/api_smoke_checks.md`
  - `artifacts/frontend_v1_smoke_checks.md`
- 分类结论：部分完成
- 对论文/答辩的影响：
  - 第 3.4“系统部署与运行”可以写，但必须按“本地运行 / 同源演示部署”口径写。
  - 在论文或答辩中引用旧命令会造成硬伤，需要先统一材料。

### 4.11 文档完备度

- 当前现状：
  - 正式主文档整体完成度较高，但和当前实物存在几处关键偏差：
    - `docs/final/PRD_v1.md` 仍把“多轮会话记忆、历史记录”列为非目标，而主仓库代码已实现最小 history。
    - `docs/final/PRD_v1.md`、`docs/final/technical_design_v1.md`、`README.md` 仍将真实 LLM 生成写成“未接入”，但 `backend/llm/` 与 live artifact 已显示最小真实接入已落地。
    - `docs/specs/frontend_v1_spec.md` 仍写“不做历史记录”，与当前前端不一致。
    - 部分 smoke artifact 仍引用不存在的 `app_minimal_api.py`。
  - 仓库中也未核验到正式系统结构图/架构图文件。
- 证据文件/代码位置：
  - `docs/final/PRD_v1.md`
  - `docs/final/technical_design_v1.md`
  - `docs/final/system_spec_v1.md`
  - `docs/specs/frontend_v1_spec.md`
  - `README.md`
  - `artifacts/api_smoke_checks.md`
  - `artifacts/frontend_v1_smoke_checks.md`
- 分类结论：部分完成
- 对论文/答辩的影响：
  - 这是当前最直接的论文/答辩风险点。
  - 风险不在于系统没做出来，而在于“正式口径没有完全跟到当前实现”。

## 5. 开题报告映射

| 开题报告目标/章节点 | 当前实现映射 | 映射结论 |
| --- | --- | --- |
| 功能需求层：提问、检索、回答、证据、拒答 | 当前主链与 answer payload 已完整覆盖 | 已落地 |
| 系统总体架构层：知识库、检索、生成、前端、部署 | 已形成离线构建链 + 在线运行链，但以单书单体 Web MVP 收口 | 已缩范围落地 |
| 知识库 / 数据底座层：双书知识库、结构化索引 | 当前真实完成的是《伤寒论》 safe/full 数据底座与 SQLite/FAISS 索引 | 已缩范围落地 |
| 检索模块层：BM25、向量检索、混合检索、重排序 | FTS5/BM25、FAISS、hybrid、RRF、Cross-Encoder 已形成正式实现 | 已落地 |
| 生成模块层：检索后生成、证据约束、可插拔 LLM | 当前为规则化 AnswerAssembler，且最小 `qwen-plus` 接入已落地，但并非开题中设想的完整 Prompt 栈 | 已缩范围落地 |
| 引用 / 证据溯源层：回答附依据、可核对 | `primary / secondary / review`、`citations`、`review_notice`、`refuse_reason` 已落实 | 已落地 |
| 前端交互层：友好 Web 界面 | 当前已落地为原生同源 SPA + history UI，不是 React + Tailwind | 已缩范围落地 |
| 测试与结果分析层：功能测试、效果验证、案例分析 | 已有 smoke + 150 条 evaluator v2 + live-call artifact，但不是 200–250 条全量评测 | 已缩范围落地 |
| 部署与运行层：系统运行与演示 | 本地运行和同源演示链路存在，但材料尚未完全收口 | 已缩范围落地 |
| 《金匮要略》双书 | 当前主仓库未核验到相关数据、索引、接口或评估链路 | 不再实现 / 不纳入当前范围 |
| 200–250 条测试集 | 当前仅核验到 150 条 goldset 工作集 | 不再实现 / 不纳入当前范围 |
| React + Tailwind 前端 | 当前主仓库未核验到相关技术栈 | 不再实现 / 不纳入当前范围 |

补充说明：

- 开题报告中的“生成”不应再机械等同于“完整自由 LLM 生成问答系统”。
- 当前更准确的论文映射应为：“检索增强主链已完成，生成模块以规则化编排为主，并补入了最小真实 LLM answer_text 改写能力。”

## 6. 关键缺口清单

### P0 必补

1. 正式口径回写缺口
   - 主文档、论文表述与代码实物在 LLM 接入、chat history、前端形态上存在偏差。
   - 若不先回写，答辩时很容易出现“代码演示一个东西，正式文档写的是另一个东西”的硬伤。
2. 正式结构图缺口
   - 开题报告点名了系统功能结构图和系统架构结构图，但当前仓库未核验到可直接进入论文的正式图件。
   - 这会直接影响第 2 章和第 3 章的可写性与答辩展示质量。

### P1 建议补

1. 运行/部署材料收口
   - 需要统一启动命令、去掉 `app_minimal_api.py` 旧引用，并把本地运行链整理成单一可信入口。
2. 测试结果论文化整理
   - 当前评估 artifact 足够强，但还缺一份“可直接搬进论文第 4 章”的摘要表述。
3. Frontend/API 规格同步
   - 当前 `docs/specs/frontend_v1_spec.md` 与实际 conversations UI 已不一致，建议同步为当前真实形态。

### P2 可解释不补

1. chat history 作为答辩主线功能
   - 代码已存在，但不必抬升为当前答辩主线。
2. `/api/v1/answers/stream` 接入前端
   - 后端已存在，当前前端未接通也不阻塞主演示。
3. 多书扩展、React 重写、200–250 样本扩容
   - 当前阶段均可明确声明“不做”，不应再倒逼扩张。

## 7. 结论

**结论：当前系统已经具备“可写论文、可演示、可答辩”的基础。**

更准确地说：

- 主系统链路已经完整落地，单书 RAG 研读支持系统的核心能力已成型。
- 当前真正的主要风险不在“系统没做出来”，而在“正式文档与论文口径尚未完全跟上当前实现”。
- chat history v1 并非“未回流主仓库”；当前主仓库已核验到其代码、API 与前端接线，只是它不应计入当前冻结答辩主链。
- 因此，后续不应再优先扩功能，而应先补答辩口径与结构图等阻塞性材料。

## 8. 唯一下一轮建议

下一轮只建议做一个目标：

**论文/答辩口径与结构图封板 v1**

理由：

- 当前存在 P0 级阻塞缺口，先补这个比继续做前端 UI/UX 或算法优化更重要。
- 一旦正式口径、结构图和运行材料统一，当前系统就能更稳定地进入论文正文与答辩演示阶段。
