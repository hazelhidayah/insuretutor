from __future__ import annotations

import httpx


class ModelProviderError(RuntimeError):
    pass


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str, *, temperature: float | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    @staticmethod
    def _extract_content(payload: object) -> str:
        try:
            content = payload["choices"][0]["message"]["content"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelProviderError("The model provider returned an unexpected response shape.") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelProviderError("The model provider returned an empty response.")
        return content.strip()

    async def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.configured:
            raise ModelProviderError(
                "No model provider is configured. Add MODEL_API_KEY, MODEL_BASE_URL, and MODEL_NAME to .env."
            )

        request_body: dict[str, object] = {"model": self.model, "messages": messages}
        if self.temperature is not None:
            request_body["temperature"] = self.temperature

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=request_body,
                )
                response.raise_for_status()
                payload = response.json()
                return self._extract_content(payload)
        except ModelProviderError:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise ModelProviderError(f"The configured model provider could not complete the request: {exc}") from exc

