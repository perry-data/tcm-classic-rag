# formula_effect_cross_chapter_bridge_patch_v1

## 修了哪些规则

- 在 `backend/answers/assembler.py` 的 `_find_formula_effect_support_rows_v1` 中加入二阶段排序。
- 第一阶段仍沿用既有 context score；第二阶段只在 top1 已经是跨章 clean direct context 时，额外检查同 formula chapter 的 clean direct context 候选。
- clean same-chapter 候选门槛为：`main_passages + direct context + 非方题/组成 + 非短尾 + 基础分 >= 0`。
- `scripts/run_formula_effect_bulk_audit_v1.py` 的 context row 分类改为复用 assembler 内部同一套分析函数，保证报告口径与实际排序一致。

## 改善规模

- `cross_chapter_bridge_primary`：`60` -> `57`
- 改善 query 数：`3`
- 改善 formula 数：`1`
- `primary_reasonable_query_count`：`111` -> `114`
- `primary_suspicious_query_count`：`111` -> `108`

## 是否有回退样本

- stable positive 回退 query 数：`0`
- stable positive 回退 formula 数：`0`
- review-only weak 误抬 query 数：`0`
- review-only weak 误抬 formula 数：`0`
- stable positive 回退公式：`_none_`
- review-only 误抬公式：`_none_`

## 下一轮是否再处理 short_tail_fragment_primary

- 建议：`是`。
- 原因：这轮能安全修掉的 bridge 样本已经被收窄到“存在 clean same-chapter direct context”的子集；剩余 bridge 大多缺少这样的同章候选，继续加 chapter penalty 很容易开始误伤 `short_tail_fragment_primary` 或触到 raw recall 边界。
