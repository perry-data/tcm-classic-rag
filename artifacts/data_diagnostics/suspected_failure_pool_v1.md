# 高疑似失败样本候选池 v1

- generated_at_utc: `2026-04-21T16:03:15.044023+00:00`
- scanned_query_count: `80`
- suspected_candidate_count: `40`
- 判定边界: 本文件只表示自动规则筛出的“高疑似失败候选”，不表示人工已确认失败。

## Signal Counts

- `commentarial_uncertain_scope_displayed`: 2
- `exact_hit_but_citation_misaligned`: 1
- `formula_cross_target_candidates`: 36
- `high_risk_candidate_dominance`: 22
- `precise_lookup_degraded`: 1

## Candidates

### 1. 桂枝去芍药汤方和桂枝去芍药加附子汤方的条文语境有什么不同？

- candidate_id: `cand_793584bad4`
- source: `goldset_original`
- answer_mode: `weak_with_review_notice`
- signals: `precise_lookup_degraded, formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-025-P-0005", "safe:main_passages:ZJSHL-CH-025-P-0006", "full:passages:ZJSHL-CH-025-P-0005", "full:passages:ZJSHL-CH-008-P-0238", "full:passages:ZJSHL-CH-025-P-0006"]`
- primary: `[]`
- why_review: 存在串方候选风险
- answer_excerpt: 两方都已识别，但当前比较仍有证据缺口，以下只按现有方文做弱整理：桂枝去芍药汤方 与 桂枝去芍药加附子汤方 的差异需要继续核对。 1. 显式加减与药味差异：桂枝去芍药加附子汤方明写加附子。 2. 语境证据缺口：当前未稳定找到 桂枝去芍药汤方和桂枝去芍药加附子汤方 的直接相关条文，因此语境差异只能暂缓判断。 3. 出处线索：桂枝去芍药汤方的方文见“卷十附方位置”；桂枝去芍药加附子汤方的方文见“卷十附方位置”；桂枝去芍药汤方相关条文位于“辨太...

### 2. 葛根黄芩黄连汤方的条文是什么？

- candidate_id: `cand_106f44d075`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, exact_hit_but_citation_misaligned, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0017", "safe:main_passages:ZJSHL-CH-009-P-0019"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0017", "safe:main_passages:ZJSHL-CH-009-P-0019"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“葛根黄芩黄连汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 葛根半斤 甘草二两，炙。味甘平 黄芩二，赵本作「三」两。味苦寒 黄连三两。味苦寒 上四味，以水八升，先煮葛根，减二升，内诸药，煮取二升，去滓，分温再服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 3. 甘草乾姜汤方和芍药甘草汤方的区别是什么？

- candidate_id: `cand_0b164b7d6c`
- source: `goldset_original`
- answer_mode: `weak_with_review_notice`
- signals: `formula_cross_target_candidates, commentarial_uncertain_scope_displayed`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0256", "safe:main_passages:ZJSHL-CH-008-P-0258", "full:annotations:ZJSHL-CH-008-P-0271", "safe:main_passages:ZJSHL-CH-008-P-0259", "safe:main_passages:ZJSHL-CH-008-P-0260", "full:passages:ZJSHL-CH-008-P-0256", "full:ambiguous_passages:ZJSHL-CH-008-P-0257", "full:passages:ZJSHL-CH-008-P-0271"]`
- primary: `[]`
- why_review: 存在串方候选风险；名家材料范围类型不清
- answer_excerpt: 这个问题目前只能先保守地理解到这里：伤寒脉浮，自汗出，小便数，心烦，微恶寒，脚挛急，反与桂枝汤，赵本无「汤」字，欲攻其表，此误也。得之便厥，咽中乾，烦燥，赵本作「躁」吐逆者，作甘草乾姜汤与之，以复其阳。若厥愈、足温者，更作芍药甘草汤与之，其脚即伸。若胃气不和，讝语者，少与调胃...。 之所以只能先这样说，是因为当前缺少更稳定的正文主证据。 建议先回看这条命中片段所在原句，再核对前后文。

### 4. 麻黄汤方的条文是什么？

