# Minimal LLM API Smoke Checks

## 运行命令

`python -m backend.api.minimal_api --llm-smoke --llm-enabled`

## LLM Config

- provider: `Alibaba Cloud Model Studio`
- interface: `OpenAI-compatible Chat Completions`
- model: `qwen-plus`
- mode: `non-thinking`
- base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- llm_enabled: `True`
- enable_thinking: `False`

## 结论

- `黄连汤方的条文是什么？` -> mode=`strong`, attempted=`True`, answer_source=`llm`, fallback=`False`, evidence_unchanged=`True`, citations_unchanged=`True`
- `烧针益阳而损阴是什么意思？` -> mode=`weak_with_review_notice`, attempted=`True`, answer_source=`llm`, fallback=`False`, evidence_unchanged=`True`, citations_unchanged=`True`
- `太阳病应该怎么办？` -> mode=`strong`, attempted=`True`, answer_source=`llm`, fallback=`False`, evidence_unchanged=`True`, citations_unchanged=`True`
- `桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？` -> mode=`strong`, attempted=`True`, answer_source=`llm`, fallback=`False`, evidence_unchanged=`True`, citations_unchanged=`True`
- `书中有没有提到量子纠缠？` -> mode=`refuse`, attempted=`False`, answer_source=`baseline_refuse`, fallback=`False`, evidence_unchanged=`True`, citations_unchanged=`True`

## Validation

- mode_match_kept: `True`
- evidence_unchanged: `True`
- citations_unchanged: `True`
- refuse_skips_llm: `True`
- llm_attempted_for_non_refuse: `True`
- answer_text_non_empty: `True`

## Query: 黄连汤方的条文是什么？

- expected_mode: `strong`
- baseline_mode: `strong`
- llm_mode: `strong`
- llm_attempted: `True`
- llm_used: `True`
- fallback_used: `False`
- answer_text_changed: `True`
- evidence_unchanged: `True`
- citations_unchanged: `True`
- llm_debug: `{
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
  "rendered_answer_text_excerpt": "1. 黄连汤方：黄连味苦寒；甘草炙，味甘平；乾姜味辛热；桂枝去皮，各三两，味辛热；人参二两。 2. 半夏半升，洗，味辛（医统本作甘、温）；大枣十二枚，擘，味甘温。 3. 上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之，人参、甘草、大枣之甘以益胃。"
}`
- baseline_citations: `[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0146",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0147",
    "citation_role": "primary"
  }
]`
- llm_citations: `[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0146",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0147",
    "citation_role": "primary"
  }
]`

## Query: 烧针益阳而损阴是什么意思？

- expected_mode: `weak_with_review_notice`
- baseline_mode: `weak_with_review_notice`
- llm_mode: `weak_with_review_notice`
- llm_attempted: `True`
- llm_used: `True`
- fallback_used: `False`
- answer_text_changed: `True`
- evidence_unchanged: `True`
- citations_unchanged: `True`
- llm_debug: `{
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
  "rendered_answer_text_excerpt": "正文强证据不足，以下内容需核对，暂不能视为确定答案。当前可先参考辅助材料： 1. 卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而（医统本作「生」）内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也。 2. 烧针发汗则损阴血而惊动心气，针处被寒气聚而成核，心气因惊而虚，肾..."
}`
- baseline_citations: `[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "citation_role": "secondary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0295",
    "citation_role": "secondary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0080",
    "citation_role": "secondary"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "citation_role": "review"
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
    "citation_role": "review"
  }
]`
- llm_citations: `[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "citation_role": "secondary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0295",
    "citation_role": "secondary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0080",
    "citation_role": "secondary"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "citation_role": "review"
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
    "citation_role": "review"
  }
]`

## Query: 太阳病应该怎么办？

- expected_mode: `strong`
- baseline_mode: `strong`
- llm_mode: `strong`
- llm_attempted: `True`
- llm_used: `True`
- fallback_used: `False`
- answer_text_changed: `True`
- evidence_unchanged: `True`
- citations_unchanged: `True`
- llm_debug: `{
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
  "rendered_answer_text_excerpt": "这是一个总括性问题，书中谈“太阳病”并非只有一个固定治法，需要分情况看。 以下按当前能稳定抓到的典型分支整理： 1. 先辨伤寒：先看或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，书中把它单列成一个分支，提示“太阳病”并非只有一种证候。依据：太阳病，或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，名曰赵本作..."
}`
- baseline_citations: `[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0195",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0002",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0220",
    "citation_role": "primary"
  }
]`
- llm_citations: `[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0195",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0002",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0220",
    "citation_role": "primary"
  }
]`

## Query: 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？

- expected_mode: `strong`
- baseline_mode: `strong`
- llm_mode: `strong`
- llm_attempted: `True`
- llm_used: `True`
- fallback_used: `False`
- answer_text_changed: `True`
- evidence_unchanged: `True`
- citations_unchanged: `True`
- llm_debug: `{
  "provider": "Alibaba Cloud Model Studio",
  "enabled": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "query_text": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
  "answer_mode": "strong",
  "attempted": true,
  "used_llm": true,
  "fallback_used": false,
  "skipped_reason": null,
  "fallback_reason": null,
  "answer_source": "llm",
  "baseline_answer_text_excerpt": "从现有方文与相关条文看，桂枝加附子汤方与桂枝加浓朴杏子汤方都从桂枝汤方加减而来，但显式加味和对应语境不同。 1. 显式加减与药味差异：桂枝加附子汤方明写加附子；桂枝加浓朴杏子汤方明写加浓朴、杏仁。 2. 条文语境：桂枝加附子汤方相关条文可见“太阳病，发汗，遂漏不止，其人恶风，小便难，四支微急，难以屈伸者”；桂枝加浓朴杏...",
  "rendered_answer_text_excerpt": "1. 显式加减与药味差异：桂枝加附子汤方于桂枝汤方内加附子一枚，炮，去皮，破八片；桂枝加浓朴杏子汤方于桂枝汤方内加浓朴二两、杏仁五十个，去皮尖。 2. 条文语境差异：桂枝加附子汤方对应条文为‘太阳病，发汗，遂漏不止，其人恶风，小便难，四支微急，难以屈伸者’；桂枝加浓朴杏子汤方对应条文为‘太阳病，下之微喘者，表未解故也’..."
}`
- baseline_citations: `[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-025-P-0004",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-025-P-0003",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0236",
    "citation_role": "secondary"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-025-P-0003",
    "citation_role": "review"
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-009-P-0053",
    "citation_role": "review"
  }
]`
- llm_citations: `[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-025-P-0004",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-025-P-0003",
    "citation_role": "primary"
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-008-P-0236",
    "citation_role": "secondary"
  },
  {
    "record_id": "full:passages:ZJSHL-CH-025-P-0003",
    "citation_role": "review"
  },
  {
    "record_id": "full:ambiguous_passages:ZJSHL-CH-009-P-0053",
    "citation_role": "review"
  }
]`

## Query: 书中有没有提到量子纠缠？

- expected_mode: `refuse`
- baseline_mode: `refuse`
- llm_mode: `refuse`
- llm_attempted: `False`
- llm_used: `False`
- fallback_used: `False`
- answer_text_changed: `False`
- evidence_unchanged: `True`
- citations_unchanged: `True`
- llm_debug: `{
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
  "baseline_answer_text_excerpt": "当前未检索到足以支撑回答的依据，暂不提供答案。"
}`
- baseline_citations: `[]`
- llm_citations: `[]`
