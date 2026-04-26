#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.answers.assembler import DEFAULT_DB_PATH, resolve_project_path  # noqa: E402
from scripts.data_plane_batch_upgrade.run_ambiguous_high_value_evidence_upgrade_v1 import (  # noqa: E402
    CANDIDATES,
    compact_text,
    json_text,
)


RUN_ID = "batch_upgrade_quality_audit_v1"
AHV_LAYER = "ambiguous_high_value_batch_safe_primary"
DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_ahv_quality_audit_v1.db"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_batch_audit"
DEFAULT_DOC_DIR = "docs/data_plane_batch_audit"

REQUIRED_FOCUS_TERMS = {
    "太阳病",
    "伤寒",
    "温病",
    "柔痓",
    "痓病",
    "结脉",
    "促脉",
    "霍乱",
    "劳复",
    "食复",
}
ALLOWED_VERDICTS = {
    "keep_safe_primary",
    "keep_safe_primary_but_needs_notes",
    "adjust_alias",
    "adjust_primary_sentence",
    "downgrade_to_review_only",
    "downgrade_to_support_only",
    "defer_for_manual_review",
}
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}


@dataclass(frozen=True)
class AuditDecision:
    term: str
    quality_audit_verdict: str
    quality_reason: str
    fix_action: str
    should_change_now: bool
    risk_level_after: str
    audit_depth: str = "light"
    primary_evidence_text: str | None = None
    primary_evidence_type: str | None = None
    primary_support_passage_id: str | None = None
    primary_source_table: str | None = None
    primary_source_object: str | None = None
    primary_source_record_id: str | None = None
    primary_source_evidence_level: str | None = None
    source_confidence: str | None = None
    promotion_state: str | None = None
    is_safe_primary_candidate: int | None = None
    aliases_to_deactivate: tuple[str, ...] = ()
    notes_append: str = ""
    review_only_reason: str | None = None
    checks: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.quality_audit_verdict not in ALLOWED_VERDICTS:
            raise ValueError(f"bad verdict for {self.term}: {self.quality_audit_verdict}")
        if self.risk_level_after not in ALLOWED_RISK_LEVELS:
            raise ValueError(f"bad risk level for {self.term}: {self.risk_level_after}")


def checks(
    primary: str,
    identity: str,
    source: str,
    alias: str,
    runtime: str,
) -> dict[str, str]:
    return {
        "primary_sentence_quality": primary,
        "term_identity_stability": identity,
        "source_layer_support": source,
        "alias_normalization_risk": alias,
        "runtime_behavior": runtime,
    }


