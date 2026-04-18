# Generation Alignment v1 Report

## 运行命令

`python -m backend.checks.generation_alignment_v1_checks`

## 开题对齐口径

- 开题原件：`docs/proposal/221030147张前_开题报告.docx`
- 开题要求生成式回答充分利用检索证据，并给出可核验的出处依据。
- 开题要求通过 Prompt 约束与结果校验降低幻觉，避免杜撰出处。
- 开题创新点明确提出“证据释义 / 要点抽取 -> 基于证据生成 -> 条文依据输出”的分步生成路径。

## LLM Config

- provider: `Alibaba Cloud Model Studio`
- model: `qwen-plus`
- base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- timeout_seconds: `20.0`
- max_output_tokens: `900`

## 总结

- total_cases: `6`
- required_cases: `3`
- explainer_cases: `3`
- mode_kept_all: `True`
- evidence_slots_kept_all: `True`
- citations_kept_all: `True`
- llm_used_all_non_refuse: `False`
- answer_text_style_all_non_refuse: `True`
- refuse_skips_llm: `True`

## Case: required_strong_huanglian_tang

- label: `required`
- query: `黄连汤方的条文是什么？`
- expected_mode: `strong`
- actual_mode: `strong`
- answer_source: `guardrail_fallback`
- attempted: `True`
- used_llm: `False`
- fallback_used: `True`
- payload_contract_kept: `True`
- evidence_slots_kept: `True`
- citations_kept: `True`
- paragraph_count: `3`
- inline_refs_present: `True`
- no_standalone_refs: `True`
- no_report_labels: `True`
- no_internal_meta: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
可以先把“黄连汤方的条文是什么”理解成和“黄连汤方：黄连味苦寒 甘草炙”、“味甘温 半夏半升，洗”直接相关的书内内容。[E1][E2]
从现有片段看，重点落在这些明写信息上，超出这层就不宜硬补。[E1][E2]
依据主要来自当前命中的条文或片段；如果要逐字确认语境，继续回看引用会更稳妥。[E1][E2]
```

### LLM Debug

`{
  "provider": "Alibaba Cloud Model Studio",
  "enabled": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "query_text": "黄连汤方的条文是什么？",
  "answer_mode": "strong",
  "attempted": true,
  "used_llm": false,
  "fallback_used": true,
  "skipped_reason": null,
  "fallback_reason": "Rendered answer_text contains a claim that cannot be aligned to its cited evidence.",
  "answer_source": "guardrail_fallback",
  "baseline_answer_text_excerpt": "和“黄连汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之，...",
  "attempts": [
    {
      "attempt": 1,
      "strict_retry": false,
      "status": "failed",
      "error": "Each paragraph must include at least one inline [E#] reference."
    },
    {
      "attempt": 2,
      "strict_retry": true,
      "status": "failed",
      "error": "Rendered answer_text contains a claim that cannot be aligned to its cited evidence."
    }
  ],
  "evidence_pack_summary": {
    "primary": [
      "E1",
      "E2",
      "E3"
    ],
    "secondary": [
      "E4",
      "E5",
      "E6"
    ],
    "review": [
      "E7",
      "E8"
    ]
  },
  "rendered_answer_text_excerpt": "可以先把“黄连汤方的条文是什么”理解成和“黄连汤方：黄连味苦寒 甘草炙”、“味甘温 半夏半升，洗”直接相关的书内内容。[E1][E2] 从现有片段看，重点落在这些明写信息上，超出这层就不宜硬补。[E1][E2] 依据主要来自当前命中的条文或片段；如果要逐字确认语境，继续回看引用会更稳妥。[E1][E2]"
}`

## Case: required_weak_shaozhen

- label: `required`
- query: `烧针益阳而损阴是什么意思？`
- expected_mode: `weak_with_review_notice`
- actual_mode: `weak_with_review_notice`
- answer_source: `llm`
- attempted: `True`
- used_llm: `True`
- fallback_used: `False`
- payload_contract_kept: `True`
- evidence_slots_kept: `True`
- citations_kept: `True`
- paragraph_count: `3`
- inline_refs_present: `True`
- no_standalone_refs: `True`
- no_report_labels: `True`
- no_internal_meta: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
‘烧针益阳而损阴’可以先理解为：用烧针这种温热刺激的方法，虽能振奋卫阳之气，却也容易耗伤荣阴（即营血、阴液），是一种利弊并存的干预方式。它提醒医者注意治法的偏性，尤其当患者本有阴虚时，强行助阳反会加重内热与躁烦。[E1][E4]

目前只能作此保守解释，是因为所见材料均为后世注文或夹注引述（如‘卫阳也，荣阴也’属释义性短语），未提供原始条文完整语境，也未说明该句出自哪一具体病证的治疗讨论。[E1][E4]

建议回看《辨脉法第一》中紧接其后的句子：‘荣气微者，谓阴虚也’，并对照《内经》原句‘阴虚而生内热’的逻辑链条，核对‘烧针’在此处是作为误治举例，还是特定条件下的权宜之法。[E1][E4]
```