- candidate_id: `cand_17e96557b0`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0023", "safe:main_passages:ZJSHL-CH-009-P-0025"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0023", "safe:main_passages:ZJSHL-CH-009-P-0025"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“麻黄汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 麻黄汤方：麻黄三两，去节。味甘温 桂枝二，医统本作三两，去皮。味辛热 甘草一两，炙。味甘平 杏仁七十个，汤，赵本无「汤」字，去皮尖。味辛温 上四味，以水九升，先煮麻黄，减二升，去上沫，内诸药，煮取二升半，去滓，温服八合，覆取微似汗，不须啜粥，馀如桂枝法将息。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 5. 大青龙汤方的条文是什么？

- candidate_id: `cand_22024903ca`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0033", "safe:main_passages:ZJSHL-CH-009-P-0034", "safe:main_passages:ZJSHL-CH-009-P-0035"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0033", "safe:main_passages:ZJSHL-CH-009-P-0034", "safe:main_passages:ZJSHL-CH-009-P-0035"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“大青龙汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 大青龙汤方：麻黄六两，去节。味甘温 桂枝二两，去皮。味辛热 甘草二两，炙。味甘平 杏人赵本人作「仁」，四十个，赵本作「枚」，去皮尖。味苦，甘温 生姜三两，切。味辛温 大枣十二，赵本无「二」字，枚，擘。味甘温 石膏如鸡子大碎。味甘，微寒 辛甘均为发散。然风宜辛散，寒宜甘发，医统本有「以」字辛甘相合，乃能发散荣卫之风寒。麻黄、甘草、石膏、杏人，以发散荣中之寒，桂枝、姜、枣，...

### 6. 葛根加半夏汤方的条文是什么？

- candidate_id: `cand_2a4ab47d0b`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-026-P-0001", "safe:main_passages:ZJSHL-CH-009-P-0012", "safe:main_passages:ZJSHL-CH-009-P-0013"]`
- primary: `["safe:main_passages:ZJSHL-CH-026-P-0001", "safe:main_passages:ZJSHL-CH-009-P-0012", "safe:main_passages:ZJSHL-CH-009-P-0013"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“葛根加半夏汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 葛根加半夏汤方：于葛根汤方内，加入半夏半升，馀根据葛根汤法。 葛根加半夏汤方：葛根四两 麻黄三两，去节，汤泡去黄汁，焙乾称 生姜三，赵本作二，两，切 甘草二两，炙 芍药二两 桂枝二两，去皮 大枣十二枚，擘 半夏半斤，赵本医统本并作「升」，洗 上八味，以水一斗，先煮葛根、麻黄，减二升，去白沫，内诸药，煮取三升，去滓，温服一升，覆取微似汗。 可以先据此理解原文意思，具体...

### 7. 调胃承气汤方的条文是什么？

- candidate_id: `cand_512035f1a1`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0264", "safe:main_passages:ZJSHL-CH-008-P-0266"]`
- primary: `["safe:main_passages:ZJSHL-CH-008-P-0264", "safe:main_passages:ZJSHL-CH-008-P-0266"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“调胃承气汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 调胃承气汤方：大黄四两，去皮，清酒浸。赵本作「洗」 甘草二两，炙，味甘平 芒硝赵本医统本并作「消」，半斤，医统本作「升」，味咸苦，大寒 右三味㕮咀，赵本无「㕮咀」二字以水三升，煑取一升，去滓，内芒硝更上火微煑，令沸，少少温服。赵本医统本并有「之」字 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 8. 栀子豉汤方和栀子乾姜汤方有什么不同？

- candidate_id: `cand_588f647f21`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, commentarial_uncertain_scope_displayed`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0175", "safe:main_passages:ZJSHL-CH-026-P-0004", "safe:main_passages:ZJSHL-CH-017-P-0050"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0175", "safe:main_passages:ZJSHL-CH-026-P-0004", "safe:main_passages:ZJSHL-CH-017-P-0050"]`
- why_review: 存在串方候选风险；名家材料范围类型不清
- answer_excerpt: 和这个问题直接相关的主条，当前主要落在这些命中片段里。 栀子乾姜汤方：栀子十四枚，赵本作「个」擘。味苦寒 乾姜二两。味辛热 栀子生姜豉汤方：于栀子豉汤方内，加生姜五两，馀根据前法。得吐，止后服。 枳实栀子豉汤方：枳实三枚，炙。苦寒 栀子十四枚，赵本作个，擘。苦寒 豉一升，绵裹。苦寒 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 9. 白虎汤方和白虎加人参汤方的区别是什么？

- candidate_id: `cand_63cf06ad35`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-025-P-0012", "safe:main_passages:ZJSHL-CH-010-P-0132", "safe:main_passages:ZJSHL-CH-011-P-0104"]`
- primary: `["safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-025-P-0012"]`
- why_review: 存在串方候选风险
- answer_excerpt: 从现有方文与相关条文看，白虎汤方与白虎加人参汤方在显式组成和相关条文语境上并不相同。 1. 显式加减与药味差异：白虎加人参汤方明写加人参。 2. 条文语境：白虎汤方相关条文可见“与”；白虎加人参汤方相关条文可见“若渴欲饮水，口乾舌燥者”。 3. 出处线索：白虎汤方的方文见“辨太阳病脉证并治法第七”；白虎加人参汤方的方文见“卷十附方位置”；白虎汤方相关条文位于“辨太阳病脉证并治法第七”；白虎加人参汤方相关条文位于“辨阳明病脉证并治法第八”...

