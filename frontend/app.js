const API_PATH = "/api/v1/answers";
const STREAM_API_PATH = "/api/v1/answers/stream";
const STREAM_SOFT_WARNING_MS = 8000;
const STREAM_HARD_TIMEOUT_MS = 30000;
const FALLBACK_SOFT_WARNING_MS = 6000;
const FALLBACK_HARD_TIMEOUT_MS = 18000;
const REQUIRED_TOP_FIELDS = [
  "query",
  "answer_mode",
  "answer_text",
  "primary_evidence",
  "secondary_evidence",
  "review_materials",
  "disclaimer",
  "review_notice",
  "refuse_reason",
  "suggested_followup_questions",
  "citations",
  "display_sections",
];
const PROGRESS_STEPS = [
  { stage: "retrieving_evidence", label: "正在检索依据" },
  { stage: "organizing_evidence", label: "正在组织证据" },
  { stage: "generating_answer", label: "正在生成回答" },
  { stage: "completed", label: "已完成" },
];
const MODE_COPY = {
  idle: {
    badge: "等待中",
    title: "等待提问",
    description: "输入问题后开始本轮研读。",
    hint: "支持 Cmd/Ctrl + Enter 提交。",
  },
  loading: {
    badge: "处理中",
    title: "正在整理回答",
    description: "正在检索依据并生成回答。",
    hint: "等待稍长时会提示处理进度，这不等同于拒答。",
  },
  strong: {
    badge: "可参考",
    title: "可直接参考",
    description: "先看正文，再回看主依据。",
    hint: "补充依据和引用收在下方展开区。",
  },
  weak_with_review_notice: {
    badge: "需核对",
    title: "需核对",
    description: "这是一条需核对的整理结果，不能直接视为定论。",
    hint: "先看核对提示，再决定是否展开依据。",
  },
  refuse: {
    badge: "暂不支持",
    title: "当前不支持这样回答",
    description: "这属于业务拒答，不是系统报错。",
    hint: "可按下方改问建议继续追问。",
  },
  error: {
    badge: "请求异常",
    title: "本次请求未完成",
    description: "这次请求没拿到完整结果，不等同于系统拒答。",
    hint: "可以直接重试上一个问题。",
  },
};
const SOURCE_LABELS = {
  main_passages: "主文",
  annotations: "注解",
  passages: "全文",
  ambiguous_passages: "异文",
};
const ROLE_LABELS = {
  primary: "主依据",
  secondary: "补充依据",
  review: "核对材料",
};
const SOURCE_UNIT_LABELS = {
  main_passages: "条文",
  passages: "条文",
  ambiguous_passages: "异文",
  annotations: "注解",
  chunks: "片段",
};

function requireElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`页面缺少必要节点: #${id}`);
  }
  return element;
}

function createRequestError(kind, message, extra = {}) {
  const error = new Error(message);
  error.kind = kind;
  Object.assign(error, extra);
  return error;
}

const refs = {};
const state = {
  streamedAnswerText: "",
  latestPayload: null,
  lastQuery: "",
  activeRequestId: 0,
  activeTransport: null,
  requestInFlight: false,
  supportingExpanded: false,
  debugRequestFailure: null,
};

function setLoading(isLoading) {
  refs.submitButton.disabled = isLoading;
  refs.submitButton.textContent = isLoading ? "发送中…" : "发送";
  refs.sampleButtons.forEach((button) => {
    button.disabled = isLoading;
  });
  refs.retryButton.disabled = isLoading || !state.lastQuery;
  if (isLoading) {
    refs.statusText.textContent = "已提交问题，正在准备回答";
  }
}

function setErrorSummary(message) {
  refs.errorText.textContent = message || "";
}

function setModeBadge(mode) {
  const copy = MODE_COPY[mode] || MODE_COPY.idle;
  refs.modeBadge.className = `mode-badge mode-${mode || "idle"}`;
  refs.modeBadge.textContent = copy.badge;
  refs.modeBadge.title = mode || "idle";
}

function setModeSummary(mode, overrides = {}) {
  const copy = MODE_COPY[mode] || MODE_COPY.idle;
  const hint = overrides.hint || copy.hint;
  refs.modeSummary.className = `mode-summary mode-summary-${mode || "idle"}`;
  refs.modeTitle.textContent = overrides.title || copy.title;
  refs.modeDescription.textContent = overrides.description || copy.description;
  refs.modeReadingHint.textContent = hint || "";
  showSection(refs.modeReadingHint, Boolean(hint));
}

function setAnswerText(text, options = {}) {
  const { placeholder = false, streaming = false } = options;
  refs.answerText.textContent = text || "";
  refs.answerText.classList.toggle("empty-copy", placeholder);
  refs.answerText.classList.toggle("is-streaming", streaming);
}

function setQueryEcho(text, options = {}) {
  const { placeholder = false } = options;
  refs.queryEcho.textContent = text || "";
  refs.queryEcho.classList.toggle("empty-copy", placeholder);
}

function autoResizeQueryInput() {
  if (!refs.queryInput) {
    return;
  }
  refs.queryInput.style.height = "auto";
  refs.queryInput.style.height = `${Math.min(refs.queryInput.scrollHeight, 220)}px`;
}

function showSection(element, visible) {
  element.hidden = !visible;
}

