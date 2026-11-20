import { FormEvent, Fragment, useMemo, useRef, useState } from "react";

import type { ApiResponse, AnswerVariant, Citation, ConversationMessage, Language } from "./chat/types";
import { asAnswerLanguage, languageLabels, selectableLanguages } from "./chat/languages";
import { TranslationControls, useAnswerTranslation } from "./features/answer-translation";

const starters = [
  "What interest rate is actually guaranteed?",
  "Can I stop paying premiums temporarily?",
  "定期提款有什么条件？",
];

function SourceMark({
  label,
  citations,
  onSelect,
}: {
  label: string;
  citations: Citation[];
  onSelect: (citation: Citation) => void;
}) {
  const citation = citations.find((item) => item.id === label);
  if (!citation) return <span>[{label}]</span>;
  return (
    <button className="source-mark" type="button" onClick={() => onSelect(citation)}>
      {label}
    </button>
  );
}

function AnswerText({
  message,
  onSelect,
}: {
  message: ConversationMessage;
  onSelect: (citation: Citation) => void;
}) {
  const citations = message.citations ?? [];
  const parts = message.content.split(/\[(S\d+)\]/g);
  return (
    <>
      {parts.map((part, index) =>
        /^S\d+$/.test(part) ? (
          <SourceMark key={`${part}-${index}`} label={part} citations={citations} onSelect={onSelect} />
        ) : (
          <Fragment key={`${part}-${index}`}>{part}</Fragment>
        ),
      )}
    </>
  );
}

