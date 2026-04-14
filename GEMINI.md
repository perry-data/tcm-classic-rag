# TCM 经典研读 RAG 系统 (tcm-classic-rag) - 项目上下文

## 项目概览
本项目是针对中医经典——**《伤寒论》**单书场景的检索增强生成 (RAG) 系统 MVP（最小可行性产品）。

### 核心架构
系统遵循结构化流水线：
`查询 (query) -> 混合检索 (hybrid retrieval) -> 证据准入 (evidence gating) -> 回答编排 (answer assembler) -> POST /api/v1/answers -> 前端 (frontend)`

- **混合检索：** 结合了稀疏检索（SQLite FTS5）和稠密检索（基于 BGE 嵌入的 FAISS），随后进行倒数排名融合 (RRF) 和重排序 (BGE Reranker)。
- **证据准入：** 根据相关性和质量将检索到的证据分类为 `primary`（核心）、`secondary`（辅助）和 `review`（参考）。
- **回答编排：** 一个复杂的、基于规则的逻辑引擎，用于对问题进行分类（例如：概括性提问 vs 细节查询），并组织最终的回答结构，包括引文和进一步追问建议。
- **Minimal API：** 一个轻量级的、线程安全的 HTTP 服务器，使用 Python 原生 `http.server` 构建，MVP 阶段避免了使用 Flask 或 FastAPI 等外部框架。
- **前端：** 一个由 API 服务器直接托管的单页应用 (SPA)。

## 构建与运行

### 环境准备
- 推荐使用 **Python 3.12**。
- 建议使用虚拟环境：`python -m venv .venv`。

### 安装
```bash
# Windows
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# macOS / Linux
./.venv/bin/python -m pip install -r requirements.txt
```

### 初始设置 (首次克隆)
FAISS 索引文件 (`.faiss`) 通常不包含在仓库中，必须在本地构建。
```bash
python scripts/build_dense_index.py
```

### 运行系统
1. **启动 API 服务器：**
   ```bash
   python -m backend.api.minimal_api --host 127.0.0.1 --port 8000
   ```
2. **访问前端：**
   在浏览器中打开 `http://127.0.0.1:8000/`。

### 冒烟测试与验证
可以通过直接运行各模块进行组件测试：
- **检索模块测试：** `python -m backend.retrieval.hybrid`
- **回答模块测试：** `python -m backend.answers.assembler`

## 开发规范

### 技术栈
- **语言：** Python 3.12+
- **数据库：** SQLite（用于结构化数据和 FTS5 检索）
- **向量库：** FAISS (CPU 版本)
- **嵌入模型：** `BAAI/bge-small-zh-v1.5`
- **重排序模型：** `BAAI/bge-reranker-base`
- **API：** 原生 `http.server.ThreadingHTTPServer`
- **前端：** 原生 HTML/CSS/JS

### 目录结构
- `backend/`: 核心逻辑（检索、回答、API、LLM）。
- `scripts/`: 数据处理、数据库构建及索引构建脚本。
- `docs/`: 详尽的文档（PRD、技术设计、规格说明）。
  - `docs/final/`: 当前系统的正式规格说明书。
- `artifacts/`: 生成的产物，如 `.db` 数据库、`.faiss` 索引及冒烟测试报告。
- `data/`: 原始及处理后的源数据。
- `frontend/`: 网页界面的静态资源。

### 核心逻辑与策略
- **基于规则的编排：** 大部分回答组织逻辑位于 `backend/answers/assembler.py`。
- **问题分类：** 概括性问题的触发规则定义在 `backend/strategies/general_question.py`。
- **LLM 集成：** 具备集成阿里云 Model Studio (通义千问) 的能力，尽管当前配置以基于规则的证据编排为主。

### 数据管理
- SQLite 数据库用于运行时数据 (`zjshl_v1.db`) 和聊天历史 (`chat_history_v1.db`)。
- 向量索引以 `.faiss` 和 `.json` (元数据) 对的形式存储在 `artifacts/` 目录中。

## 当前项目状态
- **范围：** 严格限于《伤寒论》单书。
- **回答生成：** 当前为证据驱动的基于规则的编排；正处于向 LLM 驱动生成的过渡阶段。
- **验证机制：** 依赖于本地“冒烟测试”以及 `scripts/` 目录下的自动化验证脚本。
