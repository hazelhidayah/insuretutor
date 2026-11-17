from __future__ import annotations

import httpx


class ModelProviderError(RuntimeError):
    pass


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    async def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.configured:
            raise ModelProviderError(
                "No model provider is configured. Add MODEL_API_KEY, MODEL_BASE_URL, and MODEL_NAME to .env."
            )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.1,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                return payload["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise ModelProviderError(f"The configured model provider could not complete the request: {exc}") from exc

