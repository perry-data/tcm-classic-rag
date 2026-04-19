import { type FormEvent, type KeyboardEvent as ReactKeyboardEvent, type MutableRefObject, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  RequestError,
  apiClearConversations,
  apiCreateConversation,
  apiDeleteConversation,
  apiGetConversation,
  apiListConversations,
  apiSendConversationMessage,
} from "./api";
import styles from "./App.module.css";
import type {
  AnswerMode,
  AnswerPayload,
  CitationItem,
  CommentarialItem,
  CommentarialPayload,
  CommentarialSection,
  ConversationDetail,
  ConversationMessage,
  ConversationSummary,
  IndexedEvidenceItem,
  PendingTurn,
} from "./types";
import {
  HISTORY_SEARCH_DEBOUNCE_MS,
  SAMPLE_QUERIES,
  buildEvidenceIndex,
  buildSupportingHint,
  cx,
  formatConversationTurns,
  formatDateTime,
  formatHistoryTimestamp,
  formatRecordShort,
  formatRoleLabel,
  formatSourceLabel,
  getModeCopy,
  groupConversationsForHistory,
  isOverlaySidebarViewport,
  parseAnswerLines,
  persistSidebarCollapsedPreference,
  readSidebarCollapsedPreference,
  resolveRecordTitle,
  validatePayload,
} from "./utils";

function buildConversationPath(conversationId: string | null): string {
  return conversationId ? `/chat/${encodeURIComponent(conversationId)}` : "/";
}

const TURN_START_SCROLL_OFFSET_PX = 12;
const USER_MESSAGE_CARD_SELECTOR = "[data-message-role='user']";

function getConversationSubtitle(detail: ConversationDetail | null, conversationLoading: boolean, pendingTurn: PendingTurn | null): string {
  if (conversationLoading) {
    return "";
  }
  if (!detail?.conversation) {
    return "";
  }
  if (detail.messages.length === 0 && !pendingTurn) {
    return "";
  }
  return `共 ${detail.conversation.message_count} 条消息 · 最近更新 ${formatDateTime(
    detail.conversation.updated_at || detail.conversation.created_at,
  )}`;
}

function scrollElementToTop(element: HTMLDivElement | null): void {
  if (!element) {
    return;
  }
  window.requestAnimationFrame(() => {
    element.scrollTo({
      top: 0,
      behavior: "auto",
    });
  });
}

function scrollElementToBottom(element: HTMLDivElement | null): void {
  if (!element) {
    return;
  }
  window.requestAnimationFrame(() => {
    element.scrollTo({
      top: element.scrollHeight,
      behavior: "smooth",
    });
  });
}

function scrollLatestUserMessageIntoView(element: HTMLDivElement | null, behavior: ScrollBehavior = "auto"): void {
  if (!element) {
    return;
  }
  window.requestAnimationFrame(() => {
    const userCards = element.querySelectorAll<HTMLElement>(USER_MESSAGE_CARD_SELECTOR);
    if (userCards.length === 0) {
      return;
    }

    const latestUserCard = userCards[userCards.length - 1];
    const nextTop =
      element.scrollTop +
      latestUserCard.getBoundingClientRect().top -
      element.getBoundingClientRect().top -
      TURN_START_SCROLL_OFFSET_PX;

    element.scrollTo({
      top: Math.max(0, nextTop),
      behavior,
    });
  });
}

