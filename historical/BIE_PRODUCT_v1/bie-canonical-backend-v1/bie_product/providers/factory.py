from __future__ import annotations
import os
from ai.openai_provider import OpenAIProvider


def create_provider(name: str | None = None):
    name = (name or os.getenv("BIE_PROVIDER", "openai")).lower()
    if name == "openai":
        return OpenAIProvider()
    raise ValueError(
        f"Unsupported provider '{name}'. The canonical product currently ships with OpenAI; "
        "additional providers must implement the BIEModelProvider contract."
    )
