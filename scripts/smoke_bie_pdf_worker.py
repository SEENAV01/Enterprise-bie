"""Exercise a separate worker process using only a structural PDF fixture."""

from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "productization" / "document_intelligence"
for path in (ROOT, FIXTURES):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from apps.api.main import app
from apps.api.job_service import PdfInspectionJobService
from structural_pdf_fixtures import hierarchy_pdf_with_outline


def _write_safe(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the BIE local PDF worker process")
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="bie-api-job-smoke-") as directory:
        os.environ["BIE_DATA_ROOT"] = directory
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/v1/jobs/document-inspection", content=hierarchy_pdf_with_outline(),
            headers={"content-type": "application/pdf", "Idempotency-Key": "ci-structural-smoke-v1"},
        )
        if response.status_code != 202:
            raise RuntimeError("synthetic job submission failed")
        submission = response.json()
        job_id = submission["job"]["job_id"]
        service = PdfInspectionJobService(Path(directory))
        try:
            ready = service.status(job_id)
        finally:
            service.close()
        if ready["status"] != "READY":
            raise RuntimeError("synthetic job was not ready after restart")
        worker = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_bie_pdf_worker.py"), "--once"],
            cwd=ROOT, env={**os.environ, "BIE_DATA_ROOT": directory},
            capture_output=True, text=True, check=False, timeout=120,
        )
        if worker.returncode != 0:
            raise RuntimeError("separate worker process failed")
        outcome = json.loads(worker.stdout)
        if outcome["outcome"] != "ACKED":
            raise RuntimeError("separate worker did not acknowledge the job")
        service = PdfInspectionJobService(Path(directory))
        try:
            completed = service.status(job_id)
            result = service.result(job_id)
        finally:
            service.close()
        if completed["status"] != "SUCCEEDED" or result["page_count"] != 5:
            raise RuntimeError("persisted synthetic result is invalid")
        summary = {
            "job_id": job_id,
            "status": completed["status"],
            "source_hash": result["source_hash"],
            "page_count": result["page_count"],
            "total_blocks": result["total_blocks"],
            "outline_status": result["outline_status"],
        }
        if args.evidence_dir is not None:
            args.evidence_dir.mkdir(parents=True, exist_ok=True)
            _write_safe(args.evidence_dir / "safe-submission.json", submission)
            _write_safe(args.evidence_dir / "safe-ready-status.json", ready)
            _write_safe(args.evidence_dir / "safe-completed-status.json", completed)
            _write_safe(args.evidence_dir / "safe-result-summary.json", summary)
            _write_safe(args.evidence_dir / "safe-worker-summary.json", outcome)
        print(json.dumps({"outcome": "PASS", **summary}, sort_keys=True, separators=(",", ":")))
        gc.collect()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
