# 系统优化矩阵 v1

- 文档版本：v1
- 文档日期：2026-04-09
- 文档定位：在当前稳定系统基线之上，系统化整理后续可选优化方向，形成统一判断矩阵
- 输入依据：
  - `docs/final/PRD_v1.md`
  - `docs/final/technical_design_v1.md`
  - `docs/final/system_spec_v1.md`
  - `docs/evaluation/evaluation_spec_v1.md`
  - `docs/evaluation/evaluation_plan_v1.md`
  - `docs/project_audit/proposal_vs_actual_gap_audit_v1.md`
  - `docs/project_decision/llm_generation_scope_decision_v1.md`
  - `docs/project_design/minimal_llm_api_integration_spec_v1.md`
  - `artifacts/evaluation/modelstudio_qwen_plus_regression_report.md`
  - `docs/patch_notes/modelstudio_qwen_plus_live_validation_patch_note.md`
  - 当前仓库已有 patch notes、smoke artifacts 与项目审计文档

## 1. 当前稳定基线

当前系统已经不是“边搭边试”的探索态，而是具备明确稳定边界的单书 MVP：

1. 正式主链已闭环：`query -> hybrid retrieval -> evidence gating -> answer assembler -> POST /api/v1/answers -> frontend`
2. retrieval / rerank / evidence gating / answer assembler / minimal API / frontend MVP 已实际落地并可演示。
3. `goldset_v2_working_150.json` 已形成 150 条评估集，`evaluator_v1` 回放结果为：
   - `total_questions = 150`
   - `mode_match = 150/150`
   - `citation_check_required_basic_pass = 120/120`
   - `failure_count = 0`
4. `qwen-plus` live validation 已成功：
   - 4 条 non-refuse 样例真实走到 LLM 返回
   - `refuse` 仍按设计跳过 LLM
   - `answer_mode`、evidence slots、citations 保持不变
5. 当前系统收口重点已经从“把链路跑通”转向“在不破坏稳定性的前提下，做哪一类优化最值、最稳、最利于论文收口”。

因此，本矩阵的判断原则不是“能做什么都做”，而是：

1. 不破坏当前冻结合同与主链稳定性。
2. 不同时推进多条优化主线。
3. 优先选择可量化、可复核、可写进论文第 4 章的方向。
4. 优先选择对答辩说服力提升明显、但对系统爆炸半径可控的方向。

## 2. 评分口径

为避免空泛判断，本文统一使用以下定性口径：

- 预期收益：低 / 中 / 高 / 很高
- 风险：低 / 中 / 高
- 实现成本：低 / 中 / 高
- 论文收益：低 / 中 / 高 / 很高
- 答辩观感收益：低 / 中 / 高

## 3. 优化总览矩阵

