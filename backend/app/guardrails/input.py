import re
import unicodedata


INJECTION_PATTERNS = (
    r"ignore (?:all |any |the |your )?(?:previous|prior|system) instructions",
    r"(?:reveal|output|print|show) (?:your |the )?(?:system|developer) prompt",
    r"忽略.*(?:指令|指示)",
    r"(?:显示|顯示|输出|輸出).*(?:系统|系統).*提示",
)
SENSITIVE_PATTERNS = (
    r"[\w.+-]+@[\w.-]+\.[a-z]{2,}",
    r"(?<![\w])(?:[STFGM]\d{7}[A-Z]|[A-Z]{1,2}\d{6}\([0-9A]\))(?!\w)",
    r"(?<![\w])(?:\+65[ -]?)?[689]\d{3}[ -]?\d{4}(?![\w])",
    r"(?:sk-|gh[pousr]_)[a-z0-9_-]{12,}",
    r"\bBearer\s+[a-z0-9._-]{12,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
)


def looks_like_prompt_injection(message: str) -> bool:
    normalized = unicodedata.normalize("NFKC", message)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Cf")
    normalized = " ".join(normalized.split())
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in INJECTION_PATTERNS)


def redact_sensitive(text: str) -> str:
    for pattern in SENSITIVE_PATTERNS:
        text = re.sub(pattern, "[redacted]", text, flags=re.IGNORECASE)
    return text


def clearly_outside_scope(message: str) -> bool:
    return bool(re.fullmatch(
        r"(?:what is the weather(?: today)?|how do i make pancakes|"
        r"今天天气怎么样|今天天氣怎麼樣|怎樣製作班戟)[?？。.!！\s]*",
        message.strip(),
        flags=re.IGNORECASE,
    ))
