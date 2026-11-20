import type { AnswerLanguage, Language, TranslationLanguage } from "./types";

export const languageLabels: Record<Language, string> = {
  auto: "Match my language",
  en: "English",
  "zh-CN": "简体中文",
  "zh-TW": "繁體中文",
};

export const selectableLanguages: Language[] = ["auto", "en", "zh-CN"];
export const answerLanguages: TranslationLanguage[] = ["en", "zh-CN"];

export const compactLanguageLabels: Record<TranslationLanguage, string> = {
  en: "English",
  "zh-CN": "简体",
};

export function asAnswerLanguage(language: string): AnswerLanguage {
  return (["en", "zh-CN", "zh-TW"] as AnswerLanguage[]).includes(language as AnswerLanguage)
    ? (language as AnswerLanguage)
    : "en";
}
