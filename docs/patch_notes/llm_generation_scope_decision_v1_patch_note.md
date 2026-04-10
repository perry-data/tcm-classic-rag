# LLM Generation Scope Decision v1 Patch Note

- 日期：2026-04-09
- 范围：真实 LLM API / 分步 Prompt / React + Tailwind 前端重写的专项决策
- 任务性质：只做决策文档，不改系统、不写论文正文、不重写前后端

## 变更

1. 新增 `docs/project_decision/llm_generation_scope_decision_v1.md`
   - 分开评估真实 LLM API、分步 Prompt、React + Tailwind 三项
   - 逐项给出必要性、论文收益、答辩影响、实现成本、稳定性风险判断
   - 为每项给出唯一结论：必须补做 / 不必补做 / 可做可不做但若不做需改口径
   - 给出三项内部的推荐顺序
   - 明确回答“若只补一个，最应该补哪个”

## 决策摘要

最终结论如下：

1. 真实 LLM API 接入：`可做可不做，但若不做需在论文中改口径`
2. 分步 Prompt / Prompt 组装链路：`不必补做`
3. React + Tailwind 前端重写：`不必补做`

排序建议：

1. 真实 LLM API 接入
2. 分步 Prompt / Prompt 组装链路
3. React + Tailwind 前端重写

若只补一个，推荐补：

- **真实 LLM API 的最小接入版**

不推荐把三项打包成一次大改，原因是：

- 真实 LLM API 直接影响“生成”成立程度和答辩中的 RAG 判断
- 分步 Prompt 只有在 LLM 已接入且单步 prompt 不稳时才有价值
- React + Tailwind 主要影响前端工程风格，对论文第 4 章和 RAG 说服力收益最低

## 边界说明

本轮没有：

- 接入真实 LLM API
- 新增 Prompt orchestration
- 重写前端为 React + Tailwind
- 修改 evaluator v1
- 修改 answer payload contract
- 修改 retrieval / rerank / gating / answer assembler

## 后续建议

如果后续确实要动手，只考虑“最小 LLM API 接入版”，并继续保留当前 retrieval、evidence gating、citations、answer_mode 和 payload contract。
若不动手，则论文统一改口径为“检索增强的证据驱动回答编排”，不要宣称真实 LLM、分步 Prompt 或 React + Tailwind 已完成。