function clearList(element) {
  element.innerHTML = "";
}

function createTag(tagName, className, text) {
  const node = document.createElement(tagName);
  if (className) {
    node.className = className;
  }
  if (text !== undefined) {
    node.textContent = text;
  }
  return node;
}

function formatSourceLabel(recordType) {
  return SOURCE_LABELS[recordType] || recordType || "未知来源";
}

function formatRoleLabel(displayRole) {
  return ROLE_LABELS[displayRole] || displayRole || "未标注";
}

function formatRecordShort(recordId) {
  if (!recordId) {
    return "未标注";
  }
  const parts = String(recordId).split(":");
  return parts[parts.length - 1] || recordId;
}

function getSourceObject(record) {
  return record?.record_type || record?.source_object || "";
}

function getChapterLabel(record) {
  return record?.chapter_name || record?.chapter_title || "";
}

function extractRecordOrdinal(recordId) {
  const value = String(recordId || "");
  const passageMatch = value.match(/-P-(\d+)(?!.*\d)/i);
  if (passageMatch) {
    return passageMatch[1];
  }

  const chunkMatch = value.match(/-CK-[A-Z]+-(\d+)(?!.*\d)/i) || value.match(/-CK-(\d+)(?!.*\d)/i);
  if (chunkMatch) {
    return chunkMatch[1];
  }

  const genericMatch = value.match(/(\d+)(?!.*\d)/);
  return genericMatch ? genericMatch[1] : formatRecordShort(value);
}

function formatSourceUnitLabel(sourceObject) {
  return SOURCE_UNIT_LABELS[sourceObject] || formatSourceLabel(sourceObject);
}

function joinTitleParts(parts) {
  return parts.filter(Boolean).join(" · ");
}

function buildStructuredRecordTitle(record) {
  const sourceObject = getSourceObject(record);
  const chapterLabel = getChapterLabel(record);
  const recordOrdinal = extractRecordOrdinal(record?.record_id);
  const sourceUnit = formatSourceUnitLabel(sourceObject);

  if (sourceObject === "main_passages" || sourceObject === "passages") {
    return joinTitleParts([chapterLabel, recordOrdinal ? `条文 ${recordOrdinal}` : "条文"]);
  }

  if (sourceObject === "ambiguous_passages") {
    return joinTitleParts([chapterLabel, recordOrdinal ? `异文 ${recordOrdinal}` : "异文"]);
  }

  if (sourceObject === "annotations") {
    return joinTitleParts([chapterLabel, recordOrdinal ? `注解 ${recordOrdinal}` : "注解"]);
  }

  if (sourceObject === "chunks") {
    return joinTitleParts([chapterLabel || formatSourceLabel(sourceObject), recordOrdinal ? `片段 ${recordOrdinal}` : "片段"]);
  }

  if (chapterLabel && recordOrdinal) {
    return joinTitleParts([chapterLabel, `${sourceUnit} ${recordOrdinal}`]);
  }

  if (chapterLabel) {
    return joinTitleParts([chapterLabel, sourceUnit]);
  }

  if (recordOrdinal && sourceUnit) {
    return `${sourceUnit} ${recordOrdinal}`;
  }

  return "";
}

function normalizeComparableText(text) {
  return String(text || "")
    .normalize("NFKC")
    .replace(/[\p{P}\p{S}\s]+/gu, "")
    .toLowerCase();
}

function titlesTooSimilar(title, snippet) {
  const normalizedTitle = normalizeComparableText(title);
  const normalizedSnippet = normalizeComparableText(snippet);

  if (!normalizedTitle || !normalizedSnippet) {
    return false;
  }

  if (normalizedTitle === normalizedSnippet) {
    return true;
  }

  if (normalizedTitle.length >= 6 && normalizedSnippet.startsWith(normalizedTitle)) {
    return true;
  }

  return normalizedTitle.length >= 10 && normalizedSnippet.includes(normalizedTitle);
}

function resolveRecordTitle(record, options = {}) {
  const { prefix = "" } = options;
  const rawTitle = String(record?.title || "").trim();
  const snippet = String(record?.snippet || "").trim();
  const structuredTitle = buildStructuredRecordTitle(record);
  const baseTitle = structuredTitle || rawTitle || formatRecordShort(record?.record_id);
  let resolvedTitle = baseTitle;

  if (rawTitle && titlesTooSimilar(rawTitle, snippet) && structuredTitle) {
    resolvedTitle = structuredTitle;
  }

  if (titlesTooSimilar(resolvedTitle, snippet)) {
    resolvedTitle = structuredTitle && !titlesTooSimilar(structuredTitle, snippet) ? structuredTitle : "";
  }

  if (!resolvedTitle && !snippet) {
    resolvedTitle = structuredTitle || rawTitle || formatRecordShort(record?.record_id);
  }

  if (!prefix) {
    return resolvedTitle;
  }

  return resolvedTitle ? `${prefix} · ${resolvedTitle}` : prefix;
}

