import json
from typing import Protocol

from openai import OpenAI


class LLMClient(Protocol):
    """Duck-typed interface every agent depends on. Swap in a fake for tests."""

    def complete_json(self, system: str, user: str) -> dict: ...

    def complete_text(self, system: str, user: str) -> str: ...


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to create an OpenAIClient")
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete_json(self, system: str, user: str) -> dict:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def complete_text(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        return (response.choices[0].message.content or "").strip()
