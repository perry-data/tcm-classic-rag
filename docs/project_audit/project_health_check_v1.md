# 项目体检报告 v1

- 扫描日期：2026-04-21
- 项目根目录：`/Users/man_ray/Projects/Python/tcm-classic-rag`
- 本轮边界：不改核心业务逻辑，不改 `answer_mode`、payload contract、检索主链路，不删除无法确认用途的重要文件。

## 1. 总体判断

当前项目主运行结构已经基本清晰：`backend/` 是后端主链路，`frontend/` 是前端工程，`scripts/` 是构建与评测入口，`config/` 是策略/评测配置，`data/` 是原始与处理后数据，`artifacts/` 是运行、评测、实验和截图产物，`docs/` 是正式文档与过程文档。

真正混乱的地方不在源码主链路，而在“产物层”和“文档层”：

1. `artifacts/` 过胖，包含数据库、FAISS 索引、Hugging Face 缓存、评测报告、实验报告、前端截图、运行时聊天库等多种职责。
2. `docs/` 主题细分很多，但 `docs/project/` 中旧清理清单已明显滞后，容易和当前结构冲突。
3. `thesis_private/` 是论文私有材料与生成产物混合区，适合保留，但后续应继续区分“正文草稿、最终图件、渲染检查、临时探针”。
4. 本地缓存和临时文件数量多：`__pycache__/`、`.DS_Store`、`.playwright-cli/`、Word 临时文件、`artifacts/hf_cache/`。

当前工作树在本轮开始前已有既有改动：

- `backend/answers/assembler.py` 已修改。本轮没有触碰该文件。
- `.playwright-cli/` 是未跟踪本地快照目录。本轮仅补入 `.gitignore`，没有移动这些快照。

## 2. 当前主目录职责

| 目录 / 文件组 | 当前职责 | 判断 |
| --- | --- | --- |
| `backend/` | API、检索、回答编排、LLM、对话历史、策略和检查脚本 | 清晰，属于 C 类核心，不应在清理轮触碰 |
| `frontend/` | Vite/React 前端源码与构建配置 | 清晰，`frontend/dist/` 是可重建构建产物 |
| `scripts/` | 数据构建、索引构建、评测、审计 replay、开发启动 | 基本清晰，但有若干一次性实验脚本，需保留可复现性后再归档 |
| `tests/` | pytest 测试，目前主要覆盖 commentarial 相关能力 | 清晰但覆盖面偏窄 |
| `config/` | 数据层、评测、受控 replay 配置 | 清晰，属于运行/验证配置 |
| `data/` | 原始数据包与处理后数据底座 | 清晰，属于数据源，禁止随意移动 |
| `dist/` | safe 数据包发布物 | 当前只有 `zjshl_dataset_v2_v1_safe.zip`，可重建但仍是重要交付物 |
| `docs/` | 正式文档、设计、评测、补丁说明、论文材料、项目审计 | 职责多，需用 README 和归档约束降低混淆 |
| `artifacts/` | 运行产物、评测产物、实验产物、截图、缓存、runtime | 过胖且职责混杂，是后续重点 |
| `reports/` | 数据验收报告摘要 | 与 `artifacts/`/`docs/data/` 有交叉，但当前体量小 |
| `deploy/` / `.github/` | 部署脚本、systemd/caddy、GitHub Actions | 清晰 |
| `thesis_private/` | 论文私有草稿、图件、截图、参考文献、生成检查 | 不入 Git，体量较大；可内部再分层 |
| `thesis_materials/` | 外部论文/参考材料 | 不入 Git，保留为材料库 |

## 3. 重复版本与历史残留

| 现象 | 例子 | 判断 |
| --- | --- | --- |
| 评测 goldset 多版本并存 | `goldset_v2_working_102.json`、`126.json`、`150.json` | 不是垃圾；它们记录扩样阶段。后续可在 README 标明最新主版本是 150 |
| 批次评测报告多版本 | `goldset_v2_batchA/B/C_*`、`evaluator_v1_report.*`、`evaluator_v2_report.*` | 多为评测证据，不宜删除；可按 batch 归档 |
| 文档版本多 | `chapter_03_data_methods_draft.md`、`chapter_03_data_methods_draft_v1_1.md` 等 | 论文写作版本，不入 Git；后续在 `thesis_private/README` 里声明当前版本 |
| 旧清理盘点文件滞后 | 原 `docs/project/project_inventory.md` 等 | 已归档到 `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/` |
| 正式目录混入临时文件 | 原 `docs/proposal/.!38916!...docx` | 已隔离到 `docs/project_audit/archive/quarantine_temp_files_2026-04-21/` |
| runtime DB 双位置 | `artifacts/chat_history_v1.db`、`artifacts/runtime/chat_history_v1.db` | 都不是 Git 跟踪文件；后续确认实际服务路径后再清理 |

## 4. 过胖或职责混杂目录

| 目录 | 观察 | 建议 |
| --- | --- | --- |
| `artifacts/` | 约 1.2G，其中 `artifacts/hf_cache/` 约 1.1G；同时混有评测、实验、截图、runtime、数据库和缓存 | 先分“必须保留证据 / 可重建产物 / 本地缓存 / runtime 私有状态”，不要直接删 |
| `docs/patch_notes/` | 50+ 个 patch note，按历史轮次累积 | 保留；后续可补索引 README，按主题分组 |
| `docs/evaluation/` | 评测规范、reannotation 指南、batch 计划混在一起 | 保留；可补 `README` 标明 evaluator v1/v2 和 goldset 主线 |
| `thesis_private/assembled/` | docx、生成图片、render check、template probe 混合 | 保留；后续把 `_template_probe`、`_word_test`、`_render_check_word` 标成临时/验证产物 |
| `data/processed/commentarial_layer_round3/commentarial_handoff_bundle/` | handoff 包含数据、测试、说明、manifest | 属于一次性交接包，但可能仍为 commentarial 证据来源；不动 |

## 5. 临时文件 / 缓存 / 废弃候选

| 路径 / 模式 | 状态 | 判断 |
| --- | --- | --- |
| `__pycache__/`、`*.pyc` | Git 忽略 | 可随时重建；后续可直接清理 |
| `.DS_Store` | Git 忽略 | macOS 垃圾文件；后续可清理 |
| `.playwright-cli/` | 本轮前未跟踪，本轮已加入 `.gitignore` | 本地浏览器快照；保留当前文件，不再进入 Git 噪声 |
| `artifacts/hf_cache/` | Git 忽略，约 1.1G | 模型缓存，可重建；若磁盘紧张可后续删除 |
| `artifacts/runtime/*.db` | Git 忽略 | 本地运行状态，不应提交；删除前需确认不需要保留历史聊天 |
| `frontend/dist/` | Git 忽略 | 前端构建产物，可重建；部署时可能需要，所以不直接删 |
| `thesis_private/assembled/~$*.docx` | Git 忽略 | Word 临时锁文件；可后续清理 |
| `docs/project_audit/archive/quarantine_temp_files_2026-04-21/*.tmp` | 本轮隔离 | 已从正式 proposal 目录移出，保留可回溯 |

## 6. 结论

项目当前不是“源码结构混乱”，而是“证据、实验、论文、运行产物累积后缺少索引和分层”。下一轮清理不应从 `backend/` 或 `frontend/` 开始，而应先从 `artifacts/`、旧报告索引、临时缓存和论文生成产物入手。