### 10. 茯苓桂枝甘草大枣汤方的条文是什么？

- candidate_id: `cand_741350827e`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0110", "safe:main_passages:ZJSHL-CH-009-P-0112"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0110", "safe:main_passages:ZJSHL-CH-009-P-0112"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“茯苓桂枝甘草大枣汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 茯苓桂枝甘草大枣汤方：茯苓半斤。味甘平 甘草二两，炙。味甘平 大枣十五枚，擘。味甘平 桂枝四两，去皮 上四味，以甘烂水一斗，先煮茯苓，减二升，内诸药，煮取三升，去滓，温服一升，日三服。作甘烂水法，取水二斗，置大盆内，以勺扬之，水上有珠子五六千颗相逐，取用之。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 11. 茯苓桂枝白术甘草汤方的条文是什么？

- candidate_id: `cand_8df5bcb75d`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0120", "safe:main_passages:ZJSHL-CH-009-P-0122"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0120", "safe:main_passages:ZJSHL-CH-009-P-0122"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“茯苓桂枝白术甘草汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 茯苓桂枝白术甘草汤方：茯苓四两。味甘平 桂枝三两，去皮。味辛热 白术二两。味苦甘温 甘草二两，炙。味甘平 上四味，以水六升，煮取三升，去滓，分温三服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 12. 猪苓汤方的条文是什么？

- candidate_id: `cand_94f2e169d9`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-011-P-0109"]`
- primary: `["safe:main_passages:ZJSHL-CH-011-P-0109"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“猪苓汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 猪苓汤方：猪苓去皮。甘平 茯苓甘平 阿胶甘平 滑石碎。甘寒 泽泻各一两。甘咸寒 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 13. 桃核承气汤方的条文是什么？

- candidate_id: `cand_9d75b76fb2`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0261", "safe:main_passages:ZJSHL-CH-009-P-0263"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0261", "safe:main_passages:ZJSHL-CH-009-P-0263"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“桃核承气汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 桃核承气汤方：桃人人赵本作仁，五十个，去皮尖。味甘平 桂枝二两，去皮。味辛热 大黄四两 芒硝二两 甘草二两，炙 上五味，以水七升，煮取二升半，去滓，内芒硝，更上火微沸。下火，先食温服五合，日三服，当微利。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 14. 麻黄汤方和大青龙汤方的区别是什么？

- candidate_id: `cand_a2554e6fd3`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0033", "safe:main_passages:ZJSHL-CH-009-P-0077", "safe:main_passages:ZJSHL-CH-009-P-0036"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0033"]`
- why_review: 存在串方候选风险
- answer_excerpt: 从现有方文与相关条文看，麻黄汤方与大青龙汤方在显式组成和相关条文语境上并不相同。 1. 条文语境：麻黄汤方相关条文可见“伤寒脉浮紧，不发汗，因致衄者”；大青龙汤方相关条文可见“伤寒脉浮缓，身不疼，但重，乍有轻时，无少阴证者”。 2. 出处线索：麻黄汤方的方文见“辨太阳病脉证并治第六”；大青龙汤方的方文见“辨太阳病脉证并治第六”；麻黄汤方相关条文位于“辨太阳病脉证并治第六”；大青龙汤方相关条文位于“辨太阳病脉证并治第六”。 以上差异仅按当...

