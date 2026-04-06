# Comparison Smoke Checks

## 运行命令

`python run_comparison_checks.py`

## 比较样例结论

### comparison_formula_delta_strong

- query: `桂枝加附子汤方比桂枝加厚朴杏子汤方少了什么？`
- answer_mode: `strong`
- 两个对象是否识别成功: `True`
- 是否形成结构化差异: `True`
- 是否保留 citations: `True`
- primary=2, secondary=1, review=4
- answer_text: 从现有方文与相关条文看，桂枝加附子汤方与桂枝加浓朴杏子汤方都从桂枝汤方加减而来，但显式加味和对应语境不同。
1. 显式加减关系：桂枝加附子汤方明写加附子；桂枝加浓朴杏子汤方明写加浓朴、杏仁。
2. 条文语境：桂枝加附子汤方相关条文可见“太阳病，发汗，遂漏不止，其人恶风，小便难，四支微急，难以屈伸者”；桂枝加浓朴杏子汤方核对材料可见“太阳病，下之微喘者，表未解故也”。
3. 出处线索：桂枝加附子汤方的方文见“卷十附方位置”；桂枝加浓朴杏子汤方的方文见“卷十附方位置”；桂枝加附子汤方相关条文位于“辨太阳病脉证并治法上第五”；桂枝加浓朴杏子汤方相关条文位于“辨太阳病脉证并治第六”。
以上差异仅按当前可见条文与方文整理；若要逐字核对，请继续查看引用。

### comparison_context_weak

- query: `桂枝去芍药汤方和桂枝去芍药加附子汤方的条文语境有什么不同？`
- answer_mode: `weak_with_review_notice`
- 两个对象是否识别成功: `True`
- 是否形成结构化差异: `True`
- 是否保留 citations: `True`
- primary=0, secondary=2, review=4
- answer_text: 两方都已识别，但当前比较仍有证据缺口，以下只按现有方文做弱整理：桂枝去芍药汤方 与 桂枝去芍药加附子汤方 的差异需要继续核对。
1. 显式加减与药味差异：桂枝去芍药加附子汤方明写加附子。
2. 语境证据缺口：当前未稳定找到 桂枝去芍药汤方和桂枝去芍药加附子汤方 的直接相关条文，因此语境差异只能暂缓判断。
3. 出处线索：桂枝去芍药汤方的方文见“卷十附方位置”；桂枝去芍药加附子汤方的方文见“卷十附方位置”；桂枝去芍药汤方相关条文位于“辨太阳病脉证并治法上第五”；桂枝去芍药加附子汤方相关条文位于“辨太阳病脉证并治法上第五”。
以上差异仅按当前可见条文与方文整理；若要逐字核对，请继续查看引用。

### comparison_entity_unstable

- query: `桂枝加附子汤方和桂枝加厚朴那个方的区别是什么？`
- answer_mode: `refuse`
- 两个对象是否识别成功: `False`
- 是否形成结构化差异: `False`
- 是否保留 citations: `False`
- primary=0, secondary=0, review=0
- answer_text: 当前无法基于稳定的双实体识别来组织比较答案，暂不直接作答。

### comparison_invalid_question

- query: `桂枝加附子汤方和桂枝加厚朴杏子汤方哪个好？`
- answer_mode: `refuse`
- 两个对象是否识别成功: `False`
- 是否形成结构化差异: `False`
- 是否保留 citations: `False`
- primary=0, secondary=0, review=0
- answer_text: 当前无法基于稳定的双实体识别来组织比较答案，暂不直接作答。

### comparison_demo_scene

- query: `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？`
- answer_mode: `strong`
- 两个对象是否识别成功: `True`
- 是否形成结构化差异: `True`
- 是否保留 citations: `True`
- primary=2, secondary=1, review=4
- answer_text: 从现有方文与相关条文看，桂枝加附子汤方与桂枝加浓朴杏子汤方都从桂枝汤方加减而来，但显式加味和对应语境不同。
1. 显式加减与药味差异：桂枝加附子汤方明写加附子；桂枝加浓朴杏子汤方明写加浓朴、杏仁。
2. 条文语境：桂枝加附子汤方相关条文可见“太阳病，发汗，遂漏不止，其人恶风，小便难，四支微急，难以屈伸者”；桂枝加浓朴杏子汤方核对材料可见“太阳病，下之微喘者，表未解故也”。
3. 出处线索：桂枝加附子汤方的方文见“卷十附方位置”；桂枝加浓朴杏子汤方的方文见“卷十附方位置”；桂枝加附子汤方相关条文位于“辨太阳病脉证并治法上第五”；桂枝加浓朴杏子汤方相关条文位于“辨太阳病脉证并治第六”。
以上差异仅按当前可见条文与方文整理；若要逐字核对，请继续查看引用。

## 冻结样例回归

- `黄连汤方的条文是什么？` -> expected=`strong`, actual=`strong`, pass=`True`
- `烧针益阳而损阴是什么意思？` -> expected=`weak_with_review_notice`, actual=`weak_with_review_notice`, pass=`True`
- `书中有没有提到量子纠缠？` -> expected=`refuse`, actual=`refuse`, pass=`True`

- 是否破坏原三条冻结样例: `False`
