# Comparison Patch Note

## 本轮改动

- 在 `backend/answers/assembler.py` 内新增比较类问答路径：
  - 比较意图识别
  - 双实体方名识别与最小别名归一
  - A / B 双侧定向召回
  - 基于证据的差异整理
  - comparison-specific strong / weak / refuse 裁决
- 新增 `run_comparison_checks.py`，自动产出：
  - `artifacts/comparison_examples.json`
  - `artifacts/comparison_smoke_checks.md`
- 在 `frontend/index.html` 里补了一个比较类演示样例按钮，便于现场验证

## 兼容性

- `POST /api/v1/answers` 不变
- 请求体仍然只包含 `query`
- answer payload 顶层字段不变
- 原三条冻结样例保持原模式：
  - `黄连汤方的条文是什么？ -> strong`
  - `烧针益阳而损阴是什么意思？ -> weak_with_review_notice`
  - `书中有没有提到量子纠缠？ -> refuse`

## 影响范围

- 业务层主要落在 answer assembler
- retrieval engine 没有重构，只是被比较路径复用为双实体单独召回
- 现有前端无需改 contract，只是多了一个可点的样例问题

## 本轮没有改什么

- 没有重做数据工程
- 没有重开数据库结构
- 没有推翻 safe 数据策略
- 没有扩展到多书
- 没有做知识图谱
- 没有引入多 agent
- 没有重做前端工程

## 当前限制

- 只支持 pairwise comparison
- 当前优先只做 `方名 vs 方名`
- 条文语境差异仍受现有 safe / full 分层约束
- 若某一侧只有 review 层条文线索，系统必须保留核对提示或降级

## 后续建议

- 若后续还要增强“方剂辨析”，优先补更稳定的 formula alias / title normalization
- 若要提升“条文语境”对比质量，优先补 safe 层中与方名直接相关的主条映射，而不是直接放宽 gating
- 若要提升答辩展示效果，可在现有前端上补一个轻量的 A/B 分组视觉，不必重做框架