function scrollConversationIntoView() {
  if (!refs.userMessageCard?.scrollIntoView) {
    return;
  }
  refs.userMessageCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateCountLabel(element, count, suffix = "条") {
  element.textContent = count > 0 ? `${count}${suffix}` : "";
}

function clearRequestTimers(requestId = null) {
  const activeTransport = state.activeTransport;
  if (!activeTransport) {
    return;
  }

  if (requestId !== null && activeTransport.requestId !== requestId) {
    return;
  }

  if (activeTransport.softWarningTimer) {
    window.clearTimeout(activeTransport.softWarningTimer);
  }
  if (activeTransport.hardTimeoutTimer) {
    window.clearTimeout(activeTransport.hardTimeoutTimer);
  }

  state.activeTransport = null;
}

function getAbortReason(error, controller) {
  if (error?.name !== "AbortError") {
    return null;
  }
  return controller?.__abortReason || controller?.signal?.reason || null;
}

function normalizeDebugFailure(stage, input) {
  if (!input) {
    return null;
  }

  if (typeof input === "string") {
    return {
      kind: `${stage}_transport_failed`,
      message: input,
    };
  }

  if (typeof input === "object") {
    return {
      kind: input.kind || `${stage}_transport_failed`,
      message: input.message || `${stage === "stream" ? "流式" : "标准"}请求模拟失败。`,
    };
  }

  return {
    kind: `${stage}_transport_failed`,
    message: `${stage === "stream" ? "流式" : "标准"}请求模拟失败。`,
  };
}

function failNextRequest(options = {}) {
  state.debugRequestFailure = {
    query: options.query || "",
    once: options.once !== false,
    stream: normalizeDebugFailure("stream", options.stream),
    fallback: normalizeDebugFailure("fallback", options.fallback),
  };
}

function consumeDebugFailure(stage, query) {
  const pendingFailure = state.debugRequestFailure;
  if (!pendingFailure) {
    return null;
  }

  if (pendingFailure.query && pendingFailure.query !== query) {
    return null;
  }

  const failure = pendingFailure[stage];
  if (!failure) {
    return null;
  }

  if (pendingFailure.once) {
    const nextFailure = {
      ...pendingFailure,
      [stage]: null,
    };
    state.debugRequestFailure = nextFailure.stream || nextFailure.fallback ? nextFailure : null;
  }

  return createRequestError(failure.kind, failure.message);
}

function setProgressVisualState(kind) {
  refs.progressSection.classList.remove("is-settled", "is-interrupted");
  if (kind === "settled") {
    refs.progressSection.classList.add("is-settled");
  }
  if (kind === "interrupted") {
    refs.progressSection.classList.add("is-interrupted");
  }
}

function setProgressNote(message, tone = "info") {
  refs.progressNote.textContent = message || "";
  refs.progressNote.className = "progress-note";
  refs.progressNote.classList.toggle("is-warning", tone === "warning");
  showSection(refs.progressNote, Boolean(message));
}

function clearProgressNote() {
  setProgressNote("");
}

function ensureProgressSteps() {
  if (refs.progressSteps.childElementCount === PROGRESS_STEPS.length) {
    return;
  }

  clearList(refs.progressSteps);
  const fragment = document.createDocumentFragment();

  PROGRESS_STEPS.forEach((step, index) => {
    const item = createTag("li", "progress-step");
    item.dataset.stage = step.stage;
    const marker = createTag("span", "progress-step-marker", String(index + 1));
    marker.dataset.role = "marker";
    const text = createTag("span", "progress-step-text", step.label);
    item.append(marker, text);
    fragment.append(item);
  });

  refs.progressSteps.append(fragment);
}

function updateProgress(stage, detail) {
  ensureProgressSteps();
  showSection(refs.progressSection, true);
  setProgressVisualState("active");

  const stageIndex = PROGRESS_STEPS.findIndex((item) => item.stage === stage);
  const label = PROGRESS_STEPS.find((item) => item.stage === stage)?.label || stage || "处理中";

  Array.from(refs.progressSteps.children).forEach((node, index) => {
    const marker = node.querySelector('[data-role="marker"]');
    const isComplete = stageIndex >= 0 && index < stageIndex;
    const isActive = stageIndex >= 0 && index === stageIndex && stage !== "completed";
    const isCompleted = stage === "completed" && index <= stageIndex;

    node.classList.toggle("is-complete", isComplete || isCompleted);
    node.classList.toggle("is-active", isActive);

    if (marker) {
      marker.textContent = isComplete || isCompleted ? "✓" : String(index + 1);
    }
  });

  refs.progressDetail.textContent = detail || label;
  refs.statusText.textContent = detail || label;
}

function settleProgress(detail) {
  updateProgress("completed", detail || "回答已完成。");
  setProgressVisualState("settled");
  clearProgressNote();
  refs.answerText.classList.remove("is-streaming");
}

function interruptProgress(detail) {
  ensureProgressSteps();
  showSection(refs.progressSection, true);
  setProgressVisualState("interrupted");
  clearProgressNote();

  Array.from(refs.progressSteps.children).forEach((node, index) => {
    const marker = node.querySelector('[data-role="marker"]');
    node.classList.remove("is-active");
    if (marker && !node.classList.contains("is-complete")) {
      marker.textContent = String(index + 1);
    }
  });

  refs.progressDetail.textContent = detail || "当前请求未完成。";
  refs.statusText.textContent = detail || "当前请求未完成。";
  refs.answerText.classList.remove("is-streaming");
}

function startRequestTimers(requestId, controller, options = {}) {
  const {
    softDelayMs = STREAM_SOFT_WARNING_MS,
    hardDelayMs = STREAM_HARD_TIMEOUT_MS,
    softMessage = "等待时间比平时更长，系统仍在继续处理。你可以继续等待。",
    hardKind = "request_timeout",
    hardMessage = "等待时间较长，本次请求已停止。你可以直接重试。",
  } = options;

  clearRequestTimers();

  const transportState = {
    requestId,
    controller,
    softWarningTimer: null,
    hardTimeoutTimer: null,
  };
  state.activeTransport = transportState;

  transportState.softWarningTimer = window.setTimeout(() => {
    if (state.activeRequestId !== requestId || !state.requestInFlight || state.activeTransport !== transportState) {
      return;
    }
    setProgressNote(softMessage, "warning");
  }, softDelayMs);

  transportState.hardTimeoutTimer = window.setTimeout(() => {
    if (state.activeRequestId !== requestId || !state.requestInFlight || state.activeTransport !== transportState) {
      return;
    }
    controller.__abortReason = createRequestError(hardKind, hardMessage);
    controller.abort(controller.__abortReason);
  }, hardDelayMs);
}

function clearErrorState() {
  showSection(refs.errorSection, false);
  refs.errorTitle.textContent = "请求未完成";
  refs.errorMessageText.textContent = "";
  refs.errorHelpText.textContent = "这是请求错误或超时，不等同于系统拒答。";
  refs.retryButton.disabled = !state.lastQuery;
  setErrorSummary("");
}

function showErrorState(copy) {
  setModeBadge("error");
  setModeSummary("error", {
    title: copy.title,
    description: copy.message,
    hint: copy.help,
  });
  setAnswerText("本次请求未完成，请重试。", { placeholder: true, streaming: false });
  refs.errorTitle.textContent = copy.title;
  refs.errorMessageText.textContent = copy.message;
  refs.errorHelpText.textContent = copy.help;
  refs.retryButton.disabled = !state.lastQuery;
  showSection(refs.errorSection, true);
  setErrorSummary(copy.title);
}

function normalizeErrorCopy(error) {
  if (error?.kind === "stream_and_fallback_failed") {
    const streamMessage = String(error.streamError?.message || "流式请求未完成").replace(/[。.]$/, "");
    const fallbackMessage = String(error.fallbackError?.message || "标准请求未完成").replace(/[。.]$/, "");
    return {
      title: "流式与标准请求都未完成",
      message: `${streamMessage}；随后改用标准请求时又失败：${fallbackMessage}`,
      help: "这属于请求错误或超时，不等同于系统拒答。可以直接重试上一个问题。",
    };
  }

  if (error?.kind === "request_timeout" || error?.kind === "fallback_timeout") {
    return {
      title: "等待时间过长",
      message: error.message,
      help: "页面已经结束当前请求，不会继续停留在半状态。你可以直接重试。",
    };
  }

  if (error?.kind === "fallback_response_failed" || error?.kind === "fallback_transport_failed") {
    return {
      title: "标准请求未完成",
      message: error.message,
      help: "流式回退也没有成功拿到结果。请稍后重试，或先检查本地服务状态。",
    };
  }

  return {
    title: "请求未完成",
    message: error?.message || "请求失败",
    help: "这属于请求错误或超时，不等同于系统拒答。你可以直接重试上一个问题。",
  };
}

function formatSupportingSummary(answerMode, secondary, review, citations, followups) {
  const parts = [];

  if (secondary.length > 0) {
    parts.push(`补充 ${secondary.length}`);
  }
  if (review.length > 0) {
    parts.push(`核对 ${review.length}`);
  }
  if (citations.length > 0) {
    parts.push(`引用 ${citations.length}`);
  }
  if (followups.length > 0) {
    parts.push(`${answerMode === "refuse" ? "改问" : "追问"} ${followups.length}`);
  }

  return parts.length > 0 ? parts.join(" · ") : "暂无附加信息";
}

function updateSupportingDetails(answerMode, sections, options = {}) {
  const { preserveOpen = false } = options;
  const { secondary, review, citations, followups, hasEmptyEvidence } = sections;
  const hasSupportingContent =
    secondary.length > 0 ||
    review.length > 0 ||
    citations.length > 0 ||
    followups.length > 0 ||
    hasEmptyEvidence;

  refs.supportingTitle.textContent =
    answerMode === "refuse" && followups.length > 0 ? "查看改问建议" : "查看依据与补充信息";
  refs.supportingSummary.textContent = formatSupportingSummary(
    answerMode,
    secondary,
    review,
    citations,
    followups,
  );

  showSection(refs.supportingDetails, hasSupportingContent);

  if (!hasSupportingContent) {
    refs.supportingDetails.open = false;
    state.supportingExpanded = false;
    return;
  }

  if (preserveOpen) {
    refs.supportingDetails.open = state.supportingExpanded;
    return;
  }

  const shouldOpenByDefault = answerMode === "refuse" && followups.length > 0;
  refs.supportingDetails.open = shouldOpenByDefault;
  state.supportingExpanded = shouldOpenByDefault;
}

function renderEvidenceList(target, items) {
  clearList(target);
  const fragment = document.createDocumentFragment();

  items.forEach((item) => {
    const role = item.display_role || "secondary";
    const card = createTag("article", `evidence-card role-${role}`);
    const displayTitle = resolveRecordTitle(item);
    const meta = createTag("div", "evidence-meta");

    meta.append(
      createTag("span", `role-chip role-chip-${role}`, formatRoleLabel(role)),
      createTag("span", "chip", `等级 ${item.evidence_level}`),
      createTag("span", "chip", formatSourceLabel(item.record_type)),
      createTag("span", "chip", `记录 ${formatRecordShort(item.record_id)}`),
    );

    if (getChapterLabel(item)) {
      meta.append(createTag("span", "chip", getChapterLabel(item)));
    }

    const snippet = createTag("p", "snippet", item.snippet || "");
    const footer = createTag("div", "evidence-footer");
    footer.append(createTag("p", "record-footnote", `record_id: ${item.record_id}`));

    if (displayTitle) {
      card.append(createTag("h3", "", displayTitle));
    }

    card.append(meta);

    if (item.snippet) {
      card.append(snippet);
    }

    if (Array.isArray(item.risk_flags) && item.risk_flags.length > 0) {
      const riskList = createTag("ul", "risk-flags");
      item.risk_flags.forEach((flag) => {
        riskList.append(createTag("li", "", flag));
      });
      card.append(riskList);
    }

    card.append(footer);
    fragment.append(card);
  });

  target.append(fragment);
}

function renderCitations(items) {
  clearList(refs.citationsList);
  const fragment = document.createDocumentFragment();

  items.forEach((citation) => {
    const role = citation.citation_role || "secondary";
    const item = createTag("li", `citation-item citation-role-${role}`);
    const titleText = resolveRecordTitle(citation, { prefix: citation.citation_id || "引用" });
    const meta = createTag("div", "citation-meta");
    meta.append(
      createTag("span", `role-chip role-chip-${role}`, formatRoleLabel(role)),
      createTag("span", "chip", `等级 ${citation.evidence_level}`),
      createTag("span", "chip", formatSourceLabel(citation.record_type)),
      createTag("span", "chip", `记录 ${formatRecordShort(citation.record_id)}`),
    );
    if (getChapterLabel(citation)) {
      meta.append(createTag("span", "chip", getChapterLabel(citation)));
    }
    const snippet = createTag("p", "citation-snippet", citation.snippet || "");
    const footer = createTag("div", "citation-footer");
    footer.append(createTag("p", "record-footnote", `record_id: ${citation.record_id}`));
    if (titleText) {
      item.append(createTag("h3", "", titleText));
    }
    item.append(meta);
    if (citation.snippet) {
      item.append(snippet);
    }
    item.append(footer);
    fragment.append(item);
  });

  refs.citationsList.append(fragment);
}

function renderFollowups(items) {
  clearList(refs.followupsList);
  const fragment = document.createDocumentFragment();
  items.forEach((text) => {
    fragment.append(createTag("li", "", text));
  });
  refs.followupsList.append(fragment);
}

function validatePayload(payload) {
  const missingFields = REQUIRED_TOP_FIELDS.filter((field) => !(field in payload));
  if (missingFields.length > 0) {
    throw createRequestError("invalid_payload", `响应缺少字段: ${missingFields.join(", ")}`);
  }
}

function updateEvidenceCounts(primary, secondary, review, citations, followups) {
  updateCountLabel(refs.primaryCount, primary.length);
  updateCountLabel(refs.secondaryCount, secondary.length);
  updateCountLabel(refs.reviewCount, review.length);
  updateCountLabel(refs.citationsCount, citations.length);
  updateCountLabel(refs.followupsCount, followups.length);
}

function resetResultSections() {
  refs.disclaimerText.textContent = "";
  refs.reviewNoticeText.textContent = "";
  refs.refuseReasonText.textContent = "";
  clearList(refs.primaryList);
  clearList(refs.secondaryList);
  clearList(refs.reviewList);
  clearList(refs.citationsList);
  clearList(refs.followupsList);
  updateCountLabel(refs.primaryCount, 0);
  updateCountLabel(refs.secondaryCount, 0);
  updateCountLabel(refs.reviewCount, 0);
  updateCountLabel(refs.citationsCount, 0);
  updateCountLabel(refs.followupsCount, 0);

  showSection(refs.reviewNoticeSection, false);
  showSection(refs.refuseSection, false);
  showSection(refs.emptyEvidenceSection, false);
  showSection(refs.primarySection, false);
  showSection(refs.secondarySection, false);
  showSection(refs.reviewSection, false);
  showSection(refs.citationsSection, false);
  showSection(refs.followupsSection, false);
  showSection(refs.supportingDetails, false);
  refs.supportingDetails.open = false;
  refs.supportingSummary.textContent = "暂无附加信息";
  refs.supportingTitle.textContent = "查看依据与补充信息";
  state.supportingExpanded = false;
}

function resetViewForRequest(query) {
  state.streamedAnswerText = "";
  state.latestPayload = null;
  window.__lastAnswerPayload = null;
  window.__lastStreamEvent = null;

  clearErrorState();
  clearProgressNote();
  setQueryEcho(query, { placeholder: false });
  setModeBadge("loading");
  setModeSummary("loading");
  setAnswerText("已提交问题，正在准备回答…", { placeholder: true, streaming: false });
  resetResultSections();
  ensureProgressSteps();
  updateProgress("retrieving_evidence", "已提交问题，正在建立流式连接。");
  scrollConversationIntoView();
}

function renderPayload(payload, options = {}) {
  const { preserveAnswerText = false, preserveEvidence = false } = options;
  validatePayload(payload);
  clearErrorState();
  state.latestPayload = payload;
  window.__lastAnswerPayload = payload;
  setModeBadge(payload.answer_mode);
  setModeSummary(payload.answer_mode);
  setQueryEcho(payload.query || "未返回 query", { placeholder: !(payload.query || "") });
  refs.disclaimerText.textContent = payload.disclaimer || "";

  if (!preserveAnswerText) {
    setAnswerText(payload.answer_text || "", {
      placeholder: !(payload.answer_text || ""),
      streaming: false,
    });
  }

  refs.reviewNoticeText.textContent = payload.review_notice || "";
  refs.refuseReasonText.textContent = payload.refuse_reason || "";

  const primary = Array.isArray(payload.primary_evidence) ? payload.primary_evidence : [];
  const secondary = Array.isArray(payload.secondary_evidence) ? payload.secondary_evidence : [];
  const review = Array.isArray(payload.review_materials) ? payload.review_materials : [];
  const citations = Array.isArray(payload.citations) ? payload.citations : [];
  const followups = Array.isArray(payload.suggested_followup_questions)
    ? payload.suggested_followup_questions
    : [];

  updateEvidenceCounts(primary, secondary, review, citations, followups);
  showSection(refs.reviewNoticeSection, Boolean(payload.review_notice));
  showSection(refs.refuseSection, Boolean(payload.refuse_reason));
  showSection(refs.primarySection, primary.length > 0);
  showSection(refs.secondarySection, secondary.length > 0);
  showSection(refs.reviewSection, review.length > 0);
  showSection(refs.citationsSection, citations.length > 0);
  showSection(refs.followupsSection, followups.length > 0);
  const hasEmptyEvidence = primary.length + secondary.length + review.length + citations.length === 0;
  showSection(refs.emptyEvidenceSection, hasEmptyEvidence);

  if (!preserveEvidence) {
    renderEvidenceList(refs.primaryList, primary);
    renderEvidenceList(refs.secondaryList, secondary);
    renderEvidenceList(refs.reviewList, review);
    renderCitations(citations);
    renderFollowups(followups);
  }

  updateSupportingDetails(
    payload.answer_mode,
    { secondary, review, citations, followups, hasEmptyEvidence },
    { preserveOpen: preserveEvidence },
  );
}

function applyEvidenceReadyPayload(payload) {
  validatePayload(payload);
  state.streamedAnswerText = "";
  renderPayload(payload, { preserveAnswerText: true, preserveEvidence: false });
  setAnswerText("", { placeholder: false, streaming: true });
  refs.statusText.textContent = "依据已整理，正在渐进显示 answer_text";
}

function appendAnswerDelta(delta) {
  if (!delta) {
    return;
  }
  state.streamedAnswerText += delta;
  setAnswerText(state.streamedAnswerText, { placeholder: false, streaming: true });
}

function finalizeCompletedPayload(payload) {
  const preserveEvidence = Boolean(state.latestPayload && state.latestPayload.query === payload.query);
  renderPayload(payload, { preserveAnswerText: false, preserveEvidence });
  settleProgress("回答已完成，界面已切换到最终展示。");
  refs.statusText.textContent = "请求已完成";
}

function handleStreamEvent(event, requestId) {
  if (requestId !== state.activeRequestId || !event || typeof event !== "object") {
    return false;
  }

  window.__lastStreamEvent = event;

  if (event.type === "phase") {
    updateProgress(event.stage, event.detail || event.label);
    return false;
  }

  if (event.type === "evidence_ready") {
    applyEvidenceReadyPayload(event.payload || {});
    return false;
  }

  if (event.type === "answer_delta") {
    appendAnswerDelta(event.delta || "");
    refs.statusText.textContent = "正在生成回答";
    return false;
  }

  if (event.type === "completed") {
    finalizeCompletedPayload(event.payload || state.latestPayload || {});
    return true;
  }

  if (event.type === "error") {
    throw createRequestError("stream_error_event", event?.error?.message || "流式过程中发生错误。");
  }

  return false;
}

async function consumeNdjsonStream(response, requestId, controller) {
  if (!response.body) {
    throw createRequestError("stream_unavailable", "浏览器未提供可读流，无法进入流式渲染。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
          continue;
        }
        const event = JSON.parse(line);
        completed = handleStreamEvent(event, requestId) || completed;
      }
    }

    buffer += decoder.decode();
    const trailingLine = buffer.trim();
    if (trailingLine) {
      const event = JSON.parse(trailingLine);
      completed = handleStreamEvent(event, requestId) || completed;
    }
  } catch (error) {
    const abortReason = getAbortReason(error, controller);
    if (abortReason) {
      throw abortReason;
    }
    throw error;
  }

  if (!completed) {
    throw createRequestError("stream_incomplete", "流式响应提前结束，未收到 completed 事件。");
  }
}

