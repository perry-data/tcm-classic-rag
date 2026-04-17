# Windows 11 Quickstart

本文说明如何在一台全新的 Windows 11 机器上，从 fresh clone 启动当前项目。

## 1. 前置条件

建议安装：

1. Git for Windows
2. Python 3.12
3. Node.js LTS
4. PowerShell

当前项目现在是 Python 后端 + React 前端。开发和生产构建都需要 Node.js。

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

该脚本会创建 `.venv`、安装 Python 依赖、安装前端依赖、构建 React 前端，并在需要时生成 FAISS 索引。若你更希望逐步执行，请继续按下面步骤操作。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
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

## 8. 开发模式（热更新）

如果你后面还要继续修缮功能，建议直接使用开发模式：

```powershell
.\.venv\Scripts\python.exe scripts\dev.py
```

然后访问：

```text
http://127.0.0.1:5173/
```

说明：

1. React 前端通过 Vite 提供热更新，改动保存后浏览器会自动刷新或局部热替换。
2. Python 后端会在 `backend/` 和 `config/` 的代码或 JSON 改动后自动重启。
3. 如果你需要给后端追加参数，可用 `.\.venv\Scripts\python.exe scripts\dev.py -- --llm-enabled` 这种写法。

## 9. 最小接口测试

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

## 10. 部署到你自己的 Windows 电脑

如果这套系统只是你自己使用，或者只在宿舍/家里/办公室局域网里访问，一般不需要租云服务器。你可以直接在自己的 Windows 电脑上：

1. 安装 Python 3.12 和 Node.js
2. clone 仓库并完成上面的 bootstrap
3. 用 `npm run build` 生成前端静态文件
4. 用 `python -m backend.api.minimal_api --host 0.0.0.0 --port 8000` 启动服务

这样同一局域网的其他设备，也可以通过 `http://你的Windows电脑IP:8000/` 访问。

Docker 不是必须的。现阶段你还会继续开发、继续改功能，原生运行通常更省事，也更容易直接看日志和改代码。Docker 更适合你后面想把环境彻底固定住、复制到另一台机器、或者准备正式上线时再补。

如果你要让公网用户长期访问，就要额外考虑：

1. 公网 IP 或内网穿透
2. 路由器端口转发
3. HTTPS 证书
4. Windows 防火墙与访问控制
5. 电脑长期开机和断电恢复

## 11. 常见问题

### 11.1 启动时报缺少 `dense_chunks.faiss`

先运行：

```powershell
.\.venv\Scripts\python.exe scripts\build_dense_index.py
```

### 11.2 首次运行很慢

首次运行需要下载 embedding 与 rerank 模型，并缓存到 `artifacts\hf_cache`。后续运行会复用缓存。

### 11.3 不想激活虚拟环境

本文所有命令都直接使用 `.\.venv\Scripts\python.exe`，不需要执行 `Activate.ps1`。

### 11.4 PowerShell 不识别中文或 curl 行续写

可以直接访问前端页面 `http://127.0.0.1:8000/`，或把 curl 命令写成单行：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/v1/answers -H "Content-Type: application/json" -d "{\"query\":\"黄连汤方的条文是什么？\"}"
```

### 11.5 提示 `npm` 不存在

说明当前机器还没装 Node.js，或者没有把 Node.js 加到 PATH。安装 Node.js LTS 后，重新打开一个新的 PowerShell 窗口再执行命令即可。