| 优化维度 | 当前现状 | 主要痛点 | 可做优化动作 | 预期收益 | 风险 | 实现成本 | 论文收益 | 答辩观感收益 | 当前优先级建议 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 检索质量优化 | Hybrid retrieval、RRF、Cross-Encoder rerank、evidence gating 已稳定；150 条集上 citation 基础通过率稳定。 | 现代问法与古文表述仍有语义鸿沟；总括问、解释问的泛化上限仍受检索质量约束；当前缺少 retrieval 级诊断指标。 | query 归一化、topic recall 调优、RRF/fused pool/rerank budget 调整、错误样本回放、检索层对比实验。 | 高 | 中 | 中 | 高 | 高 | P1 |
| Prompt / 生成质量优化 | `qwen-plus` 已以最小形态接入，且 live-call 成功；LLM 只改 `answer_text`，不改 mode/evidence/citations。 | 当前 prompt 仍偏单步与保守；answer_text 质量缺少系统化评分；不同题型下的表达风格仍有提升空间。 | prompt 约束微调、题型化 answer_text 模板优化、general/comparison 的结构整理、validator 与 fallback 策略细化。 | 中高 | 中 | 中 | 高 | 高 | P1 |
| 前端展示优化 | 同源原生 SPA 已稳定，能完整渲染 answer payload 三槽位、引用与改问建议。 | 页面信息密度偏高；citation 与 evidence 的可读性仍一般；弱答/拒答的解释力可继续加强。 | 信息层级重排、引用锚点与高亮、空态与弱答提示优化、演示文案优化、样例引导增强。 | 中 | 低 | 低中 | 中 | 中高 | P2 |
| 性能优化 | 目前已有可运行本地 MVP，但缺正式 latency / p50 / p95 报告。 | 尚未识别主瓶颈；如果直接做性能调优，容易变成无指标优化；当前系统规模也未逼出明显吞吐瓶颈。 | 先建 benchmark，再做 rerank budget、缓存、热启动、API 路径测量与局部剪枝。 | 中 | 中 | 中 | 中 | 中 | P2 |
| 评估体系优化 | evaluator v1 与 150 条 goldset 已立稳，能验证 mode/citation 基线与主链不回归。 | 当前更多是在证明“系统没坏”；尚不能精细回答“到底哪一层值得继续优化”；answer_text、retrieval 命中、latency、用户反馈仍缺细粒度量化。 | evaluator v2、Hit@K/Recall@K、题型分布报表、answer_text 评分规约、failure taxonomy、latency/user mini-evidence。 | 很高 | 低中 | 中 | 很高 | 高 | P0 |

## 4. 检索质量优化

### 4.1 当前现状

- 当前检索链路已经具备完整结构：SQLite FTS5/BM25 sparse recall + FAISS dense recall + RRF + Cross-Encoder rerank。
- 单书《伤寒论》场景下，source lookup、comparison、general、meaning、refusal 五类题型都已能稳定进入正式主链。
- 150 条评估集中，citation 基础检查无失败，说明当前检索与证据组织已经达到“可用且稳定”的阶段。

### 4.2 主要痛点

1. 当前评估更偏最终 payload 正确性，还没有把 retrieval 本身拆成 `Hit@K / Recall@K / rerank 前后对比` 等层级指标。
2. 现代汉语问题与古文条文之间仍存在表述落差，解释类和泛问类尤其依赖召回质量。
3. `trigram` tokenizer、focus query、candidate budget 目前主要按单书库经验调优，泛化上限仍未知。
4. 若未来想做更高质量的 general/comparison 输出，底层检索质量仍是上限约束。

### 4.3 可做的优化动作

1. 为 retrieval 单独补充题型分组指标：`Hit@K`、`Recall@K`、gold passage 命中率、rerank 前后变化。
2. 针对解释类和总括类问题，补 query normalization、focus 词提取和 topic trigger 的误差分析。
3. 调整 fused pool、rerank top-N、source budget，观察 citation 命中与弱答/强答分布是否改善。
4. 做错误样本回放集，专门定位“引用对了但检索排序仍不优”的边缘问题。
5. 在不改 evidence gating 的前提下，尝试更稳的候选裁剪策略。

### 4.4 预期收益

- 能提升解释问、总括问、现代问法场景下的证据命中质量。
- 能提升后续生成质量优化的天花板，因为 LLM 只能基于已有证据说得更好，不能替代证据命中。
- 能让论文第 3 章与第 4 章对“检索模块设计与效果”更有说服力。

### 4.5 风险

1. 检索层一旦改动过大，容易牵动 rerank、gating 和 answer_mode 分布。
2. 如果没有更细指标，调优可能变成“调到某些样例更好，但整体是否更好说不清”。
3. 对 annotations / passages / ambiguous_passages 盲目放宽召回权重，可能破坏现有证据门控。

### 4.6 实现成本

- 成本判断：中
- 主要成本不在“改一个参数”，而在于需要补检索级对比实验与回归验证。

### 4.7 对论文收益

- 收益判断：高
- 理由：检索是题目中的核心方法层，优化检索比优化 UI 更能强化第 2/3/4 章的研究主线。

