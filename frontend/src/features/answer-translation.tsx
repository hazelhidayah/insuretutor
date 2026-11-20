import { useRef, useState } from "react";
import { answerLanguages, compactLanguageLabels, languageLabels } from "../chat/languages";
import type { AnswerLanguage, AnswerVariant, ApiResponse, Citation, ConversationMessage, TranslationLanguage } from "../chat/types";

type VariantState = {
  language?: AnswerLanguage;
  displayed?: AnswerVariant;
  cache?: Partial<Record<TranslationLanguage, AnswerVariant>>;
  error?: string;
};

export function useAnswerTranslation() {
  const [variants, setVariants] = useState<Record<string, VariantState>>({});
  const [translating, setTranslating] = useState<{ messageId: string; language: TranslationLanguage } | null>(null);
  const request = useRef<AbortController | null>(null);

  function update(id: string, state: VariantState) {
    setVariants((current) => ({ ...current, [id]: { ...current[id], ...state } }));
  }

  function reset() {
    request.current?.abort();
    request.current = null;
    setVariants({});
    setTranslating(null);
  }

  async function translate(message: ConversationMessage, language: TranslationLanguage, onCitation: (citation: Citation | null) => void) {
    if (!message.question || request.current) return;
    const current = variants[message.id];
    if ((current?.language ?? message.answerLanguage) === language) return;
    if (message.answerLanguage === language) {
      update(message.id, { language, displayed: undefined, error: undefined });
      onCitation(message.citations?.[0] ?? null);
      return;
    }
    const cached = current?.cache?.[language];
    if (cached) {
      update(message.id, { language, displayed: cached, error: undefined });
      onCitation(cached.citations[0] ?? null);
      return;
    }

    const controller = new AbortController();
    request.current = controller;
    setTranslating({ messageId: message.id, language });
    update(message.id, { error: undefined });
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        signal: controller.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message.question, language, history: message.requestHistory ?? [] }),
      });
      if (!response.ok) throw new Error("Answer regeneration failed.");
      const payload = (await response.json()) as ApiResponse;
      if (controller.signal.aborted) return;
      if (message.grounded && !payload.grounded) throw new Error("The regenerated answer was withheld.");
      const displayed = { content: payload.answer, citations: payload.citations, grounded: payload.grounded, notice: payload.notice };
      update(message.id, { language, displayed, cache: { ...current?.cache, [language]: displayed } });
      onCitation(displayed.citations[0] ?? null);
    } catch {
      if (!controller.signal.aborted) {
        update(message.id, { error: "This answer could not be shown in the selected language. Please try again." });
      }
    } finally {
      if (request.current === controller) {
        request.current = null;
        setTranslating(null);
      }
    }
  }

  return { variants, translating, translate, reset };
}

export function TranslationControls({ language, pending, disabled, error, onSelect }: {
  language?: AnswerLanguage;
  pending?: TranslationLanguage;
  disabled: boolean;
  error?: string;
  onSelect: (language: TranslationLanguage) => void;
}) {
  return (
    <>
      <div className="translation-tools" aria-label="Translate answer">
        <span>Translate answer</span>
        <div>
          {answerLanguages.map((target) => (
            <button
              type="button"
              key={target}
              aria-pressed={language === target}
              aria-label={`Show answer in ${languageLabels[target]}`}
              onClick={() => onSelect(target)}
              disabled={disabled}
            >
              {compactLanguageLabels[target]}
            </button>
          ))}
        </div>
        {pending && <span className="translation-status" role="status">Translating to {languageLabels[pending]}…</span>}
      </div>
      {error && <p className="message-notice" role="alert">{error}</p>}
    </>
  );
}
