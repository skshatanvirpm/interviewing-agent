from __future__ import annotations

from functools import cached_property

from openai import OpenAI

from interviewing_agent.config import Settings


class OpenAIProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def client(self) -> OpenAI | None:
        if not self.settings.openai_api_key:
            return None
        return OpenAI(api_key=self.settings.openai_api_key)