async function readJsonSafely(response) {
  try {
    return await response.json();
  } catch (error) {
    return null;
  }
}

async function submitQueryWithStream(query, requestId, controller) {
  const debugFailure = consumeDebugFailure("stream", query);
  if (debugFailure) {
    throw debugFailure;
  }

  let response;

  try {
    response = await fetch(STREAM_API_PATH, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
      signal: controller.signal,
    });
  } catch (error) {
    const abortReason = getAbortReason(error, controller);
    if (abortReason) {
      throw abortReason;
    }
    throw createRequestError("stream_transport_failed", "流式请求未能成功建立。");
  }

  const contentType = response.headers.get("Content-Type") || "";

  if (response.status === 404 || response.status === 405) {
    return false;
  }

  if (!response.ok) {
    const payload = contentType.includes("application/json") ? await readJsonSafely(response) : null;
    throw createRequestError("stream_response_failed", payload?.error?.message || "流式请求失败。");
  }

  if (!response.body || !contentType.includes("application/x-ndjson")) {
    return false;
  }

  await consumeNdjsonStream(response, requestId, controller);
  clearRequestTimers(requestId);
  return true;
}

function prepareFallbackView(message) {
  clearProgressNote();
  setProgressNote(message, "warning");
  updateProgress("retrieving_evidence", "流式响应未完整返回，正在改用标准请求。");
  setModeBadge("loading");
  setModeSummary("loading", {
    description: "流式响应未顺利完成，系统正在改用标准请求重新获取最终结果。",
    hint: "这仍属于同一次回答流程，不等同于拒答。",
  });
  setAnswerText("流式响应未完整返回，正在改用标准请求…", {
    placeholder: true,
    streaming: false,
  });
  resetResultSections();
}

