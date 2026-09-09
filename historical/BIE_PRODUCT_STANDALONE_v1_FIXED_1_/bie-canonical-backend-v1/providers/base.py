from __future__ import annotations
from typing import Any, Dict, Protocol

class LLMProvider(Protocol):
    provider_name: str
    def generate_json(self, *, task: str, instructions: str, input_payload: Any,
                      schema_name: str, schema: Dict[str, Any], metadata: Dict[str, str] | None = None) -> Dict[str, Any]: ...
    def healthcheck(self) -> Dict[str, Any]: ...
