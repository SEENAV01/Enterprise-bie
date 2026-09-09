from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class RunContext:
    run_id: str
    source_uri: str
    input_kind: str = "source"
    artifacts: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    work_dir: Path = field(default_factory=lambda: Path("output"))

    def emit(self, stage: str, status: str, **data):
        self.events.append({"stage": stage, "status": status, **data})
