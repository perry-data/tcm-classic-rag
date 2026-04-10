const API_PATH = "/api/v1/answers";
const STREAM_API_PATH = "/api/v1/answers/stream";
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

function requireElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`页面缺少必要节点: #${id}`);
  }
  return element;
}

const refs = {};
const state = {
  streamedAnswerText: "",
  latestPayload: null,
};

function setLoading(isLoading) {
  refs.submitButton.disabled = isLoading;
  refs.submitButton.textContent = isLoading ? "查询中…" : "提交查询";
  if (isLoading) {
    refs.statusText.textContent = "已提交问题，正在准备回答";
  }
}

function setError(message) {
  refs.errorText.textContent = message || "";
  if (message) {
    refs.statusText.textContent = "请求失败";
    refs.answerText.classList.remove("is-streaming");
    if (refs.progressDetail) {
      refs.progressDetail.textContent = `请求失败：${message}`;
    }
  }
}

function setModeBadge(mode) {
  refs.modeBadge.className = `mode-badge mode-${mode || "idle"}`;
  refs.modeBadge.textContent = mode || "idle";
}

function setAnswerText(text, options = {}) {
  const { placeholder = false, streaming = false } = options;
  refs.answerText.textContent = text || "";
  refs.answerText.classList.toggle("empty-copy", placeholder);
  refs.answerText.classList.toggle("is-streaming", streaming);
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

function renderEvidenceList(target, items) {
  clearList(target);
  const fragment = document.createDocumentFragment();

  items.forEach((item) => {
    const card = createTag("article", "evidence-card");
    const title = createTag("h3", "", item.title || item.record_id);
    const meta = createTag("div", "evidence-meta");

    meta.append(
      createTag("span", "chip", `角色 ${item.display_role}`),
      createTag("span", "chip", `等级 ${item.evidence_level}`),
      createTag("span", "record-id", item.record_id),
    );

    if (item.chapter_title) {
      meta.append(createTag("span", "chip", item.chapter_title));
    }

    const snippet = createTag("p", "snippet", item.snippet || "");
    card.append(title, meta, snippet);

    if (Array.isArray(item.risk_flags) && item.risk_flags.length > 0) {
      const riskList = createTag("ul", "risk-flags");
      item.risk_flags.forEach((flag) => {
        riskList.append(createTag("li", "", flag));
      });
      card.append(riskList);
    }

    fragment.append(card);
  });

  target.append(fragment);
}

function renderCitations(items) {
  clearList(refs.citationsList);
  const fragment = document.createDocumentFragment();

  items.forEach((citation) => {
    const item = createTag("li", "citation-item");
    const title = createTag("h3", "", `${citation.citation_id} · ${citation.title}`);
    const meta = createTag("div", "citation-meta");
    meta.append(
      createTag("span", "role-chip", citation.citation_role),
      createTag("span", "chip", `等级 ${citation.evidence_level}`),
      createTag("span", "record-id", citation.record_id),
    );
    if (citation.chapter_title) {
      meta.append(createTag("span", "chip", citation.chapter_title));
    }
    const snippet = createTag("p", "citation-snippet", citation.snippet || "");
    item.append(title, meta, snippet);
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
    throw new Error(`响应缺少字段: ${missingFields.join(", ")}`);
  }
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

  const stageIndex = PROGRESS_STEPS.findIndex((item) => item.stage === stage);
  const label = PROGRESS_STEPS.find((item) => item.stage === stage)?.label || stage || "处理中";

  Array.from(refs.progressSteps.children).forEach((node, index) => {
    const marker = node.querySelector('[data-role="marker"]');
    const isComplete = stageIndex >= 0 && index < stageIndex;
    const isActive = stageIndex >= 0 && index === stageIndex && stage !== "completed";
    const isFinalComplete = stage === "completed" && index <= stageIndex;

    node.classList.toggle("is-complete", isComplete || isFinalComplete);
    node.classList.toggle("is-active", isActive);

    if (marker) {
      marker.textContent = isComplete || isFinalComplete ? "✓" : String(index + 1);
    }
  });

  refs.progressDetail.textContent = detail || label;
  refs.statusText.textContent = detail || label;
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

  showSection(refs.reviewNoticeSection, false);
  showSection(refs.refuseSection, false);
  showSection(refs.emptyEvidenceSection, false);
  showSection(refs.primarySection, false);
  showSection(refs.secondarySection, false);
  showSection(refs.reviewSection, false);
  showSection(refs.citationsSection, false);
  showSection(refs.followupsSection, false);
}

function resetViewForRequest(query) {
  state.streamedAnswerText = "";
  state.latestPayload = null;
  window.__lastAnswerPayload = null;
  window.__lastStreamEvent = null;

  refs.queryEcho.textContent = query;
  refs.answerCaption.textContent = "系统已收到问题，正在准备回答。";
  setModeBadge("loading");
  setAnswerText("已提交问题，正在准备回答…", { placeholder: true, streaming: true });
  resetResultSections();
  ensureProgressSteps();
  updateProgress("retrieving_evidence", "已提交问题，正在建立流式连接。");
}

function renderPayload(payload, options = {}) {
  const { preserveAnswerText = false } = options;
  validatePayload(payload);
  state.latestPayload = payload;
  window.__lastAnswerPayload = payload;
  setModeBadge(payload.answer_mode);
  refs.queryEcho.textContent = payload.query || "未返回 query";
  refs.disclaimerText.textContent = payload.disclaimer || "";

  if (!preserveAnswerText) {
    setAnswerText(payload.answer_text || "", {
      placeholder: !(payload.answer_text || ""),
      streaming: false,
    });
  }

  if (payload.answer_mode === "strong") {
    refs.answerCaption.textContent = "当前结果为 strong，优先展示主依据。";
  } else if (payload.answer_mode === "weak_with_review_notice") {
    refs.answerCaption.textContent = "当前结果为 weak_with_review_notice，以下内容需核对。";
  } else if (payload.answer_mode === "refuse") {
    refs.answerCaption.textContent = "当前结果为 refuse，不输出确定性答案。";
  } else {
    refs.answerCaption.textContent = "返回了未识别模式。";
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

  showSection(refs.reviewNoticeSection, Boolean(payload.review_notice));
  showSection(refs.refuseSection, Boolean(payload.refuse_reason));
  showSection(refs.primarySection, primary.length > 0);
  showSection(refs.secondarySection, secondary.length > 0);
  showSection(refs.reviewSection, review.length > 0);
  showSection(refs.citationsSection, citations.length > 0);
  showSection(refs.followupsSection, followups.length > 0);
  showSection(refs.emptyEvidenceSection, primary.length + secondary.length + review.length === 0);

  renderEvidenceList(refs.primaryList, primary);
  renderEvidenceList(refs.secondaryList, secondary);
  renderEvidenceList(refs.reviewList, review);
  renderCitations(citations);
  renderFollowups(followups);
}

function applyEvidenceReadyPayload(payload) {
  validatePayload(payload);
  state.latestPayload = payload;
  state.streamedAnswerText = "";
  setAnswerText("", { streaming: true });
  renderPayload(payload, { preserveAnswerText: true });
  refs.statusText.textContent = "依据已整理，正在渐进显示 answer_text";
}

function appendAnswerDelta(delta) {
  if (!delta) {
    return;
  }
  state.streamedAnswerText += delta;
  setAnswerText(state.streamedAnswerText, { streaming: true });
}

function handleStreamEvent(event) {
  if (!event || typeof event !== "object") {
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
    renderPayload(event.payload || state.latestPayload || {});
    updateProgress("completed", event.detail || "回答已完成。");
    refs.statusText.textContent = "请求已完成";
    return true;
  }

  if (event.type === "error") {
    throw new Error(event?.error?.message || "请求失败");
  }

  return false;
}

async function consumeNdjsonStream(response) {
  if (!response.body) {
    throw new Error("浏览器未提供可读流，无法进入流式渲染。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;

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
      completed = handleStreamEvent(event) || completed;
    }
  }

  buffer += decoder.decode();
  const trailingLine = buffer.trim();
  if (trailingLine) {
    const event = JSON.parse(trailingLine);
    completed = handleStreamEvent(event) || completed;
  }

  if (!completed) {
    throw new Error("流式响应提前结束，未收到 completed 事件。");
  }
}

async function submitQueryWithStream(query) {
  const response = await fetch(STREAM_API_PATH, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  const contentType = response.headers.get("Content-Type") || "";

  if (response.status === 404 || response.status === 405) {
    return false;
  }

  if (!response.ok) {
    if (contentType.includes("application/json")) {
      const payload = await response.json();
      throw new Error(payload?.error?.message || "请求失败");
    }
    throw new Error("请求失败");
  }

  if (!response.body || !contentType.includes("application/x-ndjson")) {
    return false;
  }

  await consumeNdjsonStream(response);
  return true;
}

async function submitQueryWithFallback(query) {
  refs.statusText.textContent = "流式接口不可用，正在回退到标准请求";
  updateProgress("retrieving_evidence", "流式接口不可用，已回退到标准请求。");

  try {
    const response = await fetch(API_PATH, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload?.error?.message || "请求失败");
    }

    renderPayload(payload);
    updateProgress("completed", "标准响应已返回。");
    refs.statusText.textContent = "请求已完成";
  } catch (error) {
    throw error;
  }
}

async function submitQuery(query) {
  setError("");
  setLoading(true);
  window.__lastSubmitQuery = query;
  resetViewForRequest(query);

  try {
    const streamed = await submitQueryWithStream(query);
    if (!streamed) {
      await submitQueryWithFallback(query);
    }
  } catch (error) {
    setError(error instanceof Error ? error.message : "请求失败");
    console.error(error);
  } finally {
    setLoading(false);
  }
}

function boot() {
  refs.form = requireElement("query-form");
  refs.queryInput = requireElement("query-input");
  refs.submitButton = requireElement("submit-button");
  refs.statusText = requireElement("status-text");
  refs.errorText = requireElement("error-text");
  refs.modeBadge = requireElement("mode-badge");
  refs.queryEcho = requireElement("query-echo");
  refs.answerCaption = requireElement("answer-caption");
  refs.progressSection = requireElement("progress-section");
  refs.progressDetail = requireElement("progress-detail");
  refs.progressSteps = requireElement("progress-steps");
  refs.answerText = requireElement("answer-text");
  refs.disclaimerText = requireElement("disclaimer-text");
  refs.reviewNoticeSection = requireElement("review-notice-section");
  refs.reviewNoticeText = requireElement("review-notice-text");
  refs.refuseSection = requireElement("refuse-section");
  refs.refuseReasonText = requireElement("refuse-reason-text");
  refs.emptyEvidenceSection = requireElement("empty-evidence-section");
  refs.primarySection = requireElement("primary-section");
  refs.primaryList = requireElement("primary-list");
  refs.secondarySection = requireElement("secondary-section");
  refs.secondaryList = requireElement("secondary-list");
  refs.reviewSection = requireElement("review-section");
  refs.reviewList = requireElement("review-list");
  refs.citationsSection = requireElement("citations-section");
  refs.citationsList = requireElement("citations-list");
  refs.followupsSection = requireElement("followups-section");
  refs.followupsList = requireElement("followups-list");
  refs.sampleButtons = Array.from(document.querySelectorAll(".sample-chip"));
  ensureProgressSteps();

  refs.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = refs.queryInput.value.trim();

    if (!query) {
      setError("请输入问题后再提交。");
      return;
    }

    await submitQuery(query);
  });

  refs.sampleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const query = button.dataset.query || "";
      refs.queryInput.value = query;
      refs.queryInput.focus();
      refs.statusText.textContent = "样例已填充，请点击“提交查询”发起请求";
    });
  });

  refs.statusText.textContent = "前端脚本已加载，等待提交";
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
