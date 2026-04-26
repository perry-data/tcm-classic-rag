# AHV2 Batch Upgrade Ledger v1

- run_id: `ambiguous_high_value_evidence_upgrade_v2`
- candidate_count: `32`
- category_A_count: `20`
- category_B_count: `8`
- category_C_count: `4`
- promoted_safe_primary_count: `20`
- support_only_registered_count: `8`
- rejected_count: `4`
- new_active_contains_learner_surface_count: `0`

## A Promoted

- `荣气微` -> `AHV2-850318ee8950` from `records_main_passages:ZJSHL-CH-003-P-0010`
- `卫气衰` -> `AHV2-81a12b6da994` from `records_main_passages:ZJSHL-CH-003-P-0012`
- `阳气微` -> `AHV2-767dfa46f2b1` from `records_main_passages:ZJSHL-CH-003-P-0021`
- `亡血` -> `AHV2-7882ca0aa96a` from `records_main_passages:ZJSHL-CH-003-P-0026`
- `平脉` -> `AHV2-310eca701a93` from `risk_registry_ambiguous:ZJSHL-CH-003-P-0029`
- `数脉` -> `AHV2-f9e89349db80` from `risk_registry_ambiguous:ZJSHL-CH-003-P-0029`
- `毛脉` -> `AHV2-5f24c7010fec` from `records_passages:ZJSHL-CH-004-P-0192`
- `纯弦脉` -> `AHV2-92d765f487d4` from `records_passages:ZJSHL-CH-004-P-0185`
- `残贼` -> `AHV2-dac342243a2d` from `records_main_passages:ZJSHL-CH-004-P-0178`
- `八邪` -> `AHV2-c29e7aff2765` from `records_passages:ZJSHL-CH-004-P-0179`
- `湿家` -> `AHV2-1e3cd430a062` from `records_passages:ZJSHL-CH-007-P-0172`
- `风湿` -> `AHV2-f5bd47a65fa0` from `risk_registry_ambiguous:ZJSHL-CH-007-P-0182`
- `水逆` -> `AHV2-1da410fb57b4` from `risk_registry_ambiguous:ZJSHL-CH-009-P-0148`
- `半表半里证` -> `AHV2-aa28a21f86c8` from `risk_registry_ambiguous:ZJSHL-CH-009-P-0210`
- `过经` -> `AHV2-dbeb47457236` from `risk_registry_ambiguous:ZJSHL-CH-009-P-0257`
- `结胸` -> `AHV2-0f3d2d43c342` from `risk_registry_ambiguous:ZJSHL-CH-010-P-0003`
- `阳明病` -> `AHV2-5a00f10e6dee` from `records_main_passages:ZJSHL-CH-011-P-0008`
- `太阴病` -> `AHV2-8709f78f1237` from `records_passages:ZJSHL-CH-013-P-0002`
- `少阴病` -> `AHV2-9f641a6ecc7d` from `records_main_passages:ZJSHL-CH-014-P-0021`
- `厥阴病` -> `AHV2-7b2df4caf446` from `records_passages:ZJSHL-CH-015-P-0193`

## B Support/Review Only

- `三菽重` -> 依赖三菽、六菽、九菽、十二菽、至骨的完整枚举体系，暂作 support/review。
- `六菽重` -> 依赖完整脉重枚举体系，不能作为独立 safe primary。
- `九菽重` -> 依赖完整脉重枚举体系，暂不进入 primary。
- `十二菽重` -> 依赖完整脉重枚举体系，暂不进入 primary。
- `纵` -> 单字术语，离开五行相乘语境后误触发风险高。
- `横` -> 单字术语，必须依赖五行相乘上下文。
- `逆` -> 单字术语，普通语义和病机语义重叠，不能 learner-safe。
- `顺` -> 单字术语，不能脱离五行相乘语境独立 primary。

## C Rejected

- `反` -> 单字普通义强，且必须与“复”及来去脉势成对解释，不能进入 runtime normalization。
- `复` -> 单字普通义强，不能脱离前后脉势和“反”对照单独升格。
- `肝乘脾` -> 术语锚点不稳定，病机说明、命名和刺法处置混在同句，当前不升格。
- `火劫发汗` -> 证据句含校记和治疗误法上下文，不能切成干净 definition primary。
