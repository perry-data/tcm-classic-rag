# Ambiguous Candidate Selection Policy v1

本轮只处理 ambiguous/full-risk/B 级材料中的 definition/concept/learner-facing evidence。

## Priority

- P0: `谓之 X`、`名曰 X`、`X 者……也`、`此为 X`、`X 之为病` 等明确命名或定义结构。
- P1: 普通学习者高频会问的术语，且句子能独立成义。
- P2: 当前 definition/concept query 容易 weak/support-only，或缺 alias/normalization 的对象。

## Exclusions

- 不恢复 raw `full:passages:*` / `full:ambiguous_passages:*` 为 primary。
- 不把一整段 ambiguous passage 粗暴恢复为 safe main。
- 单字短词、复合注释、异文/校记、方证治疗语境黏连的对象只登记 support/review 或拒绝升格。
