# Hybrid Answer Smoke Checks

## 运行命令

`python -m backend.answers.assembler`

## 结论

- retrieval_backend: `hybrid_rrf_rerank`

- `黄连汤方的条文是什么？` -> mode=`strong`, primary=3, secondary=3, review=2, citations=3
- `烧针益阳而损阴是什么意思？` -> mode=`weak_with_review_notice`, primary=0, secondary=9, review=1, citations=10
- `书中有没有提到量子纠缠？` -> mode=`refuse`, primary=0, secondary=0, review=0, citations=0
- `若噎者怎么办？` -> mode=`weak_with_review_notice`, primary=0, secondary=0, review=1, citations=1

## Validation

- strong_precision_patch_preserved: `True`
- weak_review_notice_present: `True`
- refuse_guidance_present: `True`

## Query: 黄连汤方的条文是什么？

- answer_mode: `strong`
- answer_text: 和“黄连汤方”直接相关的主条，当前主要落在这些方文或条文片段里。
黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。
味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温
上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之，人参、甘草、大枣之甘以益胃。
可以先据此理解原文意思，具体字句再结合引用继续回看。
- disclaimer: 主证据优先；补充依据与核对材料不参与主结论判定。
- review_notice: 以下补充依据与核对材料仅作说明，不作为主依据。
- refuse_reason: None
- evidence_summary: primary=3, secondary=3, review=2
- citations_summary: `[
  "safe:main_passages:ZJSHL-CH-010-P-0145",
  "safe:main_passages:ZJSHL-CH-010-P-0146",
  "safe:main_passages:ZJSHL-CH-010-P-0147"
]`
- display_sections: `[
  {
    "section_id": "answer",
    "visible": true,
    "field": "answer_text"
  },
  {
    "section_id": "review_notice",
    "visible": true,
    "field": "review_notice"
  },
  {
    "section_id": "primary_evidence",
    "visible": true,
    "field": "primary_evidence"
  },
  {
    "section_id": "secondary_evidence",
    "visible": true,
    "field": "secondary_evidence"
  },
  {
    "section_id": "review_materials",
    "visible": true,
    "field": "review_materials"
  },
  {
    "section_id": "citations",
    "visible": true,
    "field": "citations"
  },
  {
    "section_id": "refusal_guidance",
    "visible": false,
    "field": "suggested_followup_questions"
  }
]`

### Primary Evidence

[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
    "record_type": "main_passages",
    "display_role": "primary",
    "title": "黄连汤方",
    "evidence_level": "A",
    "chapter_id": "ZJSHL-CH-010",
    "chapter_title": "辨太阳病脉证并治法第七",
    "snippet": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。",
    "risk_flags": []
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0146",
    "record_type": "main_passages",
    "display_role": "primary",
    "title": "黄连汤方",
    "evidence_level": "A",
    "chapter_id": "ZJSHL-CH-010",
    "chapter_title": "辨太阳病脉证并治法第七",
    "snippet": "味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温",
    "risk_flags": []
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0147",
    "record_type": "main_passages",
    "display_role": "primary",
    "title": "黄连汤方",
    "evidence_level": "A",
    "chapter_id": "ZJSHL-CH-010",
    "chapter_title": "辨太阳病脉证并治法第七",
    "snippet": "上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之，人参、甘草、大枣之甘以益胃。",
    "risk_flags": []
  }
]

### Secondary Evidence