### LLM Debug

`{
  "provider": "Alibaba Cloud Model Studio",
  "enabled": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "query_text": "烧针益阳而损阴是什么意思？",
  "answer_mode": "weak_with_review_notice",
  "attempted": true,
  "used_llm": true,
  "fallback_used": false,
  "skipped_reason": null,
  "fallback_reason": null,
  "answer_source": "llm",
  "baseline_answer_text_excerpt": "这个问题目前只能先保守地理解到这里：卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也。。 之所以只能先这样说，是因为当前缺少更稳定的正文主证据。 建议先回看这条命中片段所在原句，再核对前后文。",
  "attempts": [
    {
      "attempt": 1,
      "strict_retry": false,
      "status": "passed",
      "rendered_answer_text_excerpt": "‘烧针益阳而损阴’可以先理解为：用烧针这种温热刺激的方法，虽能振奋卫阳之气，却也容易耗伤荣阴（即营血、阴液），是一种利弊并存的干预方式。它提醒医者注意治法的偏性，尤其当患者本有阴虚时，强行助阳反会加重内热与躁烦。[E1][E4] 目前只能作此保守解释，是因为所见材料均为后世注文或夹注引述（如‘卫阳也，荣阴也’属释义性短..."
    }
  ],
  "evidence_pack_summary": {
    "primary": [],
    "secondary": [
      "E1",
      "E2",
      "E3"
    ],
    "review": [
      "E4"
    ]
  },
  "rendered_answer_text_excerpt": "‘烧针益阳而损阴’可以先理解为：用烧针这种温热刺激的方法，虽能振奋卫阳之气，却也容易耗伤荣阴（即营血、阴液），是一种利弊并存的干预方式。它提醒医者注意治法的偏性，尤其当患者本有阴虚时，强行助阳反会加重内热与躁烦。[E1][E4] 目前只能作此保守解释，是因为所见材料均为后世注文或夹注引述（如‘卫阳也，荣阴也’属释义性短..."
}`

## Case: required_refuse_quantum

- label: `required`
- query: `书中有没有提到量子纠缠？`
- expected_mode: `refuse`
- actual_mode: `refuse`
- answer_source: `baseline_refuse`
- attempted: `False`
- used_llm: `False`
- fallback_used: `False`
- payload_contract_kept: `True`
- evidence_slots_kept: `True`
- citations_kept: `True`
- paragraph_count: `1`
- inline_refs_present: `True`
- no_standalone_refs: `True`
- no_report_labels: `True`
- no_internal_meta: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
目前还没有检索到足以支撑回答的书内依据，所以这里先不硬答。可以改问更具体的条文、方名，或某一句话在书里是什么意思。
```

### LLM Debug

`{
  "provider": "Alibaba Cloud Model Studio",
  "enabled": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "query_text": "书中有没有提到量子纠缠？",
  "answer_mode": "refuse",
  "attempted": false,
  "used_llm": false,
  "fallback_used": false,
  "skipped_reason": "refuse_mode",
  "fallback_reason": null,
  "answer_source": "baseline_refuse",
  "baseline_answer_text_excerpt": "目前还没有检索到足以支撑回答的书内依据，所以这里先不硬答。可以改问更具体的条文、方名，或某一句话在书里是什么意思。",
  "attempts": []
}`

## Case: explainer_taiyang_management

- label: `explainer`
- query: `太阳病应该怎么办？`
- expected_mode: `strong`
- actual_mode: `strong`
- answer_source: `llm`
- attempted: `True`
- used_llm: `True`
- fallback_used: `False`
- payload_contract_kept: `True`
- evidence_slots_kept: `True`
- citations_kept: `True`
- paragraph_count: `3`
- inline_refs_present: `True`
- no_standalone_refs: `True`
- no_report_labels: `True`
- no_internal_meta: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
太阳病不是单指一个病，而是外感病初起阶段的一类证候，关键在于身体正在抵抗外邪，所以必有恶寒，还常伴身体疼痛、恶心呕吐、脉象绷紧。[E1]

它又分不同情况：比如后颈和背部僵硬发紧、不出汗、怕风，就是寒邪束表又影响到太阳经脉，这时用葛根汤；而如果已经出汗、怕风、头痛发热，说明肌表不固、营卫不和，就该用桂枝汤。[E2][E3]

这些判断和对应方剂都出自《伤寒论》辨太阳病脉证并治部分的原始条文。[E1][E2][E3]
```

