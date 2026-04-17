# 《伤寒论》研读支持系统 - 毕业设计演示版 v1.0 (Defense-ready)

本系统是一个面向《伤寒论》单书场景的中医经典研读支持系统。本项目作为本科毕业设计演示版，目标是可演示、可验证、可写论文，不以生产级部署为目标。

> **免责声明**：本系统仅供毕业设计演示使用，不作为临床诊疗建议。

当前主链路：

`query -> hybrid retrieval -> evidence gating -> answer assembler -> POST /api/v1/answers -> frontend`

## 目录概览

- `backend/api/minimal_api.py`
  系统 Web 服务入口与前后端同源入口。
- `backend/retrieval/hybrid.py`
  混合检索主入口，包含 sparse + dense + RRF + rerank。
- `backend/answers/assembler.py`
  回答编排主入口（规则编排 + LLM 改写）。
- `backend/strategies/general_question.py`
  总括类问题识别与分支组织逻辑。
- `scripts/build_v1_database.py`
  V1.0 数据库构建脚本。
- `scripts/build_dense_index.py`
  FAISS 向量索引构建脚本。
- `docs/final/`
  正式主文档：PRD、技术设计、系统规格说明书。
- `artifacts/`
  数据库、向量索引及自动化验收报告。
- `frontend/`
  同源单页聊天前端。

## 快速开始

### Windows 11

推荐参考：[windows_11_quickstart.md](docs/setup/windows_11_quickstart.md)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
.\.venv\Scripts\python.exe scripts\build_dense_index.py
.\.venv\Scripts\python.exe -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

### macOS / Linux

```bash
# 构建前端（首次运行需要）
cd frontend
npm install
npm run build
cd ..

# 构建向量索引（首次运行需要）
./.venv/bin/python scripts/build_dense_index.py

# 启动服务
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

访问地址：`http://127.0.0.1:8000/`

## 开发模式

如果你还会持续修缮功能，推荐直接跑开发栈：

### Windows 11

```powershell
.\.venv\Scripts\python.exe scripts\dev.py
```

### macOS / Linux

```bash
./.venv/bin/python scripts/dev.py
```

开发模式下：

- 前端通过 Vite 提供热更新，访问 `http://127.0.0.1:5173/`
- 后端在 `backend/` 与 `config/` 变更后会自动重启
- 如果你还要给后端传额外参数，可以写成 `python scripts/dev.py -- --llm-enabled`

## 部署建议

如果系统只是部署到你自己的 Windows 电脑，或者只给局域网里的几台设备访问，通常不需要额外租云服务器。直接在那台 Windows 机器上安装 Python、Node.js，构建一次前端，再启动 `backend.api.minimal_api` 就可以。

Docker 不是必须的。对你现在这种“还要边开发边测试”的阶段，先做原生部署通常更轻、更容易排错。等你后面想把环境彻底固定下来，或者准备迁移到别的机器，再补 Docker 也完全来得及。真正需要云服务器，通常是你想让外网用户随时访问、需要稳定公网地址、HTTPS、端口转发和长期在线的时候。

## 当前正式文档

- [PRD_v1.md](docs/final/PRD_v1.md)
- [technical_design_v1.md](docs/final/technical_design_v1.md)
- [system_spec_v1.md](docs/final/system_spec_v1.md)
- [defense_runbook_v1.md](docs/final/defense_runbook_v1.md) (即将生成)

## 核心特性

- **单书研读**：专注于《伤寒论》单书的深度解析与证据挖掘。
- **混合检索**：结合 BM25 与语义向量检索，通过 RRF 融合与重排序确保准确性。
- **证据分层**：将相关条文自动划分为核心证据、辅助证据与参考资料。
- **生成式回答**：基于证据驱动的规则化编排，并支持 LLM (如 Qwen-plus) 对回答文本进行改写优化。
