from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional
from canonical_pipeline import CanonicalBIE
from .providers.factory import create_provider

class BIEProduct:
    """Stable product boundary around the canonical M1-M300 BIE engine."""
    version = "1.0.0"

    def __init__(self, work_dir: str = "output", provider=None):
        self.work_dir = Path(work_dir)
        self.provider = provider or create_provider()
        self.engine = CanonicalBIE(work_dir=self.work_dir, provider=self.provider)

    def health(self) -> Dict[str, Any]:
        return {
            "product": "BIE",
            "version": self.version,
            "engine": "canonical-m1-m300",
            "provider": self.provider.healthcheck(),
            "capabilities": [
                "document_understanding", "book_structure", "knowledge",
                "lesson_planning", "script_generation", "scene_planning",
                "video_generation_code"
            ],
        }

    def process(self, source_path: str, task: str = "book_to_video_code") -> Dict[str, Any]:
        if task != "book_to_video_code":
            raise ValueError("Unsupported task. Available task: book_to_video_code")
        ctx = self.engine.run(source_path)
        return {
            "run_id": ctx.run_id,
            "status": ctx.artifacts["manifest"]["status"],
            "manifest": ctx.artifacts["manifest"],
            "artifacts": ctx.artifacts,
            "workspace": str(self.work_dir.resolve()),
        }
