import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "none",
).strip().lower()

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "",
).strip()

OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://api.openai.com/v1",
).strip()

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "gpt-4o-mini",
).strip()


class LLMClient:
    """
    Optional LLM wrapper.

    If no LLM is configured, the pipeline uses its
    deterministic evidence-grounded writer.

    Supported provider:
        openai_compatible
    """

    def __init__(self):
        self.provider = LLM_PROVIDER
        self.api_key = OPENAI_API_KEY
        self.base_url = OPENAI_BASE_URL
        self.model = LLM_MODEL

    def enabled(self) -> bool:
        return (
            self.provider == "openai_compatible"
            and bool(self.api_key)
        )

    def complete(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 700,
    ) -> str:

        if not self.enabled():
            return ""

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an enterprise knowledge "
                            "assistant. Answer only from the "
                            "provided evidence."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if not response.choices:
                return ""

            content = (
                response.choices[0]
                .message
                .content
            )

            return (content or "").strip()

        except Exception as exc:

            print(
                f"[LLM] Request failed: {exc}"
            )

            return ""


llm = LLMClient()