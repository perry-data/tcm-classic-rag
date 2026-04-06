# General Question Patch Note

## 一、本轮改了什么

本轮新增了一个“总括类 / 泛问类问题”的最小处理补丁，核心变化有三块：

1. 问题类型识别

- 新增 `backend/strategies/general_question.py`
- 识别 `怎么办 / 怎么处理 / 有哪些情况 / 有什么分支` 等总括触发词
- 排除比较问答、方名直问这类不应进入总括路径的问题

2. 总括类回答编排

- 在 [assembler.py](/Users/man_ray/Projects/Python/tcm-classic-rag/backend/answers/assembler.py) 新增 general-question 分支
- 对总括类问题，先抽 topic，再复用现有 hybrid retrieval
- 用 topic 做更贴近主题的补充召回，并在 safe `main_passages` 内做最小 branch organization

3. 样例与校验

- 新增 [run_general_question_checks.py](/Users/man_ray/Projects/Python/tcm-classic-rag/run_general_question_checks.py)
- 输出：
  - [general_question_examples.json](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/general_question_examples.json)
  - [general_question_smoke_checks.md](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/general_question_smoke_checks.md)

## 二、兼容性

本轮保持以下外部合同不变：

- `POST /api/v1/answers` 不变
- 请求体仍只包含 `query`
- answer payload 顶层字段不变
- 现有前端单页消费方式不变

本轮也没有推翻：

- safe 数据策略
- SQLite 底座
- hybrid retrieval
- evidence gating
- minimal API

## 三、实际影响

### 1. 对总括类问题

此前：

- 容易把 `太阳病应该怎么办？` 这类问题当成普通相似检索
- 回答常常只是 top 几条主条拼接

现在：

- 会先识别这是总括性问题
- 回答开头会明确提示“并非只有一个固定答案，需要分情况看”
- 在 strong 情况下，会输出 2～4 条典型分支
- 在 weak 情况下，会明确降级为“部分线索，需核对”

### 2. 对非总括类问题

- 原路径保持不变
- `黄连汤方的条文是什么？` 仍走直答路径
- 伪泛问如 `黄连汤方应该怎么办？` 不会被误判成总括类问题

### 3. 对原冻结样例

本轮已验证原三条冻结样例未破坏：

- `黄连汤方的条文是什么？` -> `strong`
- `烧针益阳而损阴是什么意思？` -> `weak_with_review_notice`
- `书中有没有提到量子纠缠？` -> `refuse`

## 四、影响范围

本轮代码主要落在：

- [general_question.py](/Users/man_ray/Projects/Python/tcm-classic-rag/backend/strategies/general_question.py)
- [assembler.py](/Users/man_ray/Projects/Python/tcm-classic-rag/backend/answers/assembler.py)
- [run_general_question_checks.py](/Users/man_ray/Projects/Python/tcm-classic-rag/run_general_question_checks.py)

没有改动：

- API contract
- payload contract
- 前端工程结构
- 数据构建脚本
- 数据库结构

## 五、限制

本轮仍有明确边界：

- 不保证穷尽某一主题的所有分支
- branch organization 仍是启发式，不是完整知识建模
- weak 模式下的待核对线索仍较保守
- 非常宽的主题会被降级，而不会硬凑成 strong

## 六、后续建议

若后续继续做，但仍保持最小原则，优先顺序建议是：

1. 继续补更稳定的 topic 抽取
2. 继续补更细的 branch scoring / dedupe
3. 视需要给前端增加“总括类回答”的轻量展示提示

本轮不建议继续扩到：

- 多书系统
- 知识图谱
- 大规模规则工程
- payload 重构