### 15. 大承气汤方的条文是什么？

- candidate_id: `cand_ab45b641cd`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-011-P-0068", "safe:main_passages:ZJSHL-CH-011-P-0070"]`
- primary: `["safe:main_passages:ZJSHL-CH-011-P-0068", "safe:main_passages:ZJSHL-CH-011-P-0070"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“大承气汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 大承气汤方：大黄四两，酒洗。苦寒 浓朴半斤，炙，去皮。苦温 枳实五枚，炙。苦寒 芒硝三合。咸寒 上四味，以水一斗，先煮二物，取五升，去滓，内大黄，赵本有「更」字煮取二升，去滓，内芒硝，更上微火一两沸，分温再服。得下，馀勿服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 16. 大柴胡汤方的条文是什么？

- candidate_id: `cand_ac8bbfd68f`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0250"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0250"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“大柴胡汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 大柴胡汤方：柴胡半斤。味甘平 黄芩三两。味苦寒 芍药三两。味酸，微寒 半夏半升，洗。味辛温 生姜五两，切。味辛温 枳实四枚，炙。味苦寒 大枣十二枚，擘。医统本有「味」字，甘温 大黄二两。味苦寒，赵本无「大黄」一药 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 17. 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？

- candidate_id: `cand_b00c831aec`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003", "safe:main_passages:ZJSHL-CH-008-P-0236", "full:passages:ZJSHL-CH-025-P-0003", "full:passages:ZJSHL-CH-009-P-0053"]`
- primary: `["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003"]`
- why_review: 存在串方候选风险
- answer_excerpt: 从现有方文与相关条文看，桂枝加附子汤方与桂枝加浓朴杏子汤方都从桂枝汤方加减而来，但显式加味和对应语境不同。 1. 显式加减与药味差异：桂枝加附子汤方明写加附子；桂枝加浓朴杏子汤方明写加浓朴、杏仁。 2. 条文语境：桂枝加附子汤方相关条文可见“太阳病，发汗，遂漏不止，其人恶风，小便难，四支微急，难以屈伸者”；桂枝加浓朴杏子汤方核对材料可见“太阳病，下之微喘者，表未解故也”。 3. 出处线索：桂枝加附子汤方的方文见“卷十附方位置”；桂枝加浓...

### 18. 白虎汤方的条文是什么？

- candidate_id: `cand_b3da44899a`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-010-P-0167"]`
- primary: `["safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-010-P-0167"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“白虎汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 白虎汤方：知母六两。味苦寒 石膏一斤，碎。味甘寒 甘草二两，赵本有「炙」字。味甘平 粳米六合。味甘平 上四味，以水一斗，煮米熟，汤成，去滓，温服一升，日三服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 19. 大承气汤方和小承气汤方的区别是什么？

- candidate_id: `cand_d87d6541e0`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-011-P-0068", "safe:main_passages:ZJSHL-CH-011-P-0071", "safe:main_passages:ZJSHL-CH-011-P-0005", "safe:main_passages:ZJSHL-CH-015-P-0316"]`
- primary: `["safe:main_passages:ZJSHL-CH-011-P-0068", "safe:main_passages:ZJSHL-CH-011-P-0071"]`
- why_review: 存在串方候选风险
- answer_excerpt: 从现有方文与相关条文看，大承气汤方与小承气汤方在显式组成和相关条文语境上并不相同。 1. 条文语境：大承气汤方相关条文可见“手足 然汗出者，此大便已硬也”；小承气汤方相关条文可见“下利，谵语者，有燥屎也，宜”。 2. 出处线索：大承气汤方的方文见“辨阳明病脉证并治法第八”；小承气汤方的方文见“辨阳明病脉证并治法第八”；大承气汤方相关条文位于“辨阳明病脉证并治法第八”；小承气汤方相关条文位于“辨厥阴病脉证并治法第十二”。 以上差异仅按当前...

### 20. 黄连汤方的条文是什么？

