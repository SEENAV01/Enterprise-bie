"""Real TCP/process Task028 verification using labelled SYNTHETIC_TEST input.

The smoke never manually dispatches a worker. Only safe summaries may leave its
temporary local CAS. It also serves as the bounded local lifecycle test helper.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import http.client
import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
from apps.api.job_service import PdfInspectionJobService
from structural_pdf_fixtures import structural_pdf


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


class StackProcess:
    def __init__(self, data_root: Path, port: int, *, poll_interval: float = .1):
        self.root, self.port = data_root, port
        self.lines, self.errors = [], []
        self.messages = queue.Queue(maxsize=32)
        self.process = subprocess.Popen(
            [sys.executable, "-B", str(ROOT / "scripts/run_bie_local_stack.py"),
             "--port", str(port), "--poll-interval", str(poll_interval), "--shutdown-grace", "5"],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "BIE_DATA_ROOT": str(data_root), "BIE_LOCAL_STACK_CONTROL_STDIN": "1",
                 "PYTHONDONTWRITEBYTECODE": "1"},
        )
        def drain(stream, rows, notify=False):
            while True:
                line = stream.readline(4097)
                if not line:
                    break
                if len(rows) >= 32 or len(line) > 4096:
                    self.errors.append(b"output_bound_exceeded")
                    break
                rows.append(line)
                if notify:
                    self.messages.put_nowait(line)
        self.readers = [threading.Thread(target=drain, args=(self.process.stdout, self.lines, True), daemon=True),
                        threading.Thread(target=drain, args=(self.process.stderr, self.errors), daemon=True)]
        for reader in self.readers:
            reader.start()

    def ready(self):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            require(self.process.poll() is None, "stack_exited_before_readiness")
            try:
                value = json.loads(self.messages.get(timeout=.2))
            except queue.Empty:
                continue
            if value.get("event") == "stack_ready":
                status, body = self.request("GET", "/healthz")
                require(status == 200 and body == {"status": "ok", "service": "bie-api", "api_version": "v1"}, "invalid_health")
                return
        raise RuntimeError("stack_readiness_timeout")

    def request(self, method, path, data=None, key=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            headers = {"Content-Type": "application/pdf"} if data is not None else {}
            if key:
                headers["Idempotency-Key"] = key
            connection.request(method, path, body=data, headers=headers)
            response = connection.getresponse()
            body = response.read(2 * 1024**2 + 1)
            require(len(body) <= 2 * 1024**2, "response_bound_exceeded")
            return response.status, json.loads(body)
        finally:
            connection.close()

    def submit(self, data, key):
        status, body = self.request("POST", "/v1/jobs/document-inspection", data, key)
        require(status == 202 and body["api_schema_version"] == "1.0", "submission_failed")
        job = body["job"]
        require(job["source_hash"] == hashlib.sha256(data).hexdigest(), "submission_identity_failed")
        return job

    def terminal(self, job, *, expected="SUCCEEDED", timeout=120):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            require(self.process.poll() is None, "stack_died_during_job")
            status, body = self.request("GET", f"/v1/jobs/{job['job_id']}")
            require(status == 200, "status_failed")
            final = body["job"]
            require(final["source_hash"] == job["source_hash"], "status_identity_failed")
            if final["status"] in {"SUCCEEDED", "FAILED"}:
                require(final["status"] == expected, "unexpected_terminal_state")
                if final["queue_state"] == ("ACKED" if expected == "SUCCEEDED" else "DEAD_LETTER"):
                    return final
            time.sleep(.05)
        raise RuntimeError("automatic_job_timeout")

    def stop(self):
        if self.process.stdin is not None:
            self.process.stdin.close()
            self.process.stdin = None
        forced_parent = False
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            forced_parent = True
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        for reader in self.readers:
            reader.join(2)
        self.process.stdout.close()
        self.process.stderr.close()
        output = b"".join(self.lines + self.errors)
        require(str(self.root).encode() not in output and b"Traceback" not in output, "unsafe_stack_output")
        require(not forced_parent and self.process.returncode == 0, "unclean_stack_shutdown")
        require(not self.errors, "unexpected_stack_stderr")
        last = json.loads(self.lines[-1])
        require(last["event"] == "stack_stopped" and last["children_reaped"], "children_not_reaped")
        with socket.socket() as probe:
            probe.settimeout(.5)
            require(probe.connect_ex(("127.0.0.1", self.port)) != 0, "api_process_still_listening")
        return {"children_reaped": True, "stack_exit": 0, "api_port_closed": True,
                "forced_termination": last["forced_termination"]}


def persisted_states(root, job_id):
    service = PdfInspectionJobService(root)
    try:
        return [event["to_state"] for event in service.persistence.load_run_state(job_id)["events"]]
    finally:
        service.close()


def smoke(port: int) -> dict:
    report = {"source_kind": "SYNTHETIC_TEST", "manual_once_used": False,
              "product_accepted": False, "public_deployment_claimed": False}
    with tempfile.TemporaryDirectory(prefix="bie-local-stack-smoke-") as directory:
        root = Path(directory)
        process = StackProcess(root, port)
        try:
            process.ready()
            report["readiness"] = {"http_status": 200, "loopback": True}
            pdfs = [structural_pdf(text_pages={0}, text=f"SYNTHETIC_TEST document {i}") for i in range(4)]
            first = process.submit(pdfs[0], "smoke-first")
            require(first["status"] == "READY", "initial_job_not_ready")
            final = process.terminal(first)
            code, result = process.request("GET", f"/v1/jobs/{first['job_id']}/result")
            require(code == 200 and result["result"]["source_hash"] == first["source_hash"], "result_identity_failed")
            states = persisted_states(root, first["job_id"])
            require(states == ["READY", "RUNNING", "SUCCEEDED"], "durable_transition_failed")
            report["success"] = {"status": final["status"], "queue_state": final["queue_state"],
                                 "http_status": code, "source_hash": first["source_hash"], "transitions": states}
            failed = process.submit(b"%PDF-1.7\nSYNTHETIC_TEST malformed", "smoke-bad")
            terminal = process.terminal(failed, expected="FAILED")
            code, failure = process.request("GET", f"/v1/jobs/{failed['job_id']}/result")
            require(code == 409 and failure["error"]["code"] == "job_failed", "governed_failure_failed")
            report["failed_document"] = {"status": terminal["status"], "queue_state": terminal["queue_state"], "http_status": code}
            later = [process.submit(pdf, f"smoke-later-{i}") for i, pdf in enumerate(pdfs[1:])]
            completed = [process.terminal(job) for job in later]
            report["valid_after_failure"] = "PASS"
            report["multiple_jobs"] = {"distinct_valid_sources": len({j["source_hash"] for j in [first, *later]}),
                                       "succeeded": 1 + len(completed), "automatic": True}
            report["capabilities_unchanged"] = process.request("GET", "/v1/capabilities")[1]["worker_mode"] == "local_manual_run_once_v1"
            require(report["capabilities_unchanged"], "capability_contract_changed")
        finally:
            report["shutdown"] = process.stop()

        # A slow idle interval makes queued-before-stop recovery observable. The
        # canonical queue is read after clean shutdown; a missed window FAILS.
        pending_process = StackProcess(root, port, poll_interval=60)
        try:
            pending_process.ready()
            time.sleep(2)  # allow the new worker's initial empty poll to finish
            pending = pending_process.submit(structural_pdf(text_pages={0}, text="SYNTHETIC_TEST restart"), "smoke-restart")
        finally:
            report["pre_restart_shutdown"] = pending_process.stop()
        service = PdfInspectionJobService(root)
        try:
            queued = service.status(pending["job_id"])
            require(queued["status"] == queued["queue_state"] == "READY", "queued_restart_window_not_observed")
        finally:
            service.close()
        restarted = StackProcess(root, port)
        try:
            restarted.ready()
            complete = restarted.terminal(pending)
            code, value = restarted.request("GET", f"/v1/jobs/{pending['job_id']}/result")
            require(code == 200 and value["result"]["source_hash"] == pending["source_hash"], "restart_result_failed")
            report["restart_durability"] = {"before_restart": "READY", "after_restart": complete["status"],
                                            "queue_state": complete["queue_state"], "identity_preserved": True}
        finally:
            report["restart_shutdown"] = restarted.stop()
        gc.collect()
    report["passed"] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    try:
        report = smoke(args.port)
    except Exception:
        print(json.dumps({"passed": False, "error": "local_stack_smoke_failed"}))
        return 1
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.evidence_dir:
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
        (args.evidence_dir / "safe-stack-lifecycle.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
