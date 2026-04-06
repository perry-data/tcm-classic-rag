# Change Workflow v1

## 1. 目的

本流程只服务当前这个毕业设计项目，不追求大公司流程完整度，只追求三件事：

1. 不让需求漂移。
2. 不让文档再次落后于实现。
3. 不让“能跑的 MVP”被临时改动破坏。

## 2. 总原则

- 先补文档，再改代码。
- 先判断是不是影响正式基线，再决定改多大。
- 任何新增功能都不能绕开基线文档。
- 任何会影响 API / payload / 证据门控 / 正式入口的改动，都不能只靠口头说明。

## 3. 变更分类

### A 类：直接小修

适用条件：

- 只改文案、注释、错别字、展示细节
- 不改变行为
- 不改变正式入口
- 不改变 API / payload / evidence gating
- 不影响冻结样例

处理要求：

- 可以直接修改
- 不强制写 change note
- 但仍要在交付说明里写清改了什么

### B 类：范围内行为修正

适用条件：

- 修 bug
- 调小参数
- 修补模板文案
- 补回归验证
- 但不新增正式功能，不改变范围定义，不改变合同

处理要求：

- 先写一个简短 change note
- 不必改 PRD
- 若涉及实现机制或回归基线变化，必须更新 tech spec

### C 类：范围内新增功能

适用条件：

- 仍属于单书研读支持
- 但会新增一个用户可见能力或新用户路径

处理要求：

- 先写 change note
- 必须判断是否要更新 PRD
- 必须更新 tech spec
- 若引入新的正式入口、正式样例或正式文档，还要更新 baseline inventory

### D 类：基线级变更

适用条件：

- 改 API contract
- 改 payload contract
- 改正式入口
- 改 evidence gating
- 改数据边界
- 把现有扩展能力升级成正式承诺

处理要求：

- 不能直接写代码
- 必须先更新 PRD
- 必须先更新 tech spec
- 必须更新 baseline inventory
- 必须在 change note 中写清回归影响

## 4. 一个新功能进入实现前，必须先补什么文档

默认最小文档包如下：

1. 一个简短 `change note`
2. 若改变正式承诺，更新 `docs/PRD_mvp_baseline_v1.md`
3. 若改变实现链路、合同、数据边界、运行资产，更新 `docs/tech_spec_mvp_baseline_v1.md`
4. 若新增正式入口、正式样例、正式文档，更新 `docs/baseline_inventory_v1.md`

## 5. 什么情况下只写 change note

满足以下条件时，只写 change note 即可：

- 没有新增用户可见能力
- 没有改变正式范围
- 没有改变 API / payload
- 没有改变 evidence gating 规则
- 没有新增正式入口
- 只是修复现有能力中的实现问题或补充验证

change note 至少写清 5 项：

- 改动目标
- 不改什么
- 影响文件
- 回归基线
- 风险与回滚点

## 6. 什么情况下必须更新 PRD / Tech Spec

### 必须更新 PRD 的情况

- 新增一个正式功能
- 改变目标用户
- 改变“系统解决什么问题”
- 改变 MVP 成功标准
- 把当前不承诺的扩展能力升级成正式能力

### 必须更新 Tech Spec 的情况

- 改数据源
- 改数据库结构或构建链
- 改 retrieval 主链
- 改 answer payload
- 改 API contract
- 改 evidence gating
- 改正式运行入口
- 改正式回归样例

## 7. 什么情况下允许直接小修

只有同时满足下面条件，才允许直接小修：

- 不新增功能
- 不改正式合同
- 不改运行路径
- 不改回归预期
- 不新增或替换正式基线文件

典型例子：

- 文档错字
- 注释修正
- 样式微调但不改前端数据依赖
- 错误提示文案微调

## 8. Coding Agent 每轮交付必须包含什么

每轮交付至少要包含：

1. 改动范围说明
2. 明确列出是否触碰以下基线：
   - PRD
   - tech spec
   - API contract
   - payload contract
   - evidence gating
   - 正式入口
3. 验证命令与结果
4. 尚未解决的风险或假设
5. Git 收尾结果

如果本轮是功能开发，还必须回答：

- 这个功能属于哪一类变更
- 变更前是否补了 change note
- 原三条冻结样例有没有回归

## 9. 每轮最小验收要看什么

### 文档类改动

- 是否补齐了应更新的文档
- 文档是否和当前真实实现一致
- 是否明确标注 canonical / supporting / legacy

### 代码类改动

- 正式入口是否仍可运行
- 原三条冻结样例是否保持
- API contract 是否未漂移
- payload 顶层字段是否未漂移
- 若改了 gating，是否有明确回归说明

### 本项目最小必看验收项

- `POST /api/v1/answers` 可调用
- 前端首页仍可加载
- `黄连汤方的条文是什么？ -> strong`
- `烧针益阳而损阴是什么意思？ -> weak_with_review_notice`
- `书中有没有提到量子纠缠？ -> refuse`

## 10. Git 收尾要求

每轮收尾至少做以下动作：

1. `git status --short`
2. 自查 `git diff --stat` 或等价 diff
3. 只 stage 本轮相关文件
4. commit message 必须说明范围

推荐 commit message 形式：

```text
docs: add mvp baseline pack v1
fix: preserve hybrid retrieval gating baseline
feat: add <feature> within frozen mvp scope
```

额外要求：

- 不把无关变更混进同一个 commit
- 不把历史垃圾文件顺手一起改掉，除非本轮任务明确包含它
- 若使用分支 / PR，则标题和说明也必须沿用同一口径

## 11. 本流程对当前项目的硬约束

- 比较问答、总括问答、答辩增强页等，不得因为“仓库里已有代码”就默认算正式需求。
- 当前正式基线仍是单书、证据分层、三模式、最小 API、同源前端。
- 任何让这条主链失真的改动，都必须先更新文档，再动实现。
