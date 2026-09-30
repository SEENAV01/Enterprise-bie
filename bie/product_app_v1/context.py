from __future__ import annotations

from pathlib import Path

from apps.api.job_service import PdfInspectionJobService
from .store import SQLiteOperatorStore


class OperatorContext:
    """Bind Section 18 product state to the existing canonical PDF job service."""

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.operator = SQLiteOperatorStore(self.data_root / "operator" / "section18.sqlite3")
        self.native_root = self.data_root / "native_pdf_jobs"

    def job_service(self) -> PdfInspectionJobService:
        return PdfInspectionJobService(self.native_root)
