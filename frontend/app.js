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

function requireElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`页面缺少必要节点: #${id}`);
  }
  return element;
}

const refs = {};

function setLoading(isLoading) {
  refs.submitButton.disabled = isLoading;
  refs.submitButton.textContent = isLoading ? "查询中…" : "提交查询";
  if (isLoading) {
    refs.statusText.textContent = "正在请求 /api/v1/answers";
  }
}

function setError(message) {
  refs.errorText.textContent = message || "";
  if (message) {
    refs.statusText.textContent = "请求失败";
  }
}

function setModeBadge(mode) {
  refs.modeBadge.className = `mode-badge mode-${mode || "idle"}`;
  refs.modeBadge.textContent = mode || "idle";
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

function renderPayload(payload) {
  validatePayload(payload);
  window.__lastAnswerPayload = payload;
  setModeBadge(payload.answer_mode);
  refs.queryEcho.textContent = payload.query || "未返回 query";
  refs.answerText.textContent = payload.answer_text || "";
  refs.disclaimerText.textContent = payload.disclaimer || "";

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

async function submitQuery(query) {
  setError("");
  setLoading(true);
  window.__lastSubmitQuery = query;

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
    refs.statusText.textContent = "请求已完成";
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
