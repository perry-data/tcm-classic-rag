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
- llm_used_all_non_refuse: `True`
- evidence_ref_alignment_all_non_refuse: `True`
- refuse_skips_llm: `True`

## Case: required_strong_huanglian_tang

- label: `required`
- query: `黄连汤方的条文是什么？`
- expected_mode: `strong`
- actual_mode: `strong`
- answer_source: `llm`
- attempted: `True`
- used_llm: `True`
- fallback_used: `False`
- payload_contract_kept: `True`
- evidence_slots_kept: `True`
- citations_kept: `True`
- refs_on_all_lines: `True`
- point_count: `3`
- numbered_points_valid: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
《伤寒论》中黄连汤方的条文载于‘辨太阳病脉证并治法第七’，包含药物组成、性味、剂量及配伍意义 [E1][E2][E3]。
1. 黄连汤由黄连、炙甘草、乾姜、桂枝（去皮）、人参、半夏、大枣七味药组成 [E1][E2]。
2. 各药剂量与性味明确标注，如黄连味苦寒，甘草炙、味甘平，乾姜与桂枝均味辛热、各三两，人参二两，半夏半升（洗），大枣十二枚（擘） [E1][E2]。
3. 条文指出其配伍原则为：黄连之苦以降上热，桂枝、乾姜、半夏之辛以散下寒，人参、甘草、大枣之甘以缓中益胃 [E3]。
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
  "used_llm": true,
  "fallback_used": false,
  "skipped_reason": null,
  "fallback_reason": null,
  "answer_source": "llm",
  "baseline_answer_text_excerpt": "根据主依据，与“黄连汤方”直接对应的条文主要有： 1. 黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 2. 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 3. 上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之...",
  "attempts": [
    {
      "attempt": 1,
      "strict_retry": false,
      "status": "failed",
      "error": "Rendered answer_text contains forbidden marker: ZJSHL-CH-"
    },
    {
      "attempt": 2,
      "strict_retry": true,
      "status": "passed",
      "rendered_answer_text_excerpt": "《伤寒论》中黄连汤方的条文载于‘辨太阳病脉证并治法第七’，包含药物组成、性味、剂量及配伍意义 [E1][E2][E3]。 1. 黄连汤由黄连、炙甘草、乾姜、桂枝（去皮）、人参、半夏、大枣七味药组成 [E1][E2]。 2. 各药剂量与性味明确标注，如黄连味苦寒，甘草炙、味甘平，乾姜与桂枝均味辛热、各三两，人参二两，半夏..."
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
  "rendered_answer_text_excerpt": "《伤寒论》中黄连汤方的条文载于‘辨太阳病脉证并治法第七’，包含药物组成、性味、剂量及配伍意义 [E1][E2][E3]。 1. 黄连汤由黄连、炙甘草、乾姜、桂枝（去皮）、人参、半夏、大枣七味药组成 [E1][E2]。 2. 各药剂量与性味明确标注，如黄连味苦寒，甘草炙、味甘平，乾姜与桂枝均味辛热、各三两，人参二两，半夏..."
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
- refs_on_all_lines: `True`
- point_count: `4`
- numbered_points_valid: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
‘烧针益阳而损阴’指烧针疗法虽可温助卫阳，却易耗伤营阴或阴血 [E1]。
1. 烧针属温热刺激，用以‘益阳’即扶助卫阳；但因其燥烈之性，反致营阴（荣阴）受损，故称‘损阴’ [E1][E4][E5]。
2. 若患者本有阴虚内热，再施烧针，则内外热相合，营血运行不畅，可致内躁烦、外发热等表现，此为‘益阳损阴’的病机延伸 [E1][E4][E5]。
3. 临床可见烧针后损阴血、惊动心气，甚则引动肾气上逆成奔豚；或于阴阳两虚基础上加烧针，加重胸烦、面色青黄等危重征象 [E2][E3]。
4. 需核对：诸证据均未明确定义‘阳’‘阴’在此语境下的具体所指（如卫/营、气/血、表/里），亦未说明烧针操作规范与剂量阈值，相关解释存在术语模糊性 [E1][E2][E3][E4][E5]。
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
  "baseline_answer_text_excerpt": "正文强证据不足，以下内容需核对，暂不能视为确定答案。 当前可先参考辅助材料：卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也。",
  "attempts": [
    {
      "attempt": 1,
      "strict_retry": false,
      "status": "failed",
      "error": "Rendered answer_text must contain 2-4 numbered points."
    },
    {
      "attempt": 2,
      "strict_retry": true,
      "status": "passed",
      "rendered_answer_text_excerpt": "‘烧针益阳而损阴’指烧针疗法虽可温助卫阳，却易耗伤营阴或阴血 [E1]。 1. 烧针属温热刺激，用以‘益阳’即扶助卫阳；但因其燥烈之性，反致营阴（荣阴）受损，故称‘损阴’ [E1][E4][E5]。 2. 若患者本有阴虚内热，再施烧针，则内外热相合，营血运行不畅，可致内躁烦、外发热等表现，此为‘益阳损阴’的病机延伸 [..."
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
      "E4",
      "E5"
    ]
  },
  "rendered_answer_text_excerpt": "‘烧针益阳而损阴’指烧针疗法虽可温助卫阳，却易耗伤营阴或阴血 [E1]。 1. 烧针属温热刺激，用以‘益阳’即扶助卫阳；但因其燥烈之性，反致营阴（荣阴）受损，故称‘损阴’ [E1][E4][E5]。 2. 若患者本有阴虚内热，再施烧针，则内外热相合，营血运行不畅，可致内躁烦、外发热等表现，此为‘益阳损阴’的病机延伸 [..."
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
- refs_on_all_lines: `False`
- point_count: `0`
- numbered_points_valid: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
当前未检索到足以支撑回答的依据，暂不提供答案。
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
  "baseline_answer_text_excerpt": "当前未检索到足以支撑回答的依据，暂不提供答案。",
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
- refs_on_all_lines: `True`
- point_count: `3`
- numbered_points_valid: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
太阳病的处理须据其具体脉证分型而定，不可一概而论 [E1]。
1. 太阳病以必恶寒、体痛、呕逆、脉阴阳俱紧为基本识别要点，是伤寒之名的确立依据 [E1]。
2. 若兼见项背强几几、无汗、恶风，则属太阳伤寒兼经气不利，当用葛根汤主治 [E2]。
3. 若见头痛、发热、汗出、恶风，则属太阳中风证，当用桂枝汤主治 [E3]。
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
      "rendered_answer_text_excerpt": "太阳病的处理须据其具体脉证分型而定，不可一概而论 [E1]。 1. 太阳病以必恶寒、体痛、呕逆、脉阴阳俱紧为基本识别要点，是伤寒之名的确立依据 [E1]。 2. 若兼见项背强几几、无汗、恶风，则属太阳伤寒兼经气不利，当用葛根汤主治 [E2]。 3. 若见头痛、发热、汗出、恶风，则属太阳中风证，当用桂枝汤主治 [E3]。"
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
  "rendered_answer_text_excerpt": "太阳病的处理须据其具体脉证分型而定，不可一概而论 [E1]。 1. 太阳病以必恶寒、体痛、呕逆、脉阴阳俱紧为基本识别要点，是伤寒之名的确立依据 [E1]。 2. 若兼见项背强几几、无汗、恶风，则属太阳伤寒兼经气不利，当用葛根汤主治 [E2]。 3. 若见头痛、发热、汗出、恶风，则属太阳中风证，当用桂枝汤主治 [E3]。"
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
- refs_on_all_lines: `True`
- point_count: `3`
- numbered_points_valid: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
黄连汤方由黄连、炙甘草、乾姜、桂枝、人参、半夏、大枣七味药组成 [E1][E2]。
1. 黄连、炙甘草、乾姜、桂枝剂量均为三两，人参为二两 [E1]。
2. 半夏用量为半升（洗），大枣为十二枚（擘） [E2]。
3. 方中逐味标注性味，如黄连味苦寒，炙甘草味甘平，乾姜与桂枝均味辛热，人参味甘温，半夏味辛（医统本作甘温），大枣味甘温 [E1][E2]。
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
      "rendered_answer_text_excerpt": "黄连汤方由黄连、炙甘草、乾姜、桂枝、人参、半夏、大枣七味药组成 [E1][E2]。 1. 黄连、炙甘草、乾姜、桂枝剂量均为三两，人参为二两 [E1]。 2. 半夏用量为半升（洗），大枣为十二枚（擘） [E2]。 3. 方中逐味标注性味，如黄连味苦寒，炙甘草味甘平，乾姜与桂枝均味辛热，人参味甘温，半夏味辛（医统本作甘温）..."
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
  "rendered_answer_text_excerpt": "黄连汤方由黄连、炙甘草、乾姜、桂枝、人参、半夏、大枣七味药组成 [E1][E2]。 1. 黄连、炙甘草、乾姜、桂枝剂量均为三两，人参为二两 [E1]。 2. 半夏用量为半升（洗），大枣为十二枚（擘） [E2]。 3. 方中逐味标注性味，如黄连味苦寒，炙甘草味甘平，乾姜与桂枝均味辛热，人参味甘温，半夏味辛（医统本作甘温）..."
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
- refs_on_all_lines: `True`
- point_count: `3`
- numbered_points_valid: `True`
- llm_attempted_when_expected: `True`

### Answer Text

```text
桂枝加附子汤由桂枝汤原方加附子一枚（炮，去皮，破八片）组成 [E1]。
1. 该方以桂枝汤为基础方，未改变其原有药物结构 [E1]。
2. 增加的药物仅为附子一枚，且明确要求炮制、去皮、破八片 [E1]。
3. 其余药物配伍、用量及煎服方法均遵循桂枝汤原法 [E1]。
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
      "status": "passed",
      "rendered_answer_text_excerpt": "桂枝加附子汤由桂枝汤原方加附子一枚（炮，去皮，破八片）组成 [E1]。 1. 该方以桂枝汤为基础方，未改变其原有药物结构 [E1]。 2. 增加的药物仅为附子一枚，且明确要求炮制、去皮、破八片 [E1]。 3. 其余药物配伍、用量及煎服方法均遵循桂枝汤原法 [E1]。"
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
  "rendered_answer_text_excerpt": "桂枝加附子汤由桂枝汤原方加附子一枚（炮，去皮，破八片）组成 [E1]。 1. 该方以桂枝汤为基础方，未改变其原有药物结构 [E1]。 2. 增加的药物仅为附子一枚，且明确要求炮制、去皮、破八片 [E1]。 3. 其余药物配伍、用量及煎服方法均遵循桂枝汤原法 [E1]。"
}`
