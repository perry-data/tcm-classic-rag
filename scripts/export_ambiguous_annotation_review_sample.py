#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import zipfile
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FULL_DATASET_DIR = PROJECT_ROOT / "data" / "processed" / "zjshl_dataset_v2"
SAFE_ZIP_PATH = PROJECT_ROOT / "dist" / "zjshl_dataset_v2_mvp_safe.zip"
MANIFEST_OUT = PROJECT_ROOT / "artifacts" / "review" / "ambiguous_annotation_sample_manifest_v1.csv"
REVIEW_SHEET_OUT = PROJECT_ROOT / "artifacts" / "review" / "ambiguous_annotation_manual_review_sheet_v1.csv"

CONFIRMED_MISLINKS = {
    "LINK-00033": "ZJSHL-CH-003-P-0074",
    "LINK-00034": "ZJSHL-CH-003-P-0078",
    "LINK-00036": "ZJSHL-CH-003-P-0082",
    "LINK-00037": "ZJSHL-CH-003-P-0084",
    "LINK-00038": "ZJSHL-CH-003-P-0086",
    "LINK-00039": "ZJSHL-CH-003-P-0088",
}

REVIEW_TEMPLATES: dict[str, dict[str, str]] = {
    "main_l1_primary_candidate": {
        "reviewer_decision": "可作为后续受控回放中的 primary 候选",
        "decision_level": "L1",
        "can_be_primary_evidence": "Y",
        "can_enter_recall_layer": "Y",
        "can_enter_vector_index": "Y",
        "can_only_be_review_material": "N",
        "should_remain_excluded": "N",
    },
    "main_l2_recall_vector": {
        "reviewer_decision": "不宜直抬主依据，但可回放到 recall 与受控 vector",
        "decision_level": "L2",
        "can_be_primary_evidence": "N",
        "can_enter_recall_layer": "Y",
        "can_enter_vector_index": "Y",
        "can_only_be_review_material": "N",
        "should_remain_excluded": "N",
    },
    "main_l2_recall_only": {
        "reviewer_decision": "可回放到 recall 层，但暂不建议进入 vector",
        "decision_level": "L2",
        "can_be_primary_evidence": "N",
        "can_enter_recall_layer": "Y",
        "can_enter_vector_index": "N",
        "can_only_be_review_material": "N",
        "should_remain_excluded": "N",
    },
    "main_l3_review": {
        "reviewer_decision": "仅建议作为 review / risk material",
        "decision_level": "L3",
        "can_be_primary_evidence": "N",
        "can_enter_recall_layer": "N",
        "can_enter_vector_index": "N",
        "can_only_be_review_material": "Y",
        "should_remain_excluded": "N",
    },
    "main_l4_exclude": {
        "reviewer_decision": "继续排除",
        "decision_level": "L4",
        "can_be_primary_evidence": "N",
        "can_enter_recall_layer": "N",
        "can_enter_vector_index": "N",
        "can_only_be_review_material": "N",
        "should_remain_excluded": "Y",
    },
    "annotation_l2_recall": {
        "reviewer_decision": "仅按注解原文受控回放到 recall / auxiliary，不启用自动挂接",
        "decision_level": "L2",
        "can_be_primary_evidence": "N",
        "can_enter_recall_layer": "Y",
        "can_enter_vector_index": "N",
        "can_only_be_review_material": "N",
        "should_remain_excluded": "N",
    },
    "annotation_l3_review": {
        "reviewer_decision": "只保留为 review 材料，不建议进入常规召回",
        "decision_level": "L3",
        "can_be_primary_evidence": "N",
        "can_enter_recall_layer": "N",
        "can_enter_vector_index": "N",
        "can_only_be_review_material": "Y",
        "should_remain_excluded": "N",
    },
    "annotation_l4_exclude": {
        "reviewer_decision": "继续排除；不建议作为自动挂接或常规辅助材料",
        "decision_level": "L4",
        "can_be_primary_evidence": "N",
        "can_enter_recall_layer": "N",
        "can_enter_vector_index": "N",
        "can_only_be_review_material": "N",
        "should_remain_excluded": "Y",
    },
    "control_main_l1": {
        "reviewer_decision": "safe 基线中的稳定对照，可继续作为 primary",
        "decision_level": "L1",
        "can_be_primary_evidence": "Y",
        "can_enter_recall_layer": "Y",
        "can_enter_vector_index": "Y",
        "can_only_be_review_material": "N",
        "should_remain_excluded": "N",
    },
}

