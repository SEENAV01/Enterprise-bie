"""Real TCP/process Task028 verification using labelled SYNTHETIC_TEST input.

The smoke never manually dispatches a worker. Only safe summaries may leave its
temporary local CAS. It also serves as the bounded local lifecycle test helper.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
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


PHASES = frozenset({"startup_readiness", "success_lifecycle", "failure_continuity",
                    "multi_job_continuity", "pre_restart_ready_state", "restart_lifecycle", "shutdown", "smoke"})
CHECK_CODES = frozenset({
    "stack_exited_before_readiness", "invalid_health", "stack_readiness_timeout",
    "response_bound_exceeded", "submission_failed", "submission_identity_failed",
    "stack_died_during_job", "status_failed", "status_identity_failed", "unexpected_terminal_state",
    "automatic_job_timeout", "unsafe_stack_output", "unclean_stack_shutdown", "unexpected_stack_stderr",
    "children_not_reaped", "api_process_still_listening", "initial_job_not_ready", "result_identity_failed",
    "durable_transition_failed", "governed_failure_failed", "capability_contract_changed",
    "restart_ready_state_failed", "restart_identity_failed", "restart_result_failed", "distinct_sources_failed",
})


class SmokeCheck(RuntimeError):
    def __init__(self, code):
        self.code = code if code in CHECK_CODES else "smoke_failed"
        super().__init__(self.code)


class SmokeFailure(RuntimeError):
    def __init__(self, phase, code):
        self.phase = phase if phase in PHASES else "smoke"
        allowed = CHECK_CODES | {p + "_failed" for p in PHASES}
        self.code = code if code in allowed else self.phase + "_failed"
        self.cleanup_failures = []
        super().__init__(self.code)

    def safe_report(self):
        return {"passed": False, "error": "local_stack_smoke_failed", "phase": self.phase,
                "code": self.code, "cleanup_failures": self.cleanup_failures}


@contextmanager
def phase(name):
    name = name if name in PHASES else "smoke"
    print(json.dumps({"event": "smoke_phase", "phase": name, "state": "started"}), flush=True)
    try:
        yield
    except SmokeFailure:
        raise
    except Exception as exc:
        # Only our enumerated assertion codes can cross the evidence boundary.
        code = exc.code if isinstance(exc, SmokeCheck) else name + "_failed"
        raise SmokeFailure(name, code) from None
    print(json.dumps({"event": "smoke_phase", "phase": name, "state": "passed"}), flush=True)


def require(condition, code):
    if not condition:
        raise SmokeCheck(code)


def finish_process(process, report, key):
    """Retain the first causal failure even if owned-child cleanup also fails."""
    primary = sys.exception()
    try:
        with phase("shutdown"):
            report[key] = process.stop()
    except SmokeFailure as failure:
        if isinstance(primary, SmokeFailure):
            primary.cleanup_failures.append({"phase": failure.phase, "code": failure.code})
        else:
            raise


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
        raise SmokeCheck("stack_readiness_timeout")

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
            require(final["source_hash"] == job["source_hash"] and final["job_id"] == job["job_id"], "status_identity_failed")
            if final["status"] in {"SUCCEEDED", "FAILED"}:
                require(final["status"] == expected, "unexpected_terminal_state")
                if final["queue_state"] == ("ACKED" if expected == "SUCCEEDED" else "DEAD_LETTER"):
                    return final
            time.sleep(.05)
        raise SmokeCheck("automatic_job_timeout")

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


def prepare_restart_job(root):
    """Persist READY work with NO worker running; reopen real SQLite/CAS state.

    Called only after the previous owned stack has been stopped and reaped.
    Worker startup speed cannot consume this fixture before its READY proof.
    """
    data = structural_pdf(text_pages={0}, text="SYNTHETIC_TEST restart")
    service = PdfInspectionJobService(root)
    try:
        pending = service.submit(data, "smoke-restart")
        require(pending["source_hash"] == hashlib.sha256(data).hexdigest(), "restart_identity_failed")
    finally:
        service.close()
    reopened = PdfInspectionJobService(root)
    try:
        queued = reopened.status(pending["job_id"])
        require(queued["status"] == queued["queue_state"] == "READY", "restart_ready_state_failed")
        require(queued["job_id"] == pending["job_id"] and queued["source_hash"] == pending["source_hash"], "restart_identity_failed")
        require(persisted_states(root, pending["job_id"]) == ["READY"], "durable_transition_failed")
    finally:
        reopened.close()
    return pending


def smoke(port: int) -> dict:
    report = {"source_kind": "SYNTHETIC_TEST", "manual_once_used": False,
              "product_accepted": False, "public_deployment_claimed": False}
    with tempfile.TemporaryDirectory(prefix="bie-local-stack-smoke-") as directory:
        root = Path(directory)
        process = None
        try:
            with phase("startup_readiness"):
                process = StackProcess(root, port)
                process.ready()
                report["readiness"] = {"http_status": 200, "loopback": True}
            with phase("success_lifecycle"):
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
            with phase("failure_continuity"):
                failed = process.submit(b"%PDF-1.7\nSYNTHETIC_TEST malformed", "smoke-bad")
                terminal = process.terminal(failed, expected="FAILED")
                code, failure = process.request("GET", f"/v1/jobs/{failed['job_id']}/result")
                require(code == 409 and failure["error"]["code"] == "job_failed", "governed_failure_failed")
                report["failed_document"] = {"status": terminal["status"], "queue_state": terminal["queue_state"], "http_status": code}
            with phase("multi_job_continuity"):
                later = [process.submit(pdf, f"smoke-later-{i}") for i, pdf in enumerate(pdfs[1:])]
                completed = [process.terminal(job) for job in later]
                distinct = len({j["source_hash"] for j in [first, *later]})
                require(distinct == 4, "distinct_sources_failed")
                report["valid_after_failure"] = "PASS"
                report["multiple_jobs"] = {"distinct_valid_sources": distinct, "succeeded": 1 + len(completed), "automatic": True}
                report["capabilities_unchanged"] = process.request("GET", "/v1/capabilities")[1]["worker_mode"] == "local_manual_run_once_v1"
                require(report["capabilities_unchanged"], "capability_contract_changed")
        finally:
            if process is not None:
                finish_process(process, report, "shutdown")

        with phase("pre_restart_ready_state"):
            pending = prepare_restart_job(root)
            report["restart_setup"] = {"worker_running": False, "store_reopened": True,
                                       "status": "READY", "queue_state": "READY", "fixed_sleep_used": False}
        restarted = None
        try:
            with phase("restart_lifecycle"):
                restarted = StackProcess(root, port)
                restarted.ready()
                complete = restarted.terminal(pending)
                code, value = restarted.request("GET", f"/v1/jobs/{pending['job_id']}/result")
                require(code == 200 and value["result"]["source_hash"] == pending["source_hash"], "restart_result_failed")
                states = persisted_states(root, pending["job_id"])
                require(states == ["READY", "RUNNING", "SUCCEEDED"], "durable_transition_failed")
                report["restart_durability"] = {"before_restart": "READY", "after_restart": complete["status"],
                                                "queue_state": complete["queue_state"], "identity_preserved": True,
                                                "http_status": code, "transitions": states}
        finally:
            if restarted is not None:
                finish_process(restarted, report, "restart_shutdown")
        gc.collect()
    report["passed"] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        report = smoke(args.port)
    except SmokeFailure as failure:
        report = failure.safe_report()
    except Exception:
        report = SmokeFailure("smoke", "smoke_failed").safe_report()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.evidence_dir:
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
        (args.evidence_dir / "safe-stack-lifecycle.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
