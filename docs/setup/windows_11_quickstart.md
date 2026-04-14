# Windows 11 Quickstart

本文说明如何在一台全新的 Windows 11 机器上，从 fresh clone 启动当前项目。

## 1. 前置条件

建议安装：

1. Git for Windows
2. Python 3.12
3. PowerShell

当前项目是 Python 后端 + 原生前端，不需要 Node.js。

## 2. 克隆仓库

```powershell
git clone https://github.com/perry-data/tcm-classic-rag.git
cd tcm-classic-rag
```

## 3. 创建虚拟环境

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

如果你的机器没有 `py` 启动器，也可以用：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

## 4. 安装依赖

如果你想用一键准备脚本，可以直接运行：

```powershell
.\scripts\bootstrap_windows.ps1
```

如果 PowerShell 拦截本地脚本，可先在当前窗口临时放行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

该脚本会创建 `.venv`、安装依赖并生成 FAISS 索引。若你更希望逐步执行，请继续按下面步骤操作。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

说明：

1. 首次安装会拉取 `torch`、`sentence-transformers`、`faiss-cpu` 等较大的包，需要等待一段时间。
2. 当前项目运行时会下载 HuggingFace 模型到 `artifacts\hf_cache`，该目录不会入库。
3. 如果 `faiss-cpu` 在你的 Windows 环境里 pip 安装失败，建议改用 Miniforge/Conda 安装 `faiss-cpu`，再用 pip 安装其余依赖。

Conda 兜底示例：

```powershell
conda create -n tcm-rag python=3.12
conda activate tcm-rag
conda install -c conda-forge faiss-cpu
python -m pip install numpy==2.4.4 protobuf==7.34.1 sentence-transformers==5.3.0 torch==2.11.0
```

## 5. 准备运行产物

仓库已经包含 SQLite 数据库 `artifacts\zjshl_v1.db`，但 FAISS `.faiss` 二进制索引默认不入库，需要在新机器上生成一次：

```powershell
.\.venv\Scripts\python.exe scripts\build_dense_index.py
```

这一步会生成：

1. `artifacts\dense_chunks.faiss`
2. `artifacts\dense_main_passages.faiss`
3. `artifacts\dense_chunks_meta.json`
4. `artifacts\dense_main_passages_meta.json`

如果你删除了数据库，也可以重建：

```powershell
.\.venv\Scripts\python.exe scripts\build_v1_database.py --safe-source dist\zjshl_dataset_v2_v1_safe.zip --full-source data\processed\zjshl_dataset_v2
```

## 6. 运行 smoke check

```powershell
.\.venv\Scripts\python.exe -m backend.api.minimal_api --smoke
```

如果 smoke check 通过，说明数据库、FAISS 索引、模型依赖和 answer payload 合同都能跑通。

## 7. 启动系统

```powershell
.\.venv\Scripts\python.exe -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

然后打开浏览器：

```text
http://127.0.0.1:8000/
```

## 8. 最小接口测试

另开一个 PowerShell 窗口：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/v1/answers `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"黄连汤方的条文是什么？\"}"
```

预期返回 JSON，且包含：

1. `answer_mode`
2. `answer_text`
3. `primary_evidence`
4. `citations`

## 9. 常见问题

### 9.1 启动时报缺少 `dense_chunks.faiss`

先运行：

```powershell
.\.venv\Scripts\python.exe scripts\build_dense_index.py
```

### 9.2 首次运行很慢

首次运行需要下载 embedding 与 rerank 模型，并缓存到 `artifacts\hf_cache`。后续运行会复用缓存。

### 9.3 不想激活虚拟环境

本文所有命令都直接使用 `.\.venv\Scripts\python.exe`，不需要执行 `Activate.ps1`。

### 9.4 PowerShell 不识别中文或 curl 行续写

可以直接访问前端页面 `http://127.0.0.1:8000/`，或把 curl 命令写成单行：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/v1/answers -H "Content-Type: application/json" -d "{\"query\":\"黄连汤方的条文是什么？\"}"
```