AUDIT_DECISIONS: tuple[AuditDecision, ...] = (
    AuditDecision(
        term="太阳病",
        quality_audit_verdict="keep_safe_primary_but_needs_notes",
        quality_reason="六经提纲句能独立成义，但原始来源为 B 级 main passage，应限定为提纲定义，不外扩到整章太阳病材料。",
        fix_action="补充 audit notes，保留 safe primary 与现有 alias。",
        should_change_now=True,
        risk_level_after="low",
        audit_depth="focus",
        notes_append="quality_audit_v1: 六经提纲对象仅覆盖“太阳之为病”定义句，不能代表太阳病篇全部证治材料。",
        checks=checks(
            "完整“X之为病”提纲句，可独立作为定义 primary。",
            "canonical term 明确，六经病名稳定。",
            "records_main_passages B 级可由句段化对象承接。",
            "alias 仅为原文短语“太阳之为病”，风险可控。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="伤寒",
        quality_audit_verdict="keep_safe_primary_but_needs_notes",
        quality_reason="命名句完整，实际同 passage 已有 safe main 行；当前 full source 标记偏保守且 notes 需要说明只取命名句。",
        fix_action="把 source 指向同 passage 的 safe main 行，并补充来源边界 notes。",
        should_change_now=True,
        risk_level_after="low",
        audit_depth="focus",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-008-P-0195",
        primary_source_evidence_level="A",
        notes_append="quality_audit_v1: 使用同 passage safe main source；primary 只取“名曰伤寒”命名句，不恢复 full passage。",
        checks=checks(
            "症状条件加“名曰伤寒”闭合，可独立解释。",
            "canonical term 稳定，alias“伤寒病”未越界。",
            "同 passage 有 safe main A 级来源，source 可以收窄到 main。",
            "alias 无短词或跨概念风险。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="温病",
        quality_audit_verdict="adjust_alias",
        quality_reason="primary 句“温者……”可作为抽句定义，但 alias“春温”更像邻近季节术语，作为 learner-safe normalization 过宽。",
        fix_action="保留 canonical 温病 safe primary；停用“春温” learner alias 与 learner normalization。",
        should_change_now=True,
        risk_level_after="medium",
        audit_depth="focus",
        aliases_to_deactivate=("春温",),
        notes_append="quality_audit_v1: “春温”降为 inactive risky alias；温病对象只接受 canonical 温病命中。",
        checks=checks(
            "“温者，冬时感寒，至春发者是也”可独立成义。",
            "温病本身稳定，但春温存在相邻概念风险。",
            "来自 ambiguous risk registry，只能承接抽句，不提升整段。",
            "已停用春温 learner-safe alias。",
            "温病 canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="暑病",
        quality_audit_verdict="adjust_alias",
        quality_reason="定义句干净，且同 passage 有 safe main source；alias“暑病者”是原文句法残片，不宜作为 learner-safe surface。",
        fix_action="把 source 收窄到 safe main 行；停用“暑病者” alias 与 learner normalization。",
        should_change_now=True,
        risk_level_after="low",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-006-P-0012",
        primary_source_evidence_level="A",
        aliases_to_deactivate=("暑病者",),
        notes_append="quality_audit_v1: “暑病者”只作原文句法，不再作为 active learner alias。",
        checks=checks(
            "“暑病者，热极重于温也”是完整定义句。",
            "canonical term 稳定。",
            "同 passage safe main A 级来源可支撑。",
            "已移除带“者”的句法 alias。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="冬温",
        quality_audit_verdict="keep_safe_primary",
        quality_reason="“名曰冬温”命名句自足，canonical 与“冬温病”alias 边界清楚。",
        fix_action="保留 safe primary；不做 registry 改动。",
        should_change_now=False,
        risk_level_after="low",
        checks=checks(
            "命名句完整。",
            "term identity 稳定。",
            "records_passages C 层经抽句对象承接，source_confidence medium 合理。",
            "alias“冬温病”未见过宽。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="时行寒疫",
        quality_audit_verdict="adjust_alias",
        quality_reason="主句可保留，但“寒疫”比“时行寒疫”更宽，作为 active learner alias 可能误归一。",
        fix_action="把 source 指向 safe main 行；停用“寒疫” learner alias 与 learner normalization。",
        should_change_now=True,
        risk_level_after="medium",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-006-P-0024",
        primary_source_evidence_level="A",
        aliases_to_deactivate=("寒疫",),
        notes_append="quality_audit_v1: “寒疫”降为 inactive risky alias，避免把更宽寒疫问法归入时行寒疫。",
        checks=checks(
            "“皆为时行寒疫也”可独立归类。",
            "canonical term 稳定，短 alias 更宽。",
            "同 passage safe main A 级来源可支撑。",
            "已停用寒疫 active normalization。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="刚痓",
        quality_audit_verdict="keep_safe_primary",
        quality_reason="命名句完整，canonical 与异体 alias“刚痉”均有明确边界，单字“痉”已 inactive。",
        fix_action="保留 safe primary；不做 registry 改动。",
        should_change_now=False,
        risk_level_after="low",
        checks=checks(
            "“名曰刚痓”句完整。",
            "与柔痓区分明确。",
            "records_main_passages B 级可由句段化对象承接。",
            "单字痉未启用。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="柔痓",
        quality_audit_verdict="keep_safe_primary_but_needs_notes",
        quality_reason="primary 是解释句而非典型定义句，但“表虚感湿，故曰柔痓”能独立解释柔痓来源；需明确来源为 ambiguous 抽句。",
        fix_action="保留 safe primary，补充 notes 限定为 medium confidence 抽句对象。",
        should_change_now=True,
        risk_level_after="medium",
        audit_depth="focus",
        notes_append="quality_audit_v1: primary 为解释性定义句，保留 medium confidence；只升格该句，不升格整段太阳/阳明辨析。",
        checks=checks(
            "解释句短且自足，但不是完整“X者”定义。",
            "柔痓/刚痓术语身份稳定。",
            "ambiguous source 只支持抽句级 safe primary。",
            "异体 alias 柔痉合理，单字痉 inactive。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="痓病",
        quality_audit_verdict="adjust_primary_sentence",
        quality_reason="当前 primary 带长症状串和“赵本注”校记，不够干净；核心可安全切为“背反张者，痓病也”。",
        fix_action="将 primary_evidence_text 改为干净句段，并补充 notes。",
        should_change_now=True,
        risk_level_after="medium",
        audit_depth="focus",
        primary_evidence_text="背反张者，痓病也",
        primary_evidence_type="exact_term_definition",
        notes_append="quality_audit_v1: 清理长症状串和校记，primary 仅保留“背反张者，痓病也”。",
        checks=checks(
            "原 primary 混入校记；修正后句段可独立成义。",
            "痓病与单字痓区分，单字 alias inactive。",
            "records_passages C 层只以抽句对象承接。",
            "痉病异体 alias 合理。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="结脉",
        quality_audit_verdict="adjust_primary_sentence",
        quality_reason="当前 primary 来自 ambiguous 解释句且没有直接命名“结”；同组 definition_passage 有更干净的 safe main 命名句。",
        fix_action="把 primary 改为 `ZJSHL-CH-003-P-0028` 的“脉来缓，时一止复来者，名曰结”，并指向 safe main source。",
        should_change_now=True,
        risk_level_after="low",
        audit_depth="focus",
        primary_evidence_text="脉来缓，时一止复来者，名曰结",
        primary_evidence_type="exact_term_definition",
        primary_support_passage_id="ZJSHL-CH-003-P-0028",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-003-P-0028",
        primary_source_evidence_level="A",
        notes_append="quality_audit_v1: primary 从 ambiguous 解释句改为 safe main 命名句；P-0029 仅作解释支持。",
        checks=checks(
            "修正后是直接命名句。",
            "结脉与结胸/脏结边界通过“脉”限定。",
            "safe main A 级来源优于原 ambiguous 解释句。",
            "单字结 inactive，未过度归一。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="促脉",
        quality_audit_verdict="keep_safe_primary_but_needs_notes",
        quality_reason="primary 命名句合格，同 passage 有 safe main 行；需要收窄 source，避免看起来依赖 full passage。",
        fix_action="把 source 指向 safe main 行并补充 notes。",
        should_change_now=True,
        risk_level_after="low",
        audit_depth="focus",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-003-P-0028",
        primary_source_evidence_level="A",
        notes_append="quality_audit_v1: 使用 safe main 命名句；单字促继续 inactive。",
        checks=checks(
            "“脉来数，时一止复来者，名曰促”完整。",
            "促脉 term 身份稳定。",
            "同 passage safe main A 级来源可支撑。",
            "单字促 inactive。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="弦脉",
        quality_audit_verdict="keep_safe_primary_but_needs_notes",
        quality_reason="命名句合格，同 passage 有 safe main 行；需收窄 source 并保留单字弦 inactive。",
        fix_action="把 source 指向 safe main 行并补充 notes。",
        should_change_now=True,
        risk_level_after="low",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-003-P-0037",
        primary_source_evidence_level="A",
        notes_append="quality_audit_v1: source 收窄到 safe main；单字弦不作为 learner-safe alias。",
        checks=checks(
            "命名句完整。",
            "脉象 term 稳定。",
            "同 passage safe main A 级来源可支撑。",
            "单字弦 inactive。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="滑脉",
        quality_audit_verdict="adjust_primary_sentence",
        quality_reason="当前 primary 含“问曰/何谓也”问答壳，句子不够干净；核心命名句可独立切出。",
        fix_action="将 primary 改为“翕奄沉，名曰滑”，并指向 safe main source。",
        should_change_now=True,
        risk_level_after="low",
        primary_evidence_text="翕奄沉，名曰滑",
        primary_evidence_type="exact_term_definition",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-004-P-0203",
        primary_source_evidence_level="A",
        notes_append="quality_audit_v1: 去除问答壳和校记，仅保留滑脉命名句；单字滑 inactive。",
        checks=checks(
            "修正后为干净命名句。",
            "滑脉 term 稳定。",
            "同 passage safe main A 级来源可支撑。",
            "单字滑 inactive。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="革脉",
        quality_audit_verdict="keep_safe_primary_but_needs_notes",
        quality_reason="命名句短且能解释革脉，但来源为 ambiguous，且句内只称“革”，必须靠 canonical term 与 notes 约束。",
        fix_action="保留 safe primary，补 notes 限定为革脉对象，不启用单字革。",
        should_change_now=True,
        risk_level_after="medium",
        notes_append="quality_audit_v1: “革”只在革脉对象内解释；单字革保持 inactive，不外扩到普通语义。",
        checks=checks(
            "命名句短，可独立但需 canonical title 辅助。",
            "革脉作为脉象 term 稳定。",
            "ambiguous source 只支持抽句级 medium safe primary。",
            "单字革 inactive。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="行尸",
        quality_audit_verdict="adjust_primary_sentence",
        quality_reason="当前 primary 包含“师曰”和后续预后描述，超出命名句；核心应切为“脉病患不病，名曰行尸”。",
        fix_action="收窄 primary_evidence_text，并补充 source/risk notes。",
        should_change_now=True,
        risk_level_after="medium",
        primary_evidence_text="脉病患不病，名曰行尸",
        primary_evidence_type="exact_term_definition",
        notes_append="quality_audit_v1: primary 只保留命名句，不把后续“卒眩仆”等预后描述作为定义 primary。",
        checks=checks(
            "修正后命名句完整。",
            "term identity 稳定，未设置额外 alias。",
            "ambiguous source 只支持抽句级 medium safe primary。",
            "无 learner alias 扩张。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="内虚",
        quality_audit_verdict="adjust_primary_sentence",
        quality_reason="当前 primary 带后续解释，且“内虚”有泛义风险；可保留但必须限定为本段“人病脉不病”命名义。",
        fix_action="收窄 primary_evidence_text，并补 notes 限定概念边界。",
        should_change_now=True,
        risk_level_after="medium",
        primary_evidence_text="人病脉不病，名曰内虚",
        primary_evidence_type="exact_term_definition",
        notes_append="quality_audit_v1: 内虚仅按本段“人病脉不病”命名义保留；不代表泛化虚证概念。",
        checks=checks(
            "修正后为命名句，去掉后续解释。",
            "canonical term 有泛义风险，靠 notes 限定。",
            "ambiguous source 只支持抽句级 medium safe primary。",
            "无额外 alias，normalization 仅 canonical。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="血崩",
        quality_audit_verdict="keep_safe_primary_but_needs_notes",
        quality_reason="命名句完整，同 passage 有 safe main 行；需要 source 收窄并说明不纳入三焦/荣卫长解释。",
        fix_action="把 source 指向 safe main 行并补充 notes。",
        should_change_now=True,
        risk_level_after="low",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-004-P-0257",
        primary_source_evidence_level="A",
        notes_append="quality_audit_v1: 使用 safe main 命名句；不把三焦/荣卫长解释整体升为 primary。",
        checks=checks(
            "“名曰血崩”命名句完整。",
            "term identity 稳定，崩血 alias 可接受。",
            "同 passage safe main A 级来源可支撑。",
            "alias 未过宽。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="霍乱",
        quality_audit_verdict="adjust_primary_sentence",
        quality_reason="当前 primary 带“答曰”问答前缀；核心定义句干净且同 passage 有 safe main 行。",
        fix_action="将 primary 改为“呕吐而利，名曰霍乱”，并指向 safe main source。",
        should_change_now=True,
        risk_level_after="low",
        audit_depth="focus",
        primary_evidence_text="呕吐而利，名曰霍乱",
        primary_evidence_type="exact_term_definition",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-016-P-0002",
        primary_source_evidence_level="A",
        notes_append="quality_audit_v1: 去除问答前缀和校记，只保留霍乱定义句。",
        checks=checks(
            "修正后定义句完整。",
            "病名稳定。",
            "同 passage safe main A 级来源可支撑。",
            "吐利霍乱 alias 未越界。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="劳复",
        quality_audit_verdict="adjust_alias",
        quality_reason="primary 句合格，但 alias“劳动病”是句内解释性短语，现代语义过宽，不应 learner-safe。",
        fix_action="source 指向 safe main；停用“劳动病” alias 与 learner normalization。",
        should_change_now=True,
        risk_level_after="low",
        audit_depth="focus",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-017-P-0049",
        primary_source_evidence_level="A",
        aliases_to_deactivate=("劳动病",),
        notes_append="quality_audit_v1: “劳动病”降为 inactive risky alias；劳复只通过 canonical term 命中。",
        checks=checks(
            "“病者，名曰劳复”完整。",
            "劳复 term identity 稳定。",
            "同 passage safe main A 级来源可支撑。",
            "已停用过宽解释性 alias。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
    AuditDecision(
        term="食复",
        quality_audit_verdict="adjust_alias",
        quality_reason="primary 句合格，但 alias“强食复病”是人为拼接的解释短语，作为 learner normalization 过激。",
        fix_action="source 指向 safe main；停用“强食复病” alias 与 learner normalization。",
        should_change_now=True,
        risk_level_after="low",
        audit_depth="focus",
        primary_source_table="records_main_passages",
        primary_source_object="main_passages",
        primary_source_record_id="safe:main_passages:ZJSHL-CH-017-P-0049",
        primary_source_evidence_level="A",
        aliases_to_deactivate=("强食复病",),
        notes_append="quality_audit_v1: “强食复病”降为 inactive risky alias；食复只通过 canonical term 命中。",
        checks=checks(
            "“病者，名曰食复”完整。",
            "食复 term identity 稳定。",
            "同 passage safe main A 级来源可支撑。",
            "已停用构造性 alias。",
            "canonical query 命中 AHV safe definition primary。",
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit AHV batch-upgraded safe primary objects v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--before-db", default=DEFAULT_BEFORE_DB)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-dir", default=DEFAULT_DOC_DIR)
    parser.add_argument("--refresh-before", action="store_true")
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_before_db(db_path: Path, before_db: Path, refresh: bool) -> None:
    before_db.parent.mkdir(parents=True, exist_ok=True)
    if refresh or not before_db.exists():
        shutil.copy2(db_path, before_db)


def load_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed if str(item)]


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def table_rows(conn: sqlite3.Connection, table_or_view: str, order_by: str) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(f"SELECT * FROM {table_or_view} ORDER BY {order_by}")]


def get_ahv_registry_rows(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM definition_term_registry
        WHERE promotion_source_layer = ?
        ORDER BY canonical_term, concept_id
        """,
        (AHV_LAYER,),
    ).fetchall()
    return {str(row["canonical_term"]): dict(row) for row in rows}


def source_text_for_current_primary(conn: sqlite3.Connection, row: dict[str, Any]) -> str:
    table = row["primary_source_table"]
    passage_id = row["primary_support_passage_id"]
    if table == "risk_registry_ambiguous":
        table = "risk_registry_ambiguous"
    try:
        source = conn.execute(f"SELECT text FROM {table} WHERE passage_id = ?", (passage_id,)).fetchone()
    except sqlite3.Error:
        source = None
    if source is None and table != "records_passages":
        source = conn.execute("SELECT text FROM records_passages WHERE passage_id = ?", (passage_id,)).fetchone()
    return str(source["text"]) if source else ""


def deactivated_alias_lists(row: dict[str, Any], aliases: tuple[str, ...]) -> tuple[list[str], list[str]]:
    remove = set(aliases)
    query_aliases = [alias for alias in load_json_list(row["query_aliases_json"]) if alias not in remove]
    learner_surfaces = [
        alias for alias in load_json_list(row["learner_surface_forms_json"]) if alias not in remove
    ]
    return unique(query_aliases), unique(learner_surfaces)


def rebuild_retrieval_text(row: dict[str, Any], primary_text: str, query_aliases: list[str], disabled: tuple[str, ...]) -> str:
    disabled_set = set(disabled)
    old_lines = [line.strip() for line in str(row.get("retrieval_text") or "").splitlines() if line.strip()]
    retained_old = [line for line in old_lines if line not in disabled_set and line != row.get("primary_evidence_text")]
    lines = unique([primary_text, row["canonical_term"], *query_aliases, *retained_old])
    return "\n".join(lines)


def update_definition_record(
    conn: sqlite3.Connection,
    row: dict[str, Any],
    decision: AuditDecision,
) -> dict[str, Any]:
    query_aliases, learner_surfaces = deactivated_alias_lists(row, decision.aliases_to_deactivate)
    primary_text = decision.primary_evidence_text or row["primary_evidence_text"]
    retrieval_text = rebuild_retrieval_text(row, primary_text, query_aliases, decision.aliases_to_deactivate)
    notes = str(row["notes"] or "")
    if decision.notes_append and decision.notes_append not in notes:
        notes = f"{notes} {decision.notes_append}".strip()

    updates = {
        "primary_evidence_text": primary_text,
        "primary_evidence_type": decision.primary_evidence_type or row["primary_evidence_type"],
        "primary_support_passage_id": decision.primary_support_passage_id or row["primary_support_passage_id"],
        "primary_source_table": decision.primary_source_table or row["primary_source_table"],
        "primary_source_object": decision.primary_source_object or row["primary_source_object"],
        "primary_source_record_id": decision.primary_source_record_id or row["primary_source_record_id"],
        "primary_source_evidence_level": decision.primary_source_evidence_level
        or row["primary_source_evidence_level"],
        "query_aliases_json": json_text(query_aliases),
        "learner_surface_forms_json": json_text(learner_surfaces),
        "retrieval_text": retrieval_text,
        "normalized_retrieval_text": compact_text(retrieval_text),
        "source_confidence": decision.source_confidence or row["source_confidence"],
        "promotion_state": decision.promotion_state or row["promotion_state"],
        "review_only_reason": decision.review_only_reason
        if decision.review_only_reason is not None
        else row["review_only_reason"],
        "notes": notes,
        "is_safe_primary_candidate": decision.is_safe_primary_candidate
        if decision.is_safe_primary_candidate is not None
        else row["is_safe_primary_candidate"],
    }
    conn.execute(
        """
        UPDATE definition_term_registry
        SET primary_evidence_text = :primary_evidence_text,
            primary_evidence_type = :primary_evidence_type,
            primary_support_passage_id = :primary_support_passage_id,
            primary_source_table = :primary_source_table,
            primary_source_object = :primary_source_object,
            primary_source_record_id = :primary_source_record_id,
            primary_source_evidence_level = :primary_source_evidence_level,
            query_aliases_json = :query_aliases_json,
            learner_surface_forms_json = :learner_surface_forms_json,
            retrieval_text = :retrieval_text,
            normalized_retrieval_text = :normalized_retrieval_text,
            source_confidence = :source_confidence,
            promotion_state = :promotion_state,
            review_only_reason = :review_only_reason,
            notes = :notes,
            is_safe_primary_candidate = :is_safe_primary_candidate
        WHERE concept_id = :concept_id
        """,
        {**updates, "concept_id": row["concept_id"]},
    )
    return updates


def deactivate_aliases(conn: sqlite3.Connection, row: dict[str, Any], decision: AuditDecision) -> None:
    for alias in decision.aliases_to_deactivate:
        conn.execute(
            """
            UPDATE term_alias_registry
            SET alias_type = 'learner_risky',
                confidence = 0.42,
                notes = 'quality_audit_v1 inactive alias; surface is too broad or constructed for learner-safe normalization',
                is_active = 0
            WHERE concept_id = ?
              AND alias = ?
            """,
            (row["concept_id"], alias),
        )
        conn.execute(
            """
            UPDATE learner_query_normalization_lexicon
            SET confidence = 0.42,
                notes = 'quality_audit_v1 deactivated broad or constructed learner surface',
                is_active = 0
            WHERE target_id = ?
              AND surface_form = ?
            """,
            (row["concept_id"], alias),
        )


def object_payload(
    conn: sqlite3.Connection,
    before_row: dict[str, Any],
    after_row: dict[str, Any],
    decision: AuditDecision,
) -> dict[str, Any]:
    alias_rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT alias, alias_type, confidence, is_active, notes
            FROM term_alias_registry
            WHERE concept_id = ?
            ORDER BY alias, alias_type
            """,
            (after_row["concept_id"],),
        )
    ]
    learner_rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT surface_form, match_mode, confidence, is_active, notes
            FROM learner_query_normalization_lexicon
            WHERE target_id = ?
            ORDER BY surface_form
            """,
            (after_row["concept_id"],),
        )
    ]
    before_aliases = load_json_list(before_row["query_aliases_json"])
    after_aliases = load_json_list(after_row["query_aliases_json"])
    before_surfaces = load_json_list(before_row["learner_surface_forms_json"])
    after_surfaces = load_json_list(after_row["learner_surface_forms_json"])
    changed_fields = [
        field
        for field in (
            "primary_support_passage_id",
            "primary_source_table",
            "primary_source_object",
            "primary_source_record_id",
            "primary_source_evidence_level",
            "primary_evidence_type",
            "primary_evidence_text",
            "source_confidence",
            "promotion_state",
            "is_safe_primary_candidate",
            "notes",
        )
        if before_row.get(field) != after_row.get(field)
    ]
    if before_aliases != after_aliases:
        changed_fields.append("query_aliases_json")
    if before_surfaces != after_surfaces:
        changed_fields.append("learner_surface_forms_json")
    return {
        "concept_id": after_row["concept_id"],
        "canonical_term": after_row["canonical_term"],
        "is_focus_term": after_row["canonical_term"] in REQUIRED_FOCUS_TERMS,
        "audit_depth": decision.audit_depth,
        "quality_audit_verdict": decision.quality_audit_verdict,
        "quality_reason": decision.quality_reason,
        "fix_action": decision.fix_action,
        "should_change_now": decision.should_change_now,
        "risk_level_after": decision.risk_level_after,
        "checks": decision.checks,
        "changed_fields": changed_fields,
        "before": {
            "primary_support_passage_id": before_row["primary_support_passage_id"],
            "primary_source_table": before_row["primary_source_table"],
            "primary_source_object": before_row["primary_source_object"],
            "primary_source_record_id": before_row["primary_source_record_id"],
            "primary_source_evidence_level": before_row["primary_source_evidence_level"],
            "primary_evidence_type": before_row["primary_evidence_type"],
            "primary_evidence_text": before_row["primary_evidence_text"],
            "source_confidence": before_row["source_confidence"],
            "promotion_state": before_row["promotion_state"],
            "query_aliases": before_aliases,
            "learner_surface_forms": before_surfaces,
            "is_safe_primary_candidate": before_row["is_safe_primary_candidate"],
        },
        "after": {
            "primary_support_passage_id": after_row["primary_support_passage_id"],
            "primary_source_table": after_row["primary_source_table"],
            "primary_source_object": after_row["primary_source_object"],
            "primary_source_record_id": after_row["primary_source_record_id"],
            "primary_source_evidence_level": after_row["primary_source_evidence_level"],
            "primary_evidence_type": after_row["primary_evidence_type"],
            "primary_evidence_text": after_row["primary_evidence_text"],
            "source_confidence": after_row["source_confidence"],
            "promotion_state": after_row["promotion_state"],
            "query_aliases": after_aliases,
            "learner_surface_forms": after_surfaces,
            "is_safe_primary_candidate": after_row["is_safe_primary_candidate"],
        },
        "source_text_excerpt": source_text_for_current_primary(conn, after_row),
        "alias_registry_rows": alias_rows,
        "learner_normalization_rows": learner_rows,
    }


def metrics_from_objects(objects: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "audited_ahv_object_count": len(objects),
        "keep_safe_primary_count": sum(
            1
            for item in objects
            if item["quality_audit_verdict"]
            in {"keep_safe_primary", "keep_safe_primary_but_needs_notes", "adjust_alias", "adjust_primary_sentence"}
            and item["after"]["is_safe_primary_candidate"] == 1
        ),
        "adjusted_object_count": sum(1 for item in objects if item["changed_fields"]),
        "downgraded_object_count": sum(
            1 for item in objects if item["quality_audit_verdict"].startswith("downgrade_to_")
        ),
        "alias_adjusted_count": sum(
            1
            for item in objects
            if "query_aliases_json" in item["changed_fields"]
            or "learner_surface_forms_json" in item["changed_fields"]
        ),
        "focus_audited_count": sum(1 for item in objects if item["is_focus_term"]),
    }


def write_ledger(output_dir: Path, objects: list[dict[str, Any]], before_db: Path, db_path: Path) -> dict[str, Any]:
    verdict_counts: dict[str, int] = {}
    for item in objects:
        verdict_counts[item["quality_audit_verdict"]] = verdict_counts.get(item["quality_audit_verdict"], 0) + 1
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "before_db": str(before_db),
        "after_db": str(db_path),
        "metrics": metrics_from_objects(objects),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "required_focus_terms": sorted(REQUIRED_FOCUS_TERMS),
        "audited_objects": objects,
        "lists": {
            "confirmed_keep_safe_primary": [
                item
                for item in objects
                if item["quality_audit_verdict"] == "keep_safe_primary"
            ],
            "refined_but_kept_safe_primary": [
                item
                for item in objects
                if item["quality_audit_verdict"]
                in {"keep_safe_primary_but_needs_notes", "adjust_alias", "adjust_primary_sentence"}
            ],
            "downgraded_objects": [
                item for item in objects if item["quality_audit_verdict"].startswith("downgrade_to_")
            ],
        },
    }
    write_json(output_dir / "ahv_quality_audit_ledger_v1.json", payload)

    lines = [
        "# AHV Quality Audit Ledger v1",
        "",
        f"- run_id: `{RUN_ID}`",
        f"- audited_ahv_object_count: `{payload['metrics']['audited_ahv_object_count']}`",
        f"- keep_safe_primary_count: `{payload['metrics']['keep_safe_primary_count']}`",
        f"- adjusted_object_count: `{payload['metrics']['adjusted_object_count']}`",
        f"- downgraded_object_count: `{payload['metrics']['downgraded_object_count']}`",
        f"- alias_adjusted_count: `{payload['metrics']['alias_adjusted_count']}`",
        "",
        "| term | verdict | changed_fields | risk_after | fix_action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in objects:
        lines.append(
            f"| {item['canonical_term']} | {item['quality_audit_verdict']} | "
            f"{', '.join(item['changed_fields']) or '-'} | {item['risk_level_after']} | {item['fix_action']} |"
        )
    write_md(output_dir / "ahv_quality_audit_ledger_v1.md", lines)
    return payload


def write_before_after(output_dir: Path, ledger: dict[str, Any]) -> None:
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "before_db": ledger["before_db"],
        "after_db": ledger["after_db"],
        "metrics": ledger["metrics"],
        "object_changes": [
            {
                "concept_id": item["concept_id"],
                "canonical_term": item["canonical_term"],
                "quality_audit_verdict": item["quality_audit_verdict"],
                "changed_fields": item["changed_fields"],
                "before": item["before"],
                "after": item["after"],
            }
            for item in ledger["audited_objects"]
        ],
    }
    write_json(output_dir / "ahv_quality_audit_before_after_v1.json", payload)


def write_snapshots(conn: sqlite3.Connection, output_dir: Path) -> None:
    write_json(
        output_dir / "definition_term_registry_ahv_audited_v1_snapshot.json",
        table_rows(conn, "definition_term_registry", "canonical_term, concept_id"),
    )
    write_json(
        output_dir / "term_alias_registry_ahv_audited_v1_snapshot.json",
        table_rows(conn, "term_alias_registry", "canonical_term, alias, alias_id"),
    )
    write_json(
        output_dir / "learner_query_normalization_ahv_audited_v1_snapshot.json",
        table_rows(conn, "learner_query_normalization_lexicon", "entry_type, surface_form, target_term"),
    )


def write_doc(doc_dir: Path, ledger: dict[str, Any]) -> None:
    lists = ledger["lists"]
    lines = [
        "# Batch Upgrade Quality Audit v1",
        "",
        "本轮只审计上轮新增的 20 个 AHV safe primary definition/concept objects，不新增对象，不改 prompt、前端、API payload、answer_mode 或 commentarial 主逻辑。",
        "",
        "## Scope",
        "",
        f"- audited_ahv_object_count: `{ledger['metrics']['audited_ahv_object_count']}`",
        f"- focus_audited_count: `{ledger['metrics']['focus_audited_count']}`",
        f"- adjusted_object_count: `{ledger['metrics']['adjusted_object_count']}`",
        f"- downgraded_object_count: `{ledger['metrics']['downgraded_object_count']}`",
        f"- alias_adjusted_count: `{ledger['metrics']['alias_adjusted_count']}`",
        "",
        "## Confirmed Keep Safe Primary",
        "",
    ]
    if lists["confirmed_keep_safe_primary"]:
        for item in lists["confirmed_keep_safe_primary"]:
            lines.append(f"- `{item['canonical_term']}`: {item['quality_reason']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Refined But Kept Safe Primary", ""])
    if lists["refined_but_kept_safe_primary"]:
        for item in lists["refined_but_kept_safe_primary"]:
            lines.append(f"- `{item['canonical_term']}`: {item['fix_action']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Downgraded Objects", ""])
    if lists["downgraded_objects"]:
        for item in lists["downgraded_objects"]:
            lines.append(f"- `{item['canonical_term']}`: {item['quality_reason']}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- raw `full:passages:*` / `full:ambiguous_passages:*` remains forbidden in runtime `primary_evidence`.",
            "- review/support-only objects are not promoted by this audit.",
            "- alias cleanup only deactivates over-broad learner surfaces; canonical AHV object ids are unchanged.",
        ]
    )
    write_md(doc_dir / "batch_upgrade_quality_audit_v1.md", lines)


def validate_decisions(rows_by_term: dict[str, dict[str, Any]]) -> None:
    decision_terms = {decision.term for decision in AUDIT_DECISIONS}
    row_terms = set(rows_by_term)
    if len(row_terms) != 20:
        raise RuntimeError(f"expected 20 AHV safe primary rows, found {len(row_terms)}")
    if decision_terms != row_terms:
        missing = sorted(row_terms - decision_terms)
        extra = sorted(decision_terms - row_terms)
        raise RuntimeError(f"audit decision terms mismatch; missing={missing}, extra={extra}")
    focus_missing = sorted(REQUIRED_FOCUS_TERMS - decision_terms)
    if focus_missing:
        raise RuntimeError(f"missing required focus terms: {focus_missing}")


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    before_db = resolve_project_path(args.before_db)
    output_dir = resolve_project_path(args.output_dir)
    doc_dir = resolve_project_path(args.doc_dir)
    ensure_before_db(db_path, before_db, args.refresh_before)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        before_rows = get_ahv_registry_rows(conn)
        validate_decisions(before_rows)
        with conn:
            for decision in AUDIT_DECISIONS:
                row = before_rows[decision.term]
                if decision.should_change_now:
                    update_definition_record(conn, row, decision)
                    deactivate_aliases(conn, row, decision)
        after_rows = get_ahv_registry_rows(conn)
        objects = [
            object_payload(conn, before_rows[decision.term], after_rows[decision.term], decision)
            for decision in AUDIT_DECISIONS
        ]
        ledger = write_ledger(output_dir, objects, before_db, db_path)
        write_before_after(output_dir, ledger)
        write_snapshots(conn, output_dir)
        write_doc(doc_dir, ledger)
    finally:
        conn.close()

    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "db_path": str(db_path),
                "before_db": str(before_db),
                "metrics": ledger["metrics"],
                "output_dir": str(output_dir),
                "doc_dir": str(doc_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
