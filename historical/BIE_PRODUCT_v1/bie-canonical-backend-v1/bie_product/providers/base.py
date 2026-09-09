from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BIEModelProvider(ABC):
    provider_name = "base"

    @abstractmethod
    def generate_json(self, *, task: str, instructions: str, input_payload: Any,
                      schema_name: str, schema: Dict[str, Any],
                      metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def healthcheck(self) -> Dict[str, Any]:
        raise NotImplementedError