### LLM Debug

`{
  "provider": "Alibaba Cloud Model Studio",
  "enabled": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "query_text": "太阳病应该怎么办？",
  "answer_mode": "strong",
  "attempted": true,
  "used_llm": true,
  "fallback_used": false,
  "skipped_reason": null,
  "fallback_reason": null,
  "answer_source": "llm",
  "baseline_answer_text_excerpt": "这是一个总括性问题，书中谈“太阳病”并非只有一个固定治法，需要分情况看。 以下先按当前能稳定抓到的典型分支整理： 1. 先辨伤寒：先看或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，书中把它单列成一个分支，提示“太阳病”并非只有一种证候。 依据：太阳病，或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，名曰赵...",
  "attempts": [
    {
      "attempt": 1,
      "strict_retry": false,
      "status": "passed",
      "rendered_answer_text_excerpt": "太阳病不是单指一个病，而是外感病初起阶段的一类证候，关键在于身体正在抵抗外邪，所以必有恶寒，还常伴身体疼痛、恶心呕吐、脉象绷紧。[E1] 它又分不同情况：比如后颈和背部僵硬发紧、不出汗、怕风，就是寒邪束表又影响到太阳经脉，这时用葛根汤；而如果已经出汗、怕风、头痛发热，说明肌表不固、营卫不和，就该用桂枝汤。[E2][E3..."
    }
  ],
  "evidence_pack_summary": {
    "primary": [
      "E1",
      "E2",
      "E3"
    ],
    "secondary": [
      "E4",
      "E5",
      "E6"
    ],
    "review": [
      "E7",
      "E8"
    ]
  },
  "rendered_answer_text_excerpt": "太阳病不是单指一个病，而是外感病初起阶段的一类证候，关键在于身体正在抵抗外邪，所以必有恶寒，还常伴身体疼痛、恶心呕吐、脉象绷紧。[E1] 它又分不同情况：比如后颈和背部僵硬发紧、不出汗、怕风，就是寒邪束表又影响到太阳经脉，这时用葛根汤；而如果已经出汗、怕风、头痛发热，说明肌表不固、营卫不和，就该用桂枝汤。[E2][E3..."
}`

## Case: explainer_huanglian_composition

- label: `explainer`
- query: `黄连汤方由什么组成？`
- expected_mode: `strong`
- actual_mode: `strong`
- answer_source: `llm`
- attempted: `True`
- used_llm: `True`
- fallback_used: `False`
- payload_contract_kept: `True`
- evidence_slots_kept: `True`
- citations_kept: `True`
- paragraph_count: `3`
- inline_refs_present: `True`
- no_standalone_refs: `True`
- no_report_labels: `True`
- no_internal_meta: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
黄连汤是一个由七味药组成的复方，核心配伍以黄连清上热、乾姜温下寒，配合桂枝通阳、人参补虚、半夏降逆、甘草与大枣调和诸药并顾护中气。[E1][E2]

方中每味药都标注了性味，如黄连苦寒、乾姜辛热、桂枝辛热、甘草甘平、人参甘温、半夏辛、大枣甘温，这些性味描述不是泛泛而谈，而是紧扣该药在此方中的作用定位。[E1][E2]

