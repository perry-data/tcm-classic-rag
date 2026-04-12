# fahan_controlled_replay_v1 patch note

## 实验目的

本轮只做一个最小的 `main_passages` 受控回放实验，用来验证“什么是发汗药”当前答非所问，是否主要由 safe 误杀关键 `main_passages` 导致。

本轮明确不做：

- 不碰 `annotation`
- 不恢复 `annotation_links`
- 不改前端
- 不扩 evaluator
- 不大改 rerank / evidence gating
- 不改 answer assembler 的主裁决逻辑

## 本轮回放条目

- `ZJSHL-CH-006-P-0120`
- `ZJSHL-CH-006-P-0127`

对应 allowlist 配置文件：

- `config/controlled_replay/fahan_main_passages_allowlist_v1.json`

## 进入层级

- `recall`: 开启
- `vector`: 关闭
- `primary_candidate`: 关闭

实现口径：

- allowlist 条目只在 feature flag 打开时生效
- 回放条目以 synthetic record 的方式进入 retrieval merge
- synthetic record 的 `record_table` 固定为 `controlled_replay_main_passages`
- synthetic record 的 `evidence_level` 固定为 `B`
- synthetic record 只允许进入 `secondary_evidence`
- 不直接抬为默认 `primary`

feature flag：

- 环境变量：`TCM_ENABLE_FAHAN_CONTROLLED_REPLAY_V1`
- 默认关闭
- `1 / true / yes / on` 可开启

## 代码改动

- 在 `backend/retrieval/hybrid.py` 中新增：
  - allowlist 配置加载
  - env flag 开关
  - 从 `data/processed/zjshl_dataset_v2/main_passages.json` 读取 allowlist 对应原文
  - controlled replay recall stage
  - retrieval trace 中的 `controlled_replay` 调试信息
- 在 `backend/retrieval/minimal.py` 中新增：
  - `controlled_replay_main_passages` 的 source budget
  - `controlled_replay_main_passages -> secondary_evidence` 的受控落位
- 在 `backend/answers/assembler.py` 中只补了一个兼容点：
  - 当 synthetic replay record 不在 `vw_retrieval_records_unified` 中时，允许从 `engine.record_by_id` 回读原文元数据，避免 evidence snippet 为空

## 为什么这样放，不那样放

- `ZJSHL-CH-006-P-0120` 在上一轮人工复核中判为 `L2`：
  - 对“发汗药”问题解释力强
  - 适合回放到 `recall`
  - 但仍不宜直接当 canonical primary
- `ZJSHL-CH-006-P-0127` 也判为 `L2`：
  - 更像“使用说明型补充解释”
  - 适合补 secondary / recall
  - 不宜直接包装成定义句
- 本轮先不进 vector：
  - 目的是先把变量收窄到“回放到 evidence pool 后会不会改变答案”
  - 避免把 recall 影响和 dense 影响混在一起
- 本轮先不进 primary：
  - 用户要求保持受控回放
  - 如果直接抬 primary，就无法判断问题到底是“证据没进来”还是“证据进来了但没被主裁决采纳”

## 预期验证点

- `什么是发汗药`：
  - `ZJSHL-CH-006-P-0120` 或 `ZJSHL-CH-006-P-0127` 是否能稳定进入 raw candidates / secondary evidence
- `桂枝汤是发汗药吗`：
  - `ZJSHL-CH-006-P-0120` 是否能作为 query-critical 补充证据回到 evidence chain
- `太阳病是什么`
- `竹叶石膏汤方有什么作用`
  - 用作回归检查，确保本轮 replay 不外溢
