import type {
  AnswerMode,
  AnswerPayload,
  CitationItem,
  ConversationSummary,
  EvidenceItem,
  IndexedEvidenceItem,
} from "./types";

export const REQUIRED_TOP_FIELDS: Array<keyof AnswerPayload> = [
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

export const HISTORY_SEARCH_DEBOUNCE_MS = 180;
export const SIDEBAR_PREFERENCE_KEY = "tcm-classic-rag.sidebar-collapsed";
export const CLIENT_ID_STORAGE_KEY = "tcm_rag_client_id";
const CLIENT_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/;
const CLIENT_ID_PREFIX = "anon_";
let cachedClientId: string | null = null;

export const SAMPLE_QUERIES = [
  "黄连汤方的条文是什么？",
  "烧针益阳而损阴是什么意思？",
  "书中有没有提到量子纠缠？",
  "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
];

export const MODE_COPY = {
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
} as const;

const SOURCE_LABELS: Record<string, string> = {
  main_passages: "主文",
  annotations: "注解",
  passages: "全文",
  ambiguous_passages: "异文",
};

const ROLE_LABELS: Record<string, string> = {
  primary: "主依据",
  secondary: "补充依据",
  review: "核对材料",
};

const SOURCE_UNIT_LABELS: Record<string, string> = {
  main_passages: "条文",
  passages: "条文",
  ambiguous_passages: "异文",
  annotations: "注解",
  chunks: "片段",
};

const EVIDENCE_REF_RE = /\[(E\d+)\]/g;

export function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

export function validatePayload(payload: unknown): asserts payload is AnswerPayload {
  if (!payload || typeof payload !== "object") {
    throw new Error("响应 payload 不是对象。");
  }
  const missingFields = REQUIRED_TOP_FIELDS.filter((field) => !(field in payload));
  if (missingFields.length > 0) {
    throw new Error(`响应缺少字段: ${missingFields.join(", ")}`);
  }
}

export function getModeCopy(mode: AnswerMode | "idle" | "loading" | "error") {
  return MODE_COPY[mode] || MODE_COPY.idle;
}

export function formatDateTime(value: string | null | undefined): string {
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

function parseDateValue(value: string | null | undefined): Date | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function getCalendarDayDiff(laterDate: Date, earlierDate: Date): number {
  const laterDay = new Date(laterDate.getFullYear(), laterDate.getMonth(), laterDate.getDate());
  const earlierDay = new Date(earlierDate.getFullYear(), earlierDate.getMonth(), earlierDate.getDate());
  return Math.round((laterDay.getTime() - earlierDay.getTime()) / 86400000);
}

export function formatHistoryTimestamp(value: string | null | undefined): string {
  const date = parseDateValue(value);
  if (!date) {
    return "时间未知";
  }

  const now = new Date();
  const dayDiff = Math.max(0, getCalendarDayDiff(now, date));
  if (dayDiff <= 1) {
    return new Intl.DateTimeFormat("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }
  if (dayDiff < 7) {
    return new Intl.DateTimeFormat("zh-CN", {
      weekday: "short",
    }).format(date);
  }
  if (date.getFullYear() === now.getFullYear()) {
    return new Intl.DateTimeFormat("zh-CN", {
      month: "numeric",
      day: "numeric",
    }).format(date);
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "numeric",
    day: "numeric",
  }).format(date);
}

export function formatConversationTurns(messageCount: number): string {
  const turns = Math.max(0, Math.floor(Number(messageCount || 0) / 2));
  return `${turns} 轮`;
}

function resolveHistoryGroupInfo(value: string | null | undefined): { key: string; label: string } {
  const date = parseDateValue(value);
  if (!date) {
    return { key: "older", label: "更早" };
  }

  const dayDiff = Math.max(0, getCalendarDayDiff(new Date(), date));
  if (dayDiff === 0) {
    return { key: "today", label: "今天" };
  }
  if (dayDiff === 1) {
    return { key: "yesterday", label: "昨天" };
  }
  if (dayDiff < 7) {
    return { key: "recent", label: "最近 7 天" };
  }
  return { key: "older", label: "更早" };
}

export function groupConversationsForHistory(conversations: ConversationSummary[]) {
  const groups: Array<{ key: string; label: string; items: ConversationSummary[] }> = [];
  const groupMap = new Map<string, { key: string; label: string; items: ConversationSummary[] }>();

  conversations.forEach((conversation) => {
    const info = resolveHistoryGroupInfo(conversation.updated_at || conversation.created_at);
    let group = groupMap.get(info.key);
    if (!group) {
      group = { key: info.key, label: info.label, items: [] };
      groupMap.set(info.key, group);
      groups.push(group);
    }
    group.items.push(conversation);
  });

  return groups;
}

export function readSidebarCollapsedPreference(): boolean {
  try {
    return window.localStorage.getItem(SIDEBAR_PREFERENCE_KEY) === "1";
  } catch {
    return false;
  }
}

export function persistSidebarCollapsedPreference(collapsed: boolean): void {
  try {
    window.localStorage.setItem(SIDEBAR_PREFERENCE_KEY, collapsed ? "1" : "0");
  } catch {
    // Ignore persistence failures so the UI still works in restricted environments.
  }
}

function buildAnonymousClientId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return `${CLIENT_ID_PREFIX}${globalThis.crypto.randomUUID().replace(/-/g, "")}`;
  }

  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).slice(2, 18);
  return `${CLIENT_ID_PREFIX}${timestamp}${randomPart}`;
}

