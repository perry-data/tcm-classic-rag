# tcm-classic-rag

《伤寒论》单书场景的中医经典研读支持系统 MVP。

当前主链路：

`query -> hybrid retrieval -> evidence gating -> answer assembler -> POST /api/v1/answers -> frontend`

## 目录概览

- `backend/api/minimal_api.py`
  最小 HTTP 服务与同源前端入口。
- `backend/retrieval/hybrid.py`
  当前检索主入口，包含 sparse + dense + RRF + rerank。
- `backend/answers/assembler.py`
  当前回答编排主入口。
- `backend/retrieval/minimal.py`
  minimal 检索基线与 hybrid 检索共享骨架。
- `backend/strategies/general_question.py`
  总括类问题识别与分支组织逻辑。
- `scripts/build_mvp_database.py`
  SQLite 数据库构建脚本。
- `scripts/build_dense_index.py`
  FAISS 索引构建脚本。
- `scripts/`
  数据验收与 safe 数据底座构建脚本。
- `config/`
  当前冻结配置，包括数据库 schema draft 和 evidence policy。
- `frontend/`
  同源单页前端。
- `docs/final/`
  当前正式主文档：PRD、技术设计、系统 spec。
- `docs/foundation/`
  范围冻结与项目边界约束。
- `docs/data/`
  数据验收、safe 数据策略、分层启用与数据库落库方案。
- `docs/contracts/`
  answer payload 与 minimal API 合同。
- `docs/specs/`
  当前仍有效的实现 spec 与冻结说明。
- `docs/notes/`
  patch note、排障记录、对齐说明。
- `docs/archive/`
  已被后续实现覆盖的历史方案文档。
- `docs/project/`
  项目盘点与清理快照，偏内部维护用途。
- `docs/proposal/`
  开题报告原件。
- `artifacts/`
  数据库、FAISS 索引、examples 和 smoke checks 产物。
- `data/`
  原始与处理后的数据底座。
- `dist/`
  safe 数据包产物。

## 常用命令

### Windows 11 fresh clone

新 Windows 11 机器请优先看：

- [windows_11_quickstart.md](docs/setup/windows_11_quickstart.md)

最小流程：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\build_dense_index.py
.\.venv\Scripts\python.exe -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

然后打开：

```text
http://127.0.0.1:8000/
```

说明：仓库包含 `artifacts/zjshl_mvp.db`，但 `.faiss` 二进制索引默认不入库，所以 fresh clone 后需要先运行一次 `scripts/build_dense_index.py`。

### macOS / Linux

构建数据库：

```bash
./.venv/bin/python scripts/build_mvp_database.py --safe-source dist/zjshl_dataset_v2_mvp_safe.zip --full-source data/processed/zjshl_dataset_v2
```

构建向量索引：

```bash
./.venv/bin/python scripts/build_dense_index.py
```

运行检索 smoke：

```bash
./.venv/bin/python -m backend.retrieval.hybrid
```

运行回答 smoke：

```bash
./.venv/bin/python -m backend.answers.assembler
```

启动前后端同源服务：

```bash
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

## 当前正式文档

- [PRD_v1.md](docs/final/PRD_v1.md)
- [technical_design_v1.md](docs/final/technical_design_v1.md)
- [system_spec_v1.md](docs/final/system_spec_v1.md)

## 说明

- 当前正式范围是《伤寒论》单书 MVP，不是多书系统。
- 当前回答层是证据驱动的规则化编排，尚未接入真实 LLM 生成模块。
- `docs/project/` 下的盘点/清理文档保留为维护快照，不代表它们的路径快照会随每次整理自动更新。
