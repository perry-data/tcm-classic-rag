# formula_effect_primary_prioritization_v1

## 1. 问题定义

本轮只处理一小类单方剂 query：

- `X方有什么作用`
- `X方主什么 / 主治什么`
- `X方用于什么情况 / 适用于什么情况`

目标不是给出现代功效总结，也不是把“方题 / 方文 / 组成”重新包装一遍，而是尽量把回答建立在《伤寒论》里更直接的使用语境上：

- 优先回答“它在什么证候/情境下被直接使用”
- 再附该语境对应的主条
- 方文只作为补充，不反客为主

本轮仍然沿用既有 `formula_effect_query` 专用路径，不扩 definition/category family，不启用 annotation / annotation_links，不重写 retrieval 主链。

## 2. 当前常见错误模式

### 2.1 primary 选到“提及该方但不是最好使用语境”的条文

典型现象：

- 选中跨章引用条文
- 选中带 `宜X汤` / `与X汤` 的承接性短片段
- 选中包含别方对照或转折说明的混合条文

这样虽然也是“提到了该方”，但并不是最适合作为“X方有什么作用”的 primary。

### 2.2 context clause 抽取得到短残片

典型现象：

- `欲解外者，宜桂枝汤主之` 被截成 `欲解外`
- `可与麻黄汤` / `解表宜桂枝汤` 被截成 `可与` / `解表宜`

这会让 answer_text 虽然形式上仍是“基于语境解释”，但实际已经退化成不自然、不完整的短片段。

### 2.3 方文或方题错误占主依据

当直接使用语境不够强时，系统容易退回：

- 方题直出
- 方文直出
- 组成相关内容在解释里喧宾夺主

这会让“作用类 query”看起来像“条文/组成查询”的变体，而不是对直接使用语境的解释。

## 3. 哪类 evidence 应优先做 primary

本轮 primary 优先级只做最小收束，核心原则是：

### 3.1 优先同一方剂的直接使用语境条文

理想 primary 应满足：

- 明确只有该方剂，不夹带其他方剂并列判断
- 条文前半段本身就携带症状/证候/使用情境
- 读者即使不看方文，也能从条文直接理解“此方用于哪类情况”

例如：

- `啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣乾呕者，桂枝汤主之`
- `伤寒解后，虚羸少气，气逆欲吐者，竹叶石膏汤主之`

### 3.2 优先“症状/证候语境完整”的条文，而不是“承接动作词”残片

对 formula_effect 来说，下面这类上下文质量更高：

- 有连续症状或证候描述
- 有多个并列征象
- 读出来就是“什么情况下用它”

而不是只剩：

- `宜`
- `与`
- `可与`
- `当`

### 3.3 review 层语境只能做 weak 解释，不误抬成 strong

如果直接语境只存在于 `passages` / `ambiguous_passages`：

- 可以组织保守解释
- 可以放进 `review_materials`
- 可以在 weak answer_text 里说明“目前只能从核对层材料看到……”

但不应把这类 evidence 误抬成 `primary_evidence`。

## 4. 哪类 evidence 不应错误占 primary

### 4.1 方文标题行 / 组成行

这些行可以支撑：

- 组成类 query
- 条文/方文查看
- 作用类回答中的补充出处

但不应在作用类 query 中抢占 primary。

### 4.2 含多个方剂的对照句

如果同一行同时出现：

- `桂枝汤`
- `麻黄汤`

这类行更适合作为比较/辨析材料，不应在单方剂作用问法里优先成为 primary。

### 4.3 仅有“宜X汤 / 与X汤 / 可与X汤”的承接性引用句

这类句子对定位有帮助，但如果上下文被截成短残片，就不应压过更完整的直接证候条文。

### 4.4 带明显校勘/按语/详见提示的噪声片段

如：

- `赵本`
- `医统本`
- `详见`
- `本云`
- `按`

这些内容可以存在于原文，但不应因为词面匹配而错误提高 primary 优先级。

## 5. 本轮最小策略

本轮只做两件最小事：

### 5.1 formula_effect support row prioritization v1

在既有 `formula_effect_query` 专用路径内部，对 support row 做更细的优先级调整：

- 更偏向“直接症状/证候语境完整”的条文
- 对多方并列、短尾承接词、校勘噪声做扣分
- 不改 raw retrieval candidate 生成

### 5.2 formula_effect context clause extraction v1

在作用类 bundle 内，对 context clause 做更稳妥的抽取：

- 先去掉明显 inline notes
- 再清掉 `宜 / 与 / 可与 / 当` 这类尾部承接词
- 避免 answer_text 落成不自然的短片段

## 6. 本轮边界与不做内容

本轮明确不做：

- 不扩更多 family
- 不回头继续改 definition/category family
- 不启用 annotation
- 不启用 annotation_links
- 不大改 retrieval raw candidate 生成
- 不重写 assembler 全局逻辑
- 不改前端
- 不扩 evaluator 平台
- 不把作用类回答扩展成现代临床功效总结

本轮只回答一个问题：

`formula_effect_query` 在 raw recall 大体不变的前提下，能否通过最小 primary prioritization + context extraction，把答案更稳定地拉回“基于直接使用语境的解释”。

## 7. 实验开关

本轮实验开关：

- `TCM_ENABLE_FORMULA_EFFECT_PRIMARY_RULES_V1`

约定：

- `0`：before
- `1`：after
- 未显式设置时：当前分支默认启用 after 行为