async function submitQueryWithFallback(query, requestId, triggerError) {
  prepareFallbackView(triggerError?.message || "流式请求未完成，正在改用标准请求。");

  const controller = new AbortController();
  startRequestTimers(requestId, controller, {
    softDelayMs: FALLBACK_SOFT_WARNING_MS,
    hardDelayMs: FALLBACK_HARD_TIMEOUT_MS,
    softMessage: "标准请求等待时间较长，系统仍在继续处理。你可以继续等待。",
    hardKind: "fallback_timeout",
    hardMessage: "标准请求等待时间较长，本次请求已停止。你可以直接重试。",
  });

  const debugFailure = consumeDebugFailure("fallback", query);
  if (debugFailure) {
    throw debugFailure;
  }

  let response;
  try {
    response = await fetch(API_PATH, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
      signal: controller.signal,
    });
  } catch (error) {
    const abortReason = getAbortReason(error, controller);
    if (abortReason) {
      throw abortReason;
    }
    throw createRequestError("fallback_transport_failed", "标准请求未能成功返回。");
  }

  const payload = await readJsonSafely(response);
  if (!response.ok) {
    throw createRequestError("fallback_response_failed", payload?.error?.message || "标准请求失败。");
  }
  if (!payload) {
    throw createRequestError("fallback_response_failed", "标准请求未返回可解析的 JSON。");
  }

  clearRequestTimers(requestId);
  renderPayload(payload, { preserveAnswerText: false, preserveEvidence: false });
  settleProgress("标准响应已返回，界面已完成收尾。");
  refs.statusText.textContent = "请求已完成";
}

