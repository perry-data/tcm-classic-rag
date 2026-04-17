# 答辩运行手册 (毕业设计演示版 V1.0)

- 日期：2026-04-14
- 目标：确保系统在答辩/演示现场能够一键启动并稳定运行。

## 1. 运行准备 (Environment)

### 1.1 核心依赖
- **Python**: 推荐 3.12.x。
- **虚拟环境**: 已安装并激活 `.venv`。
- **API Key**: 确保已在根目录创建 `.env` 文件（参照 `.env.example`）并配置 `TCM_RAG_LLM_API_KEY`。

### 1.2 数据与索引检查
确保以下关键文件存在于 `artifacts/` 目录：
- `zjshl_v1.db` (SQLite 数据库)
- `dense_chunks.faiss` / `dense_main_passages.faiss` (向量索引)

*若向量索引缺失，请运行构建脚本：*
```bash
./.venv/bin/python scripts/build_dense_index.py
```

## 2. 启动系统 (Execution)

在项目根目录下执行统一启动命令：

```bash
# 激活虚拟环境 (macOS/Linux)
source .venv/bin/activate
# 首次或前端代码更新后，先构建 React 前端
cd frontend
npm install
npm run build
cd ..

# 启动前后端同源服务 (开启 LLM 支持)
python -m backend.api.minimal_api --host 127.0.0.1 --port 8000 --llm-enabled
```

*说明：启动后，访问地址为 [http://127.0.0.1:8000](http://127.0.0.1:8000)*

如需前端开发调试，可额外开一个终端：

```bash
cd frontend
npm run dev
```

此时前端地址为 [http://127.0.0.1:5173](http://127.0.0.1:5173)，并会自动代理 `/api` 到 `8000` 端口。

## 3. 演示路径 (Demo Queries)

请按以下顺序演示，以展示系统的不同反馈强度：

| 顺序 | 演示问题 | 预期结果 (亮点) |
| --- | --- | --- |
| 1 | `黄连汤方的条文是什么？` | **Strong 模式**：展示精准匹配、核心证据分层与引用。 |
| 2 | `烧针益阳而损阴是什么意思？` | **Weak 模式**：展示 LLM 对语义的解释、弱回答提醒与辅助资料。 |
| 3 | `书中有没有提到量子纠缠？` | **Refuse 模式**：展示系统的拒答机制与改问建议，体现学术严肃性。 |

## 4. 常见问题排查 (Troubleshooting)

1. **页面打不开 (Connection Refused)**:
   - 检查 `minimal_api` 进程是否仍在运行。
   - 确保端口 `8000` 未被其他程序占用。
2. **回答速度极慢**:
   - 检查网络连接（访问 LLM API 需要联网）。
   - 若环境无网络，可去掉 `--llm-enabled` 参数启动，系统将切换至纯规则编排模式。
3. **报错 `FAISS index not found`**:
   - 请务必先运行一次 `scripts/build_dense_index.py`。
4. **历史会话加载失败**:
   - 检查 `artifacts/chat_history_v1.db` 文件的读写权限。
