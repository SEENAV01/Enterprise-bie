from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class OpenAIConfig:
    model: str = os.getenv("BIE_OPENAI_MODEL", "gpt-5.6-luna")
    timeout: float = float(os.getenv("BIE_OPENAI_TIMEOUT", "120"))
    max_output_tokens: int = int(os.getenv("BIE_OPENAI_MAX_OUTPUT_TOKENS", "12000"))


class OpenAIProvider:
    """Canonical BIE model-provider adapter.

    BIE owns the workflow, schemas, provenance and validation. OpenAI supplies
    model reasoning/generation behind this adapter. The API key is never stored
    in source; the official SDK reads OPENAI_API_KEY from the environment.
    """

    provider_name = "openai"

    def __init__(self, config: Optional[OpenAIConfig] = None, client=None):
        self.config = config or OpenAIConfig()
        if client is not None:
            self.client = client
        else:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "OpenAI provider requires the official openai package. "
                    "Install requirements.txt."
                ) from exc
            self.client = OpenAI(timeout=self.config.timeout)

    def generate_json(
        self,
        *,
        task: str,
        instructions: str,
        input_payload: Any,
        schema_name: str,
        schema: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        prompt = json.dumps(input_payload, ensure_ascii=False, default=str)
        response = self.client.responses.create(
            model=self.config.model,
            instructions=instructions,
            input=prompt,
            max_output_tokens=self.config.max_output_tokens,
            store=False,
            metadata={"bie_task": task, **(metadata or {})},
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        raw = response.output_text
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenAI returned non-JSON output for {task}") from exc
        return {
            "task": task,
            "provider": self.provider_name,
            "model": self.config.model,
            "response_id": getattr(response, "id", None),
            "result": result,
            "request_id": getattr(response, "_request_id", None),
        }

    def healthcheck(self) -> Dict[str, Any]:
        # Do not spend tokens for a healthcheck. Verify configuration only.
        key_present = bool(os.getenv("OPENAI_API_KEY"))
        return {
            "provider": self.provider_name,
            "model": self.config.model,
            "api_key_configured": key_present,
            "ready": key_present,
        }