### 4.8 对答辩观感收益

- 收益判断：高
- 理由：老师最容易追问“你这个系统到底检索得准不准”；检索优化能直接支撑这一点。

### 4.9 当前判断

检索质量优化很重要，但不适合在当前阶段盲做。它更适合作为**评估体系优化之后的第一条技术主线**，而不是现在立刻抢跑。

## 5. Prompt / 生成质量优化

### 5.1 当前现状

- 当前真实 LLM 接入已经完成最小落地：`qwen-plus` 只参与 `answer_text`，不改 mode/evidence/citations。
- live validation 已证明 non-refuse 样例能真实走到 Model Studio 返回，且 payload 结构稳定。
- 当前生成优化空间主要不在“能不能接 LLM”，而在“在不破坏稳定边界的前提下，answer_text 能不能更清楚、更自然、更适合研读支持场景”。

### 5.2 主要痛点

1. 当前生成质量验证仍偏 smoke，尚未形成题型化 answer_text 质量量表。
2. single-step prompt 够稳，但表达质量仍偏保守，尤其在 general/comparison 上还有结构整理空间。
3. weak 模式如何保持“需核对”语气同时不显得过碎，仍有优化余地。
4. 当前 validator 主要防越界，尚未系统评价“同一证据下，baseline 与 LLM 版本哪个更适合论文和答辩展示”。

### 5.3 可做的优化动作

1. 针对 source lookup / meaning / general / comparison 四类 non-refuse 问题分别细化 prompt 约束。
2. 对 `answer_text` 的长度、编号结构、弱答语气、比较结构进行专门调优。
3. 增加 baseline vs LLM 的对照评审表，评估可读性、结构清晰度、证据一致性。
4. 优化 validator 与 fallback 记录，让生成优化可回归、可定位。
5. 补一组题型 representative set，对 qwen-plus 输出做人工 rubric 打分。

### 5.4 预期收益

- 用户最直观感受到的回答自然度、条理性、解释清晰度会提升。
- 对答辩展示非常友好，因为老师首先看到的是最终答案文本，而不是内部检索 trace。
- 在不改 evidence/citation 的前提下，生成优化的爆炸半径相对受控。

### 5.5 风险

1. 如果没有 answer_text 评价尺子，生成优化容易沦为主观审美调 prompt。
2. 过度追求流畅，可能削弱 weak 模式的谨慎边界。
3. 一旦 prompt 过长或过复杂，latency、稳定性和 fallback 频率都可能上升。

### 5.6 实现成本

- 成本判断：中
- prompt 本身不难改，难点在于要建立生成质量的评价与回归机制。

### 5.7 对论文收益

- 收益判断：高
- 理由：它能增强“RAG 中的生成部分已真实进入链路”的说服力。

### 5.8 对答辩观感收益

- 收益判断：高
- 理由：最终展示层最容易被感知的是回答文本质量，而非内部实现。

### 5.9 当前判断

生成质量优化值得做，但它**依赖评估体系先升级**。没有 answer_text 评分和对照回放前，直接把它作为第一轮主线会比较盲。

## 6. 前端展示优化

### 6.1 当前现状

- 原生 HTML/CSS/JS 同源前端已稳定，可渲染 answer payload 的主要字段与三种 answer_mode。
- 前端初始化、提交状态、错误提示、弱答/拒答空态已经过联调修复。
- 当前前端对毕设演示来说已经“够用”，不是明显故障态。

### 6.2 主要痛点

1. evidence、citations、review_notice 的信息密度较高，阅读负担仍偏重。
2. weak/refuse 的“为什么这样回答”还可以展示得更清楚。
3. 引用、主证据、补充依据之间的层级感可继续增强。
4. 当前页面更偏工程可用，不是“论文截图特别好看”的状态。

### 6.3 可做的优化动作

