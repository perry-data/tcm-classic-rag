# Batch Upgrade Ledger v1

- run_id: `ambiguous_high_value_evidence_upgrade_v1`
- candidate_count: `32`
- promoted_safe_primary_count: `20`
- support_only_registered_count: `8`
- rejected_count: `4`
- alias_risk_conflict_count: `0`

## A Promoted

- `太阳病` -> `AHV-fdb12048d73e` from `records_main_passages:ZJSHL-CH-008-P-0191`
- `伤寒` -> `AHV-82d1c8a78473` from `records_passages:ZJSHL-CH-008-P-0195`
- `温病` -> `AHV-65a3bdee145b` from `risk_registry_ambiguous:ZJSHL-CH-006-P-0017`
- `暑病` -> `AHV-d1abf1c57ecf` from `records_passages:ZJSHL-CH-006-P-0012`
- `冬温` -> `AHV-9dfd46e14608` from `records_passages:ZJSHL-CH-006-P-0020`
- `时行寒疫` -> `AHV-bb8f9a64a54e` from `records_passages:ZJSHL-CH-006-P-0024`
- `刚痓` -> `AHV-87d3ca263c08` from `records_main_passages:ZJSHL-CH-007-P-0157`
- `柔痓` -> `AHV-cdac1a4b7e7b` from `risk_registry_ambiguous:ZJSHL-CH-007-P-0160`
- `痓病` -> `AHV-01cf7a0eba28` from `records_passages:ZJSHL-CH-007-P-0166`
- `结脉` -> `AHV-bbdfc9d9b74e` from `risk_registry_ambiguous:ZJSHL-CH-003-P-0029`
- `促脉` -> `AHV-472e3287583d` from `records_passages:ZJSHL-CH-003-P-0028`
- `弦脉` -> `AHV-54c535ab7161` from `records_passages:ZJSHL-CH-003-P-0037`
- `滑脉` -> `AHV-5d33fe1b97eb` from `records_passages:ZJSHL-CH-004-P-0203`
- `革脉` -> `AHV-6fb7ea26388a` from `risk_registry_ambiguous:ZJSHL-CH-003-P-0040`
- `行尸` -> `AHV-901247b4beaf` from `risk_registry_ambiguous:ZJSHL-CH-004-P-0200`
- `内虚` -> `AHV-b52564cf7480` from `risk_registry_ambiguous:ZJSHL-CH-004-P-0200`
- `血崩` -> `AHV-439df1ff9f25` from `risk_registry_ambiguous:ZJSHL-CH-004-P-0257`
- `霍乱` -> `AHV-72cae785c0ac` from `records_passages:ZJSHL-CH-016-P-0002`
- `劳复` -> `AHV-68ab3aae2083` from `records_passages:ZJSHL-CH-017-P-0049`
- `食复` -> `AHV-8df0a4ec9de9` from `records_passages:ZJSHL-CH-017-P-0049`

## B Support Only

- `高` -> `单字术语，离开寸口/卫气上下文后歧义过大，只能 support/review。`
- `章` -> `单字术语且依赖荣气盛上下文，不能进入 primary normalization。`
- `纲` -> `依赖高章两个前置术语，语义不自足，暂作 support-only。`
- `惵` -> `单字罕见术语，需保留上下文核对，不能 learner-safe 归一。`
- `卑` -> `单字现代义强，离开荣气弱上下文容易误解。`
- `损` -> `单字且依赖前后文，不作为 primary。`
- `缓` -> `单字别名冲突多，当前只保留为 support-only。`
- `迟` -> `单字泛义强，不能直接进入 runtime normalization。`

## C Rejected

- `动` -> 单字术语多义风险极高，直接归一会污染现代/普通语义查询。
- `两阳` -> 概念依赖火气、风邪、发黄/衄/小便难等长链上下文，当前不能作为 learner-safe primary。
- `清邪中上` -> 清邪/浊邪/洁/浑在同一长段复合说明中交叉出现，单独抽取会误导。
- `寒格` -> 该句与“更复吐下”“乾姜黄连黄芩人参汤”处置语境黏连，当前证据粒度不够干净。
