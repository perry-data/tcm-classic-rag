# Minimal LLM API Integration Spec v1 Patch Note

- 日期：2026-04-09
- 范围：最小真实 LLM API 接入版的实现规格冻结
- 任务性质：只冻结边界和改动范围，不写代码、不接真实 API、不改前端

## 变更

1. 新增 `docs/project_design/minimal_llm_api_integration_spec_v1.md`
   - 冻结最小接入位置
   - 冻结字段职责边界
   - 冻结单步 prompt 结构
   - 冻结失败回退机制
   - 说明对 evaluator / smoke 的影响
   - 冻结最小配置与运行方式
   - 明确单一 provider 策略
2. 新增 `docs/project_design/minimal_llm_api_sequence_v1.md`
   - 用时序方式描述请求、retrieval、gating、baseline answer、LLM render、validator、fallback、payload 返回的顺序
   - 明确 refuse path 跳过 LLM
   - 明确 strong / weak path 的 LLM 触发条件
   - 明确 smoke / regression 顺序

## 冻结结论摘要

本版最小真实 LLM API 接入方案冻结为：

1. LLM 插在 `AnswerAssembler` 内部，位于 deterministic assembly 之后、payload 返回之前
2. `answer_mode`、evidence slots、citations、payload contract 全部继续由规则层控制
3. LLM 只允许参与 `answer_text`
4. `refuse` 路径不调用 LLM
5. strong / weak_with_review_notice 只有在显式启用 LLM 时才尝试调用
6. API 超时、provider 失败、输出解析失败、输出越界时，一律自动回退当前 deterministic `answer_text`
7. prompt 只允许单步，不扩成多步 Prompt
8. provider 先固定单一 provider，不做通用 provider 抽象层

## 对现有系统的影响判断

保持不变的部分：

- retrieval
- rerank
- gating
- citations
- answer_mode
- payload contract
- frontend

需要新增但不改主链的部分：

- LLM client
- prompt builder
- output validator
- 最小 LLM smoke / regression artifact

## 后续实现建议

实现轮次应先做 disabled-by-default 的最小接入，再跑 5 条 LLM smoke，最后复跑 150 条 evaluator v1。
不建议在同一轮顺手做多步 Prompt、前端重写或 provider 抽象扩展。
