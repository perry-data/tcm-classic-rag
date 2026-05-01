# Full Chain P1 Repairs v1

## 本轮目标

只处理 full_chain_production_like_regression_v1 暴露的 3 个 P1 query：两条方剂比较与 `干呕是什么意思？`。不做 AHV3，不批量新增 safe primary definition object，不改前端，不改 API contract，不大改 prompt。

## Before Failure

| query | before_failure_type | before_primary_ids |
| --- | --- | --- |
| 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | {"A": "data_layer_bad_alias", "B": "data_layer_bad_alias", "C": "data_layer_bad_alias"} | {"A": ["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003"], "B": ["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003"], "C": ["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003"]} |
| 麻黄汤方和桂枝汤方的区别是什么？ | {"A": "data_layer_bad_alias", "B": "data_layer_bad_alias", "C": "data_layer_bad_alias"} | {"A": ["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-008-P-0217"], "B": ["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-008-P-0217"], "C": ["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-008-P-0217"]} |
| 干呕是什么意思？ | {"A": "retrieval_miss", "B": "retrieval_miss", "C": "retrieval_miss"} | {"A": [], "B": [], "C": []} |

## 根因与修复

### 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？

- 根因：DB 里的 exact alias 已存在；before 的 `matched_formula_ids` 缺一方，是 regression harness 捕获了 comparison 分支内部单方检索，而不是原始 pair query。另一个真实问题是 strong comparison 的 citations 包含 secondary/review。
- 修复动作：`run_single_query()` 优先使用 `query_request.query_text == spec.query` 的检索，否则做原始 query 诊断检索；`_build_comparison_citations()` strong 模式只输出 primary citations。
- DB / alias / formula registry / definition registry / assembler：不改 DB、alias、formula registry、definition registry；改 assembler citation 组装和 regression capture。
- runtime：comparison citation payload 行为收窄，answer_mode 仍为 strong。
- 修复后 slots：primary 覆盖 `safe:main_passages:ZJSHL-CH-025-P-0004` 与 `safe:main_passages:ZJSHL-CH-025-P-0003`；secondary/review 保留佐证，不进 citations。

### 麻黄汤方和桂枝汤方的区别是什么？

- 根因：同上，exact alias 与 formula object coverage 已具备；before 失败来自内部单方检索被误当原 query 诊断，并叠加 comparison citation slot 过宽。
- 修复动作：同一处 regression capture 修复与 comparison citations 收窄。
- DB / alias / formula registry / definition registry / assembler：不改 DB、alias、formula registry、definition registry；改 assembler citation 组装和 regression capture。
- runtime：comparison citation payload 行为收窄，answer_mode 仍为 strong。
- 修复后 slots：primary 覆盖 `safe:main_passages:ZJSHL-CH-009-P-0022` 与 `safe:main_passages:ZJSHL-CH-008-P-0217`；secondary/review 保留佐证，不进 citations。

### 干呕是什么意思？

- 根因：书内主文多作 `乾呕`，简体 query `干呕` 没有 exact learner normalization；同时没有已审计的 learner-safe definition object。不能为追求 strong 把 full passage 或解释材料硬升 primary。
- 修复动作：在 assembler 增加 P1 exact conservative meaning guard，仅对 `干呕/乾呕` 这两个 exact topic 生效；它返回 weak_with_review_notice，主依据为空，配置好的正文线索进入 secondary，full passage 解释只作 secondary/review 级核对材料，并跳过 LLM 改写。
- DB / alias / formula registry / definition registry / assembler：不改 DB、alias、formula registry、definition registry；只改 assembler exact guard。
- runtime：`干呕是什么意思？` 从 refuse 变为 weak_with_review_notice；不新增 active contains normalization，不新增 active 单字 alias。
- 修复后 slots：primary 为空；secondary 至少包含 `safe:main_passages:ZJSHL-CH-014-P-0188`、`safe:main_passages:ZJSHL-CH-015-P-0324`、`safe:main_passages:ZJSHL-CH-008-P-0215`；raw full passage 不进入 primary。

## 回归结论

- A / B / C completed: `['A_data_plane_baseline', 'B_retrieval_rerank', 'C_production_like_full_chain']`
- total_cases: `51`
- passed_cases: `51`
- failed_cases: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_total: `0`
- wrong_definition_primary_total: `0`
- formula_bad_anchor_top5_total: `0`
- citation_error_total: `0`
- assembler_slot_error_total: `0`
- answer_mode_calibration_error_total: `0`

## 影响面

- P0 guards：纳入 4 个原始 P0 query，均通过。
- AHV v1 / AHV2：纳入 exact normalization guards，验证 concept 命中未回退；不把既有非 P1 canonical-primary slot 议题混入本轮，未新增 AHV3。
- formula comparison：P1 两组与白虎汤/白虎加人参汤 comparison 均通过，双方方名都有 primary 覆盖。
- review-only boundary：神丹、将军、胆瘅未进入 primary。
- 剩余风险：`干呕` 当前只是 exact guard 下的 weak learner answer；若以后要 strong，应另开对象审计，抽取独立 learner-safe definition object 后再回归。
