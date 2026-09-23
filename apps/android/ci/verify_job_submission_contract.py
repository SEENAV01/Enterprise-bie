"""Bounded, synthetic-only loopback smoke for the persistent submission contract."""

from __future__ import annotations

from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pypdf import PdfWriter


ROOT = Path(__file__).resolve().parents[3]
BASE = "http://127.0.0.1:8765"
KEY = "6128e2b7-52ae-4f2d-92c0-282c9fc6378e"


def synthetic_pdf(pages: int) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def submit(data: bytes) -> tuple[int, dict[str, object]]:
    request = Request(
        BASE + "/v1/jobs/document-inspection",
        data=data,
        method="POST",
        headers={"Content-Type": "application/pdf", "Idempotency-Key": KEY, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read(256 * 1024 + 1))
    except HTTPError as error:
        return error.code, json.loads(error.read(256 * 1024 + 1))


def main() -> int:
    evidence = Path(sys.argv[1])
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bie-pdf-submit-smoke-") as data_root:
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts/run_bie_api.py"), "--host", "127.0.0.1", "--port", "8765"],
            cwd=ROOT,
            env={**os.environ, "BIE_DATA_ROOT": data_root},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 20
            while True:
                if process.poll() is not None:
                    raise RuntimeError("loopback API exited before readiness")
                try:
                    with urlopen(BASE + "/healthz", timeout=2) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("loopback API readiness timed out") from None
                    time.sleep(0.2)

            data = synthetic_pdf(1)
            status, first = submit(data)
            job = first.get("job", {})
            if status != 202 or first.get("api_schema_version") != "1.0":
                raise RuntimeError("submission contract status/schema mismatch")
            if not re.fullmatch(r"job-[0-9a-f]{64}", str(job.get("job_id", ""))):
                raise RuntimeError("job identity mismatch")
            if job.get("status") != "READY" or job.get("source_hash") != hashlib.sha256(data).hexdigest():
                raise RuntimeError("job state/source mismatch")
            if job.get("result_available") is not False:
                raise RuntimeError("result availability mismatch")
            replay_status, replay = submit(data)
            if replay_status != 202 or replay.get("job", {}).get("job_id") != job["job_id"]:
                raise RuntimeError("idempotent replay mismatch")
            conflict_status, conflict = submit(synthetic_pdf(2))
            if conflict_status != 409 or conflict.get("error", {}).get("code") != "idempotency_conflict":
                raise RuntimeError("conflict contract mismatch")
            safe = {
                "submission": {"http_status": status, "api_schema_version": first["api_schema_version"], "job": job},
                "replay": {"http_status": replay_status, "same_job_id": True},
                "conflict": {"http_status": conflict_status, "error_code": "idempotency_conflict"},
            }
            (evidence / "safe-job-submission.json").write_text(
                json.dumps(safe, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
            )
            print("Canonical job submission loopback: PASS")
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