SAMPLES: list[dict[str, str]] = [
    # A. 高风险 / 被移除 / 被降级的 main_passages
    {
        "sample_id": "A01",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-003-P-0049",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "removed_ambiguous_query_gloss",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "ZJSHL-CH-003-P-0048",
        "manual_comment": "语义完整，能补“发汗后不汗解”的解释，但仍属解释性材料，不宜直抬主依据。",
    },
    {
        "sample_id": "A02",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-003-P-0050",
        "related_query_topic": "",
        "suggested_review_bucket": "removed_ambiguous_self_contained_qa",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "ZJSHL-CH-003-P-0051",
        "manual_comment": "问答体完整，具有独立检索价值，但 ambiguous 命中后更适合先做 recall/复核。",
    },
    {
        "sample_id": "A03",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-006-P-0120",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "removed_ambiguous_query_definition",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "ZJSHL-CH-006-P-0119",
        "manual_comment": "对“发汗药”问题非常有用，但带有解释性归纳和外引语气，宜放在 recall / vector，而非 primary。",
    },
    {
        "sample_id": "A04",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-006-P-0126",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "removed_ambiguous_procedural_context",
        "review_profile": "main_l3_review",
        "related_passage_id": "ZJSHL-CH-006-P-0127",
        "manual_comment": "讲的是服法节奏，脱离上下文容易被错读为通用规则，更适合 review。",
    },
    {
        "sample_id": "A05",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-006-P-0127",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "removed_ambiguous_query_usage_note",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "ZJSHL-CH-006-P-0126",
        "manual_comment": "对“发汗药怎么用”有直接解释力，可回放到 recall / vector，但不宜包装成 canonical 定义。",
    },
    {
        "sample_id": "A06",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-007-P-0165",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "removed_ambiguous_risk_caution",
        "review_profile": "main_l3_review",
        "related_passage_id": "ZJSHL-CH-007-P-0164",
        "manual_comment": "内容有价值，但主要是“发汗太多则亡阳”的风险提示，适合作为 review 旁证。",
    },
    {
        "sample_id": "A07",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0201",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "removed_ambiguous_definition_like",
        "review_profile": "main_l1_primary_candidate",
        "related_passage_id": "",
        "manual_comment": "句子短而完整，是高信息密度的定义型条文；若人工核定无解析歧义，可列入 primary 候选池。",
    },
    {
        "sample_id": "A08",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0227",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "removed_ambiguous_explanatory_followup",
        "review_profile": "main_l2_recall_only",
        "related_passage_id": "ZJSHL-CH-008-P-0226",
        "manual_comment": "是对坏病/逆治的解释性跟条，可回放到 recall，但 dense 化会抬高上下文依赖风险。",
    },
    {
        "sample_id": "A09",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-003-P-0103",
        "related_query_topic": "",
        "suggested_review_bucket": "removed_ambiguous_long_inferential",
        "review_profile": "main_l3_review",
        "related_passage_id": "",
        "manual_comment": "长条虽完整，但推演链较长、外引较多，容易被误当成稳定定义，先放 review 更稳妥。",
    },
    {
        "sample_id": "A10",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-017-P-0064",
        "related_query_topic": "竹叶石膏汤方作用",
        "suggested_review_bucket": "removed_ambiguous_formula_effect_gloss",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "ZJSHL-CH-017-P-0063",
        "manual_comment": "直接解释竹叶石膏汤所对治的病机，适合受控回放到 recall / vector，但不宜替代主条。",
    },
    {
        "sample_id": "A11",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-003-P-0010",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_fragment",
        "review_profile": "main_l4_exclude",
        "related_passage_id": "",
        "manual_comment": "语句过短、上下文依赖强，单独检索时极易误召回。",
    },
    {
        "sample_id": "A12",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-003-P-0012",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_observation",
        "review_profile": "main_l3_review",
        "related_passage_id": "",
        "manual_comment": "观察性短句本身成立，但脱离前后文不宜参与常规召回。",
    },
    {
        "sample_id": "A13",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-004-P-0161",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_shorthand",
        "review_profile": "main_l3_review",
        "related_passage_id": "",
        "manual_comment": "诊断速记型表达，适合 review，对开放召回帮助有限。",
    },
    {
        "sample_id": "A14",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-004-P-0239",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_complete_but_dense",
        "review_profile": "main_l3_review",
        "related_passage_id": "",
        "manual_comment": "句子完整但术语密度高，仍依赖语段背景来判定含义，先作 review 更合适。",
    },
    {
        "sample_id": "A15",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-006-P-0102",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_general_statement",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "",
        "manual_comment": "虽然很短，但语义自足，可作为“伤寒多从风寒得之”的高精简 recall 候选。",
    },
    {
        "sample_id": "A16",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-006-P-0109",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_rule_statement",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "",
        "manual_comment": "规则型短条可用于召回和向量索引补充，但不建议单独扛主依据。",
    },
    {
        "sample_id": "A17",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-006-P-0143",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_high_stakes",
        "review_profile": "main_l3_review",
        "related_passage_id": "",
        "manual_comment": "高风险断语过短，单句上线容易造成脱离条件的绝对化表达。",
    },
    {
        "sample_id": "A18",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-014-P-0021",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_definition_like",
        "review_profile": "main_l1_primary_candidate",
        "related_passage_id": "",
        "manual_comment": "典型“X之为病”定义句，虽短但语义完整，是 short demotion 中最值得复核回升的一类。",
    },
    {
        "sample_id": "A19",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-015-P-0251",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_formula_indication",
        "review_profile": "main_l1_primary_candidate",
        "related_passage_id": "",
        "manual_comment": "方证直接对应，短而完整，后续可讨论回升为 primary 候选。",
    },
    {
        "sample_id": "A20",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-010-P-0168",
        "related_query_topic": "",
        "suggested_review_bucket": "downgraded_short_formula_indication",
        "review_profile": "main_l1_primary_candidate",
        "related_passage_id": "",
        "manual_comment": "标准方证主治句式，safe 仅因字数降级，存在明显过保守迹象。",
    },
    # B. annotation 或 annotation 挂接不稳相关样本
    {
        "sample_id": "B01",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0073",
        "link_id": "LINK-00033",
        "expected_target_id": "ZJSHL-CH-003-P-0074",
        "related_query_topic": "",
        "suggested_review_bucket": "confirmed_mislink_longer_explanatory",
        "review_profile": "annotation_l3_review",
        "manual_comment": "注解内容本身有解释力，但当前错挂明确；若不先改锚点，不应进入常规使用链路。",
    },
    {
        "sample_id": "B02",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0077",
        "link_id": "LINK-00034",
        "expected_target_id": "ZJSHL-CH-003-P-0078",
        "related_query_topic": "",
        "suggested_review_bucket": "confirmed_mislink_summary",
        "review_profile": "annotation_l4_exclude",
        "manual_comment": "摘要语高度依赖正确挂点，当前形态不宜放回任何线上层。",
    },
    {
        "sample_id": "B03",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0081",
        "link_id": "LINK-00036",
        "expected_target_id": "ZJSHL-CH-003-P-0082",
        "related_query_topic": "",
        "suggested_review_bucket": "confirmed_mislink_summary",
        "review_profile": "annotation_l4_exclude",
        "manual_comment": "“肝绝也”类摘要语缺乏自足语境，错挂时几乎必然造成串条。",
    },
    {
        "sample_id": "B04",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0083",
        "link_id": "LINK-00037",
        "expected_target_id": "ZJSHL-CH-003-P-0084",
        "related_query_topic": "",
        "suggested_review_bucket": "confirmed_mislink_summary",
        "review_profile": "annotation_l4_exclude",
        "manual_comment": "摘要型注解不自足，且确认存在相邻偏移，不建议恢复。",
    },
    {
        "sample_id": "B05",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0085",
        "link_id": "LINK-00038",
        "expected_target_id": "ZJSHL-CH-003-P-0086",
        "related_query_topic": "",
        "suggested_review_bucket": "confirmed_mislink_summary",
        "review_profile": "annotation_l4_exclude",
        "manual_comment": "同段连续偏移中的摘要语，当前形态风险高于收益。",
    },
    {
        "sample_id": "B06",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0087",
        "link_id": "LINK-00039",
        "expected_target_id": "ZJSHL-CH-003-P-0088",
        "related_query_topic": "",
        "suggested_review_bucket": "confirmed_mislink_chain_summary",
        "review_profile": "annotation_l3_review",
        "manual_comment": "比纯摘要略完整，但仍明显依赖正确挂条；先作为 review 材料保留。",
    },
    {
        "sample_id": "B07",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0053",
        "link_id": "LINK-00024",
        "related_query_topic": "",
        "suggested_review_bucket": "heuristic_suspect_long_explanation",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "长解释条有内容价值，可考虑按“未自动挂接的注解原文”回放到 recall。",
    },
    {
        "sample_id": "B08",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0079",
        "link_id": "LINK-00035",
        "related_query_topic": "",
        "suggested_review_bucket": "heuristic_suspect_summary",
        "review_profile": "annotation_l4_exclude",
        "manual_comment": "一句式病机摘要，既疑似偏移又不自足，继续排除更稳妥。",
    },
    {
        "sample_id": "B09",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0089",
        "link_id": "LINK-00040",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "heuristic_suspect_long_explanation",
        "review_profile": "annotation_l3_review",
        "manual_comment": "内容长但推演链复杂，且疑似挂到前条，建议仅保留为 review。",
    },
    {
        "sample_id": "B10",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0091",
        "link_id": "LINK-00041",
        "related_query_topic": "",
        "suggested_review_bucket": "heuristic_suspect_followup",
        "review_profile": "annotation_l3_review",
        "manual_comment": "更像上一条解释链的延续，常规召回价值不高。",
    },
    {
        "sample_id": "B11",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-003-P-0098",
        "link_id": "LINK-00044",
        "related_query_topic": "",
        "suggested_review_bucket": "heuristic_suspect_long_explanation",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "解释力较强，可作为 raw annotation 受控回放，但不恢复自动挂接。",
    },
    {
        "sample_id": "B12",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-004-P-0133",
        "link_id": "LINK-00056",
        "related_query_topic": "",
        "suggested_review_bucket": "heuristic_suspect_long_explanation",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "长注解释义完整，值得进入 recall 候选；挂接仍需人工复核。",
    },
    {
        "sample_id": "B13",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-004-P-0148",
        "link_id": "LINK-00063",
        "related_query_topic": "",
        "suggested_review_bucket": "heuristic_suspect_low_confidence_short",
        "review_profile": "annotation_l3_review",
        "manual_comment": "本身已经 low confidence，且句长短，不建议常规放回。",
    },
    {
        "sample_id": "B14",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-004-P-0240",
        "link_id": "LINK-00108",
        "related_query_topic": "",
        "suggested_review_bucket": "heuristic_suspect_short_diagnostic",
        "review_profile": "annotation_l3_review",
        "manual_comment": "短诊断句可作人工核对线索，但不适合作为线上辅助证据。",
    },
    {
        "sample_id": "B15",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-008-P-0192",
        "link_id": "LINK-00205",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "stable_annotation_control_definition",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "这是“文本本身可用、但 link 仍不宜自动放开”的正面对照样本。",
    },
    {
        "sample_id": "B16",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-008-P-0194",
        "link_id": "LINK-00206",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "stable_annotation_control_definition",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "文本解释力稳定，可按注解原文参与 recall / secondary，不恢复自动证据链。",
    },
    {
        "sample_id": "B17",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-008-P-0196",
        "link_id": "LINK-00207",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "stable_annotation_control_definition",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "与 target 贴合度高，是“局部可放开 raw annotation”的代表样本。",
    },
    {
        "sample_id": "B18",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-008-P-0216",
        "link_id": "LINK-00213",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "stable_annotation_control_branch",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "条文解释非常强，但仍建议保持“注解原文、未自动挂接”的展示口径。",
    },
    {
        "sample_id": "B19",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-008-P-0221",
        "link_id": "LINK-00215",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "stable_annotation_control_branch",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "可作为 branch 说明的辅助材料，但不建议越级成主依据。",
    },
    {
        "sample_id": "B20",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-008-P-0202",
        "link_id": "LINK-00208",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "stable_annotation_control_definition",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "温病界分解释较稳定，是“局部可放开 annotation 原文”的另一类样本。",
    },
    # C. 与已知问题查询相关的候选样本
    {
        "sample_id": "C01",
        "source_type": "annotation",
        "original_id": "ZJSHL-CH-006-P-0118",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "query_fahan_annotation",
        "review_profile": "annotation_l2_recall",
        "manual_comment": "对“神丹者，发汗之药也”类问法很有帮助，但仍应按 raw annotation 使用。",
    },
    {
        "sample_id": "C02",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-003-P-0090",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "query_fahan_kept_context",
        "review_profile": "main_l2_recall_only",
        "related_passage_id": "",
        "manual_comment": "更适合回答“何时当发汗”，对“什么是发汗药”只能作语境补充。",
    },
    {
        "sample_id": "C03",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0069",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "query_fahan_short_formula_rule",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "",
        "manual_comment": "直接命中“可发汗，宜麻黄汤”，适合补召回和 short-form rule 检索。",
    },
    {
        "sample_id": "C04",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0071",
        "related_query_topic": "发汗药",
        "suggested_review_bucket": "query_fahan_short_formula_rule",
        "review_profile": "main_l2_recall_vector",
        "related_passage_id": "",
        "manual_comment": "与 C03 同类，是“发汗条件 + 方名”短句的代表样本。",
    },
    {
        "sample_id": "C05",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0191",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "query_taiyang_definition",
        "review_profile": "main_l1_primary_candidate",
        "related_passage_id": "",
        "manual_comment": "就是“太阳病是什么”的高价值定义条，short demotion 有明显过保守迹象。",
    },
    {
        "sample_id": "C06",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0193",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "query_taiyang_branch",
        "review_profile": "main_l1_primary_candidate",
        "related_passage_id": "",
        "manual_comment": "不是总定义，但可作为太阳病典型分支的强证据条。",
    },
    {
        "sample_id": "C07",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0207",
        "related_query_topic": "太阳病",
        "suggested_review_bucket": "query_taiyang_course",
        "review_profile": "main_l2_recall_only",
        "related_passage_id": "",
        "manual_comment": "病程/再经语境可补足总括问，但不宜替代定义条。",
    },
    {
        "sample_id": "C08",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-017-P-0063",
        "related_query_topic": "竹叶石膏汤方作用",
        "suggested_review_bucket": "query_formula_effect_primary",
        "review_profile": "main_l1_primary_candidate",
        "related_passage_id": "",
        "manual_comment": "方证主条完整，足以作为该问题的 primary。",
    },
    {
        "sample_id": "C09",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-017-P-0065",
        "related_query_topic": "竹叶石膏汤方作用",
        "suggested_review_bucket": "query_formula_heading",
        "review_profile": "main_l2_recall_only",
        "related_passage_id": "",
        "manual_comment": "方题与药味可增强检索聚焦，但回答“作用”时不宜抬得过高。",
    },
    {
        "sample_id": "C10",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-017-P-0066",
        "related_query_topic": "竹叶石膏汤方作用",
        "suggested_review_bucket": "query_formula_ingredients",
        "review_profile": "main_l3_review",
        "related_passage_id": "",
        "manual_comment": "配伍信息可辅助人工核对，但对“作用”问本身帮助有限，更适合 review。",
    },
    # D. 对照样本（当前 safe 中保留且相对稳定的样本）
    {
        "sample_id": "D01",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0195",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "safe 基线中的稳定正文条，可持续作为 primary 对照。",
    },
    {
        "sample_id": "D02",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0215",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "分支条文完整、检索友好，是 safe 保留策略的正样本。",
    },
    {
        "sample_id": "D03",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0217",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "方题本身结构清晰，是 safe 主条层可用性的代表样本。",
    },
    {
        "sample_id": "D04",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-008-P-0219",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "方后法完整，展示 safe 中保留下来的长条是稳定可用的。",
    },
    {
        "sample_id": "D05",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0002",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "主治句完整，是 safe 正文层的典型稳定样本。",
    },
    {
        "sample_id": "D06",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0004",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "稳定的方题条，有助于校准“方剂相关内容并未被过度压缩”。",
    },
    {
        "sample_id": "D07",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0006",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "长配方法保留稳定，是 safe 主条与 chunk 互相回指的好对照。",
    },
    {
        "sample_id": "D08",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0022",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "经典方题条留在 safe 中且语义自足，可作为稳定基线。",
    },
    {
        "sample_id": "D09",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0025",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "长方法条保留稳定，说明 safe 并非对所有长条一刀切保守。",
    },
    {
        "sample_id": "D10",
        "source_type": "main_passage",
        "original_id": "ZJSHL-CH-009-P-0038",
        "related_query_topic": "",
        "suggested_review_bucket": "stable_safe_main_control",
        "review_profile": "control_main_l1",
        "related_passage_id": "",
        "manual_comment": "复合条件主条仍能稳定留在 safe 中，适合作为对照样本。",
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_safe_payloads(zip_path: Path) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in ("main_passages.json", "annotations.json"):
            payloads[name] = json.loads(zf.read(name).decode("utf-8"))
    return payloads


def truncate_text(text: str, limit: int = 84) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def detect_main_safe_status(
    original_id: str,
    full_main_index: dict[str, dict[str, Any]],
    safe_main_index: dict[str, dict[str, Any]],
    ambiguous_ids: set[str],
) -> str:
    full_row = full_main_index[original_id]
    safe_row = safe_main_index.get(original_id)
    if safe_row is None:
        return "removed" if original_id in ambiguous_ids else "removed"
    if full_row.get("retrieval_primary") and not safe_row.get("retrieval_primary"):
        return "downgraded"
    return "kept"


def build_suspicious_link_index(
    main_rows: list[dict[str, Any]],
    annotation_rows: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    main_index = {row["passage_id"]: row for row in main_rows}
    annotation_index = {row["passage_id"]: row for row in annotation_rows}
    main_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in main_rows:
        main_by_file[row["source_file"]].append(row)
    for rows in main_by_file.values():
        rows.sort(key=lambda row: row["source_item_no"])

    suspicious: dict[str, dict[str, Any]] = {}
    for link in links:
        annotation_row = annotation_index[link["from_passage_id"]]
        target_row = main_index[link["to_passage_id"]]
        next_main = next(
            (row for row in main_by_file[annotation_row["source_file"]] if row["source_item_no"] > annotation_row["source_item_no"]),
            None,
        )
        if not next_main or next_main["passage_id"] == target_row["passage_id"]:
            continue
        current_ratio = SequenceMatcher(None, annotation_row["text"], target_row["text"]).ratio()
        next_ratio = SequenceMatcher(None, annotation_row["text"], next_main["text"]).ratio()
        if next_ratio > current_ratio + 0.05:
            suspicious[link["link_id"]] = {
                "current_target_id": target_row["passage_id"],
                "expected_target_id": next_main["passage_id"],
                "current_ratio": round(current_ratio, 3),
                "expected_ratio": round(next_ratio, 3),
            }
    return suspicious


def manifest_risk_reason(sample: dict[str, str], current_safe_status: str, suspicious_index: dict[str, dict[str, Any]]) -> str:
    bucket = sample["suggested_review_bucket"]
    if sample["source_type"] == "main_passage":
        if current_safe_status == "removed":
            if sample["related_query_topic"]:
                return "ambiguous_passages_registry_hit; removed_from_safe_main; query_topic_candidate"
            return "ambiguous_passages_registry_hit; removed_from_safe_main"
        if current_safe_status == "downgraded":
            return "short_text_lt20; retrieval_primary_demoted_in_safe"
        if bucket.startswith("stable_safe_main_control"):
            return "safe_retained_control"
        return "safe_retained_query_candidate"

    link_id = sample.get("link_id", "")
    if link_id in CONFIRMED_MISLINKS:
        return "annotation_link_disabled_in_safe; confirmed_mislink_to_previous_main"
    if link_id and link_id in suspicious_index:
        return "annotation_link_disabled_in_safe; heuristic_adjacent_shift_suspect"
    return "annotation_link_disabled_in_safe; medium_confidence_link_not_flagged"


def related_anchor_value(sample: dict[str, str], annotation_link_by_from: dict[str, dict[str, Any]], suspicious_index: dict[str, dict[str, Any]]) -> str:
    if sample["source_type"] == "main_passage":
        return sample.get("related_passage_id", "")
    link = annotation_link_by_from.get(sample["original_id"])
    if not link:
        return ""
    current_target = link["to_passage_id"]
    expected_target = sample.get("expected_target_id") or suspicious_index.get(link["link_id"], {}).get("expected_target_id")
    if expected_target and expected_target != current_target:
        return f"{current_target} (expected {expected_target})"
    return current_target


def semantic_value_note(profile: str) -> str:
    if profile == "main_l1_primary_candidate":
        return "文本本体完整，语义自足，具备独立支撑定义/方证/治法判断的潜力。"
    if profile == "main_l2_recall_vector":
        return "文本较完整，适合补 recall 与受控向量召回，但不宜直接抬主依据。"
    if profile == "main_l2_recall_only":
        return "文本能补主题召回，但上下文依赖仍偏强，暂不建议 dense 化。"
    if profile == "main_l3_review":
        return "文本有参考价值，但解释跳跃或上下文依赖较强，更适合 review。"
    if profile == "main_l4_exclude":
        return "文本过短或碎片化，语义不自足，不适合作为独立检索对象。"
    if profile == "annotation_l2_recall":
        return "注解原文本身解释力较强，可作辅助说明或 raw annotation recall。"
    if profile == "annotation_l3_review":
        return "注解文本有核对价值，但当前更像人工复核材料，不宜常规放回。"
    if profile == "annotation_l4_exclude":
        return "注解过短或过于摘要化，离开准确挂点后语义价值很低。"
    return "safe 对照样本文本完整、结构稳定，可作为当前基线。"


def risk_note(sample: dict[str, str], current_safe_status: str) -> str:
    bucket = sample["suggested_review_bucket"]
    if sample["source_type"] == "annotation":
        if bucket.startswith("confirmed_mislink"):
            return "若按当前 link 放开，会把相邻条文解释错挂成“已验证依据”。"
        if bucket.startswith("heuristic_suspect"):
            return "存在“挂到前一条”的偏移信号，未人工复核前不宜恢复自动挂接。"
        return "文本本体较稳，但 annotation_links 整体仍未过验收，只能按未挂接注解使用。"
    if current_safe_status == "removed":
        return "ambiguous 命中说明该条在解析层仍有不稳定因素，直接回主链可能造成伪定义或错引。"
    if current_safe_status == "downgraded":
        return "主要风险来自句长过短，检索和 rerank 时容易被高相似噪声放大。"
    return "风险相对较低，本轮主要作为 safe 基线对照。"


def anchor_stability_note(
    sample: dict[str, str],
    current_safe_status: str,
    annotation_link_by_from: dict[str, dict[str, Any]],
    suspicious_index: dict[str, dict[str, Any]],
) -> str:
    if sample["source_type"] == "main_passage":
        related = sample.get("related_passage_id", "")
        if current_safe_status == "removed" and related:
            return f"当前无自动挂点；与相邻条文 {related} 存在近邻语境关系，需人工确认后再决定是否挂回。"
        if current_safe_status == "removed":
            return "当前无稳定自动锚点；若要放回，宜先按邻接语境做人工定位。"
        if current_safe_status == "downgraded":
            return "无 annotation 挂接问题；当前降级主要由短文本阈值触发。"
        return "safe 中已保留，锚点与对象边界稳定。"

    link = annotation_link_by_from.get(sample["original_id"])
    if not link:
        return "无现成主锚点；不适合自动挂接。"
    current_target = link["to_passage_id"]
    expected_target = sample.get("expected_target_id") or suspicious_index.get(link["link_id"], {}).get("expected_target_id")
    if expected_target and expected_target != current_target:
        return f"当前 link 指向 {current_target}，但更接近 {expected_target}；自动挂接不稳。"
    return f"当前 link 指向 {current_target}；本轮未见明显错挂信号，但仍不建议直接恢复 annotation_links。"


def build_review_row(
    sample: dict[str, str],
    current_safe_status: str,
    annotation_link_by_from: dict[str, dict[str, Any]],
    suspicious_index: dict[str, dict[str, Any]],
) -> dict[str, str]:
    template = REVIEW_TEMPLATES[sample["review_profile"]]
    row = {
        "sample_id": sample["sample_id"],
        **template,
        "anchor_stability_note": anchor_stability_note(sample, current_safe_status, annotation_link_by_from, suspicious_index),
        "semantic_value_note": semantic_value_note(sample["review_profile"]),
        "risk_note": risk_note(sample, current_safe_status),
        "final_comment": sample["manual_comment"],
    }
    return row


def main() -> None:
    full_main = load_json(FULL_DATASET_DIR / "main_passages.json")
    full_annotations = load_json(FULL_DATASET_DIR / "annotations.json")
    full_annotation_links = load_json(FULL_DATASET_DIR / "annotation_links.json")
    ambiguous_rows = load_json(FULL_DATASET_DIR / "ambiguous_passages.json")
    safe_payloads = load_safe_payloads(SAFE_ZIP_PATH)

    full_main_index = {row["passage_id"]: row for row in full_main}
    full_annotation_index = {row["passage_id"]: row for row in full_annotations}
    safe_main_index = {row["passage_id"]: row for row in safe_payloads["main_passages.json"]}
    annotation_link_by_from = {row["from_passage_id"]: row for row in full_annotation_links}
    ambiguous_ids = {row["passage_id"] for row in ambiguous_rows}
    suspicious_index = build_suspicious_link_index(full_main, full_annotations, full_annotation_links)

    manifest_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    status_counter: Counter[str] = Counter()
    level_counter: Counter[str] = Counter()

    for sample in SAMPLES:
        source_type = sample["source_type"]
        original_id = sample["original_id"]
        if source_type == "main_passage":
            source_row = full_main_index[original_id]
            current_safe_status = detect_main_safe_status(original_id, full_main_index, safe_main_index, ambiguous_ids)
        else:
            source_row = full_annotation_index[original_id]
            current_safe_status = "disabled"

        manifest_row = {
            "sample_id": sample["sample_id"],
            "source_type": source_type,
            "original_id": original_id,
            "current_safe_status": current_safe_status,
            "risk_reason": manifest_risk_reason(sample, current_safe_status, suspicious_index),
            "text_excerpt": truncate_text(source_row["text"]),
            "related_anchor_or_passage_id": related_anchor_value(sample, annotation_link_by_from, suspicious_index),
            "related_query_topic": sample["related_query_topic"],
            "suggested_review_bucket": sample["suggested_review_bucket"],
        }
        review_row = build_review_row(sample, current_safe_status, annotation_link_by_from, suspicious_index)
        manifest_rows.append(manifest_row)
        review_rows.append(review_row)
        status_counter[current_safe_status] += 1
        level_counter[review_row["decision_level"]] += 1

    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sample_id",
                "source_type",
                "original_id",
                "current_safe_status",
                "risk_reason",
                "text_excerpt",
                "related_anchor_or_passage_id",
                "related_query_topic",
                "suggested_review_bucket",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    with REVIEW_SHEET_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sample_id",
                "reviewer_decision",
                "decision_level",
                "can_be_primary_evidence",
                "can_enter_recall_layer",
                "can_enter_vector_index",
                "can_only_be_review_material",
                "should_remain_excluded",
                "anchor_stability_note",
                "semantic_value_note",
                "risk_note",
                "final_comment",
            ],
        )
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"Wrote manifest: {MANIFEST_OUT}")
    print(f"Wrote review sheet: {REVIEW_SHEET_OUT}")
    print(f"Sample count: {len(SAMPLES)}")
    print("Safe status counts:", dict(status_counter))
    print("Decision level counts:", dict(level_counter))


if __name__ == "__main__":
    main()
