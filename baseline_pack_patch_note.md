# Baseline Pack Patch Note

## 本轮做了什么

本轮没有继续新增业务功能，而是围绕当前真实项目状态建立了“项目基线文档包 v1”。

新增文档包括：

- `docs/PRD_mvp_baseline_v1.md`
- `docs/tech_spec_mvp_baseline_v1.md`
- `docs/repo_map_v1.md`
- `docs/baseline_inventory_v1.md`
- `docs/change_workflow_v1.md`
- `docs/cleanup_plan_v1.md`
- `baseline_pack_patch_note.md`

本轮完成的核心工作是：

1. 定义当前正式基线是什么
2. 定义哪些文件是 supporting，哪些是 legacy / patch / historical
3. 明确当前 MVP 的正式范围和非目标范围
4. 明确后续新增功能前必须遵守的最小变更流程
5. 给出最小整编方案，但不做激进重构

## 本轮没有做什么

本轮明确没有做以下事情：

- 没有新增业务功能
- 没有修改核心问答逻辑
- 没有推翻当前最小 API
- 没有推翻当前 payload contract
- 没有移动核心运行入口
- 没有大规模整理目录
- 没有重开多书、知识图谱、多 agent、数据库重做等讨论

## 为什么本轮先做文档整编，而不是继续加功能

原因很直接：

1. 当前 MVP 已经跑通，但正式边界、正式入口、正式文档没有统一口径。
2. 如果继续直接加功能，最容易发生的是：
   - 需求漂移
   - 根目录继续堆 patch note
   - 代码和文档继续脱节
   - 答辩和论文越来越难讲清
3. 当前仓库里已经出现“实际代码能力大于正式范围”的迹象，例如比较问答和总括问答扩展；如果现在不先封板，后面会更难区分什么是正式承诺、什么只是现存扩展。

因此，本轮优先把“当前系统到底是什么、后续应按什么流程继续改”写死，比再加一个功能更有价值。

## 本轮产出后的状态

经过本轮整编，当前项目已经具备：

- 正式 PRD
- 正式 tech spec
- 正式 repo map
- 正式 baseline inventory
- 正式最小 change workflow
- 正式 cleanup plan

这意味着后续继续开发时，已经不需要再重新讨论“当前正式基线是什么”。

## 本轮最小验证

本轮只新增文档，没有改动核心逻辑。为确认现有闭环未被破坏，已做最小非侵入式验证：

- 启动：`./.venv/bin/python app_minimal_api.py --host 127.0.0.1 --port 8001`
- 路由检查：
  - `GET / -> 200`
  - `GET /frontend/app.js -> 200`
  - `GET /frontend/styles.css -> 200`
  - `HEAD /api/v1/answers -> 405` 且 `Allow: POST`
- 三条冻结样例：
  - `黄连汤方的条文是什么？ -> strong`
  - `烧针益阳而损阴是什么意思？ -> weak_with_review_notice`
  - `书中有没有提到量子纠缠？ -> refuse`

因此，本轮文档整编没有破坏现有最小 API、同源前端入口和冻结样例模式。

## 本轮建议的下一步

下一轮如果要继续推进，应按 `docs/change_workflow_v1.md` 执行：

1. 先判断变更类型
2. 先补 change note / 必要文档
3. 再实现
4. 保住冻结样例与正式入口

在此之前，不建议再直接往根目录追加新的 patch note 并继续加功能。
