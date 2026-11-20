export type Language = "auto" | "en" | "zh-CN" | "zh-TW";
export type AnswerLanguage = Exclude<Language, "auto">;
export type TranslationLanguage = Extract<AnswerLanguage, "en" | "zh-CN">;

export type Citation = {
  id: string;
  source: string;
  page: number;
  section: string;
  excerpt: string;
};

export type ApiResponse = {
  answer: string;
  citations: Citation[];
  language: string;
  grounded: boolean;
  notice?: string;
};

export type ConversationMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  grounded?: boolean;
  notice?: string;
  answerLanguage?: AnswerLanguage;
  question?: string;
  requestHistory?: HistoryMessage[];
};

export type HistoryMessage = Pick<ConversationMessage, "role" | "content">;

export type AnswerVariant = {
  content: string;
  citations: Citation[];
  grounded: boolean;
  notice?: string;
};