async function submitQuery(query) {
  setErrorSummary("");
  setLoading(true);
  state.lastQuery = query;
  state.requestInFlight = true;
  const requestId = state.activeRequestId + 1;
  state.activeRequestId = requestId;
  window.__lastSubmitQuery = query;
  resetViewForRequest(query);

  const streamController = new AbortController();
  startRequestTimers(requestId, streamController, {
    softDelayMs: STREAM_SOFT_WARNING_MS,
    hardDelayMs: STREAM_HARD_TIMEOUT_MS,
    softMessage: "等待时间比平时更长，系统仍在继续处理。你可以继续等待。",
    hardKind: "request_timeout",
    hardMessage: "等待时间较长，本次流式请求已停止。你可以直接重试。",
  });

  let streamError = null;

  try {
    const streamed = await submitQueryWithStream(query, requestId, streamController);
    if (!streamed) {
      streamError = createRequestError("stream_unavailable", "流式接口不可用，已自动回退到标准请求。");
    } else {
      return;
    }
  } catch (error) {
    if (requestId !== state.activeRequestId) {
      return;
    }
    streamError = error;
  }

  if (requestId !== state.activeRequestId) {
    return;
  }

  try {
    await submitQueryWithFallback(query, requestId, streamError);
  } catch (fallbackError) {
    const combinedError = createRequestError(
      "stream_and_fallback_failed",
      fallbackError.message,
      { streamError, fallbackError },
    );
    const errorCopy = normalizeErrorCopy(combinedError);
    interruptProgress(errorCopy.title);
    showErrorState(errorCopy);
    console.error(streamError);
    console.error(fallbackError);
  } finally {
    if (requestId === state.activeRequestId) {
      state.requestInFlight = false;
      clearRequestTimers(requestId);
      setLoading(false);
    }
  }
}