export default function App() {
  const navigate = useNavigate();
  const { conversationId: routeConversationId } = useParams();

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [historySearchInput, setHistorySearchInput] = useState("");
  const [historySearch, setHistorySearch] = useState("");
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [conversationLoading, setConversationLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [pendingTurn, setPendingTurn] = useState<PendingTurn | null>(null);
  const [deletingConversationId, setDeletingConversationId] = useState<string | null>(null);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [statusText, setStatusText] = useState("正在初始化聊天界面…");
  const [errorText, setErrorText] = useState("");
  const [queryText, setQueryText] = useState("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => readSidebarCollapsedPreference());
  const [overlaySidebarOpen, setOverlaySidebarOpen] = useState(false);
  const [overlayMode, setOverlayMode] = useState(() => isOverlaySidebarViewport());
  const [bootstrapped, setBootstrapped] = useState(false);

  const chatBodyRef = useRef<HTMLDivElement | null>(null);
  const queryInputRef = useRef<HTMLTextAreaElement | null>(null);
  const historyRequestSeqRef = useRef(0);
  const conversationRequestSeqRef = useRef(0);
  const skipSearchEffectRef = useRef(true);

  const activeConversationRef = useRef<ConversationDetail | null>(activeConversation);
  const activeConversationIdRef = useRef<string | null>(activeConversationId);
  const historySearchRef = useRef(historySearch);
  const sendingRef = useRef(sending);
  const conversationLoadingRef = useRef(conversationLoading);

  activeConversationRef.current = activeConversation;
  activeConversationIdRef.current = activeConversationId;
  historySearchRef.current = historySearch;
  sendingRef.current = sending;
  conversationLoadingRef.current = conversationLoading;

  function closeOverlaySidebar(): void {
    if (overlayMode) {
      setOverlaySidebarOpen(false);
    }
  }

  function clearActiveConversationState(): void {
    conversationRequestSeqRef.current += 1;
    setActiveConversationId(null);
    setActiveConversation(null);
    setPendingTurn(null);
    setConversationLoading(false);
  }

  async function refreshConversationList(search = historySearchRef.current): Promise<void> {
    const normalizedSearch = search.trim();
    const requestSeq = historyRequestSeqRef.current + 1;
    historyRequestSeqRef.current = requestSeq;
    setHistorySearch(normalizedSearch);
    setConversationsLoading(true);

    try {
      const payload = await apiListConversations(normalizedSearch);
      if (requestSeq !== historyRequestSeqRef.current) {
        return;
      }

      const nextItems = Array.isArray(payload.items) ? payload.items : [];
      setConversations(nextItems);
      setConversationsLoading(false);
      setActiveConversation((current) => {
        if (!current?.conversation) {
          return current;
        }
        const updated = nextItems.find((item) => item.id === current.conversation.id);
        if (!updated) {
          return current;
        }
        return {
          ...current,
          conversation: {
            ...current.conversation,
            ...updated,
          },
        };
      });
    } catch (error) {
      if (requestSeq !== historyRequestSeqRef.current) {
        return;
      }
      console.error(error);
      setConversations([]);
      setConversationsLoading(false);
      setErrorText(error instanceof Error ? error.message : "历史会话加载失败。");
      setStatusText("历史会话加载失败");
    }
  }

  async function openConversation(nextConversationId: string | null): Promise<void> {
    if (!nextConversationId) {
      clearActiveConversationState();
      scrollElementToTop(chatBodyRef.current);
      return;
    }

    if (sendingRef.current) {
      return;
    }

    closeOverlaySidebar();

    if (
      activeConversationRef.current?.conversation.id === nextConversationId &&
      !conversationLoadingRef.current
    ) {
      return;
    }

    const requestSeq = conversationRequestSeqRef.current + 1;
    conversationRequestSeqRef.current = requestSeq;
    setActiveConversationId(nextConversationId);
    setConversationLoading(true);
    setPendingTurn(null);
    setErrorText("");
    setStatusText("正在恢复历史会话…");

    try {
      const payload = await apiGetConversation(nextConversationId);
      if (requestSeq !== conversationRequestSeqRef.current) {
        return;
      }

      setActiveConversation({
        conversation: payload.conversation,
        messages: Array.isArray(payload.messages) ? payload.messages : [],
      });
      setActiveConversationId(payload.conversation.id);
      setConversationLoading(false);
      setStatusText("历史会话已恢复，可继续发送");
      scrollElementToBottom(chatBodyRef.current);
    } catch (error) {
      if (requestSeq !== conversationRequestSeqRef.current) {
        return;
      }
      console.error(error);
      setConversationLoading(false);
      if (error instanceof RequestError && error.status === 404) {
        clearActiveConversationState();
        navigate("/", { replace: true });
        setErrorText("要打开的会话不存在，已返回空白会话页。");
        setStatusText("会话不存在");
        scrollElementToTop(chatBodyRef.current);
        return;
      }

      setErrorText(error instanceof Error ? error.message : "会话恢复失败。");
      setStatusText("会话恢复失败");
    }
  }

  async function createAndActivateConversation(silent = false): Promise<ConversationSummary> {
    if (!silent) {
      setStatusText("正在创建新会话…");
      setErrorText("");
    }

    const payload = await apiCreateConversation();
    const conversation = payload.conversation;
    skipSearchEffectRef.current = true;
    setHistorySearchInput("");
    setHistorySearch("");
    setActiveConversationId(conversation.id);
    setActiveConversation({
      conversation,
      messages: [],
    });
    navigate(buildConversationPath(conversation.id));
    await refreshConversationList("");

    if (!silent) {
      setStatusText("已创建新会话，可以开始提问");
    }

    return conversation;
  }

  async function ensureConversationForSend(): Promise<string> {
    if (activeConversationIdRef.current && activeConversationRef.current) {
      return activeConversationIdRef.current;
    }

    const conversation = await createAndActivateConversation(true);
    return conversation.id;
  }

  async function submitCurrentQuery(query: string): Promise<void> {
    const normalizedQuery = query.trim();
    if (!normalizedQuery) {
      setErrorText("请输入问题后再发送。");
      setStatusText("请先输入问题");
      return;
    }

    if (sendingRef.current) {
      return;
    }

    let conversationId: string;
    try {
      conversationId = await ensureConversationForSend();
    } catch (error) {
      console.error(error);
      setErrorText(error instanceof Error ? error.message : "当前无法创建新会话。");
      setStatusText("发送前创建会话失败");
      return;
    }

    setSending(true);
    setPendingTurn({
      role: "user",
      content: normalizedQuery,
      created_at: new Date().toISOString(),
    });
    setErrorText("");
    setStatusText("正在为当前会话生成回答…");
    scrollLatestUserMessageIntoView(chatBodyRef.current, "smooth");

    try {
      const payload = await apiSendConversationMessage(conversationId, normalizedQuery);
      const existingMessages = activeConversationRef.current?.messages || [];
      setActiveConversation({
        conversation: payload.conversation,
        messages: existingMessages.concat(Array.isArray(payload.messages) ? payload.messages : []),
      });
      setActiveConversationId(payload.conversation.id);
      setPendingTurn(null);
      setQueryText("");
      scrollLatestUserMessageIntoView(chatBodyRef.current);
      await refreshConversationList(historySearchRef.current);
      setStatusText("回答已写入当前会话");
      queryInputRef.current?.focus();
    } catch (error) {
      console.error(error);
      setPendingTurn(null);
      setErrorText(error instanceof Error ? error.message : "本次消息未能成功写入会话。");
      setStatusText("本次消息未发送成功");
    } finally {
      setSending(false);
    }
  }

  async function handleNewChat(): Promise<void> {
    if (sendingRef.current) {
      return;
    }

    closeOverlaySidebar();
    const shouldRefreshHistory = conversationsLoading || Boolean(historySearchRef.current);
    skipSearchEffectRef.current = true;
    setHistorySearchInput("");
    setHistorySearch("");
    clearActiveConversationState();
    setQueryText("");
    setErrorText("");
    setStatusText("已回到空白新对话，可直接输入第一条问题");
    navigate("/");
    scrollElementToTop(chatBodyRef.current);
    if (shouldRefreshHistory) {
      await refreshConversationList("");
    }
    queryInputRef.current?.focus();
  }

  async function handleDeleteConversation(conversationId: string): Promise<void> {
    if (sendingRef.current || deletingConversationId || clearingHistory) {
      return;
    }

    const conversation =
      conversations.find((item) => item.id === conversationId) || activeConversationRef.current?.conversation;
    const confirmed = window.confirm(`确定删除“${conversation?.title || "当前会话"}”吗？此操作不可撤销。`);
    if (!confirmed) {
      return;
    }

    setDeletingConversationId(conversationId);
    setErrorText("");
    setStatusText("正在删除会话…");

    try {
      await apiDeleteConversation(conversationId);
      const deletedActive = activeConversationIdRef.current === conversationId;

      if (deletedActive) {
        clearActiveConversationState();
        navigate("/", { replace: true });
      }

      await refreshConversationList(historySearchRef.current);
      if (deletedActive) {
        scrollElementToTop(chatBodyRef.current);
      }

      setStatusText("会话已删除");
    } catch (error) {
      console.error(error);
      setErrorText(error instanceof Error ? error.message : "会话删除失败。");
      setStatusText("会话删除失败");
    } finally {
      setDeletingConversationId(null);
    }
  }

  async function handleClearHistory(): Promise<void> {
    if (sendingRef.current || deletingConversationId || clearingHistory) {
      return;
    }

    const confirmed = window.confirm("确定清空当前浏览器中的全部历史对话吗？此操作不会影响其他设备或其他浏览器。");
    if (!confirmed) {
      return;
    }

    setClearingHistory(true);
    setErrorText("");
    setStatusText("正在清空当前浏览器历史…");

    try {
      const payload = await apiClearConversations();
      skipSearchEffectRef.current = true;
      setHistorySearchInput("");
      setHistorySearch("");
      clearActiveConversationState();
      setQueryText("");
      navigate("/", { replace: true });
      await refreshConversationList("");
      scrollElementToTop(chatBodyRef.current);
      if (payload.deleted_count > 0) {
        setStatusText(`已清空当前浏览器历史（${payload.deleted_count} 条会话）`);
      } else {
        setStatusText("当前浏览器没有可清空的历史会话");
      }
    } catch (error) {
      console.error(error);
      setErrorText(error instanceof Error ? error.message : "清空历史失败。");
      setStatusText("清空历史失败");
    } finally {
      setClearingHistory(false);
    }
  }

  function handleSidebarToggle(): void {
    if (overlayMode) {
      setOverlaySidebarOpen((current) => !current);
      return;
    }

    setSidebarCollapsed((current) => {
      const next = !current;
      persistSidebarCollapsedPreference(next);
      return next;
    });
  }

  function handleSampleQueryFill(query: string): void {
    setQueryText(query);
    setErrorText("");
    setStatusText("样例已填充，可继续发送到当前会话");
    window.requestAnimationFrame(() => {
      queryInputRef.current?.focus();
      queryInputRef.current?.setSelectionRange(query.length, query.length);
    });
  }

  function handleFormSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void submitCurrentQuery(queryText);
  }

  function handleTextareaKeyDown(event: ReactKeyboardEvent<HTMLTextAreaElement>): void {
    const shouldSubmit = event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing;
    if (!shouldSubmit || sendingRef.current) {
      return;
    }
    event.preventDefault();
    void submitCurrentQuery(queryText);
  }

  useEffect(() => {
    if (queryInputRef.current) {
      // Reset height to allow shrinking
      queryInputRef.current.style.height = "auto";
      // Set height based on scrollHeight, CSS max-height will constrain it
      queryInputRef.current.style.height = `${queryInputRef.current.scrollHeight}px`;
    }
  }, [queryText]);

  useEffect(() => {
    let cancelled = false;

    async function initialize(): Promise<void> {
      setStatusText("正在加载历史会话…");
      await refreshConversationList("");
      if (cancelled) {
        return;
      }
      setBootstrapped(true);
      if (!routeConversationId) {
        setStatusText("前端脚本已加载，可从空白会话开始，也可打开左侧历史");
      }
    }

    void initialize();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!bootstrapped) {
      return;
    }

    if (skipSearchEffectRef.current) {
      skipSearchEffectRef.current = false;
      return;
    }

    const timer = window.setTimeout(() => {
      void refreshConversationList(historySearchInput);
    }, HISTORY_SEARCH_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
    };
  }, [bootstrapped, historySearchInput]);

  useEffect(() => {
    if (!bootstrapped) {
      return;
    }

    if (sendingRef.current) {
      navigate(buildConversationPath(activeConversationIdRef.current), { replace: true });
      return;
    }

    void openConversation(routeConversationId || null);
  }, [bootstrapped, navigate, routeConversationId]);

  useEffect(() => {
    function handleResize(): void {
      const nextOverlayMode = isOverlaySidebarViewport();
      setOverlayMode(nextOverlayMode);
      if (!nextOverlayMode) {
        setOverlaySidebarOpen(false);
      }
    }

    function handleGlobalKeydown(event: globalThis.KeyboardEvent): void {
      if (event.key === "Escape") {
        setOverlaySidebarOpen(false);
      }
    }

    window.addEventListener("resize", handleResize);
    window.addEventListener("keydown", handleGlobalKeydown);

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("keydown", handleGlobalKeydown);
    };
  }, []);

  const sidebarOpen = overlayMode ? overlaySidebarOpen : !sidebarCollapsed;
  const isSearching = Boolean(historySearch);
  const confirmedMessages = activeConversation?.messages || [];
  const hasMessages = confirmedMessages.length > 0 || Boolean(pendingTurn);
  const showEmptyState = !conversationLoading && !hasMessages;

  return (
    <div
      className={cx(
        styles.page,
        overlayMode && sidebarOpen && styles.pageSidebarOverlayOpen,
      )}
    >
      <header className={styles.toolbar}>
        <div className={styles.toolbarActions}>
          <button
            className={styles.iconButton}
            type="button"
            onClick={handleSidebarToggle}
            aria-controls="history-sidebar"
            aria-expanded={sidebarOpen}
            aria-label={sidebarOpen ? "收起历史会话侧栏" : "展开历史会话侧栏"}
            title={sidebarOpen ? "收起历史会话侧栏" : "展开历史会话侧栏"}
          >
            <span className={styles.iconGlyph}>☰</span>
          </button>
          <button
            className={styles.iconButton}
            type="button"
            onClick={() => {
              void handleNewChat();
            }}
            disabled={sending || clearingHistory}
            aria-label="新建对话"
            title="新建对话"
          >
            <span className={styles.iconGlyph}>＋</span>
          </button>
        </div>

        <div className={styles.toolbarCenter}>
          <h1 className={styles.toolbarTitle}>{activeConversation?.conversation.title || "新对话"}</h1>
          <p className={styles.toolbarSubtitle}>
            {getConversationSubtitle(activeConversation, conversationLoading, pendingTurn)}
          </p>
        </div>


      </header>

      <button
        className={styles.sidebarBackdrop}
        type="button"
        hidden={!(overlayMode && sidebarOpen)}
        aria-label="关闭历史会话侧栏"
        onClick={closeOverlaySidebar}
      />

      <div
        className={cx(
          styles.shell,
          !sidebarOpen && styles.shellSidebarCollapsed,
        )}
      >
        <aside
          id="history-sidebar"
          className={styles.sidebar}
          aria-hidden={!sidebarOpen}
        >
          <div className={styles.sidebarHead}>
            <h2 className={styles.sidebarTitle}>历史对话</h2>
            <button
              className={styles.sidebarActionButton}
              type="button"
              onClick={() => {
                void handleClearHistory();
              }}
              disabled={sending || Boolean(deletingConversationId) || clearingHistory}
              title={clearingHistory ? "清空中…" : "清空当前浏览器历史"}
            >
              {clearingHistory ? "清空中…" : "清空历史"}
            </button>
          </div>

          <div className={styles.sidebarSearch}>
            <input
              type="search"
              value={historySearchInput}
              onChange={(event) => {
                setHistorySearchInput(event.target.value);
              }}
              disabled={sending || clearingHistory}
              aria-label="搜索历史对话"
              placeholder="搜索标题或消息内容"
              autoComplete="off"
            />

            <div className={styles.sidebarMeta}>
              <p>{isSearching ? "搜索结果" : "最近会话"}</p>
              <p aria-live="polite">
                {conversationsLoading
                  ? isSearching
                    ? "搜索中…"
                    : "加载中…"
                  : `${conversations.length} 条${isSearching ? "结果" : ""}`}
              </p>
            </div>
          </div>

          <div className={styles.sidebarListShell}>
            {conversationsLoading ? (
              <StateCard
                title="正在加载历史会话"
                copy="列表载入后，你可以从左侧直接恢复旧会话并继续聊天。"
              />
            ) : null}

            {!conversationsLoading && conversations.length === 0 && !isSearching ? (
              <StateCard
                title="还没有历史会话"
                copy="点击上方“新建对话”，或者直接在右侧输入问题开始第一轮会话。"
              />
            ) : null}

            {!conversationsLoading && conversations.length === 0 && isSearching ? (
              <StateCard
                title="没有匹配结果"
                copy="当前搜索没有命中标题或消息内容，可以尝试缩短关键词后重试。"
              />
            ) : null}

            {!conversationsLoading && conversations.length > 0 ? (
              <ul className={styles.conversationList}>
                {groupConversationsForHistory(conversations).map((group) => (
                  <li key={group.key} className={styles.conversationGroup}>
                    <div className={styles.conversationGroupHead}>
                      <p className={styles.conversationGroupTitle}>{group.label}</p>
                    </div>
                    <ul className={styles.conversationGroupList}>
                      {group.items.map((conversation) => {
                        const isActive = conversation.id === activeConversationId;
                        return (
                          <li
                            key={conversation.id}
                            className={cx(styles.conversationItem, isActive && styles.conversationItemActive)}
                          >
                            <button
                              className={styles.conversationButton}
                              type="button"
                              disabled={sending || clearingHistory}
                              onClick={() => {
                                navigate(buildConversationPath(conversation.id));
                                closeOverlaySidebar();
                              }}
                            >
                              <p className={styles.conversationItemTitle}>{conversation.title || "新对话"}</p>
                              <div className={styles.conversationItemMeta}>
                                <span>{formatHistoryTimestamp(conversation.updated_at || conversation.created_at)}</span>
                                <span>{formatConversationTurns(conversation.message_count)}</span>
                              </div>
                            </button>

                            <button
                              className={styles.menuButton}
                              type="button"
                              disabled={sending || clearingHistory || deletingConversationId === conversation.id}
                              aria-label={`删除会话 ${conversation.title || "新对话"}`}
                              title={deletingConversationId === conversation.id ? "删除中…" : "删除会话"}
                              onClick={() => {
                                void handleDeleteConversation(conversation.id);
                              }}
                            >
                              {deletingConversationId === conversation.id ? "…" : "×"}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </aside>

        <main className={styles.chatPanel}>
          <div ref={chatBodyRef} className={cx(styles.chatBody, showEmptyState && styles.chatBodyEmpty)}>
            {conversationLoading ? (
              <StateCard title="正在加载会话" copy="正在恢复完整聊天记录，请稍候。" large />
            ) : null}

            {showEmptyState ? (
              <EmptyChatStage
                disabled={sending || conversationLoading || clearingHistory}
                onSelectSample={handleSampleQueryFill}
              />
            ) : null}

            {!conversationLoading && hasMessages ? (
              <section className={styles.messageFeed} aria-label="当前会话">
                {confirmedMessages.map((message) =>
                  message.role === "user" ? (
                    <UserMessageCard key={message.id} message={message} />
                  ) : (
                    <AssistantMessageCard
                      key={message.id}
                      message={message}
                    />
                  ),
                )}

                {pendingTurn ? <UserMessageCard message={pendingTurn} pending /> : null}
                {pendingTurn ? <PendingAssistantCard /> : null}
              </section>
            ) : null}
          </div>

          <footer className={styles.composerShell}>
            <section className={styles.composerPanel} aria-label="底部输入区">
              <form className={styles.composerForm} onSubmit={handleFormSubmit}>
                <textarea
                  ref={queryInputRef}
                  value={queryText}
                  onChange={(event) => {
                    setQueryText(event.target.value);
                  }}
                  onKeyDown={handleTextareaKeyDown}
                  disabled={sending || conversationLoading || clearingHistory}
                  aria-label="当前问题"
                  rows={1}
                  placeholder="输入问题"
                />
                <div className={styles.composerActions}>
                  <button
                    className={styles.submitButton}
                    type="submit"
                    disabled={sending || conversationLoading || clearingHistory}
                    aria-label={sending ? "发送中" : "发送"}
                  >
                    <span className={styles.submitButtonText}>{sending ? "发送中…" : "发送"}</span>
                    <span className={styles.submitButtonIcon} aria-hidden="true">
                      {sending ? "…" : "↑"}
                    </span>
                  </button>
                </div>
              </form>
            </section>
          </footer>
        </main>
      </div>
    </div>
  );
}

function StateCard(props: { title: string; copy: string; large?: boolean }) {
  return (
    <section className={cx(styles.stateCard, props.large && styles.stateCardLarge)}>
      <p className={styles.stateTitle}>{props.title}</p>
      <p className={styles.stateCopy}>{props.copy}</p>
    </section>
  );
}

function EmptyChatStage(props: { disabled: boolean; onSelectSample: (query: string) => void }) {
  return (
    <section className={styles.emptyStage} aria-label="空白会话">
      <div className={styles.emptyStageInner}>
        <div className={styles.emptySampleList}>
          {SAMPLE_QUERIES.map((query) => (
            <button
              key={query}
              className={styles.sampleChip}
              type="button"
              disabled={props.disabled}
              onClick={() => {
                props.onSelectSample(query);
              }}
            >
              {query}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function UserMessageCard(props: { message: { content: string; created_at: string }; pending?: boolean }) {
  return (
    <article
      className={cx(styles.messageCard, styles.userMessage, props.pending && styles.pendingCard)}
      data-message-role="user"
    >
      <p className={styles.userBubble}>{props.message.content || ""}</p>
    </article>
  );
}

function PendingAssistantCard() {
  const modeCopy = getModeCopy("loading");
  return (
    <article className={cx(styles.messageCard, styles.assistantMessage, styles.pendingCard)}>
      <div className={styles.messageHead}>
        <p className={styles.messageTime}>正在生成中</p>
        <span className={styles.modeBadge} data-mode="loading">
          {modeCopy.badge}
        </span>
      </div>
      <div className={styles.assistantMain}>
        <section className={styles.answerBlock}>
          <p className={styles.answerLine}>正在检索依据并生成回答…</p>
        </section>
        <ModeSummary mode="loading" />
      </div>
    </article>
  );
}

function BrokenAssistantCard(props: { message: ConversationMessage; error: Error }) {
  return (
    <article className={cx(styles.messageCard, styles.assistantMessage)}>
      <div className={styles.messageHead}>
        <p className={styles.messageTime}>{formatDateTime(props.message.created_at)}</p>
        <span className={styles.modeBadge} data-mode="error">
          渲染失败
        </span>
      </div>

      <div className={styles.assistantMain}>
        <section className={styles.answerBlock}>
          <p className={styles.answerLine}>{props.message.content || "无正文内容"}</p>
        </section>
        <ModeSummary mode="error" />
      </div>

      <div className={styles.calloutList}>
        <Callout title="渲染异常" body={props.error.message || "这条历史消息的结构不完整。"} tone="refuse" />
      </div>
    </article>
  );
}

function AssistantMessageCard(props: { message: ConversationMessage }) {
  try {
    validatePayload(props.message.answer_payload);
    return (
      <AssistantMessageCardInner
        message={props.message}
        payload={props.message.answer_payload}
      />
    );
  } catch (error) {
    console.error(error);
    return <BrokenAssistantCard message={props.message} error={error instanceof Error ? error : new Error("渲染失败")} />;
  }
}

function AssistantMessageCardInner(props: {
  message: ConversationMessage;
  payload: AnswerPayload;
}) {
  const { primary, secondary, review, evidenceMap } = buildEvidenceIndex(props.payload);
  const commentarial = props.payload.commentarial || null;
  const citations = Array.isArray(props.payload.citations) ? props.payload.citations : [];
  const followups = Array.isArray(props.payload.suggested_followup_questions)
    ? props.payload.suggested_followup_questions
    : [];
  const lines = parseAnswerLines(props.payload.answer_text);
  const modeCopy = getModeCopy(props.payload.answer_mode);
  const [highlightedEvidenceId, setHighlightedEvidenceId] = useState<string | null>(null);
  const evidenceRefs = useRef<Record<string, HTMLElement | null>>({});

  function jumpToEvidence(evidenceId: string): void {
    const card = evidenceRefs.current[evidenceId];
    if (!card) {
      return;
    }

    card.scrollIntoView({ behavior: "smooth", block: "center" });
    setHighlightedEvidenceId(evidenceId);
    window.setTimeout(() => {
      setHighlightedEvidenceId((current) => (current === evidenceId ? null : current));
    }, 2000);
  }

  return (
    <article className={cx(styles.messageCard, styles.assistantMessage)}>
      <div className={styles.messageHead}>
        <p className={styles.messageTime}>{formatDateTime(props.message.created_at)}</p>
        <span className={styles.modeBadge} data-mode={props.payload.answer_mode}>
          {modeCopy.badge}
        </span>
      </div>

      <div className={styles.assistantMain}>
        <section className={styles.answerBlock}>
          {lines.map((line, index) => (
            <p key={`${props.message.id}-${index}`} className={cx(styles.answerLine, index === 0 && styles.answerLead)}>
              <span>{line.text || line.rawLine}</span>
              {line.evidenceIds.length > 0 ? (
                <span className={styles.evidenceChipList}>
                  {line.evidenceIds.map((evidenceId) => {
                    const evidence = evidenceMap.get(evidenceId);
                    const title = evidence ? resolveRecordTitle(evidence) : "";
                    const tooltip = [title, evidence?.snippet || ""].filter(Boolean).join("\n");
                    return (
                      <button
                        key={`${props.message.id}-${index}-${evidenceId}-chip`}
                        type="button"
                        className={styles.evidenceChip}
                        title={tooltip}
                        onClick={() => {
                          jumpToEvidence(evidenceId);
                        }}
                      >
                        {evidenceId}
                      </button>
                    );
                  })}
                </span>
              ) : null}
            </p>
          ))}
        </section>

        {props.payload.disclaimer ? <p className={styles.disclaimerText}>{props.payload.disclaimer}</p> : null}
        <ModeSummary mode={props.payload.answer_mode} />
      </div>

      {props.payload.refuse_reason ? (
        <div className={styles.calloutList}>
          {props.payload.refuse_reason ? (
            <Callout title="拒答原因" body={props.payload.refuse_reason} tone="refuse" />
          ) : null}
        </div>
      ) : null}

      {commentarial ? <CommentarialPanels payload={commentarial} /> : null}

      <section className={styles.supporting}>
        <div className={styles.supportingHead}>
          <p className={styles.supportingKicker}>依据与附加信息</p>
        </div>

        {primary.length === 0 &&
        secondary.length === 0 &&
        review.length === 0 &&
        citations.length === 0 &&
        followups.length === 0 ? (
          <section className={styles.supportPanel}>
            <p className={styles.stateCopy}>当前结果没有可展示证据。若为拒答模式，这是预期行为。</p>
          </section>
        ) : null}

        {primary.length > 0 ? (
          <EvidencePanel
            title="主依据"
            hint={buildSupportingHint(props.payload.answer_mode, "primary")}
            items={primary}
            highlightedEvidenceId={highlightedEvidenceId}
            evidenceRefs={evidenceRefs}
            tone="primary"
          />
        ) : null}

        {props.payload.review_notice ? (
          <Callout title="核对提示" body={props.payload.review_notice} tone="review" />
        ) : null}

        {secondary.length > 0 ? (
          <EvidencePanel
            title="补充依据"
            hint={buildSupportingHint(props.payload.answer_mode, "secondary")}
            items={secondary}
            highlightedEvidenceId={highlightedEvidenceId}
            evidenceRefs={evidenceRefs}
          />
        ) : null}

        {review.length > 0 ? (
          <EvidencePanel
            title="核对材料"
            hint={buildSupportingHint(props.payload.answer_mode, "review")}
            items={review}
            highlightedEvidenceId={highlightedEvidenceId}
            evidenceRefs={evidenceRefs}
            tone="review"
          />
        ) : null}

        {citations.length > 0 ? (
          <CitationsPanel
            items={citations}
            hint={buildSupportingHint(props.payload.answer_mode, "citations")}
          />
        ) : null}

        {followups.length > 0 ? (
          <FollowupsPanel
            items={followups}
            hint={buildSupportingHint(props.payload.answer_mode, "followups")}
          />
        ) : null}
      </section>
    </article>
  );
}

function ModeSummary(props: { mode: AnswerMode | "loading" | "error" }) {
  if (props.mode === "weak_with_review_notice") return null;

  const copy = getModeCopy(props.mode);
  return (
    <section className={styles.modeSummary} data-mode={props.mode}>
      <div>
        <p className={styles.modeKicker}>结果状态</p>
        <h3 className={styles.modeTitle}>{copy.title}</h3>
        <p className={styles.modeDescription}>{copy.description}</p>
      </div>
      <p className={styles.modeHint}>{copy.hint}</p>
    </section>
  );
}

function Callout(props: { title: string; body: string; tone: "review" | "refuse" }) {
  return (
    <section className={styles.callout} data-tone={props.tone}>
      <div className={styles.panelHead}>
        <h3>{props.title}</h3>
      </div>
      <p>{props.body}</p>
    </section>
  );
}

function CommentarialPanels(props: { payload: CommentarialPayload }) {
  const sections = Array.isArray(props.payload.sections)
    ? props.payload.sections.filter((section) => Array.isArray(section.items) && section.items.length > 0)
    : [];
  if (sections.length === 0) {
    return null;
  }

  return (
    <section className={styles.commentarialShell}>
      <div className={styles.commentarialHead}>
        <div>
          <p className={styles.supportingKicker}>名家视角层</p>
          <h3 className={styles.commentarialTitle}>{resolveCommentarialTitle(props.payload.route)}</h3>
        </div>
        <span className={styles.commentarialRouteBadge}>{resolveCommentarialBadge(props.payload.route)}</span>
      </div>
      {props.payload.lead_note ? <p className={styles.commentarialLead}>{props.payload.lead_note}</p> : null}
      <div className={cx(styles.commentarialSectionGrid, props.payload.route === "comparison_view" && styles.commentarialSectionGridComparison)}>
        {sections.map((section) =>
          section.collapsed_by_default ? (
            <details key={section.section_id} className={styles.commentarialFold}>
              <summary className={styles.commentarialFoldSummary}>
                <span>{section.title}</span>
                <span className={styles.sectionCount}>{section.items.length}条</span>
              </summary>
              <CommentarialSectionCards section={section} />
            </details>
          ) : (
            <section key={section.section_id} className={styles.commentarialPanel}>
              <div className={styles.panelHead}>
                <div>
                  <h3>
                    {section.title}
                    <span className={styles.sectionCount}>{section.items.length}条</span>
                  </h3>
                  <p>{resolveCommentarialHint(section)}</p>
                </div>
              </div>
              <CommentarialSectionCards section={section} />
            </section>
          ),
        )}
      </div>
    </section>
  );
}

function CommentarialSectionCards(props: { section: CommentarialSection }) {
  return (
    <div className={cx(styles.commentarialCards, props.section.layout === "comparison" && styles.commentarialCardsComparison)}>
      {props.section.items.map((item) => (
        <CommentarialCard key={item.unit_id} item={item} />
      ))}
    </div>
  );
}

function CommentarialCard(props: { item: CommentarialItem }) {
  return (
    <article className={styles.commentarialCard}>
      <div className={styles.commentarialCardHead}>
        <div>
          <p className={styles.commentarialCommentator}>{props.item.commentator}</p>
          <h4>{props.item.title}</h4>
        </div>
        <div className={styles.commentarialBadgeList}>
          <span className={styles.commentarialBadge}>{props.item.anchor_type}</span>
          {props.item.theme_display_tier ? <span className={styles.commentarialBadge}>{props.item.theme_display_tier}</span> : null}
        </div>
      </div>
      {props.item.quoted_original_text ? <p className={styles.commentarialQuote}>原文锚点：{props.item.quoted_original_text}</p> : null}
      <p className={styles.commentarialSummary}>{props.item.summary_text}</p>
      {props.item.resolved_primary_anchor_passage_ids.length > 0 ? (
        <p className={styles.commentarialMeta}>
          主锚：{props.item.resolved_primary_anchor_passage_ids.join("、")}
        </p>
      ) : null}
      {props.item.resolved_supporting_anchor_passage_ids.length > 0 ? (
        <p className={styles.commentarialMeta}>
          辅锚：{props.item.resolved_supporting_anchor_passage_ids.join("、")}
        </p>
      ) : null}
      {props.item.unresolved_anchor_keys.length > 0 ? (
        <p className={styles.commentarialWarning}>
          未回填锚点：{props.item.unresolved_anchor_keys.join("、")}
        </p>
      ) : null}
      <details className={styles.commentarialDetail}>
        <summary>展开讲稿原文</summary>
        <pre>{props.item.display_text}</pre>
      </details>
    </article>
  );
}

function resolveCommentarialTitle(route: string): string {
  if (route === "named_view") return "点名名家";
  if (route === "comparison_view") return "两家比较";
  if (route === "meta_learning_view") return "学习方法";
  return "补充解读";
}

function resolveCommentarialBadge(route: string): string {
  if (route === "named_view") return "Named";
  if (route === "comparison_view") return "Compare";
  if (route === "meta_learning_view") return "Meta";
  return "Assistive";
}

function resolveCommentarialHint(section: CommentarialSection): string {
  if (section.view_mode === "comparison_view") {
    return "该区块只展示名家比较材料，不替代 canonical 主依据。";
  }
  if (section.view_mode === "meta_learning_view") {
    return "该区块用于学习方法与研读路径提示。";
  }
  if (section.view_mode === "assistive_view") {
    return "该区块默认折叠，仅作辅助解读。";
  }
  return "该区块用于点名名家视角展示，仍与 canonical 证据层隔离。";
}

function PanelHead(props: { title: string; hint: string; count: number }) {
  return (
    <div className={styles.panelHead}>
      <div>
        <h3>
          {props.title}
          {props.count > 0 ? <span className={styles.sectionCount}>{props.count}条</span> : null}
        </h3>
        <p>{props.hint}</p>
      </div>
    </div>
  );
}

function EvidencePanel(props: {
  title: string;
  hint: string;
  items: IndexedEvidenceItem[];
  highlightedEvidenceId: string | null;
  evidenceRefs: MutableRefObject<Record<string, HTMLElement | null>>;
  tone?: "primary" | "review";
}) {
  return (
    <section className={styles.supportPanel} data-tone={props.tone || "default"}>
      <PanelHead title={props.title} hint={props.hint} count={props.items.length} />
      <div className={styles.evidenceList}>
        {props.items.map((item) => (
          <article
            key={`${props.title}-${item.record_id}-${item.eId}`}
            ref={(node) => {
              props.evidenceRefs.current[item.eId] = node;
            }}
            className={cx(
              styles.evidenceCard,
              props.highlightedEvidenceId === item.eId && styles.evidenceCardHighlighted,
            )}
            data-evidence-id={item.eId}
          >
            <div className={styles.evidenceTop}>
              <h4>{resolveRecordTitle(item) || item.title || formatRecordShort(item.record_id)}</h4>
              <span className={styles.evidenceIndex}>{item.eId}</span>
            </div>

            <div className={styles.evidenceMeta}>
              <span className={styles.roleChip} data-role={item.display_role}>
                {formatRoleLabel(item.display_role)}
              </span>
              <span className={styles.metaChip}>等级 {item.evidence_level}</span>
              <span className={styles.metaChip}>{formatSourceLabel(item.record_type)}</span>
              <span className={styles.metaChip}>记录 {formatRecordShort(item.record_id)}</span>
              {item.chapter_title ? <span className={styles.metaChip}>{item.chapter_title}</span> : null}
            </div>

            {item.snippet ? <p className={styles.evidenceSnippet}>{item.snippet}</p> : null}

            {Array.isArray(item.risk_flags) && item.risk_flags.length > 0 ? (
              <ul className={styles.riskFlags}>
                {item.risk_flags.map((flag) => (
                  <li key={`${item.record_id}-${flag}`}>{flag}</li>
                ))}
              </ul>
            ) : null}

            <p className={styles.recordFootnote}>record_id: {item.record_id}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function CitationsPanel(props: { items: CitationItem[]; hint: string }) {
  return (
    <section className={styles.supportPanel}>
      <PanelHead title="回答引用" hint={props.hint} count={props.items.length} />
      <ol className={styles.citationList}>
        {props.items.map((citation) => (
          <li key={`${citation.citation_id}-${citation.record_id}`} className={styles.citationItem}>
            <h4>{resolveRecordTitle(citation, { prefix: citation.citation_id || "引用" })}</h4>
            <div className={styles.evidenceMeta}>
              <span className={styles.roleChip} data-role={citation.citation_role}>
                {formatRoleLabel(citation.citation_role)}
              </span>
              <span className={styles.metaChip}>等级 {citation.evidence_level}</span>
              <span className={styles.metaChip}>{formatSourceLabel(citation.record_type)}</span>
              <span className={styles.metaChip}>记录 {formatRecordShort(citation.record_id)}</span>
              {citation.chapter_title ? <span className={styles.metaChip}>{citation.chapter_title}</span> : null}
            </div>
            {citation.snippet ? <p className={styles.evidenceSnippet}>{citation.snippet}</p> : null}
            <p className={styles.recordFootnote}>record_id: {citation.record_id}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function FollowupsPanel(props: { items: string[]; hint: string }) {
  return (
    <section className={styles.supportPanel}>
      <PanelHead title="改问建议" hint={props.hint} count={props.items.length} />
      <ul className={styles.followupsList}>
        {props.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