export function getOrCreateAnonymousClientId(): string {
  if (cachedClientId && CLIENT_ID_RE.test(cachedClientId)) {
    return cachedClientId;
  }

  try {
    const stored = window.localStorage.getItem(CLIENT_ID_STORAGE_KEY);
    if (stored && CLIENT_ID_RE.test(stored)) {
      cachedClientId = stored;
      return stored;
    }
  } catch {
    // Fall back to an in-memory id when storage is unavailable.
  }

  const clientId = buildAnonymousClientId();
  cachedClientId = clientId;

  try {
    window.localStorage.setItem(CLIENT_ID_STORAGE_KEY, clientId);
  } catch {
    // Ignore persistence failures so the current page session can still work.
  }

  return clientId;
}

export function isOverlaySidebarViewport(): boolean {
  return window.matchMedia("(max-width: 1180px)").matches;
}

export function formatSourceLabel(recordType: string): string {
  return SOURCE_LABELS[recordType] || recordType || "未知来源";
}

export function formatRoleLabel(displayRole: string): string {
  return ROLE_LABELS[displayRole] || displayRole || "未标注";
}

export function formatRecordShort(recordId: string): string {
  if (!recordId) {
    return "未标注";
  }
  const parts = String(recordId).split(":");
  return parts[parts.length - 1] || recordId;
}

function getSourceObject(record: Partial<EvidenceItem> | Partial<CitationItem>): string {
  return record.record_type || "";
}

function getChapterLabel(record: Partial<EvidenceItem> | Partial<CitationItem>): string {
  return record.chapter_title || "";
}

function extractRecordOrdinal(recordId: string): string {
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

function formatSourceUnitLabel(sourceObject: string): string {
  return SOURCE_UNIT_LABELS[sourceObject] || formatSourceLabel(sourceObject);
}

function joinTitleParts(parts: string[]): string {
  return parts.filter(Boolean).join(" · ");
}

function buildStructuredRecordTitle(record: Partial<EvidenceItem> | Partial<CitationItem>): string {
  const sourceObject = getSourceObject(record);
  const chapterLabel = getChapterLabel(record);
  const recordOrdinal = extractRecordOrdinal(record.record_id || "");
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

function normalizeComparableText(text: string): string {
  return String(text || "")
    .normalize("NFKC")
    .replace(/[\p{P}\p{S}\s]+/gu, "")
    .toLowerCase();
}

function titlesTooSimilar(title: string, snippet: string): boolean {
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

export function resolveRecordTitle(
  record: Partial<EvidenceItem> | Partial<CitationItem>,
  options: { prefix?: string } = {},
): string {
  const { prefix = "" } = options;
  const rawTitle = String(record.title || "").trim();
  const snippet = String(record.snippet || "").trim();
  const structuredTitle = buildStructuredRecordTitle(record);
  const baseTitle = structuredTitle || rawTitle || formatRecordShort(record.record_id || "");
  let resolvedTitle = baseTitle;

  if (rawTitle && titlesTooSimilar(rawTitle, snippet) && structuredTitle) {
    resolvedTitle = structuredTitle;
  }

  if (titlesTooSimilar(resolvedTitle, snippet)) {
    resolvedTitle = structuredTitle && !titlesTooSimilar(structuredTitle, snippet) ? structuredTitle : "";
  }

  if (!resolvedTitle && !snippet) {
    resolvedTitle = structuredTitle || rawTitle || formatRecordShort(record.record_id || "");
  }

  if (!prefix) {
    return resolvedTitle;
  }

  return resolvedTitle ? `${prefix} · ${resolvedTitle}` : prefix;
}

export function buildSupportingHint(
  answerMode: AnswerMode,
  slot: "primary" | "secondary" | "review" | "citations" | "followups",
): string {
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

export function buildEvidenceIndex(payload: AnswerPayload): {
  primary: IndexedEvidenceItem[];
  secondary: IndexedEvidenceItem[];
  review: IndexedEvidenceItem[];
  evidenceMap: Map<string, IndexedEvidenceItem>;
} {
  let evidenceNumber = 1;
  const evidenceMap = new Map<string, IndexedEvidenceItem>();
  const assign = (items: EvidenceItem[]) =>
    items.map((item) => {
      const indexed = { ...item, eId: `E${evidenceNumber++}` };
      evidenceMap.set(indexed.eId, indexed);
      return indexed;
    });

  const primary = assign(Array.isArray(payload.primary_evidence) ? payload.primary_evidence : []);
  const secondary = assign(Array.isArray(payload.secondary_evidence) ? payload.secondary_evidence : []);
  const review = assign(Array.isArray(payload.review_materials) ? payload.review_materials : []);

  return { primary, secondary, review, evidenceMap };
}

export function parseAnswerLines(text: string): Array<{ rawLine: string; text: string; evidenceIds: string[] }> {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const evidenceIds = Array.from(line.matchAll(EVIDENCE_REF_RE)).map((match) => match[1]);
      const normalizedText = line.replace(EVIDENCE_REF_RE, "").trimEnd();
      return {
        rawLine: line,
        text: normalizedText,
        evidenceIds,
      };
    });
}
