import { FormEvent, Fragment, useMemo, useRef, useState } from "react";

type Language = "auto" | "en" | "zh-CN" | "zh-TW";

type Citation = {
  id: string;
  source: string;
  page: number;
  section: string;
  excerpt: string;
};

type ApiResponse = {
  answer: string;
  citations: Citation[];
  language: string;
  grounded: boolean;
  notice?: string;
};

type ConversationMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  grounded?: boolean;
  notice?: string;
};

const starters = [
  "What interest rate is actually guaranteed?",
  "Can I stop paying premiums temporarily?",
  "定期提款有甚麼條件？",
];

const languageLabels: Record<Language, string> = {
  auto: "Match my language",
  en: "English",
  "zh-CN": "简体中文",
  "zh-TW": "繁體中文",
};

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

  const recentCitations = useMemo(
    () => messages.slice().reverse().find((message) => message.citations?.length)?.citations ?? [],
    [messages],
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
    setMessages([...previousMessages, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          language,
          history: previousMessages.map(({ role, content }) => ({ role, content })),
        }),
      });
      if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
      const payload = (await response.json()) as ApiResponse;
      const assistantMessage: ConversationMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: payload.answer,
        citations: payload.citations,
        grounded: payload.grounded,
        notice: payload.notice,
      };
      setMessages((current) => [...current, assistantMessage]);
      if (payload.citations[0]) setActiveCitation(payload.citations[0]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "I couldn’t reach the InsureTutor service. Check that the application is running, then try again.",
          grounded: false,
          notice: error instanceof Error ? error.message : "Unexpected request error",
        },
      ]);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void submitQuestion(question);
  }

  function startOver() {
    setMessages([]);
    setActiveCitation(null);
    setQuestion("");
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
              <h1>Understand the policy.<br />Keep the fine print in view.</h1>
              <p className="opening-copy">
                Ask in English, 简体中文, or 繁體中文. Every supported answer points back to the supplied brochure,
                so you can inspect the evidence yourself.
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
              {messages.map((message) => (
                <article className={`message message-${message.role}`} key={message.id}>
                  <div className="message-meta">
                    <span>{message.role === "user" ? "You" : "InsureTutor"}</span>
                    {message.role === "assistant" && (
                      <span className={message.grounded ? "grounded" : "withheld"}>
                        {message.grounded ? "Sources checked" : "Not grounded"}
                      </span>
                    )}
                  </div>
                  <div className="message-content">
                    {message.role === "assistant" ? (
                      <AnswerText message={message} onSelect={setActiveCitation} />
                    ) : (
                      message.content
                    )}
                  </div>
                  {message.notice && <p className="message-notice">{message.notice}</p>}
                </article>
              ))}
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
                  {Object.entries(languageLabels).map(([value, label]) => (
                    <option value={value} key={value}>{label}</option>
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
