const CONVERSATIONS_API_PATH = "/api/v1/conversations";
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
const MODE_COPY = {
  idle: {
    badge: "等待中",
    title: "等待提问",
    description: "开始发送后，这里会切换到当前回答的结果状态与阅读建议。",
    hint: "当前会话恢复后，会按 strong / weak / refuse 展示每条 assistant 消息。",
  },
  loading: {
    badge: "处理中",
    title: "正在整理回答",
    description: "系统正在检索依据、组织证据并准备最终回答。",
    hint: "发送期间会暂时锁定会话切换，避免结果串写到别的历史会话。",
  },
  strong: {
    badge: "可参考",
    title: "可直接参考的回答",
    description: "当前回答优先依据主依据整理，可先读回答，再回看主依据区核对原文。",
    hint: "阅读顺序建议：回答 -> 主依据 -> 补充依据 -> 回答引用。",
  },
  weak_with_review_notice: {
    badge: "需核对",
    title: "需核对的回答",
    description: "当前没有足够强的正文证据，回答只提供可核对线索，不能视为确定结论。",
    hint: "请优先看核对提示，再对照补充依据和核对材料阅读。",
  },
  refuse: {
    badge: "暂不支持",
    title: "当前不支持这样回答",
    description: "这属于正常的业务拒答，不是系统报错。请先看拒答原因，再按改问建议继续追问。",
    hint: "阅读顺序建议：拒答原因 -> 改问建议 -> 重新收窄问题。",
  },
  error: {
    badge: "请求异常",
    title: "本次请求未完成",
    description: "这是请求错误、超时或服务异常，不等同于系统拒答。",
    hint: "可以直接重试当前问题；如果问题持续存在，再检查本地服务状态。",
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
const HISTORY_SEARCH_DEBOUNCE_MS = 180;

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

function showSection(element, visible) {
  element.hidden = !visible;
}

function clearList(element) {
  element.innerHTML = "";
}

const refs = {};
const state = {
  conversations: [],
  activeConversationId: null,
  activeConversation: null,
  historySearch: "",
  conversationsLoading: true,
  conversationLoading: false,
  sending: false,
  pendingTurn: null,
  deletingConversationId: null,
  historyRequestSeq: 0,
  conversationRequestSeq: 0,
  historySearchTimer: null,
};

function setStatus(message) {
  refs.statusText.textContent = message || "";
}

function setError(message) {
  refs.errorText.textContent = message || "";
}

function setComposerDisabled(disabled) {
  refs.queryInput.disabled = disabled;
  refs.submitButton.disabled = disabled;
  refs.submitButton.textContent = disabled ? "发送中…" : "发送";
  refs.sampleButtons.forEach((button) => {
    button.disabled = disabled;
  });
}

function resetComposerState() {
  refs.queryInput.value = "";
  if (refs.sampleQueries) {
    refs.sampleQueries.open = false;
  }
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
  return record?.chapter_title || record?.chapter_name || "";
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

function validatePayload(payload) {
  const missingFields = REQUIRED_TOP_FIELDS.filter((field) => !(field in payload));
  if (missingFields.length > 0) {
    throw createRequestError("invalid_payload", `响应缺少字段: ${missingFields.join(", ")}`);
  }
}

function getModeCopy(mode) {
  return MODE_COPY[mode] || MODE_COPY.idle;
}

function getAnswerCaption(mode) {
  if (mode === "strong") {
    return "可直接参考的回答已生成，建议先看正文，再核对主依据。";
  }
  if (mode === "weak_with_review_notice") {
    return "这是需核对的回答，请务必结合核对提示与核对材料阅读。";
  }
  if (mode === "refuse") {
    return "当前不支持这样回答；请先看拒答原因与改问建议。";
  }
  if (mode === "loading") {
    return "系统已收到问题，正在为当前会话生成下一条回答。";
  }
  return "当前结果正在等待进一步操作。";
}

function formatDateTime(value) {
  if (!value) {
    return "刚刚";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "时间未知";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatConversationTurns(messageCount) {
  const turns = Math.max(0, Math.floor(Number(messageCount || 0) / 2));
  return `${turns} 轮`;
}

function buildConversationPath(conversationId) {
  return conversationId ? `/chat/${encodeURIComponent(conversationId)}` : "/";
}

function parseConversationIdFromLocation() {
  const path = window.location.pathname.replace(/\/+$/, "");
  if (!path || path === "") {
    return null;
  }
  if (path === "/chat") {
    return null;
  }
  const chatMatch = path.match(/^\/chat\/([^/]+)$/);
  if (!chatMatch) {
    return null;
  }
  return decodeURIComponent(chatMatch[1]);
}

function updateBrowserLocation(conversationId, options = {}) {
  const { replace = false } = options;
  const nextPath = buildConversationPath(conversationId);
  const method = replace ? "replaceState" : "pushState";
  if (window.location.pathname === nextPath) {
    return;
  }
  window.history[method]({ conversationId }, "", nextPath);
}

async function readJsonSafely(response) {
  try {
    return await response.json();
  } catch (error) {
    return null;
  }
}

async function fetchJson(url, options = {}) {
  let response;

  try {
    response = await fetch(url, options);
  } catch (error) {
    throw createRequestError("network_error", "请求未成功返回，请确认本地服务仍在运行。");
  }

  const payload = await readJsonSafely(response);
  if (!response.ok) {
    throw createRequestError(
      "response_error",
      payload?.error?.message || "请求失败。",
      { status: response.status, payload },
    );
  }
  if (!payload) {
    throw createRequestError("invalid_json", "服务返回了不可解析的 JSON。");
  }
  return payload;
}

async function apiListConversations(search) {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJson(`${CONVERSATIONS_API_PATH}${query}`);
}

async function apiCreateConversation() {
  return fetchJson(CONVERSATIONS_API_PATH, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  });
}

async function apiGetConversation(conversationId) {
  return fetchJson(`${CONVERSATIONS_API_PATH}/${encodeURIComponent(conversationId)}`);
}

async function apiDeleteConversation(conversationId) {
  return fetchJson(`${CONVERSATIONS_API_PATH}/${encodeURIComponent(conversationId)}`, {
    method: "DELETE",
  });
}

async function apiSendConversationMessage(conversationId, query) {
  return fetchJson(`${CONVERSATIONS_API_PATH}/${encodeURIComponent(conversationId)}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });
}

function buildCountBadge(count) {
  const badge = createTag("span", "section-count", `${count}条`);
  return badge;
}

function buildPanelHead(title, count, hint) {
  const head = createTag("div", "panel-head");
  const copyWrap = createTag("div", "");
  const heading = createTag("h3", "", title);
  if (count > 0) {
    heading.append(buildCountBadge(count));
  }
  copyWrap.append(heading);
  if (hint) {
    copyWrap.append(createTag("p", "", hint));
  }
  head.append(copyWrap);
  return head;
}

function createEvidenceCard(item) {
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

  if (item.chapter_title) {
    meta.append(createTag("span", "chip", item.chapter_title));
  }

  if (displayTitle) {
    card.append(createTag("h3", "", displayTitle));
  }

  card.append(meta);

  if (item.snippet) {
    card.append(createTag("p", "snippet", item.snippet));
  }

  if (Array.isArray(item.risk_flags) && item.risk_flags.length > 0) {
    const riskList = createTag("ul", "risk-flags");
    item.risk_flags.forEach((flag) => {
      riskList.append(createTag("li", "", flag));
    });
    card.append(riskList);
  }

  const footer = createTag("div", "evidence-footer");
  footer.append(createTag("p", "record-footnote", `record_id: ${item.record_id}`));
  card.append(footer);

  return card;
}

function createCitationItem(citation) {
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

  if (citation.chapter_title) {
    meta.append(createTag("span", "chip", citation.chapter_title));
  }

  if (titleText) {
    item.append(createTag("h3", "", titleText));
  }
  item.append(meta);

  if (citation.snippet) {
    item.append(createTag("p", "citation-snippet", citation.snippet));
  }

  const footer = createTag("div", "citation-footer");
  footer.append(createTag("p", "record-footnote", `record_id: ${citation.record_id}`));
  item.append(footer);
  return item;
}

function createEvidencePanel(title, hint, items, className) {
  const section = createTag("section", `support-panel ${className}`.trim());
  section.append(buildPanelHead(title, items.length, hint));
  const list = createTag("div", "evidence-list");
  items.forEach((item) => {
    list.append(createEvidenceCard(item));
  });
  section.append(list);
  return section;
}

function createCitationsPanel(items, hint) {
  const section = createTag("section", "support-panel");
  section.append(buildPanelHead("回答引用", items.length, hint));
  const list = createTag("ol", "citation-list");
  items.forEach((item) => {
    list.append(createCitationItem(item));
  });
  section.append(list);
  return section;
}

function createFollowupsPanel(items, hint) {
  const section = createTag("section", "support-panel");
  section.append(buildPanelHead("改问建议", items.length, hint));
  const list = createTag("ul", "followups-list");
  items.forEach((text) => {
    list.append(createTag("li", "", text));
  });
  section.append(list);
  return section;
}

function createCallout(title, bodyText, className) {
  const section = createTag("section", `callout ${className}`.trim());
  const head = createTag("div", "panel-head");
  head.append(createTag("h3", "", title));
  section.append(head, createTag("p", "", bodyText));
  return section;
}

function createModeSummary(mode) {
  const copy = getModeCopy(mode);
  const summary = createTag("section", `mode-summary mode-summary-${mode || "idle"}`);
  const copyWrap = createTag("div", "mode-summary-copy");
  copyWrap.append(
    createTag("p", "mode-summary-kicker", "结果状态"),
    createTag("h4", "", copy.title),
    createTag("p", "mode-description", copy.description),
  );
  summary.append(copyWrap, createTag("p", "mode-reading-hint", copy.hint));
  return summary;
}

function buildSupportingHint(answerMode, slot) {
  if (slot === "primary") {
    return answerMode === "strong"
      ? "这些条目直接支撑上方回答，应优先作为正式依据阅读。"
      : "当前结果没有可直接作为主依据展示的条目。";
  }
  if (slot === "secondary") {
    return answerMode === "weak_with_review_notice"
      ? "这些条目是当前可先参考的线索，但仍不能替代确定答案。"
      : "这些条目用于补充理解，不替代主依据。";
  }
  if (slot === "review") {
    return answerMode === "weak_with_review_notice"
      ? "这些材料只用于进一步核对边界与出处，避免把弱结论误当成确定答案。"
      : "这些材料用于复核出处与风险点。";
  }
  if (slot === "citations") {
    return answerMode === "weak_with_review_notice"
      ? "这些引用对应当前弱整理与核对材料，不等于已确认结论。"
      : "这些引用与当前回答和证据区块直接对应，便于回看出处。";
  }
  return answerMode === "refuse"
    ? "当前问题不适合直接作答，可优先按这些方向继续追问。"
    : "当前问题如果还想继续收窄，可以从这些方向继续追问。";
}

function createUserMessageCard(message, options = {}) {
  const { pending = false } = options;
  const article = createTag("article", `message-card user-message${pending ? " pending-card" : ""}`);
  const head = createTag("div", "message-head");
  const copy = createTag("div", "message-head-copy");
  copy.append(
    createTag("p", "message-role", pending ? "当前发送中" : "本轮问题"),
    createTag("h3", "", pending ? "用户消息（待写入）" : "用户提问"),
    createTag("p", "message-time", formatDateTime(message.created_at)),
  );
  head.append(copy, createTag("span", "message-tag", "user"));
  article.append(head, createTag("p", "user-bubble", message.content || ""));
  return article;
}

function createAssistantMessageCard(message) {
  const payload = message.answer_payload;
  validatePayload(payload);

  const primary = Array.isArray(payload.primary_evidence) ? payload.primary_evidence : [];
  const secondary = Array.isArray(payload.secondary_evidence) ? payload.secondary_evidence : [];
  const review = Array.isArray(payload.review_materials) ? payload.review_materials : [];
  const citations = Array.isArray(payload.citations) ? payload.citations : [];
  const followups = Array.isArray(payload.suggested_followup_questions)
    ? payload.suggested_followup_questions
    : [];
  const modeCopy = getModeCopy(payload.answer_mode);

  const article = createTag("article", "message-card assistant-message");
  const head = createTag("div", "message-head assistant-head");
  const copy = createTag("div", "message-head-copy");
  copy.append(
    createTag("p", "message-role", "assistant response"),
    createTag("h3", "", "研读助手"),
    createTag("p", "message-time", formatDateTime(message.created_at)),
  );
  const badge = createTag("span", `mode-badge mode-${payload.answer_mode || "idle"}`, modeCopy.badge);
  head.append(copy, badge);
  article.append(head);

  const main = createTag("div", "assistant-main");
  main.append(createTag("p", "assistant-caption", getAnswerCaption(payload.answer_mode)));

  const answerBlock = createTag("section", "answer-block");
  answerBlock.append(
    createTag("p", "answer-block-label", "回答正文"),
    createTag("p", "answer-text", payload.answer_text || ""),
  );
  main.append(answerBlock);

  if (payload.disclaimer) {
    main.append(createTag("p", "disclaimer-text", payload.disclaimer));
  }
  main.append(createModeSummary(payload.answer_mode));
  article.append(main);

  if (payload.review_notice || payload.refuse_reason) {
    const callouts = createTag("div", "assistant-callouts");
    if (payload.review_notice) {
      callouts.append(createCallout("核对提示", payload.review_notice, "callout-review"));
    }
    if (payload.refuse_reason) {
      callouts.append(createCallout("拒答原因", payload.refuse_reason, "callout-refuse"));
    }
    article.append(callouts);
  }

  const supporting = createTag("section", "assistant-supporting");
  const supportingHead = createTag("div", "assistant-supporting-head");
  supportingHead.append(
    createTag("p", "supporting-kicker", "依据与附加信息"),
    createTag("p", "supporting-note", "这些信息会随当前 assistant 消息一起恢复。"),
  );
  supporting.append(supportingHead);

  if (primary.length === 0 && secondary.length === 0 && review.length === 0 && citations.length === 0 && followups.length === 0) {
    const emptyPanel = createTag("section", "support-panel");
    emptyPanel.append(createTag("p", "state-copy", "当前结果没有可展示证据。若为拒答模式，这是预期行为。"));
    supporting.append(emptyPanel);
  } else {
    if (primary.length > 0) {
      supporting.append(
        createEvidencePanel("主依据", buildSupportingHint(payload.answer_mode, "primary"), primary, "primary-panel"),
      );
    }
    if (secondary.length > 0) {
      supporting.append(
        createEvidencePanel("补充依据", buildSupportingHint(payload.answer_mode, "secondary"), secondary, ""),
      );
    }
    if (review.length > 0) {
      supporting.append(
        createEvidencePanel("核对材料", buildSupportingHint(payload.answer_mode, "review"), review, "review-panel"),
      );
    }
    if (citations.length > 0) {
      supporting.append(createCitationsPanel(citations, buildSupportingHint(payload.answer_mode, "citations")));
    }
    if (followups.length > 0) {
      supporting.append(createFollowupsPanel(followups, buildSupportingHint(payload.answer_mode, "followups")));
    }
  }

  article.append(supporting);
  return article;
}

function createBrokenAssistantCard(message, error) {
  const article = createTag("article", "message-card assistant-message");
  const head = createTag("div", "message-head");
  const copy = createTag("div", "message-head-copy");
  copy.append(
    createTag("p", "message-role", "assistant response"),
    createTag("h3", "", "研读助手"),
    createTag("p", "message-time", formatDateTime(message.created_at)),
  );
  head.append(copy, createTag("span", "mode-badge mode-error", "渲染失败"));
  article.append(head);

  const main = createTag("div", "assistant-main");
  main.append(createTag("p", "assistant-caption", "这条历史消息已恢复，但其 answer payload 无法完整渲染。"));
  const answerBlock = createTag("section", "answer-block");
  answerBlock.append(
    createTag("p", "answer-block-label", "已保存文本"),
    createTag("p", "answer-text", message.content || "无正文内容"),
  );
  main.append(answerBlock);
  main.append(createModeSummary("error"));
  article.append(main);

  const callouts = createTag("div", "assistant-callouts");
  callouts.append(
    createCallout("渲染异常", error?.message || "这条历史消息的结构不完整。", "callout-refuse"),
  );
  article.append(callouts);
  return article;
}

function createPendingAssistantCard() {
  const article = createTag("article", "message-card assistant-message pending-card");
  const head = createTag("div", "message-head");
  const copy = createTag("div", "message-head-copy");
  copy.append(
    createTag("p", "message-role", "assistant response"),
    createTag("h3", "", "研读助手"),
    createTag("p", "message-time", "正在生成中"),
  );
  head.append(copy, createTag("span", "mode-badge mode-loading", MODE_COPY.loading.badge));
  article.append(head);

  const main = createTag("div", "assistant-main");
  main.append(createTag("p", "assistant-caption", getAnswerCaption("loading")));
  const answerBlock = createTag("section", "answer-block");
  answerBlock.append(
    createTag("p", "answer-block-label", "回答正文"),
    createTag("p", "answer-text pending-answer-copy", "正在检索依据并生成回答…"),
  );
  main.append(answerBlock);
  main.append(createModeSummary("loading"));
  article.append(main);
  return article;
}

function renderHistoryList() {
  clearList(refs.conversationList);
  refs.historySearch.disabled = state.sending;
  refs.newChatButton.disabled = state.sending;

  const isSearching = Boolean(state.historySearch);
  showSection(refs.historyLoading, state.conversationsLoading);
  showSection(refs.historyEmpty, !state.conversationsLoading && state.conversations.length === 0 && !isSearching);
  showSection(refs.historyNoResults, !state.conversationsLoading && state.conversations.length === 0 && isSearching);

  if (state.conversationsLoading) {
    refs.historyStatus.textContent = isSearching
      ? `正在搜索“${state.historySearch}”…`
      : "正在加载历史会话…";
    return;
  }

  if (state.conversations.length === 0) {
    refs.historyStatus.textContent = isSearching ? `没有匹配“${state.historySearch}”的会话` : "还没有历史会话";
    return;
  }

  refs.historyStatus.textContent = isSearching
    ? `共找到 ${state.conversations.length} 条匹配会话`
    : `共 ${state.conversations.length} 条历史会话`;

  state.conversations.forEach((conversation) => {
    const item = createTag(
      "li",
      `conversation-item${conversation.id === state.activeConversationId ? " is-active" : ""}`,
    );

    const button = createTag("button", "conversation-item-button");
    button.type = "button";
    button.disabled = state.sending;
    button.addEventListener("click", () => {
      void openConversation(conversation.id);
    });

    const title = createTag("p", "conversation-item-title", conversation.title || "新对话");
    const meta = createTag("div", "conversation-item-meta");
    meta.append(
      createTag("span", "conversation-item-time", formatDateTime(conversation.updated_at || conversation.created_at)),
      createTag("span", "conversation-item-count", formatConversationTurns(conversation.message_count)),
    );

    button.append(title, meta);
    item.append(button);

    const menu = createTag("details", "conversation-menu");
    const summary = createTag("summary", "conversation-menu-summary", "⋯");
    if (state.sending) {
      summary.setAttribute("disabled", "disabled");
    }
    summary.addEventListener("click", (event) => {
      if (state.sending) {
        event.preventDefault();
      }
    });
    menu.append(summary);

    const panel = createTag("div", "conversation-menu-panel");
    const deleteButton = createTag(
      "button",
      "conversation-menu-action",
      state.deletingConversationId === conversation.id ? "Deleting…" : "Delete",
    );
    deleteButton.type = "button";
    deleteButton.disabled = state.sending || state.deletingConversationId === conversation.id;
    deleteButton.addEventListener("click", (event) => {
      event.preventDefault();
      menu.open = false;
      void handleDeleteConversation(conversation.id);
    });
    panel.append(deleteButton);
    menu.append(panel);
    item.append(menu);

    refs.conversationList.append(item);
  });
}

function renderConversationHeader() {
  const conversation = state.activeConversation?.conversation;

  if (state.conversationLoading) {
    refs.conversationTitle.textContent = "正在恢复会话…";
    refs.conversationSubtitle.textContent = "正在读取当前会话的完整消息流，请稍候。";
    return;
  }

  if (!conversation) {
    refs.conversationTitle.textContent = "新对话";
    refs.conversationSubtitle.textContent =
      "主区会展示当前会话的完整消息流；点击左侧历史项可恢复旧会话并继续发送。";
    return;
  }

  refs.conversationTitle.textContent = conversation.title || "新对话";
  if ((state.activeConversation?.messages || []).length === 0 && !state.pendingTurn) {
    refs.conversationSubtitle.textContent = "当前会话已创建，尚无消息。发送首轮问题后会自动生成标题并写入历史。";
    return;
  }

  refs.conversationSubtitle.textContent = `共 ${conversation.message_count} 条消息 · 最近更新 ${formatDateTime(
    conversation.updated_at || conversation.created_at,
  )}`;
}

function renderConversationBody() {
  renderConversationHeader();
  setComposerDisabled(state.sending || state.conversationLoading);

  showSection(refs.conversationLoading, state.conversationLoading);

  if (state.conversationLoading) {
    showSection(refs.conversationEmpty, false);
    showSection(refs.messageFeed, false);
    clearList(refs.messageFeed);
    return;
  }

  const confirmedMessages = state.activeConversation?.messages || [];
  const hasMessages = confirmedMessages.length > 0 || Boolean(state.pendingTurn);

  if (!state.activeConversationId || !state.activeConversation) {
    refs.conversationEmpty.querySelector(".state-title").textContent = "从下方输入框开始新会话，或打开左侧历史";
    refs.conversationEmpty.querySelector(".state-copy").textContent =
      "首轮发送后会自动生成会话标题；之后你可以从左侧搜索标题或消息内容，再点回对应会话继续聊天。";
    showSection(refs.conversationEmpty, true);
    showSection(refs.messageFeed, false);
    clearList(refs.messageFeed);
    return;
  }

  if (!hasMessages) {
    refs.conversationEmpty.querySelector(".state-title").textContent = "当前会话还没有消息";
    refs.conversationEmpty.querySelector(".state-copy").textContent =
      "现在就可以发送第一条问题。首轮完成后，左侧会话标题会自动改成首问摘要。";
    showSection(refs.conversationEmpty, true);
    showSection(refs.messageFeed, false);
    clearList(refs.messageFeed);
    return;
  }

  showSection(refs.conversationEmpty, false);
  showSection(refs.messageFeed, true);
  clearList(refs.messageFeed);

  confirmedMessages.forEach((message) => {
    if (message.role === "user") {
      refs.messageFeed.append(createUserMessageCard(message));
      return;
    }

    try {
      refs.messageFeed.append(createAssistantMessageCard(message));
    } catch (error) {
      console.error(error);
      refs.messageFeed.append(createBrokenAssistantCard(message, error));
    }
  });

  if (state.pendingTurn) {
    refs.messageFeed.append(createUserMessageCard(state.pendingTurn, { pending: true }));
    refs.messageFeed.append(createPendingAssistantCard());
  }
}

function scrollConversationBodyToTop() {
  if (!refs.chatBody) {
    return;
  }
  window.requestAnimationFrame(() => {
    refs.chatBody.scrollTo({
      top: 0,
      behavior: "auto",
    });
  });
}

function scrollFeedToBottom() {
  if (!refs.chatBody) {
    return;
  }
  window.requestAnimationFrame(() => {
    refs.chatBody.scrollTo({
      top: refs.chatBody.scrollHeight,
      behavior: "smooth",
    });
  });
}

function clearActiveConversationState() {
  state.conversationRequestSeq += 1;
  state.activeConversationId = null;
  state.activeConversation = null;
  state.pendingTurn = null;
  state.conversationLoading = false;
}

function syncActiveConversationSummaryFromList() {
  if (!state.activeConversation?.conversation) {
    return;
  }
  const updated = state.conversations.find((item) => item.id === state.activeConversation.conversation.id);
  if (updated) {
    state.activeConversation.conversation = {
      ...state.activeConversation.conversation,
      ...updated,
    };
  }
}

async function refreshConversationList(search = state.historySearch) {
  state.historySearch = search.trim();
  const requestSeq = state.historyRequestSeq + 1;
  state.historyRequestSeq = requestSeq;
  state.conversationsLoading = true;
  renderHistoryList();

  try {
    const payload = await apiListConversations(state.historySearch);
    if (requestSeq !== state.historyRequestSeq) {
      return;
    }
    state.conversations = Array.isArray(payload.items) ? payload.items : [];
    state.conversationsLoading = false;
    syncActiveConversationSummaryFromList();
    renderHistoryList();
    renderConversationHeader();
  } catch (error) {
    if (requestSeq !== state.historyRequestSeq) {
      return;
    }
    console.error(error);
    state.conversations = [];
    state.conversationsLoading = false;
    renderHistoryList();
    setError(error.message || "历史会话加载失败。");
    setStatus("历史会话加载失败");
  }
}

async function openConversation(conversationId, options = {}) {
  const { updateUrl = true, replaceUrl = false } = options;

  if (!conversationId) {
    clearActiveConversationState();
    if (updateUrl) {
      updateBrowserLocation(null, { replace: replaceUrl });
    }
    renderHistoryList();
    renderConversationBody();
    scrollConversationBodyToTop();
    return;
  }

  if (state.sending) {
    return;
  }

  if (state.activeConversation?.conversation?.id === conversationId && !state.conversationLoading) {
    if (updateUrl) {
      updateBrowserLocation(conversationId, { replace: replaceUrl });
    }
    return;
  }

  const requestSeq = state.conversationRequestSeq + 1;
  state.conversationRequestSeq = requestSeq;
  state.activeConversationId = conversationId;
  state.conversationLoading = true;
  state.pendingTurn = null;
  setError("");
  setStatus("正在恢复历史会话…");
  if (updateUrl) {
    updateBrowserLocation(conversationId, { replace: replaceUrl });
  }
  renderHistoryList();
  renderConversationBody();

  try {
    const payload = await apiGetConversation(conversationId);
    if (requestSeq !== state.conversationRequestSeq) {
      return;
    }
    state.activeConversation = {
      conversation: payload.conversation,
      messages: Array.isArray(payload.messages) ? payload.messages : [],
    };
    state.activeConversationId = payload.conversation.id;
    state.conversationLoading = false;
    syncActiveConversationSummaryFromList();
    renderHistoryList();
    renderConversationBody();
    setStatus("历史会话已恢复，可继续发送");
    scrollFeedToBottom();
  } catch (error) {
    if (requestSeq !== state.conversationRequestSeq) {
      return;
    }
    console.error(error);
    state.conversationLoading = false;
    if (error.status === 404) {
      state.activeConversationId = null;
      state.activeConversation = null;
      updateBrowserLocation(null, { replace: true });
      setError("要打开的会话不存在，已返回空白会话页。");
      setStatus("会话不存在");
    } else {
      setError(error.message || "会话恢复失败。");
      setStatus("会话恢复失败");
    }
    renderHistoryList();
    renderConversationBody();
  }
}

async function createAndActivateConversation(options = {}) {
  const { silent = false } = options;

  if (!silent) {
    setStatus("正在创建新会话…");
    setError("");
  }

  const payload = await apiCreateConversation();
  const conversation = payload.conversation;
  refs.historySearch.value = "";
  state.activeConversationId = conversation.id;
  state.activeConversation = {
    conversation,
    messages: [],
  };
  updateBrowserLocation(conversation.id);
  await refreshConversationList("");
  renderHistoryList();
  renderConversationBody();
  if (!silent) {
    setStatus("已创建新会话，可以开始提问");
  }
  return conversation;
}

async function handleNewChat() {
  if (state.sending) {
    return;
  }

  try {
    const shouldRefreshHistory = state.conversationsLoading || Boolean(state.historySearch);
    refs.historySearch.value = "";
    state.historySearch = "";
    clearActiveConversationState();
    resetComposerState();
    setError("");
    setStatus("已回到空白新对话，可直接输入第一条问题");
    updateBrowserLocation(null);
    renderHistoryList();
    renderConversationBody();
    scrollConversationBodyToTop();
    if (shouldRefreshHistory) {
      await refreshConversationList("");
    }
    refs.queryInput.focus();
  } catch (error) {
    console.error(error);
    setError(error.message || "新对话复位失败。");
    setStatus("新对话复位失败");
  }
}

async function handleDeleteConversation(conversationId) {
  if (state.sending || state.deletingConversationId) {
    return;
  }

  const conversation =
    state.conversations.find((item) => item.id === conversationId) || state.activeConversation?.conversation;
  const confirmed = window.confirm(`确定删除“${conversation?.title || "当前会话"}”吗？此操作不可撤销。`);
  if (!confirmed) {
    return;
  }

  state.deletingConversationId = conversationId;
  renderHistoryList();
  setError("");
  setStatus("正在删除会话…");

  try {
    await apiDeleteConversation(conversationId);
    const deletedActive = state.activeConversationId === conversationId;
    if (deletedActive) {
      clearActiveConversationState();
      updateBrowserLocation(null, { replace: true });
    }

    await refreshConversationList(state.historySearch);
    if (deletedActive) {
      renderConversationBody();
      scrollConversationBodyToTop();
    }
    setStatus("会话已删除");
  } catch (error) {
    console.error(error);
    setError(error.message || "会话删除失败。");
    setStatus("会话删除失败");
  } finally {
    state.deletingConversationId = null;
    renderHistoryList();
  }
}

async function ensureConversationForSend() {
  if (state.activeConversationId && state.activeConversation) {
    return state.activeConversationId;
  }
  const conversation = await createAndActivateConversation({ silent: true });
  return conversation.id;
}

async function submitCurrentQuery(query) {
  if (!query) {
    setError("请输入问题后再发送。");
    setStatus("请先输入问题");
    return;
  }

  if (state.sending) {
    return;
  }

  let conversationId;
  try {
    conversationId = await ensureConversationForSend();
  } catch (error) {
    console.error(error);
    setError(error.message || "当前无法创建新会话。");
    setStatus("发送前创建会话失败");
    return;
  }

  state.sending = true;
  state.pendingTurn = {
    role: "user",
    content: query,
    created_at: new Date().toISOString(),
  };
  setError("");
  setStatus("正在为当前会话生成回答…");
  renderHistoryList();
  renderConversationBody();
  scrollFeedToBottom();

  try {
    const payload = await apiSendConversationMessage(conversationId, query);
    const existingMessages = state.activeConversation?.messages || [];
    state.activeConversation = {
      conversation: payload.conversation,
      messages: existingMessages.concat(Array.isArray(payload.messages) ? payload.messages : []),
    };
    state.activeConversationId = payload.conversation.id;
    state.pendingTurn = null;
    refs.queryInput.value = "";
    await refreshConversationList(state.historySearch);
    renderConversationBody();
    setStatus("回答已写入当前会话");
    refs.queryInput.focus();
    scrollFeedToBottom();
  } catch (error) {
    console.error(error);
    state.pendingTurn = null;
    renderConversationBody();
    setError(error.message || "本次消息未能成功写入会话。");
    setStatus("本次消息未发送成功");
  } finally {
    state.sending = false;
    renderHistoryList();
    renderConversationBody();
  }
}

function scheduleHistorySearch() {
  if (state.historySearchTimer) {
    window.clearTimeout(state.historySearchTimer);
  }
  state.historySearchTimer = window.setTimeout(() => {
    void refreshConversationList(refs.historySearch.value);
  }, HISTORY_SEARCH_DEBOUNCE_MS);
}

function handlePopState() {
  if (state.sending) {
    updateBrowserLocation(state.activeConversationId, { replace: true });
    return;
  }

  const conversationId = parseConversationIdFromLocation();
  if (!conversationId) {
    void openConversation(null, { updateUrl: false });
    return;
  }
  void openConversation(conversationId, { updateUrl: false });
}

async function boot() {
  refs.newChatButton = requireElement("new-chat-button");
  refs.historySearch = requireElement("history-search");
  refs.historyStatus = requireElement("history-status");
  refs.historyLoading = requireElement("history-loading");
  refs.historyEmpty = requireElement("history-empty");
  refs.historyNoResults = requireElement("history-no-results");
  refs.conversationList = requireElement("conversation-list");
  refs.conversationTitle = requireElement("conversation-title");
  refs.conversationSubtitle = requireElement("conversation-subtitle");
  refs.statusText = requireElement("status-text");
  refs.errorText = requireElement("error-text");
  refs.chatBody = requireElement("chat-body");
  refs.conversationLoading = requireElement("conversation-loading");
  refs.conversationEmpty = requireElement("conversation-empty");
  refs.messageFeed = requireElement("message-feed");
  refs.form = requireElement("query-form");
  refs.queryInput = requireElement("query-input");
  refs.submitButton = requireElement("submit-button");
  refs.sampleQueries = document.querySelector(".sample-queries");
  refs.sampleButtons = Array.from(document.querySelectorAll(".sample-chip"));

  refs.newChatButton.addEventListener("click", () => {
    void handleNewChat();
  });

  refs.historySearch.addEventListener("input", () => {
    scheduleHistorySearch();
  });

  refs.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitCurrentQuery(refs.queryInput.value.trim());
  });

  refs.queryInput.addEventListener("keydown", (event) => {
    const shouldSubmit =
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.isComposing;

    if (!shouldSubmit || state.sending) {
      return;
    }
    event.preventDefault();
    refs.form.requestSubmit();
  });

  refs.sampleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const query = button.dataset.query || "";
      refs.queryInput.value = query;
      refs.queryInput.focus();
      refs.queryInput.setSelectionRange(query.length, query.length);
      setError("");
      setStatus("样例已填充，可继续发送到当前会话");
    });
  });

  window.addEventListener("popstate", handlePopState);

  renderHistoryList();
  renderConversationBody();
  setStatus("正在加载历史会话…");

  await refreshConversationList("");

  const conversationId = parseConversationIdFromLocation();
  if (conversationId) {
    await openConversation(conversationId, { updateUrl: false });
  } else {
    renderConversationBody();
    setStatus("前端脚本已加载，可从空白会话开始，也可打开左侧历史");
  }

  window.__frontendTestHooks = {
    parseConversationIdFromLocation,
    validatePayload,
    resolveRecordTitle,
    titlesTooSimilar,
  };
  window.__frontendBooted = true;
}

boot().catch((error) => {
  console.error(error);
  setError(error.message || "前端初始化失败。");
  setStatus("前端初始化失败");
});