1. 重新组织 evidence 卡片层级，让主依据、补充依据、核对材料更容易扫读。
2. 优化 citation 展示与锚点跳转，让“回答-证据-引用”关联更直观。
3. 针对 weak/refuse 加强提示文案与 follow-up questions 的引导。
4. 优化 loading / success / error 的交互反馈，让演示观感更稳定。
5. 精简页面视觉噪音，提高论文截图和答辩展示的可读性。

### 6.4 预期收益

- 能改善演示观感、截图效果和首次理解成本。
- 对答辩时“系统看起来是不是清楚、是不是像一个完整系统”有帮助。

### 6.5 风险

1. 前端若改动过大，可能引入新的联调问题。
2. 若滑向重写框架或大改交互，会偏离当前项目收口策略。

### 6.6 实现成本

- 成本判断：低中
- 局部展示优化成本不高，但若演变成重写前端，成本会迅速失控。

### 6.7 对论文收益

- 收益判断：中
- 理由：主要增强第 3 章展示与截图效果，不直接提升检索或回答质量证据。

### 6.8 对答辩观感收益

- 收益判断：中高
- 理由：UI 观感确实影响老师的第一印象，但不是研究主价值所在。

### 6.9 当前判断

前端展示优化属于“能加分，但不是当前最值得先做”的方向。适合作为后置润色项，而不是当前第一轮主线。

## 7. 性能优化

### 7.1 当前现状

- 当前系统能在本地单机稳定运行，但仓库内尚无正式的 latency benchmark artifact。
- 现有证据更多是功能 smoke、evaluator 回放与 live validation，而不是响应时间统计。
- 项目定位仍是本地演示型 MVP，不是生产级高并发系统。

### 7.2 主要痛点

1. 目前还不知道真正的瓶颈是在 sparse recall、dense recall、rerank、LLM 还是前端/HTTP 往返。
2. 没有 p50 / p95 / 均值 / 题型分布，就很难判断“慢在何处、是否值得调”。
3. 若现在直接做性能调优，容易陷入无基线、无收益证明的局面。

### 7.3 可做的优化动作

1. 先补 API 层 benchmark：五类代表问题多轮调用，记录环境、均值、p50、p95。
2. 再根据结果决定是否做 rerank top-N、candidate budget、缓存、warm-up 等局部优化。
3. 将 baseline 与 LLM-enabled 两种路径分别统计，区分 retrieval cost 与 generation cost。
4. 对 smoke/evaluator 路径增加简要 timing trace，定位主要耗时模块。

### 7.4 预期收益

- 能提升系统响应稳定性。
- 能补足开题报告里“响应速度测试”的证据缺口。
- 若 p95 偏高，性能优化对演示体验会有明显改善。

### 7.5 风险

1. 若没有 benchmark 先行，性能优化会很容易做成“凭感觉压参数”。
2. 一些性能手段如果影响 rerank 或 LLM 质量，可能得不偿失。
3. 当前数据规模不大，过早做复杂性能工程化收益有限。

### 7.6 实现成本

- 成本判断：中
- 先测量成本不高，但真正调优要看瓶颈是否落在模型或 rerank 环节。

### 7.7 对论文收益

- 收益判断：中
- 理由：它能补性能测试口径，但不是当前研究贡献的主轴。

### 7.8 对答辩观感收益

- 收益判断：中
- 理由：系统不卡顿会加分，但如果当前无明显卡顿，则边际收益有限。

### 7.9 当前判断

性能优化不应作为当前第一轮独立主线。当前更合理的做法是先把**性能测量纳入评估体系优化**，再决定是否值得做性能调优。

## 8. 评估体系优化

### 8.1 当前现状

- evaluator v1、evaluation spec v1、evaluation plan v1、150 条 goldset 已经构成正式评估底座。
- 当前最强证据是：150 条回放零失败，mode 与 citation 基本稳定。
- 当前系统已经从“没有尺子”进化到“有一把基础尺子”，但这把尺子还偏粗。

### 8.2 主要痛点

