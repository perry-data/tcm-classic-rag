const form = document.getElementById("query-form");
const queryInput = document.getElementById("query-input");
const submitButton = document.getElementById("submit-button");
const statusText = document.getElementById("status-text");
const errorText = document.getElementById("error-text");
const modeBadge = document.getElementById("mode-badge");
const queryEcho = document.getElementById("query-echo");
const answerCaption = document.getElementById("answer-caption");
const answerText = document.getElementById("answer-text");
const disclaimerText = document.getElementById("disclaimer-text");
const reviewNoticeSection = document.getElementById("review-notice-section");
const reviewNoticeText = document.getElementById("review-notice-text");
const refuseSection = document.getElementById("refuse-section");
const refuseReasonText = document.getElementById("refuse-reason-text");
const emptyEvidenceSection = document.getElementById("empty-evidence-section");
const primarySection = document.getElementById("primary-section");
const primaryList = document.getElementById("primary-list");
const secondarySection = document.getElementById("secondary-section");
const secondaryList = document.getElementById("secondary-list");
const reviewSection = document.getElementById("review-section");
const reviewList = document.getElementById("review-list");
const citationsSection = document.getElementById("citations-section");
const citationsList = document.getElementById("citations-list");
const followupsSection = document.getElementById("followups-section");
const followupsList = document.getElementById("followups-list");
const sampleButtons = Array.from(document.querySelectorAll(".sample-chip"));

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

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "查询中…" : "提交查询";
  if (isLoading) {
    statusText.textContent = "正在请求 /api/v1/answers";
  }
}

function setError(message) {
  errorText.textContent = message || "";
  if (message) {
    statusText.textContent = "请求失败";
  }
}

function setModeBadge(mode) {
  modeBadge.className = `mode-badge mode-${mode || "idle"}`;
  modeBadge.textContent = mode || "idle";
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
  clearList(citationsList);
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

  citationsList.append(fragment);
}

function renderFollowups(items) {
  clearList(followupsList);
  const fragment = document.createDocumentFragment();
  items.forEach((text) => {
    fragment.append(createTag("li", "", text));
  });
  followupsList.append(fragment);
}

function validatePayload(payload) {
  const missingFields = REQUIRED_TOP_FIELDS.filter((field) => !(field in payload));
  if (missingFields.length > 0) {
    throw new Error(`响应缺少字段: ${missingFields.join(", ")}`);
  }
}

function renderPayload(payload) {
  validatePayload(payload);
  setModeBadge(payload.answer_mode);
  queryEcho.textContent = payload.query || "未返回 query";
  answerText.textContent = payload.answer_text || "";
  disclaimerText.textContent = payload.disclaimer || "";

  if (payload.answer_mode === "strong") {
    answerCaption.textContent = "当前结果为 strong，优先展示主依据。";
  } else if (payload.answer_mode === "weak_with_review_notice") {
    answerCaption.textContent = "当前结果为 weak_with_review_notice，以下内容需核对。";
  } else if (payload.answer_mode === "refuse") {
    answerCaption.textContent = "当前结果为 refuse，不输出确定性答案。";
  } else {
    answerCaption.textContent = "返回了未识别模式。";
  }

  reviewNoticeText.textContent = payload.review_notice || "";
  refuseReasonText.textContent = payload.refuse_reason || "";

  const primary = Array.isArray(payload.primary_evidence) ? payload.primary_evidence : [];
  const secondary = Array.isArray(payload.secondary_evidence) ? payload.secondary_evidence : [];
  const review = Array.isArray(payload.review_materials) ? payload.review_materials : [];
  const citations = Array.isArray(payload.citations) ? payload.citations : [];
  const followups = Array.isArray(payload.suggested_followup_questions)
    ? payload.suggested_followup_questions
    : [];

  showSection(reviewNoticeSection, Boolean(payload.review_notice));
  showSection(refuseSection, Boolean(payload.refuse_reason));
  showSection(primarySection, primary.length > 0);
  showSection(secondarySection, secondary.length > 0);
  showSection(reviewSection, review.length > 0);
  showSection(citationsSection, citations.length > 0);
  showSection(followupsSection, followups.length > 0);
  showSection(emptyEvidenceSection, primary.length + secondary.length + review.length === 0);

  renderEvidenceList(primaryList, primary);
  renderEvidenceList(secondaryList, secondary);
  renderEvidenceList(reviewList, review);
  renderCitations(citations);
  renderFollowups(followups);
}

async function submitQuery(query) {
  setError("");
  setLoading(true);

  try {
    const response = await fetch("/api/v1/answers", {
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
    statusText.textContent = "请求已完成";
  } catch (error) {
    setError(error instanceof Error ? error.message : "请求失败");
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();

  if (!query) {
    setError("请输入问题后再提交。");
    return;
  }

  await submitQuery(query);
});

sampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const query = button.dataset.query || "";
    queryInput.value = query;
    queryInput.focus();
  });
});
