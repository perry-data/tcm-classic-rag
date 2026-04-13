# Frontend UI/UX Polish v1 验收说明

## 结论

本轮只围绕聊天页简约化修缮收口，四个目标均已处理：

- 左侧历史栏改为稳定侧栏，列表区独立滚动
- `新建对话` 回到空白态，不再残留旧会话状态
- 输入区明显收紧，视觉重量下降
- 回复区改成正文优先、次级信息弱化的轻量层级

## 最小回归结果

- `node --check frontend/app.js` 通过
- `PYTHONPYCACHEPREFIX=/tmp/tcm_pycache python3 -m py_compile backend/api/minimal_api.py backend/retrieval/minimal.py` 通过
- 本地前端页面可正常加载历史列表与历史会话
- `POST /api/v1/conversations` 可创建新会话
- `POST /api/v1/conversations/{id}/messages` 可正常完成首轮发送并自动生成标题
- `GET /api/v1/conversations/{id}` 可恢复完整消息流
- `DELETE /api/v1/conversations/{id}` 可删除会话

## 截图

- `sidebar_stable.png`
- `new_chat_reset.png`
- `composer_compact.png`
- `assistant_compact.png`