function App() {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [language, setLanguage] = useState<Language>("auto");
  const [loading, setLoading] = useState(false);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const activeRequestRef = useRef<AbortController | null>(null);

  const { translating, translate, reset, variants } = useAnswerTranslation();
  const recentCitations = useMemo(
    () => messages.slice().reverse().map((message) => ({ ...message, ...variants[message.id]?.displayed })).find((message) => message.citations?.length)?.citations ?? [],
    [messages, variants],
  );

  async function submitQuestion(value: string) {
    const trimmed = value.trim();
    if (!trimmed || loading) return;

    const userMessage: ConversationMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    const previousMessages = messages;
    const requestHistory = previousMessages.map(({ role, content }) => ({ role, content }));
    setMessages([...previousMessages, userMessage]);
    setQuestion("");
    setLoading(true);
    const controller = new AbortController();
    activeRequestRef.current?.abort();
    activeRequestRef.current = controller;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        signal: controller.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          language,
          history: requestHistory,
        }),
      });
      if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
      const payload = (await response.json()) as ApiResponse;
      const responseLanguage = asAnswerLanguage(payload.language);
      const answerVariant: AnswerVariant = {
        content: payload.answer,
        citations: payload.citations,
        grounded: payload.grounded,
        notice: payload.notice,
      };
      const assistantMessage: ConversationMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        ...answerVariant,
        question: trimmed,
        requestHistory,
        answerLanguage: responseLanguage,
      };
      setMessages((current) => [...current, assistantMessage]);
      if (payload.citations[0]) setActiveCitation(payload.citations[0]);
    } catch (error) {
      if (controller.signal.aborted) return;
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "InsureTutor is temporarily unavailable. Please try again. If the issue continues, check that the application is running.",
          grounded: false,
          notice: error instanceof Error ? error.message : "Unexpected request error",
        },
      ]);
    } finally {
      if (activeRequestRef.current === controller) {
        activeRequestRef.current = null;
        setLoading(false);
        requestAnimationFrame(() => inputRef.current?.focus());
      }
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void submitQuestion(question);
  }

  function startOver() {
    activeRequestRef.current?.abort();
    reset();
    activeRequestRef.current = null;
    setMessages([]);
    setActiveCitation(null);
    setQuestion("");
    setLoading(false);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  const displayedCitations = activeCitation
    ? [activeCitation, ...recentCitations.filter((item) => item.id !== activeCitation.id)]
    : recentCitations;

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="wordmark" href="#main" aria-label="InsureTutor home">
          <span className="wordmark-seal" aria-hidden="true">IT</span>
          <span>
            <strong>InsureTutor</strong>
            <small>Policy answers, with evidence</small>
          </span>
        </a>
        <div className="topbar-actions">
          <span className="corpus-status"><i aria-hidden="true" /> Brochure connected</span>
          <button className="quiet-button" type="button" onClick={startOver} disabled={messages.length === 0}>
            New conversation
          </button>
        </div>
      </header>

      <main id="main" className="workspace">
        <section className="conversation" aria-label="Conversation">
          {messages.length === 0 ? (
            <div className="opening">
              <p className="opening-index">FLEXI-ULife Prime Saver · Reference edition</p>
              <h1>Understand the plan<br />and its conditions.</h1>
              <p className="opening-copy">
                Ask about benefits, charges, or conditions in English or 简体中文.
                Open a cited brochure page to review the details for yourself.
              </p>
              <div className="starter-list" aria-label="Example questions">
                {starters.map((starter) => (
                  <button type="button" key={starter} onClick={() => void submitQuestion(starter)}>
                    <span>{starter}</span>
                    <span aria-hidden="true">Ask</span>
                  </button>
                ))}
              </div>
              <p className="opening-note">
                Educational information only. InsureTutor does not assess suitability or replace the policy contract.
              </p>
            </div>
          ) : (
            <div className="message-list" aria-live="polite">
              {messages.map((message) => {
                const variant = variants[message.id];
                const displayed = { ...message, ...variant?.displayed };
                const translatingThisMessage = translating?.messageId === message.id;
                return (
                <article className={`message message-${message.role}`} key={message.id} lang={variant?.language ?? message.answerLanguage}>
                  <div className="message-meta">
                    <span>{message.role === "user" ? "You" : "InsureTutor"}</span>
                    {message.role === "assistant" && (
                      <span className={displayed.grounded ? "grounded" : "withheld"}>
                        {displayed.grounded ? "Sources checked" : "Not grounded"}
                      </span>
                    )}
                  </div>
                  <div className="message-content">
                    {message.role === "assistant" ? (
                      <AnswerText message={displayed} onSelect={setActiveCitation} />
                    ) : (
                      message.content
                    )}
                  </div>
                  {displayed.notice && <p className="message-notice">{displayed.notice}</p>}
                  {message.role === "assistant" && message.question && (
                    <TranslationControls
                      language={variant?.language ?? message.answerLanguage}
                      pending={translatingThisMessage ? translating.language : undefined}
                      disabled={Boolean(translating) || loading}
                      error={variant?.error}
                      onSelect={(target) => void translate(message, target, setActiveCitation)}
                    />
                  )}
                </article>
                );
              })}
              {loading && (
                <div className="thinking" role="status">
                  <span /><span /><span /> Checking the brochure
                </div>
              )}
            </div>
          )}

          <form className="composer" onSubmit={handleSubmit}>
            <label htmlFor="question">Ask about the plan</label>
            <textarea
              id="question"
              ref={inputRef}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="e.g. Is the 4% interest rate guaranteed?"
              rows={2}
              maxLength={2000}
              disabled={loading}
            />
            <div className="composer-tools">
              <label className="language-picker">
                <span>Reply in</span>
                <select value={language} onChange={(event) => setLanguage(event.target.value as Language)}>
                  {selectableLanguages.map((value) => (
                    <option value={value} key={value}>{languageLabels[value]}</option>
                  ))}
                </select>
              </label>
              <span className="character-count">{question.length}/2000</span>
              <button className="send-button" type="submit" disabled={!question.trim() || loading}>
                {loading ? "Checking…" : "Ask InsureTutor"}
              </button>
            </div>
          </form>
        </section>

        <aside className="evidence" aria-label="Source evidence">
          <div className="evidence-heading">
            <div>
              <p>Source desk</p>
              <h2>Evidence used</h2>
            </div>
            <span>{displayedCitations.length || "—"}</span>
          </div>

          {displayedCitations.length ? (
            <div className="evidence-list">
              {displayedCitations.map((citation) => (
                <button
                  type="button"
                  key={`${citation.id}-${citation.page}`}
                  className={`evidence-item ${activeCitation?.id === citation.id ? "active" : ""}`}
                  onClick={() => setActiveCitation(citation)}
                >
                  <span className="page-tab">p. {citation.page}</span>
                  <strong>{citation.section}</strong>
                  <span>{citation.excerpt}</span>
                  <small>{citation.source}</small>
                </button>
              ))}
            </div>
          ) : (
            <div className="evidence-empty">
              <div className="document-glyph" aria-hidden="true">
                <span /><span /><span /><span />
              </div>
              <h3>Your sources will appear here</h3>
              <p>Ask a question to see the exact brochure pages used to support the response.</p>
            </div>
          )}

          <div className="evidence-footer">
            <strong>About the source</strong>
            <p>The brochure contains general information and may not include every policy term or exclusion.</p>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
