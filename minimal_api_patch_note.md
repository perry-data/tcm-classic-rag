# Minimal API Patch Note

## 本轮变更

- 新增最小 HTTP transport adapter：`app_minimal_api.py`
- 落地最小接口：`POST /api/v1/answers`
- 请求体只要求：
  - `query`
- 响应体直接返回当前 answer payload，不额外包裹 `data`
- 新增 HTTP 侧验证产物：
  - `artifacts/api_examples.json`
  - `artifacts/api_smoke_checks.md`

## 设计原则

本轮实现刻意保持极薄：

- 不引入完整后端框架
- 不重构现有检索或 answer assembler
- 不改 answer payload 合同
- 不改数据库 schema
- 不做鉴权、用户系统、历史记录、多书扩展

HTTP adapter 的职责只有一个：

- 接收 `query`
- 调用现有 `AnswerAssembler`
- 直接返回稳定 answer payload

## 保持不变的业务规则

以下业务规则本轮没有改动：

- Hybrid retrieval 仍由 `run_hybrid_retrieval.py` 负责
- evidence gating 规则保持不变
- `strong / weak_with_review_notice / refuse` 三模式保持不变
- `annotation_links` 继续禁用
- `chunks` 不直接进入 `primary_evidence`
- `annotations` 不进入 `primary_evidence`
- `passages / ambiguous_passages` 不进入 `primary_evidence`
- 黄连汤方主证据精度补丁保持不回归
- answer payload 顶层字段保持不变

## 启动方式

启动服务：

```bash
./.venv/bin/python app_minimal_api.py --host 127.0.0.1 --port 8000
```

运行 HTTP smoke checks：

```bash
./.venv/bin/python app_minimal_api.py --smoke
```

## 本轮范围外

- 前端页面
- UI
- payload 重构
- Hybrid retrieval 重构
- answer assembler 重构
- 鉴权
- 用户系统
- 多书扩展
