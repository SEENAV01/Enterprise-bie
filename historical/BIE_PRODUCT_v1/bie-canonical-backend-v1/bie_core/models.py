from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class RunContext:
    run_id: str
    source_uri: str
    input_kind: str = "source"
    work_dir: Any = field(default_factory=lambda: __import__("pathlib").Path("output"))
    artifacts: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def emit(self, stage: str, status: str, **data):
        self.events.append({"stage": stage, "status": status, **data})
