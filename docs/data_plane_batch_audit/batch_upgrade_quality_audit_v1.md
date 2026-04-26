# Batch Upgrade Quality Audit v1

本轮只审计上轮新增的 20 个 AHV safe primary definition/concept objects，不新增对象，不改 prompt、前端、API payload、answer_mode 或 commentarial 主逻辑。

## Scope

- audited_ahv_object_count: `20`
- focus_audited_count: `10`
- adjusted_object_count: `18`
- downgraded_object_count: `0`
- alias_adjusted_count: `5`

## Confirmed Keep Safe Primary

- `冬温`: “名曰冬温”命名句自足，canonical 与“冬温病”alias 边界清楚。
- `刚痓`: 命名句完整，canonical 与异体 alias“刚痉”均有明确边界，单字“痉”已 inactive。

## Refined But Kept Safe Primary

- `太阳病`: 补充 audit notes，保留 safe primary 与现有 alias。
- `伤寒`: 把 source 指向同 passage 的 safe main 行，并补充来源边界 notes。
- `温病`: 保留 canonical 温病 safe primary；停用“春温” learner alias 与 learner normalization。
- `暑病`: 把 source 收窄到 safe main 行；停用“暑病者” alias 与 learner normalization。
- `时行寒疫`: 把 source 指向 safe main 行；停用“寒疫” learner alias 与 learner normalization。
- `柔痓`: 保留 safe primary，补充 notes 限定为 medium confidence 抽句对象。
- `痓病`: 将 primary_evidence_text 改为干净句段，并补充 notes。
- `结脉`: 把 primary 改为 `ZJSHL-CH-003-P-0028` 的“脉来缓，时一止复来者，名曰结”，并指向 safe main source。
- `促脉`: 把 source 指向 safe main 行并补充 notes。
- `弦脉`: 把 source 指向 safe main 行并补充 notes。
- `滑脉`: 将 primary 改为“翕奄沉，名曰滑”，并指向 safe main source。
- `革脉`: 保留 safe primary，补 notes 限定为革脉对象，不启用单字革。
- `行尸`: 收窄 primary_evidence_text，并补充 source/risk notes。
- `内虚`: 收窄 primary_evidence_text，并补 notes 限定概念边界。
- `血崩`: 把 source 指向 safe main 行并补充 notes。
- `霍乱`: 将 primary 改为“呕吐而利，名曰霍乱”，并指向 safe main source。
- `劳复`: source 指向 safe main；停用“劳动病” alias 与 learner normalization。
- `食复`: source 指向 safe main；停用“强食复病” alias 与 learner normalization。

## Downgraded Objects

- none

## Guardrails

- raw `full:passages:*` / `full:ambiguous_passages:*` remains forbidden in runtime `primary_evidence`.
- review/support-only objects are not promoted by this audit.
- alias cleanup only deactivates over-broad learner surfaces; canonical AHV object ids are unchanged.