[
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0016",
    "record_type": "main_passages",
    "display_role": "secondary",
    "title": "葛根黄芩黄连汤方",
    "evidence_level": "B",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "葛根黄芩黄连汤方：赵本芩、连互易",
    "risk_flags": [
      "short_text_demoted"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0017",
    "record_type": "main_passages",
    "display_role": "secondary",
    "title": "葛根黄芩黄连汤方",
    "evidence_level": "A",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "葛根半斤 甘草二两，炙。味甘平 黄芩二，赵本作「三」两。味苦寒 黄连三两。味苦寒",
    "risk_flags": [
      "topic_mismatch_demoted"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0019",
    "record_type": "main_passages",
    "display_role": "secondary",
    "title": "葛根黄芩黄连汤方",
    "evidence_level": "A",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "上四味，以水八升，先煮葛根，减二升，内诸药，煮取二升，去滓，分温再服。",
    "risk_flags": [
      "topic_mismatch_demoted"
    ]
  }
]

### Review Materials

[
  {
    "record_id": "full:passages:ZJSHL-CH-010-P-0145",
    "record_type": "passages",
    "display_role": "review",
    "title": "黄连汤方",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-010",
    "chapter_title": "辨太阳病脉证并治法第七",
    "snippet": "黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。",
    "risk_flags": [
      "ledger_mixed_roles"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0016",
    "record_type": "passages",
    "display_role": "review",
    "title": "葛根黄芩黄连汤方",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "葛根黄芩黄连汤方：赵本芩、连互易",
    "risk_flags": [
      "ledger_mixed_roles"
    ]
  }
]

### Suggested Follow-up Questions

_no rows_

## Query: 烧针益阳而损阴是什么意思？

- answer_mode: `weak_with_review_notice`
- answer_text: 这个问题目前只能先保守地理解到这里：卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也。。
之所以只能先这样说，是因为当前缺少更稳定的正文主证据。
建议先回看这条命中片段所在原句，再核对前后文。
- disclaimer: 当前只输出弱表述与核对材料，不输出确定性答案。
- review_notice: 正文强证据不足，以下内容需核对，不应视为确定答案。
- refuse_reason: None
- evidence_summary: primary=0, secondary=9, review=1
- citations_summary: `[
  "full:annotations:ZJSHL-CH-003-P-0016",
  "safe:main_passages:ZJSHL-CH-009-P-0295",
  "safe:main_passages:ZJSHL-CH-010-P-0080",
  "full:passages:ZJSHL-CH-003-P-0015",
  "full:passages:ZJSHL-CH-003-P-0017",
  "full:passages:ZJSHL-CH-009-P-0294",
  "full:passages:ZJSHL-CH-009-P-0296",
  "full:passages:ZJSHL-CH-010-P-0079",
  "full:passages:ZJSHL-CH-010-P-0081",
  "full:passages:ZJSHL-CH-003-P-0016"
]`
- display_sections: `[
  {
    "section_id": "answer",
    "visible": true,
    "field": "answer_text"
  },
  {
    "section_id": "review_notice",
    "visible": true,
    "field": "review_notice"
  },
  {
    "section_id": "primary_evidence",
    "visible": false,
    "field": "primary_evidence"
  },
  {
    "section_id": "secondary_evidence",
    "visible": true,
    "field": "secondary_evidence"
  },
  {
    "section_id": "review_materials",
    "visible": true,
    "field": "review_materials"
  },
  {
    "section_id": "citations",
    "visible": true,
    "field": "citations"
  },
  {
    "section_id": "refusal_guidance",
    "visible": false,
    "field": "suggested_followup_questions"
  }
]`

### Primary Evidence

_no rows_

### Secondary Evidence

[
  {
    "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
    "record_type": "annotations",
    "display_role": "secondary",
    "title": "卫阳也荣阴也烧针益阳而损阴荣气微者谓阴虚也内经曰",
    "evidence_level": "B",
    "chapter_id": "ZJSHL-CH-003",
    "chapter_title": "辨脉法第一",
    "snippet": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也。",
    "risk_flags": [
      "annotation_unlinked"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-009-P-0295",
    "record_type": "main_passages",
    "display_role": "secondary",
    "title": "烧针发汗则损阴血而惊动心气针处被寒气聚而成核心气因惊而虚肾气乘寒气而动发为奔豚金匮要略曰",
    "evidence_level": "A",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "烧针发汗，则损阴血，而惊动心气。针处被寒，气聚而成核。心气因惊而虚，肾气乘寒气而动，发为奔豚。《金匮要略》曰：病有奔豚，从惊发得之。肾气欲上乘心，故其气从少腹上冲心也。先灸核上，以散其寒，与桂枝加桂汤，以泄奔豚之气。",
    "risk_flags": [
      "topic_mismatch_demoted"
    ]
  },
  {
    "record_id": "safe:main_passages:ZJSHL-CH-010-P-0080",
    "record_type": "main_passages",
    "display_role": "secondary",
    "title": "太阳病医发汗遂发热恶寒因复下之心下痞表里俱虚阴阳气并竭无阳则阴独复加烧针因胸烦面色青黄肤者难治今色微黄手足温者易愈",
    "evidence_level": "A",
    "chapter_id": "ZJSHL-CH-010",
    "chapter_title": "辨太阳病脉证并治法第七",
    "snippet": "太阳病，医发汗，遂发热恶寒，因复下之，心下痞，表里俱虚，阴阳气并竭，无阳则阴独，复加烧针，因胸烦，面色青黄，肤 者，难治；今色微黄，手足温者，易愈。",
    "risk_flags": [
      "topic_mismatch_demoted"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0015",
    "record_type": "passages",
    "display_role": "secondary",
    "title": "上下文补充",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-003",
    "chapter_title": "辨脉法第一",
    "snippet": "荣气微者，加烧针，则血流赵本作「留」不行，更发热而躁烦也。",
    "risk_flags": [
      "context_padding"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0017",
    "record_type": "passages",
    "display_role": "secondary",
    "title": "上下文补充",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-003",
    "chapter_title": "辨脉法第一",
    "snippet": "脉赵本注：「一云秋脉」蔼蔼，如车盖者，名曰阳结也。",
    "risk_flags": [
      "context_padding"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0294",
    "record_type": "passages",
    "display_role": "secondary",
    "title": "上下文补充",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "烧针令其汗，针处被寒，核起而赤者，必发奔豚。气从少腹上冲心者，灸其核上各一壮，与桂枝加桂汤，赵本有「桂枝加桂汤方」详见本书卷十更加桂二两。赵本有「也」字",
    "risk_flags": [
      "context_padding"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0296",
    "record_type": "passages",
    "display_role": "secondary",
    "title": "上下文补充",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "火逆，下之，因烧针烦躁者，桂枝甘草龙骨牡蛎汤主之。",
    "risk_flags": [
      "context_padding"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-010-P-0079",
    "record_type": "passages",
    "display_role": "secondary",
    "title": "上下文补充",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-010",
    "chapter_title": "辨太阳病脉证并治法第七",
    "snippet": "右上赵本无「上」字三味等分，各别捣为散。以水一升半，先煮大枣肥者十枚，取八合，去滓，内药末。强人服一钱匕，羸人服半钱，温服之，平旦服。若下少病不除者，明日更服，加半钱，得快下利后，糜粥自养。",
    "risk_flags": [
      "context_padding"
    ]
  },
  {
    "record_id": "full:passages:ZJSHL-CH-010-P-0081",
    "record_type": "passages",
    "display_role": "secondary",
    "title": "上下文补充",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-010",
    "chapter_title": "辨太阳病脉证并治法第七",
    "snippet": "太阳病，因发汗，遂发热恶寒者，外虚阳气，邪复不除也，因复下之，又虚其里，表中虚，邪内陷，传于心下为痞。发汗表虚为竭阳，下之里虚为竭阴；表证罢为无阳，里有痞为阴独。",
    "risk_flags": [
      "context_padding"
    ]
  }
]

### Review Materials

[
  {
    "record_id": "full:passages:ZJSHL-CH-003-P-0016",
    "record_type": "passages",
    "display_role": "review",
    "title": "卫阳也荣阴也烧针益阳而损阴荣气微者谓阴虚也内经曰",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-003",
    "chapter_title": "辨脉法第一",
    "snippet": "卫阳也，荣阴也。烧针益阳而损阴。荣气微者，谓阴虚也。《内经》曰：阴虚而医统本作「生」内热，方其内热，又加烧针以补阳，不惟两热相合而荣血不行，必更外发然而内躁烦也。",
    "risk_flags": [
      "ledger_mixed_roles",
      "ambiguous_source"
    ]
  }
]

### Suggested Follow-up Questions

_no rows_

## Query: 书中有没有提到量子纠缠？

- answer_mode: `refuse`
- answer_text: 目前还没有检索到足以支撑回答的书内依据，所以这里先不硬答。可以改问更具体的条文、方名，或某一句话在书里是什么意思。
- disclaimer: 当前为统一拒答结构，不输出推测性答案。
- review_notice: None
- refuse_reason: 未检索到足以支撑回答的主证据、辅助证据或可供核对的风险材料。
- evidence_summary: primary=0, secondary=0, review=0
- citations_summary: `[]`
- display_sections: `[
  {
    "section_id": "answer",
    "visible": true,
    "field": "answer_text"
  },
  {
    "section_id": "review_notice",
    "visible": false,
    "field": "review_notice"
  },
  {
    "section_id": "primary_evidence",
    "visible": false,
    "field": "primary_evidence"
  },
  {
    "section_id": "secondary_evidence",
    "visible": false,
    "field": "secondary_evidence"
  },
  {
    "section_id": "review_materials",
    "visible": false,
    "field": "review_materials"
  },
  {
    "section_id": "citations",
    "visible": false,
    "field": "citations"
  },
  {
    "section_id": "refusal_guidance",
    "visible": true,
    "field": "suggested_followup_questions"
  }
]`

### Primary Evidence

_no rows_

### Secondary Evidence

_no rows_

### Review Materials

_no rows_

### Suggested Follow-up Questions

[
  "请改问具体条文，例如：某一条文的原文或含义是什么？",
  "请改问具体方名，例如：黄连汤方的组成或条文是什么？",
  "请改问书中某个明确术语或概念，例如：某句话出自哪一条？"
]

## Query: 若噎者怎么办？

- answer_mode: `weak_with_review_notice`
- answer_text: 这是一个总括性问题，书中谈“若噎者”并非只有一个固定治法，需要分情况看。
当前只能先整理出部分可核对的分支线索：
分支组织仍不完整，建议继续收窄到某一支再问。
- disclaimer: 当前只输出部分分支整理与核对材料，不输出完整定案。
- review_notice: 这是总括性问题，但当前只能整理出部分分支线索，以下内容需核对，不应视为完整答案。
- refuse_reason: None
- evidence_summary: primary=0, secondary=0, review=1
- citations_summary: `[
  "full:passages:ZJSHL-CH-009-P-0046"
]`
- display_sections: `[
  {
    "section_id": "answer",
    "visible": true,
    "field": "answer_text"
  },
  {
    "section_id": "review_notice",
    "visible": true,
    "field": "review_notice"
  },
  {
    "section_id": "primary_evidence",
    "visible": false,
    "field": "primary_evidence"
  },
  {
    "section_id": "secondary_evidence",
    "visible": false,
    "field": "secondary_evidence"
  },
  {
    "section_id": "review_materials",
    "visible": true,
    "field": "review_materials"
  },
  {
    "section_id": "citations",
    "visible": true,
    "field": "citations"
  },
  {
    "section_id": "refusal_guidance",
    "visible": true,
    "field": "suggested_followup_questions"
  }
]`

### Primary Evidence

_no rows_

### Secondary Evidence

_no rows_

### Review Materials

[
  {
    "record_id": "full:passages:ZJSHL-CH-009-P-0046",
    "record_type": "passages",
    "display_role": "review",
    "title": "若噎者去麻黄加附子一枚炮经曰",
    "evidence_level": "C",
    "chapter_id": "ZJSHL-CH-009",
    "chapter_title": "辨太阳病脉证并治第六",
    "snippet": "若噎者，去麻黄，加附子一枚，炮。经曰：水得寒气，冷必相搏，其人即KT 。加附子温散水寒。病患有寒，复发汗，胃中冷，必吐蛔，去麻黄恶发汗。赵本从「经曰」以下皆无",
    "risk_flags": [
      "ledger_mixed_roles",
      "ambiguous_source"
    ]
  }
]

### Suggested Follow-up Questions

[
  "请改问更窄的一支，例如：若噎者中某一支具体对应哪条？",
  "请改问更窄的处理线索，例如：若噎者里某种表现为什么用某方？"
]