function retryLastQuery() {
  if (!state.lastQuery || refs.submitButton.disabled) {
    return;
  }
  refs.queryInput.value = state.lastQuery;
  autoResizeQueryInput();
  refs.queryInput.focus();
  refs.queryInput.setSelectionRange(state.lastQuery.length, state.lastQuery.length);
  void submitQuery(state.lastQuery);
}

function boot() {
  refs.form = requireElement("query-form");
  refs.queryInput = requireElement("query-input");
  refs.submitButton = requireElement("submit-button");
  refs.retryButton = requireElement("retry-button");
  refs.statusText = requireElement("status-text");
  refs.errorText = requireElement("error-text");
  refs.modeBadge = requireElement("mode-badge");
  refs.userMessageCard = requireElement("user-message-card");
  refs.queryEcho = requireElement("query-echo");
  refs.modeSummary = requireElement("mode-summary");
  refs.modeTitle = requireElement("mode-title");
  refs.modeDescription = requireElement("mode-description");
  refs.modeReadingHint = requireElement("mode-reading-hint");
  refs.progressSection = requireElement("progress-section");
  refs.progressDetail = requireElement("progress-detail");
  refs.progressSteps = requireElement("progress-steps");
  refs.progressNote = requireElement("progress-note");
  refs.answerText = requireElement("answer-text");
  refs.disclaimerText = requireElement("disclaimer-text");
  refs.errorSection = requireElement("error-section");
  refs.errorTitle = requireElement("error-title");
  refs.errorMessageText = requireElement("error-message-text");
  refs.errorHelpText = requireElement("error-help-text");
  refs.reviewNoticeSection = requireElement("review-notice-section");
  refs.reviewNoticeText = requireElement("review-notice-text");
  refs.refuseSection = requireElement("refuse-section");
  refs.refuseReasonText = requireElement("refuse-reason-text");
  refs.emptyEvidenceSection = requireElement("empty-evidence-section");
  refs.primarySection = requireElement("primary-section");
  refs.primaryCount = requireElement("primary-count");
  refs.primaryList = requireElement("primary-list");
  refs.supportingDetails = requireElement("supporting-details");
  refs.supportingTitle = requireElement("supporting-title");
  refs.supportingSummary = requireElement("supporting-summary");
  refs.secondarySection = requireElement("secondary-section");
  refs.secondaryCount = requireElement("secondary-count");
  refs.secondaryList = requireElement("secondary-list");
  refs.reviewSection = requireElement("review-section");
  refs.reviewCount = requireElement("review-count");
  refs.reviewList = requireElement("review-list");
  refs.citationsSection = requireElement("citations-section");
  refs.citationsCount = requireElement("citations-count");
  refs.citationsList = requireElement("citations-list");
  refs.followupsSection = requireElement("followups-section");
  refs.followupsCount = requireElement("followups-count");
  refs.followupsList = requireElement("followups-list");
  refs.sampleButtons = Array.from(document.querySelectorAll(".sample-chip"));

  ensureProgressSteps();
  setModeBadge("idle");
  setModeSummary("idle");
  setQueryEcho("尚未查询", { placeholder: true });
  autoResizeQueryInput();
  clearErrorState();

  refs.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = refs.queryInput.value.trim();

    if (!query) {
      setErrorSummary("请输入问题后再提交。");
      refs.statusText.textContent = "请先输入问题";
      return;
    }

    await submitQuery(query);
  });

  refs.queryInput.addEventListener("input", () => {
    autoResizeQueryInput();
  });

  refs.queryInput.addEventListener("keydown", (event) => {
    const shouldSubmit = (event.metaKey || event.ctrlKey) && event.key === "Enter";
    if (!shouldSubmit || refs.submitButton.disabled) {
      return;
    }
    event.preventDefault();
    refs.form.requestSubmit();
  });

  refs.retryButton.addEventListener("click", () => {
    retryLastQuery();
  });

  refs.supportingDetails.addEventListener("toggle", () => {
    state.supportingExpanded = refs.supportingDetails.open;
  });

  refs.sampleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const query = button.dataset.query || "";
      refs.queryInput.value = query;
      autoResizeQueryInput();
      refs.queryInput.focus();
      refs.queryInput.setSelectionRange(query.length, query.length);
      refs.statusText.textContent = "样例已填充，可直接发送";
      setErrorSummary("");
    });
  });

  refs.statusText.textContent = "前端脚本已加载，等待提交";
  window.__frontendTestHooks = {
    submitQuery,
    failNextRequest,
    clearPlannedFailures: () => {
      state.debugRequestFailure = null;
    },
    getRequestState: () => ({
      activeRequestId: state.activeRequestId,
      requestInFlight: state.requestInFlight,
      activeTransportRequestId: state.activeTransport?.requestId || null,
      lastQuery: state.lastQuery,
      latestAnswerMode: state.latestPayload?.answer_mode || null,
      debugRequestFailure: state.debugRequestFailure,
    }),
    normalizeErrorCopy,
    resolveRecordTitle,
    titlesTooSimilar,
    renderPayload,
    showErrorState,
  };
  window.__frontendBooted = true;
}

try {
  boot();
} catch (error) {
  window.__frontendBooted = false;
  console.error(error);
  const statusElement = document.getElementById("status-text");
  const errorElement = document.getElementById("error-text");
  if (statusElement) {
    statusElement.textContent = "前端初始化失败";
  }
  if (errorElement) {
    errorElement.textContent = error instanceof Error ? error.message : "前端初始化失败";
  }
}
