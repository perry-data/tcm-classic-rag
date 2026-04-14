# React 前端回退 (react_backout_v1)

## 1. 变更摘要
由于 React 前端重构版 (frontend_react/) 的交互与布局稳定性尚未达到生产演示标准，且为了优先保证核心研读流程的可靠性，本补丁撤销了 React 前端的所有实验性变更，恢复原生 frontend/ (HTML/JS/CSS) 为系统的默认演示前端。

## 2. 背景说明
*   **回退原因**：React 版本布局存在乱序、证据面板挤占主阅读轴等 UI/UX 问题，回退至原生版本可确保演示时体验稳定。
*   **回退范围**：后端 `minimal_api.py` 逻辑、前端入口、构建产物、重构说明文档。

## 3. 变更明细
### 回退/删除的内容：
*   **代码**：完全移除了 `frontend_react/` 源码目录及构建产物。
*   **后端**：回滚了 `backend/api/minimal_api.py` 中用于托管 React SPA 的相关逻辑（包括 `--react-dist` 参数、静态资源路由、SPA 路径回滚逻辑）。
*   **文档**：移除了相关重构及救火补丁说明 (`docs/patch_notes/frontend_react_refactor_v1.md` 等)。

### 恢复的内容：
*   **默认前端**：系统现在默认启动即 serve `frontend/index.html`。
*   **静态资源**：继续由原有的 `/frontend/` 路径提供原生静态资源支持。

## 4. 相关提交 (Commits)
本次回退针对的工作流在未提交状态下进行了 `git restore` 清理。若需追溯 React 实验性分支，请参考之前的会话快照。

## 5. 默认运行方式
启动后端：
```bash
python -m backend.api.minimal_api
```
启动后访问 `http://127.0.0.1:8000` 即可进入原生稳定版前端。

## 6. 验收总结
前端加载、会话创建、问答主链、对话切换均已在回退分支 `revert/react-backout-v1` 上通过回归验证。详见 `artifacts/react_backout_v1/verification.md`。
