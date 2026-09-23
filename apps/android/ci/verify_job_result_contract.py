"""Synthetic-only loopback smoke for canonical persistent job status and result."""

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
MAX_RESPONSE = 256 * 1024
COUNTS = (
    "total_blocks", "heading_candidate_count", "materialized_chapter_count",
    "materialized_section_count", "materialized_subsection_count",
    "native_outline_entry_count", "outline_resolvable_page_count",
    "reconciliation_match_count", "unmatched_outline_count",
    "ambiguous_detected_title_count", "exact_page_match_count",
)


def request(path: str, *, data: bytes | None = None, key: str | None = None) -> tuple[int, dict]:
    headers = {"Accept": "application/json"}
    if data is not None:
        headers.update({"Content-Type": "application/pdf", "Idempotency-Key": key or ""})
    req = Request(BASE + path, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urlopen(req, timeout=15) as response:
            payload = response.read(MAX_RESPONSE + 1)
            status = response.status
    except HTTPError as error:
        payload = error.read(MAX_RESPONSE + 1)
        status = error.code
    if len(payload) > MAX_RESPONSE:
        raise RuntimeError("loopback response exceeded bound")
    return status, json.loads(payload)


def synthetic_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def worker(env: dict[str, str], expected: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_bie_pdf_worker.py"), "--once"],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, timeout=60, check=False,
    )
    try:
        outcome = json.loads(completed.stdout)
    except ValueError as exc:
        raise RuntimeError("worker did not return governed outcome") from exc
    if outcome.get("outcome") != expected or completed.returncode != (0 if expected == "ACKED" else 1):
        raise RuntimeError("worker outcome mismatch")


def require_status(job_id: str, source_hash: str, stage: str, queue: str, available: bool) -> dict:
    http, payload = request(f"/v1/jobs/{job_id}")
    job = payload.get("job", {})
    if http != 200 or payload.get("api_schema_version") != "1.0" or any((
        job.get("job_id") != job_id,
        job.get("source_hash") != source_hash,
        job.get("status") != stage,
        job.get("queue_state") != queue,
        job.get("result_available") is not available,
    )):
        raise RuntimeError("job status contract mismatch")
    return payload


def main() -> int:
    evidence = Path(sys.argv[1])
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bie-job-result-smoke-") as data_root:
        env = {**os.environ, "BIE_DATA_ROOT": data_root}
        api = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts/run_bie_api.py"), "--host", "127.0.0.1", "--port", "8765"],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 20
            while True:
                if api.poll() is not None:
                    raise RuntimeError("loopback API exited before readiness")
                try:
                    status, health = request("/healthz")
                    if status == 200 and health.get("status") == "ok":
                        break
                except (URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("loopback API readiness timed out") from None
                    time.sleep(0.2)

            data = synthetic_pdf()
            source_hash = hashlib.sha256(data).hexdigest()
            status, submitted = request(
                "/v1/jobs/document-inspection", data=data,
                key="task026-success-synthetic",
            )
            job = submitted.get("job", {})
            job_id = job.get("job_id", "")
            if status != 202 or submitted.get("api_schema_version") != "1.0" or not re.fullmatch(r"job-[0-9a-f]{64}", job_id):
                raise RuntimeError("success submission contract mismatch")
            if job.get("source_hash") != source_hash or job.get("status") != "READY":
                raise RuntimeError("success submission identity mismatch")
            ready = require_status(job_id, source_hash, "READY", "READY", False)
            worker(env, "ACKED")
            succeeded = require_status(job_id, source_hash, "SUCCEEDED", "ACKED", True)
            result_status, result = request(f"/v1/jobs/{job_id}/result")
            safe = result.get("result", {})
            if result_status != 200 or result.get("api_schema_version") != "1.0" or result.get("job_id") != job_id:
                raise RuntimeError("result envelope mismatch")
            if safe.get("source_hash") != source_hash or not isinstance(safe.get("byte_length"), int) or safe["byte_length"] <= 0:
                raise RuntimeError("safe result identity mismatch")
            if not isinstance(safe.get("page_count"), int) or safe["page_count"] < 1:
                raise RuntimeError("safe page count mismatch")
            if any(not isinstance(safe.get(name), int) or safe[name] < 0 for name in COUNTS):
                raise RuntimeError("safe result count mismatch")
            if not safe.get("hierarchy_policy") or not safe.get("toc_reconciliation_policy") or safe.get("outline_status") not in {
                "no_native_outline", "native_outline_reconciled",
            }:
                raise RuntimeError("safe result policy mismatch")
            repeat_status, repeat = request(f"/v1/jobs/{job_id}/result")
            if repeat_status != 200 or repeat != result:
                raise RuntimeError("safe result replay mismatch")

            malformed = b"%PDF-1.7\ninvalid synthetic document"
            failed_hash = hashlib.sha256(malformed).hexdigest()
            failed_status, failed_submit = request(
                "/v1/jobs/document-inspection", data=malformed,
                key="task026-failure-synthetic",
            )
            failed_id = failed_submit.get("job", {}).get("job_id", "")
            if failed_status != 202 or not re.fullmatch(r"job-[0-9a-f]{64}", failed_id):
                raise RuntimeError("failure submission contract mismatch")
            worker(env, "FAILED")
            failed = require_status(failed_id, failed_hash, "FAILED", "DEAD_LETTER", False)
            error_status, failed_result = request(f"/v1/jobs/{failed_id}/result")
            if error_status != 409 or failed_result.get("error", {}).get("code") != "job_failed":
                raise RuntimeError("failed-result contract mismatch")

            receipts = {
                "submission": {"http_status": status, "job_id": job_id, "source_hash": source_hash},
                "ready_status": ready,
                "succeeded_status": succeeded,
                "safe_result_summary": {key: safe[key] for key in (
                    "source_hash", "byte_length", "page_count", *COUNTS,
                    "hierarchy_policy", "toc_reconciliation_policy", "outline_status",
                )},
                "failed_status": failed,
                "failed_result_error": {"http_status": error_status, "error_code": "job_failed"},
            }
            for name, item in receipts.items():
                (evidence / f"{name.replace('_', '-')}.json").write_text(
                    json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8",
                )
            print("Canonical job success/failure lifecycle loopback: PASS")
            return 0
        finally:
            api.terminate()
            try:
                api.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api.kill()
                api.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
