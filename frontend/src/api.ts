import type {
  ApiErrorPayload,
  AnswerPayload,
  ConversationClearResponse,
  ConversationCreateResponse,
  ConversationDetail,
  ConversationListResponse,
  ConversationMessageResponse,
} from "./types";
import { getOrCreateAnonymousClientId } from "./utils";

const CONVERSATIONS_API_PATH = "/api/v1/conversations";
const ANSWERS_API_PATH = "/api/v1/answers";
const CLIENT_ID_HEADER = "X-TCM-Client-Id";

export class RequestError extends Error {
  kind: string;
  status?: number;
  payload?: ApiErrorPayload;

  constructor(kind: string, message: string, extra: { status?: number; payload?: ApiErrorPayload } = {}) {
    super(message);
    this.name = "RequestError";
    this.kind = kind;
    this.status = extra.status;
    this.payload = extra.payload;
  }
}

async function readJsonSafely<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(url, options);
  } catch {
    throw new RequestError("network_error", "请求未成功返回，请确认本地服务仍在运行。");
  }

  const payload = await readJsonSafely<T & ApiErrorPayload>(response);
  if (!response.ok) {
    throw new RequestError(
      "response_error",
      payload?.error?.message || "请求失败。",
      { status: response.status, payload: payload || undefined },
    );
  }
  if (!payload) {
    throw new RequestError("invalid_json", "服务返回了不可解析的 JSON。");
  }

  return payload;
}

function withConversationClient(options: RequestInit = {}): RequestInit {
  const headers = new Headers(options.headers);
  headers.set(CLIENT_ID_HEADER, getOrCreateAnonymousClientId());
  return {
    ...options,
    headers,
  };
}

export function apiListConversations(search: string): Promise<ConversationListResponse> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJson<ConversationListResponse>(`${CONVERSATIONS_API_PATH}${query}`, withConversationClient());
}

export function apiCreateConversation(): Promise<ConversationCreateResponse> {
  return fetchJson<ConversationCreateResponse>(CONVERSATIONS_API_PATH, withConversationClient({
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  }));
}

export function apiGetConversation(conversationId: string): Promise<ConversationDetail> {
  return fetchJson<ConversationDetail>(
    `${CONVERSATIONS_API_PATH}/${encodeURIComponent(conversationId)}`,
    withConversationClient(),
  );
}

export function apiDeleteConversation(conversationId: string): Promise<{ id: string; deleted: boolean }> {
  return fetchJson<{ id: string; deleted: boolean }>(
    `${CONVERSATIONS_API_PATH}/${encodeURIComponent(conversationId)}`,
    withConversationClient({
      method: "DELETE",
    }),
  );
}

export function apiClearConversations(): Promise<ConversationClearResponse> {
  return fetchJson<ConversationClearResponse>(CONVERSATIONS_API_PATH, withConversationClient({
    method: "DELETE",
  }));
}

export function apiSendConversationMessage(
  conversationId: string,
  query: string,
): Promise<ConversationMessageResponse> {
  return fetchJson<ConversationMessageResponse>(
    `${CONVERSATIONS_API_PATH}/${encodeURIComponent(conversationId)}/messages`,
    withConversationClient({
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    }),
  );
}

export function apiAnswer(query: string): Promise<AnswerPayload> {
  return fetchJson<AnswerPayload>(ANSWERS_API_PATH, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });
}
