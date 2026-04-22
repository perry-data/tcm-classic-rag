# 目录整理建议 v1

- 目标：在不破坏当前运行前提下，让目录职责更清楚。
- 原则：先加索引和归档，不大规模改路径；核心代码路径保持稳定。

## 1. 建议的目标结构

```text
tcm-classic-rag/
  backend/                 # 后端运行主链路：API / retrieval / answers / llm / history
  frontend/                # 前端工程源码；dist 为可重建构建产物
  scripts/                 # 可执行构建、评测、replay、开发启动脚本
  tests/                   # pytest 测试
  config/                  # 运行策略、评测 schema、受控 replay 配置
  data/
    raw/                   # 原始输入数据
    processed/             # 处理后数据底座
  dist/                    # 可发布/交付的数据包，不放临时构建散件
  docs/
    final/                 # 答辩/论文可引用的正式文档
    contracts/             # API/payload 合同
    specs/                 # 功能与技术规格
    design/                # 单项设计说明
    evaluation/            # 评测方案、标注准则、评估语义
    patch_notes/           # 历史变更说明，建议补 README 索引
    project_audit/         # 项目体检、清理计划、历史审计
    archive/               # 过时但需保留的历史文档
  artifacts/
    evaluation/            # goldset、evaluator 报告
    experiments/           # 受控实验、before/after
    frontend/              # 前端截图和验收图片
    runtime/               # 本地运行状态，默认不入 Git
    cache/                 # 可重建缓存，默认不入 Git
    archive/               # 历史产物归档
  reports/                 # 若继续保留，只放脚本生成的简短摘要；也可迁入 artifacts/reports/
  deploy/                  # 部署脚本和服务配置
  thesis_private/          # 本地论文私有区，不入 Git
  thesis_materials/        # 本地参考材料库，不入 Git
```

## 2. 不建议移动的路径

| 路径 | 原因 |
| --- | --- |
| `backend/` | 当前导入关系、API 启动命令和 README 均以此为准 |
| `frontend/src/` | 前端工程结构清楚，移动会影响 Vite/TS 配置 |
| `scripts/build_v1_database.py`、`scripts/build_dense_index.py` | README、后端错误提示和部署说明都引用这些入口 |
| `data/raw/`、`data/processed/zjshl_dataset_v2/` | 数据源与构建脚本绑定，移动风险高 |
| `dist/zjshl_dataset_v2_v1_safe.zip` | safe 数据包已有明确交付含义 |
| `docs/final/`、`docs/contracts/` | 正式文档和合同，不和过程文档混放 |

## 3. 建议渐进整理步骤

### 第 1 步：索引优先

补充 README，而不是先移动文件：

- `docs/patch_notes/README.md`：按 backend/frontend/evaluation/data/thesis 分组列 patch note。
- `docs/evaluation/README.md`：说明 evaluator v1/v2、goldset 主版本、reannotation 文件关系。
- `artifacts/README.md`：声明哪些是可重建产物、哪些是论文证据、哪些是 runtime/cache。

### 第 2 步：归档历史文档

已经开始执行：

- 旧 `docs/project/*` 已归档到 `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/`。
- Word 临时文件已隔离到 `docs/project_audit/archive/quarantine_temp_files_2026-04-21/`。

下一步可考虑：

- 将 `docs/archive/` 里的早期 retrieval upgrade 文档保留为历史文档，不再和当前 specs 混读。
- 将 `docs/system_completion_audit_v1.md` 这类根层文档移动或复制索引到 `docs/project_audit/`，但需先确认引用关系。

### 第 3 步：整理 artifacts

建议不要一次性重命名所有 artifacts。先新增 README 标准，再按小批次迁移：

| 当前路径 | 建议方向 | 风险 |
| --- | --- | --- |
| `artifacts/frontend_react_refactor_v1/`、`frontend_uiux_polish_v1/`、`frontend_evidence_marker_ui_v1/` | 统一到 `artifacts/frontend/` 下 | 中等；可能影响文档引用 |
| `artifacts/evaluation/goldset_v2_working_102.json`、`126.json` | 移入 `artifacts/evaluation/archive/`，保留 `150` 在顶层 | 中等；需要更新评测文档引用 |
| `artifacts/hf_cache/` | 改为 `artifacts/cache/hf/` 或继续忽略原路径 | 中等；脚本/模型缓存路径可能依赖环境变量 |
| `artifacts/runtime/` | 保留 runtime 专区 | 低；不要提交 DB |
| `artifacts/experiments/` | 保留，补 README | 低 |

### 第 4 步：脚本分层

当前 `scripts/` 不算太乱，暂不建议大搬家。后续如要分层，可采用：

```text
scripts/
  build/        # database/index/safe dataset
  evaluate/     # evaluator v1/v2
  experiments/  # formula_effect、controlled replay
  dev.py
  bootstrap_windows.ps1
```

但这会影响 README、文档命令和 imports，必须单独一轮做，不适合本轮。

## 4. 目录职责约束

1. `backend/` 只放运行代码和后端检查，不放一次性报告。
2. `scripts/` 只放可执行入口，不放生成结果。
3. `docs/final/` 只放答辩/论文可直接引用的正式材料。
4. `docs/project_audit/` 专门放体检、审计、清理计划和历史审计归档。
5. `artifacts/runtime/` 和缓存目录默认不入 Git。
6. `thesis_private/` 保持本地私有，不作为系统源码交付的一部分。