- candidate_id: `cand_ffe5e58b72`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates, high_risk_candidate_dominance`
- citations: `["safe:main_passages:ZJSHL-CH-010-P-0145", "safe:main_passages:ZJSHL-CH-010-P-0146", "safe:main_passages:ZJSHL-CH-010-P-0147"]`
- primary: `["safe:main_passages:ZJSHL-CH-010-P-0145", "safe:main_passages:ZJSHL-CH-010-P-0146", "safe:main_passages:ZJSHL-CH-010-P-0147"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“黄连汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之，人参、甘草、大枣之甘以益胃。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 21. 卫气者所以温分肉是什么意思？

- candidate_id: `cand_a1f969c59e`
- source: `goldset_original`
- answer_mode: `weak_with_review_notice`
- signals: `high_risk_candidate_dominance`
- citations: `["full:annotations:ZJSHL-CH-003-P-0013", "full:annotations:ZJSHL-CH-004-P-0209", "full:passages:ZJSHL-CH-003-P-0012", "full:passages:ZJSHL-CH-004-P-0208", "full:passages:ZJSHL-CH-003-P-0014", "full:passages:ZJSHL-CH-003-P-0013", "full:passages:ZJSHL-CH-004-P-0209"]`
- primary: `[]`
- why_review: 命中了一个或多个自动疑似失败信号
- answer_excerpt: 这个问题目前只能先保守地理解到这里：《针经》云：卫气者，所以温分肉、充皮毛、肥腠理、司开合者也。脉浮，汗出如流珠者，腠理不密，开合不司，为卫气外衰也。浮主候卫，沉主候荣，以浮沉别荣卫之衰微，理固然矣。。 之所以只能先这样说，是因为当前缺少更稳定的正文主证据。 建议先回看这条命中片段所在原句，再核对前后文。

### 22. 小建中汤方的条文是什么？

- candidate_id: `cand_05e3255455`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0239", "safe:main_passages:ZJSHL-CH-009-P-0241"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0239", "safe:main_passages:ZJSHL-CH-009-P-0241"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“小建中汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 小建中汤方：桂枝三两，去皮。味辛热 甘草三赵本作「二」两，炙。味甘平 大枣十二枚，擘。味甘温 芍药六两。味酸微寒 生姜三两，切。味辛温 胶饴一升。味甘温 上六味，以水七升，煮取三升，去滓，内胶赵本无「胶」字饴，更上微火，消解，温服一升，日三服。呕家不可用建中汤，以甜故也。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 23. 小承气汤方的条文是什么？

- candidate_id: `cand_08c1d286fe`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-011-P-0071", "safe:main_passages:ZJSHL-CH-011-P-0072", "safe:main_passages:ZJSHL-CH-011-P-0073"]`
- primary: `["safe:main_passages:ZJSHL-CH-011-P-0071", "safe:main_passages:ZJSHL-CH-011-P-0072", "safe:main_passages:ZJSHL-CH-011-P-0073"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“小承气汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 小承气汤方：大黄四两。赵本有「酒洗」二字 浓朴二两，炙，去皮。 枳实三枚，大者，炙 大热结实者，与大承气汤；小热微结者，与小承气汤。以热不大甚，故于大承气汤去芒硝；又以结不至坚，故不熊校记：故亦减浓朴、枳实也，汪本亦改不。按汪以方内仍有枳实，故云不减，殊不思改半斤或二两，五枚为三枚，乃所谓减也，且以上句文义推之，正是亦，非... 以上赵本作「右」三味，以水四升，煮取一升...

### 24. 桂枝汤方和葛根汤方的区别是什么？

- candidate_id: `cand_08cbccddcb`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-009-P-0004", "safe:main_passages:ZJSHL-CH-009-P-0055", "safe:main_passages:ZJSHL-CH-008-P-0222"]`
- primary: `["safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-009-P-0004"]`
- why_review: 存在串方候选风险
- answer_excerpt: 从现有方文与相关条文看，桂枝汤方与葛根汤方在显式组成和相关条文语境上并不相同。 1. 显式加减与药味差异：葛根汤方另去节桂、皮芍药。 2. 条文语境：桂枝汤方相关条文可见“欲解外者，宜”；葛根汤方相关条文可见“太阳病，项背强几几，反汗出恶风者，桂枝加”。 3. 出处线索：桂枝汤方的方文见“辨太阳病脉证并治法上第五”；葛根汤方的方文见“辨太阳病脉证并治第六”；桂枝汤方相关条文位于“辨太阳病脉证并治第六”；葛根汤方相关条文位于“辨太阳病脉证...

### 25. 小青龙汤方的条文是什么？

- candidate_id: `cand_0f55ad9523`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0040", "safe:main_passages:ZJSHL-CH-009-P-0043"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0040", "safe:main_passages:ZJSHL-CH-009-P-0043"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“小青龙汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 小青龙汤方：麻黄三两：去节。味甘温 芍药三两。味酸微寒 五味子半升。味酸温 乾姜三两。味辛热 甘草三两，炙。味甘平 桂枝三两，去皮。味辛热 半夏半升，汤。赵本无「汤」字，洗。 上八味，以水一斗，先煮麻黄，减二升，去上沫，内诸药，煮取三升，去滓，温服一升。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 26. 乾姜附子汤方的条文是什么？

- candidate_id: `cand_161cb3777f`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0093", "safe:main_passages:ZJSHL-CH-009-P-0095"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0093", "safe:main_passages:ZJSHL-CH-009-P-0095"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“乾姜附子汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 乾姜附子汤方：乾姜一两。味辛热 附子一枚生用，去皮，破，赵本作切，八片。味辛热 上二味，以水三升，煮取一升，去滓，顿服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 27. 小柴胡汤方和大柴胡汤方有什么异同？

- candidate_id: `cand_2cbf0388ac`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-015-P-0326", "safe:main_passages:ZJSHL-CH-011-P-0123", "safe:main_passages:ZJSHL-CH-026-P-0005"]`
- primary: `["safe:main_passages:ZJSHL-CH-015-P-0326", "safe:main_passages:ZJSHL-CH-011-P-0123", "safe:main_passages:ZJSHL-CH-026-P-0005"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和这个问题直接相关的主条，当前主要落在这些命中片段里。 呕而发热者，小柴胡汤主之。赵本有「小柴胡汤方」详见卷三 阳明病，发潮热，大便溏，小便自可，胸胁满不去者，小柴胡汤主之。赵本作「与小柴胡汤」，又有「小柴胡汤方」详见卷三 柴胡加芒硝汤方：于小柴胡汤方内，加芒硝六两，馀根据前法。服不解，更服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 28. 半夏泻心汤方和甘草泻心汤方的区别是什么？

- candidate_id: `cand_2db2f60048`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-010-P-0068", "safe:main_passages:ZJSHL-CH-027-P-0009", "full:passages:ZJSHL-CH-010-P-0068", "full:passages:ZJSHL-CH-010-P-0066", "full:passages:ZJSHL-CH-027-P-0009", "full:passages:ZJSHL-CH-010-P-0095"]`
- primary: `["safe:main_passages:ZJSHL-CH-010-P-0068", "safe:main_passages:ZJSHL-CH-027-P-0009"]`
- why_review: 存在串方候选风险
- answer_excerpt: 从现有方文与相关条文看，半夏泻心汤方与甘草泻心汤方在显式组成和相关条文语境上并不相同。 1. 条文语境：半夏泻心汤方核对材料可见“但满而不痛者，此为痞，柴胡不中与之，宜”；甘草泻心汤方核对材料可见“医见心下痞，谓病不尽，复下之，其痞益甚，此非结热，但以胃中虚，客气上逆，故使硬也”。 2. 出处线索：半夏泻心汤方的方文见“辨太阳病脉证并治法第七”；甘草泻心汤方的方文见“《以上六方，病证并在第三卷内。》”；半夏泻心汤方相关条文位于“辨太阳病...

### 29. 桂枝甘草汤方的条文是什么？

- candidate_id: `cand_429d7f77f9`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0105"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0105"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“桂枝甘草汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 桂枝甘草汤方：桂枝四两，去皮。味辛热 甘草二两，炙。味甘平 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 30. 葛根汤方的条文是什么？

- candidate_id: `cand_42c5f6df7a`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0004", "safe:main_passages:ZJSHL-CH-009-P-0006"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0004", "safe:main_passages:ZJSHL-CH-009-P-0006"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“葛根汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 葛根汤方：葛根四两麻黄三两，去节桂赵本有「枝」字，二两，去皮芍药二两，切。赵本无「切」字甘草二两，炙生姜三两，切 大枣十二枚，擘 右柒味㕮咀，赵本无「㕮咀」二字以水一斗，先煑麻黄葛根，减二升，去赵本有「白」字沫，内诸药，煑取三升，去滓，温服一升，覆取微似汗，不须啜粥，赵本无「不须啜粥」一句馀如桂枝法，将息及禁忌。赵本有「诸汤皆仿此」五字 可以先据此理解原文意思，具体字句再...

### 31. 桂枝汤方的条文是什么？

- candidate_id: `cand_5ce10df646`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-008-P-0219"]`
- primary: `["safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-008-P-0219"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“桂枝汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 桂枝汤方：桂枝三两，去皮，味辛热，按：下药性，赵本无，以后并同 芍药三两。味苦酸，微寒 甘草二两，炙，味甘平 生姜三两，切，味辛温 大枣十二枚，擘，味甘温 右伍味，㕮咀。赵本有「三味」二字以水柒升，微火煑取三升，去滓，适寒温，服壹升。服已须臾，歠热稀粥壹升馀，以助药力，温覆令壹时许，遍身漐漐，微似有汗者益佳，不可令如水流漓，病必不除。若壹服汗出病差，停后服，不必尽剂；若不...

### 32. 小柴胡汤方的条文是什么？

- candidate_id: `cand_60c559f8bc`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-009-P-0211", "safe:main_passages:ZJSHL-CH-009-P-0213"]`
- primary: `["safe:main_passages:ZJSHL-CH-009-P-0211", "safe:main_passages:ZJSHL-CH-009-P-0213"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“小柴胡汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 小柴胡汤方：柴胡半斤。味苦，微寒 黄芩三两。味苦寒 人参三两。味甘温 甘草三两，赵本有「炙」字。味甘平 半夏半升，洗。味辛温 生姜三两，切。味辛温 大枣十三，赵本医统本并作「二」，枚，擘。味甘温 上七味，以水一斗二升，煮取六升，去滓，再煎，取三升，温服一升，日三服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 33. 四逆汤方和茯苓四逆汤方的区别是什么？

- candidate_id: `cand_7a19a3a044`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0267", "safe:main_passages:ZJSHL-CH-009-P-0130", "safe:main_passages:ZJSHL-CH-015-P-0305", "full:passages:ZJSHL-CH-009-P-0130", "full:passages:ZJSHL-CH-009-P-0128"]`
- primary: `["safe:main_passages:ZJSHL-CH-008-P-0267", "safe:main_passages:ZJSHL-CH-009-P-0130"]`
- why_review: 存在串方候选风险
- answer_excerpt: 从现有方文与相关条文看，四逆汤方与茯苓四逆汤方在显式组成和相关条文语境上并不相同。 1. 条文语境：四逆汤方相关条文可见“下利清谷，里寒外热，汗出而厥者，通脉”；茯苓四逆汤方核对材料可见“发汗若下之，病仍不解，烦躁者”。 2. 出处线索：四逆汤方的方文见“辨太阳病脉证并治法上第五”；茯苓四逆汤方的方文见“辨太阳病脉证并治第六”；四逆汤方相关条文位于“辨厥阴病脉证并治法第十二”；茯苓四逆汤方相关条文位于“辨太阳病脉证并治第六”。 以上差异...

### 34. 甘草乾姜汤方的条文是什么？

- candidate_id: `cand_7dc27b2e4a`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0258", "safe:main_passages:ZJSHL-CH-008-P-0259", "safe:main_passages:ZJSHL-CH-008-P-0260"]`
- primary: `["safe:main_passages:ZJSHL-CH-008-P-0258", "safe:main_passages:ZJSHL-CH-008-P-0259", "safe:main_passages:ZJSHL-CH-008-P-0260"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“甘草乾姜汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 甘草乾姜汤方：甘草四两，炙，味甘平 乾姜二两，炮，味辛热 《内经》曰：辛甘发散为阳，甘草乾姜相合，以复阳气。 右㕮咀，赵本作「二味」以水叁升，煑取一升五合，去滓，分温再服。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 35. 蔼蔼如车盖是什么意思？

- candidate_id: `cand_88d7c4acb7`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `high_risk_candidate_dominance`
- citations: `["full:passages:ZJSHL-CH-003-P-0018"]`
- primary: `["full:passages:ZJSHL-CH-003-P-0018"]`
- why_review: 命中了一个或多个自动疑似失败信号
- answer_excerpt: 从现有解释句看，“蔼蔼如车盖”可先参考“蔼蔼如车盖者，大而厌厌聂聂也。”来理解。 直接依据：蔼蔼如车盖者，大而厌厌聂聂也。

### 36. 四逆汤方的条文是什么？

- candidate_id: `cand_a7440fcbec`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0267", "safe:main_passages:ZJSHL-CH-008-P-0268", "safe:main_passages:ZJSHL-CH-008-P-0269"]`
- primary: `["safe:main_passages:ZJSHL-CH-008-P-0267", "safe:main_passages:ZJSHL-CH-008-P-0268", "safe:main_passages:ZJSHL-CH-008-P-0269"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“四逆汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 四逆汤方：甘草二两，炙。味甘平乾姜一两半。味辛热附子一枚，生用，去皮，破八片。辛，大热 《内经》曰：寒淫于内，治以甘热；又曰：寒淫所胜，平以辛热。甘草姜附相合，为甘辛大热之剂，乃可发散阴阳之气。 右三味㕮咀，赵本无「㕮咀」二字以水三升，煑取一升二合，去滓，分温再服，强人可大附子一枚，乾姜三两。 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 37. 累累如循长竿是什么意思？

- candidate_id: `cand_ab98b920c5`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `high_risk_candidate_dominance`
- citations: `["full:passages:ZJSHL-CH-003-P-0020"]`
- primary: `["full:passages:ZJSHL-CH-003-P-0020"]`
- why_review: 命中了一个或多个自动疑似失败信号
- answer_excerpt: 从现有解释句看，“累累如循长竿”可先参考“累累如循长竿者，连连而强直也。”来理解。 直接依据：累累如循长竿者，连连而强直也。

### 38. 芍药甘草汤方的条文是什么？

- candidate_id: `cand_bcc3d6a51c`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-008-P-0261", "safe:main_passages:ZJSHL-CH-008-P-0262", "safe:main_passages:ZJSHL-CH-008-P-0263"]`
- primary: `["safe:main_passages:ZJSHL-CH-008-P-0261", "safe:main_passages:ZJSHL-CH-008-P-0262", "safe:main_passages:ZJSHL-CH-008-P-0263"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“芍药甘草汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 芍药甘草汤方：白芍药四两。味，医统本有「苦」字，酸，微寒 甘草四两，炙。甘平 芍药，白补而赤泻，白收而赤散也。酸以收之，甘以缓之，酸甘相合，用补阴血。 右二味㕮咀，赵本无「㕮咀」二字以水叁升，煑取一升半，赵本作「五合」去滓，分温再服之。赵本无「之」字 可以先据此理解原文意思，具体字句再结合引用继续回看。

### 39. 荣气微者加烧针是什么意思？

- candidate_id: `cand_c2b1ea5cbd`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `high_risk_candidate_dominance`
- citations: `["full:passages:ZJSHL-CH-003-P-0015"]`
- primary: `["full:passages:ZJSHL-CH-003-P-0015"]`
- why_review: 命中了一个或多个自动疑似失败信号
- answer_excerpt: 从现有解释句看，“荣气微者加烧针”可先参考“荣气微者，加烧针，则血流不行，更发热而躁烦也。”来理解。 直接依据：荣气微者，加烧针，则血流不行，更发热而躁烦也。

### 40. 半夏泻心汤方的条文是什么？

- candidate_id: `cand_c83bc9a5e3`
- source: `goldset_original`
- answer_mode: `strong`
- signals: `formula_cross_target_candidates`
- citations: `["safe:main_passages:ZJSHL-CH-010-P-0068"]`
- primary: `["safe:main_passages:ZJSHL-CH-010-P-0068"]`
- why_review: 存在串方候选风险
- answer_excerpt: 和“半夏泻心汤方”直接相关的主条，当前主要落在这些方文或条文片段里。 半夏泻心汤方：半夏半升。赵本注：「一方用半夏一升」，洗。味辛平 黄芩味苦寒 乾姜味辛热 人参以上各三两。味甘温 黄连一两。味苦寒 大枣十二枚，擘。味温甘。医统本作甘温 甘草三两，炙。味甘平 可以先据此理解原文意思，具体字句再结合引用继续回看。