全方药物组成及剂量信息集中见于《辨太阳病脉证并治法第七》中‘黄连汤方’条下的方文组成部分。[E1][E2]
```

### LLM Debug

`{
  "provider": "Alibaba Cloud Model Studio",
  "enabled": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "query_text": "黄连汤方由什么组成？",
  "answer_mode": "strong",
  "attempted": true,
  "used_llm": true,
  "fallback_used": false,
  "skipped_reason": null,
  "fallback_reason": null,
  "answer_source": "llm",
  "baseline_answer_text_excerpt": "根据当前主依据，黄连汤方的组成可先按方文直读： 1. 黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 2. 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温",
  "attempts": [
    {
      "attempt": 1,
      "strict_retry": false,
      "status": "passed",
      "rendered_answer_text_excerpt": "黄连汤是一个由七味药组成的复方，核心配伍以黄连清上热、乾姜温下寒，配合桂枝通阳、人参补虚、半夏降逆、甘草与大枣调和诸药并顾护中气。[E1][E2] 方中每味药都标注了性味，如黄连苦寒、乾姜辛热、桂枝辛热、甘草甘平、人参甘温、半夏辛、大枣甘温，这些性味描述不是泛泛而谈，而是紧扣该药在此方中的作用定位。[E1][E2] 全..."
    }
  ],
  "evidence_pack_summary": {
    "primary": [
      "E1",
      "E2"
    ],
    "secondary": [],
    "review": [
      "E3",
      "E4"
    ]
  },
  "rendered_answer_text_excerpt": "黄连汤是一个由七味药组成的复方，核心配伍以黄连清上热、乾姜温下寒，配合桂枝通阳、人参补虚、半夏降逆、甘草与大枣调和诸药并顾护中气。[E1][E2] 方中每味药都标注了性味，如黄连苦寒、乾姜辛热、桂枝辛热、甘草甘平、人参甘温、半夏辛、大枣甘温，这些性味描述不是泛泛而谈，而是紧扣该药在此方中的作用定位。[E1][E2] 全..."
}`

## Case: explainer_guizhi_plus_fuzi_composition

- label: `explainer`
- query: `桂枝加附子汤方由什么组成？`
- expected_mode: `strong`
- actual_mode: `strong`
- answer_source: `llm`
- attempted: `True`
- used_llm: `True`
- fallback_used: `False`
- payload_contract_kept: `True`
- evidence_slots_kept: `True`
- citations_kept: `True`
- paragraph_count: `3`
- inline_refs_present: `True`
- no_standalone_refs: `True`
- no_report_labels: `True`
- no_internal_meta: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
桂枝加附子汤不是全新创制的方子，而是以桂枝汤为基础，额外加入一味炮附子所形成的加减方。[E1]

这个‘加’字很关键：它说明除附子外，其他药物种类、剂量和煎服方法都完全遵循桂枝汤的原有规定，没有改动。[E1]

需要特别注意的是，原文虽将术附汤一并列出，并称其‘附于此方内’，但这只是文本编排上的相邻关系，并不表示术附汤的成分属于桂枝加附子汤的组成部分。[E1]
```

### LLM Debug

`{
  "provider": "Alibaba Cloud Model Studio",
  "enabled": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "query_text": "桂枝加附子汤方由什么组成？",
  "answer_mode": "strong",
  "attempted": true,
  "used_llm": true,
  "fallback_used": false,
  "skipped_reason": null,
  "fallback_reason": null,
  "answer_source": "llm",
  "baseline_answer_text_excerpt": "根据当前主依据，桂枝加附子汤方的组成可先按方文直读： 1. 桂枝加附子汤方：于桂枝汤方内，加附子一枚，炮，去皮，破八片，馀根据前法。术附汤方，附于此方内，去桂枝，加白术四两，根据前法。",
  "attempts": [
    {
      "attempt": 1,
      "strict_retry": false,
      "status": "failed",
      "error": "Each paragraph must include at least one inline [E#] reference."
    },
    {
      "attempt": 2,
      "strict_retry": true,
      "status": "passed",
      "rendered_answer_text_excerpt": "桂枝加附子汤不是全新创制的方子，而是以桂枝汤为基础，额外加入一味炮附子所形成的加减方。[E1] 这个‘加’字很关键：它说明除附子外，其他药物种类、剂量和煎服方法都完全遵循桂枝汤的原有规定，没有改动。[E1] 需要特别注意的是，原文虽将术附汤一并列出，并称其‘附于此方内’，但这只是文本编排上的相邻关系，并不表示术附汤的成..."
    }
  ],
  "evidence_pack_summary": {
    "primary": [
      "E1"
    ],
    "secondary": [],
    "review": [
      "E2"
    ]
  },
  "rendered_answer_text_excerpt": "桂枝加附子汤不是全新创制的方子，而是以桂枝汤为基础，额外加入一味炮附子所形成的加减方。[E1] 这个‘加’字很关键：它说明除附子外，其他药物种类、剂量和煎服方法都完全遵循桂枝汤的原有规定，没有改动。[E1] 需要特别注意的是，原文虽将术附汤一并列出，并称其‘附于此方内’，但这只是文本编排上的相邻关系，并不表示术附汤的成..."
}`