1. 当前 evaluator 更擅长回答“系统有没有明显回归”，还不擅长回答“哪一层最值得优化”。
2. retrieval 层缺少 `Hit@K / Recall@K / rerank 前后收益` 等细粒度指标。
3. qwen-plus live 已成功，但 answer_text 的质量收益还没有形成正式评价口径。
4. latency、用户感知、failure taxonomy 还没有统一纳入一套评估工件。
5. 如果现在直接改 retrieval 或 prompt，很难给出严谨的 before/after 对比。

### 8.3 可做的优化动作

1. 建 evaluator v2：补 retrieval 级指标、题型分布报表、失败类型统计。
2. 为 answer_text 建人工 rubric：清晰度、证据一致性、结构性、弱答边界保持。
3. 将 baseline vs LLM、题型分组、代表性难题集纳入同一评估流程。
4. 把 latency mini-benchmark 并入评估 artifact，而不是另开一套零散文档。
5. 为第 4 章准备可直接引用的表格、统计项和失败样本分类。

### 8.4 预期收益

- 后续所有优化都将变得可测、可对比、可复盘。
- 能直接支撑论文第 4 章结果分析，而不只是提供工程自测记录。
- 能让“只做一条主线优化”真正成立，因为每轮都能明确看到收益和代价。

### 8.5 风险

1. 评估变细之后，可能会暴露当前系统之前未显性的短板。
2. 需要一定文档与脚本收束成本。

但总体风险仍低于直接重构 retrieval、prompt 或前端。

### 8.6 实现成本

- 成本判断：中
- 主要是补评估口径、报表与工件，不需要推翻现有业务主链。

### 8.7 对论文收益

- 收益判断：很高
- 理由：它直接决定第 4 章能否从“有一批结果”升级为“有一套可信比较框架”。

### 8.8 对答辩观感收益

- 收益判断：高
- 理由：老师最常追问的是“你如何证明优化有效”；评估体系优化正是这类问题的最好答案。

### 8.9 当前判断

评估体系优化是当前最适合先做的方向。它既不破坏稳定主链，又能为检索、生成、性能三条后续优化主线建立可执行的量化基础。

## 9. 本阶段不值得优先做的优化

以下方向当前不值得优先推进，原因分别是收益低、稳定性风险高、论文收口收益差，或更适合写进展望：

1. React + Tailwind 前端重写
   - 当前原生 SPA 已能稳定演示。
   - 重写框架对检索增强系统的研究主价值帮助有限。
   - 容易引入新的联调与演示风险。
2. 多步 Prompt 编排链路
   - 当前单步 prompt 已可稳定 live-call。
   - 在 answer_text 评价体系未建立前，多步 prompt 会先提升复杂度，而不是先提升可证收益。
3. 直接扩到多书或恢复《金匮要略》
   - 会破坏当前单书冻结边界，连带影响数据、检索、评估与论文口径。
4. 盲目把 dense index 扩到 annotations / passages / ambiguous_passages
   - 这会抬高风险材料在排序中的权重，可能破坏现有 evidence gating。
5. 在 evaluator 粒度未升级前，把 goldset 从 150 继续堆到 200-250
   - 当前更缺的是“尺子更准”，不是“题目更多”。
6. 生产级部署、高并发、复杂运维优化
   - 超出当前毕设收口目标，收益与成本不匹配。
7. 改 answer payload contract 或 evidence 分层规则
   - 这会直接破坏当前最宝贵的稳定基线。

## 10. 矩阵结论

基于当前稳定基线，五大维度的综合判断如下：

1. **P0：评估体系优化**
2. **P1：检索质量优化**
3. **P1：Prompt / 生成质量优化**
4. **P2：性能优化**
5. **P2：前端展示优化**

其中，真正适合作为下一轮唯一主线的，不是“直接去改 retrieval 或 prompt”，而是先把**评估体系优化**做好，再进入第一条技术型优化主线。
