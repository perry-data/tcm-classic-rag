# Frontend Minimal Chat Layout Patch Note

## 本轮目标

本轮只做一件事：

- 把前端重构成更接近现代极简对话页的单轮聊天界面

范围只限于：

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

并补充：

- `docs/patch_notes/frontend_minimal_chat_layout_patch_note.md`
- `artifacts/demo/frontend_minimal_chat_layout_demo.md`

本轮未改动：

- `backend/api/minimal_api.py`
- `backend/answers/assembler.py`
- answer payload 语义
- retrieval / rerank / prompt 主逻辑

## 结构改动

页面重新收束为三层：

1. 极轻量顶部区
   - 只保留系统名、单轮模式与实时状态
2. 中间对话主区域
   - 用户问题卡
   - assistant 回答卡
3. 底部轻量输入器
   - 单列 slim composer
   - 弱化样例入口

和上一轮相比，页面不再像：

- 顶部说明页
- 中部结果面板
- 底部大控制台

而是回到：

- 先看问题
- 再看回答
- 需要时再展开依据

## 删字重构

本轮删除或压缩了以下“废话型文案”：

- 顶部 hero 介绍
- header meta 区的接口说明
- “页面把一次提问组织成同一阅读流”这类布局说明
- `assistant response` / `supporting` 的结构解释
- `composer-copy` 整块说明
- “当前页面只承接一条用户问题和一条系统回答”这类产品说明书文案
- 主依据 / 补充依据 / 核对材料 / 引用 / 改问建议的逐块长提示

保留下来的文案只服务当前决策：

- strong / weak / refuse / error 状态解释
- `review_notice`
- `refuse_reason`
- 错误提示
- 极少量输入提示

## Composer 缩小方式

底部 composer 从“面板式控制区”改成了真正的轻输入器：

- 删除 `composer-copy`
- 移除“大标题 + 描述 + 输入框”的组合
- 布局改成单列输入器
- `textarea` 初始高度改成单行自适应
- 发送按钮尺寸与输入器重新协调
- 样例入口改成右下角弱化 `details`
- 保留 sticky，但视觉厚度明显下降

## 默认展示策略

本轮把“正文优先，依据后看”落实为默认行为：

- 回答正文保持主阅读焦点
- `primary_evidence` 仍可直接显示，但作为回答下属区块
- `secondary_evidence / review_materials / citations / followups`
  统一进入 `supporting-details`
- `supporting-details` 默认收起
- `refuse` 模式下如果有改问建议，则默认展开
- `weak_with_review_notice` 继续保留独立 `review_notice`

这意味着页面不会一进来就铺满多块证据面板。

## Evidence Card 去重

本轮没有回退标题 / 正文重复修复，且继续优先使用结构化简标题。

规则保持为：

1. `main_passages / passages / ambiguous_passages / annotations / chunks`
   优先生成结构化标题
2. 若标题与 `snippet` 高相似，则降级成结构化简标题
3. 若仍相似，则隐藏标题

实际弱样本仍会渲染为：

- `辨脉法第一 · 注解 0016`

而不再把长正文句子重复显示两次。

## 代码改动

### `frontend/index.html`

- 删除重型 header 与说明性块
- 删除 `composer-copy`
- 新增 `supporting-details`
- 保留 `review_notice / refuse_reason / error` 的独立 callout
- 将 composer 改为单行自适应输入器 + 弱化样例入口

### `frontend/styles.css`

- 重写整体布局为窄主轴聊天页
- 压轻 header、assistant card 与 composer
- 让正文优先于 supporting 信息
- 将 supporting 统一为低强调折叠区
- 保留状态色，但减少面板堆叠感

### `frontend/app.js`

- 删除与布局自解释相关的渲染文案
- 将 supporting 信息改为统一折叠入口
- 让 `refuse` 模式默认展开改问建议
- 增加 `textarea` 自动高度收缩 / 扩展
- 保留流式、回退、超时、重试、错误态与 dedup 逻辑

## 验证摘要

验证日期：

- 2026-04-10

已确认：

1. 本地 API 仍返回：
   - `黄连汤方的条文是什么？` -> `strong`
   - `烧针益阳而损阴是什么意思？` -> `weak_with_review_notice`
   - `书中有没有提到量子纠缠？` -> `refuse`
2. 前端渲染钩子验证通过：
   - `strong` 默认显示主依据，附加信息折叠
   - `weak_with_review_notice` 默认隐藏主依据，保留核对提示，附加信息折叠
   - `refuse` 默认展开改问建议
   - `error` 能单独进入错误态，不混同拒答
3. evidence 去重样本继续成立：
   - 原始长标题被收敛为 `辨脉法第一 · 注解 0016`

## 结论

这轮不是单纯“缩一点间距”，而是信息架构级的减重：

- header 不再抢主视觉
- 页面废话明显减少
- 中间阅读轴回到“用户问题 + 系统回答”
- composer 不再像底部控制台
- 依据区默认更克制
