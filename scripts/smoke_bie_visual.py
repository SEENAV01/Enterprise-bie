"""Bounded real PDF/process Task034 journeys; technical source evidence only."""
import argparse
import gc
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class SmokeFailure(Exception):
    def __init__(self, code, diagnostics=None):
        self.code, self.diagnostics = code, diagnostics or {}
        super().__init__(code)


def check(value, code):
    if not value:
        raise SmokeFailure(code)


def target():
    # Explicit SYNTHETIC_TEST configuration, never a production device fallback.
    return dict(profile_id="technical-2d-readable-v1", capabilities=["2d", "math_text"],
        max_complexity=0.7, supports_interaction=False, supports_3d=False, supports_simulation=False,
        viewport_width=1280, viewport_height=720, font_px=24, foreground="#111111", background="#FFFFFF")


def journey(lines, applicability):
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.visual_producer import VisualProducerControlPlane
    from apps.operator.process_supervision import supervise, child_environment
    from apps.operator.process_limits import PdfProcessBudget
    from bie.productization.visual_contract import PROFILE, profile_config, visual_config
    from bie.productization.visual_slice import STAGES
    from bie.productization.contracts import digest
    sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
    sys.path.insert(0, str(ROOT / "tests/productization/director"))
    from structural_pdf_fixtures import positioned_text_pdf
    from protocol_support import config_for_stack
    from scripts.smoke_bie_director import excludes_private

    raw = positioned_text_pdf([[(72, 740 - 40 * i, text) for i, text in enumerate(lines)]])
    config = profile_config(director=config_for_stack(), visual=visual_config(target()))
    credentials = Credentials()
    token = secrets.token_urlsafe(40)
    principal = Principal("smoke034", "local", frozenset({"read", "source", "create", "worker"}),
                          time.time() + 180)
    credentials.grant(token, principal)
    with tempfile.TemporaryDirectory(prefix="bie-prod034-") as temporary:
        root = Path(temporary)
        operator = Service(root, credentials)
        port = VisualProducerControlPlane(operator, enabled_profiles={PROFILE})
        source = operator.import_pdf(principal, raw)
        run = port.admit(principal, source["source_id"], "smoke", producer_config=config)["run_id"]
        environment = child_environment()
        environment["BIE_OPERATOR_TOKEN"] = token
        command = [sys.executable, "-I", "-B", str(ROOT / "apps/operator/visual_worker_child.py"),
            "--data-root", str(root), "--run-id", run, "--tenant", "local", "--technical-test-providers"]
        started = time.monotonic()
        first = supervise(command, environment, PdfProcessBudget())
        child_seconds = round(time.monotonic() - started, 3)
        if not first.completed or first.exit_code != 0:
            with port.native(principal, run, "read") as native:
                saved = native.persistence.load_run_state(run)
                safe = {s: a["attempts"][-1]["diagnostics"] for s, a in saved["stages"].items()
                        if a["attempts"][-1]["diagnostics"]}
                states = {s: a["attempts"][-1]["state"] for s, a in saved["stages"].items()}
                queues = native.queue.stats()
            raise SmokeFailure("child_execution_failed" if first.completed else "child_supervision_incomplete",
                dict(safe_diagnostics=safe, persisted_stage_states=states, queue_counts=queues,
                     exit_code=first.exit_code, child_wall_seconds=child_seconds, child_output_bytes=len(first.output)))
        second = supervise(command + ["--verify-only"], environment, PdfProcessBudget())
        check(second.completed and second.exit_code == 0, "restart_failed")
        original, reopened = json.loads(first.output), json.loads(second.output)
        check(original == reopened, "restart_identity_failed")
        final = port.status(principal, run)
        check(reopened["status_sha256"] == digest(final), "full_projection_binding_failed")
        check(port.admit(principal, source["source_id"], "smoke", producer_config=config) == final,
              "idempotent_replay_failed")
        blocked = applicability == "REVIEW_REQUIRED"
        expected = dict.fromkeys(STAGES, "SUCCEEDED")
        if blocked:
            expected.update(MATH="BLOCKED", REASONING="PENDING", PEDAGOGY="PENDING",
                            DIRECTOR="PENDING", VISUAL="PENDING")
        check(final["stages"] == expected, "stage_states_failed")
        check(final["math"]["applicability"] == applicability, "math_applicability_failed")
        check(all(v == "NOT_RUN" for v in final["downstream"].values()), "downstream_execution_forbidden")
        identities = {}
        with port.native(principal, run, "read") as native:
            saved = native.persistence.load_run_state(run)
            for stage in STAGES:
                attempt = saved["stages"][stage]["attempts"][-1]
                if final["stages"][stage] == "PENDING":
                    check(not attempt["output_artifact_refs"] and not attempt["evidence_refs"], "blocked_output_forbidden")
                    continue
                message = native.queue.get(native.task_id(run, stage, attempt["attempt"]))
                check(message.state == ("DEAD_LETTER" if stage == "MATH" and blocked else "ACKED"), "queue_terminal_failed")
                identities[stage] = []
                for ref in attempt["output_artifact_refs"] + attempt["evidence_refs"]:
                    row = native.record(run, ref)
                    identities[stage].append(dict(artifact_id=ref, sha256=row.blob_digest))
                for ref in attempt["evidence_refs"]:
                    check(excludes_private(native.read(run, ref), tuple(lines) + (str(root), token)), "safe_evidence_leakage")
            if not blocked:
                plan, receipt = native.verified_visual(run, "local")
                check(len(plan["stages"]) == 8 and plan["review_required"] and not plan["accepted"], "visual_review_contract")
                check(receipt["animation_input_compatibility"], "animation_compatibility_failed")
                check(native.queue.stats()["ACKED"] == 9, "nine_acks_required")
                check(receipt["input_artifact_ids"] == saved["stages"]["VISUAL"]["attempts"][-1]["input_artifact_refs"], "visual_exact_inputs_failed")
            else:
                check(final["visual"] is None and final["director"] is None, "false_visual_success")
                check(not any(native.persistence.load_artifact(a).stage_id in ("DIRECTOR", "VISUAL")
                              for a in native.persistence.artifacts_for_run(run)), "blocked_execution_forbidden")
        check(excludes_private(final, tuple(lines) + (str(root), token)), "safe_projection_leakage")
        gc.collect()
        return dict(passed=True, stages=final["stages"], source_sha256=source["sha256"], identities=identities,
            math_applicability=applicability, visual=final["visual"], real_native_pdf=True,
            real_child_process=True, second_process_restart=True, idempotent_replay=True,
            child_wall_seconds=child_seconds, child_output_bytes=len(first.output),
            queue_terminal_verified=True, evidence_kind="SYNTHETIC_TEST", downstream_not_run=True,
            animation_executed=False, audio_complete=False, product_accepted=False)


def run_smoke():
    result = dict(passed=True, product_accepted=False)
    for name, lines, applicability in (
        ("quantitative", ("Chart B x A y B: C 2; D 3.", "2 + 3 = 5"), "REQUIRED"),
        ("chronology", ("Timeline: A at 1810; B at 1820.",), "NOT_REQUIRED"),
        ("cellular", ("Cell: A C; B C.",), "NOT_REQUIRED"),
        ("unsupported_math", ("Chart B x A y B: C 2; D 3.", "Compute the matrix inverse."), "REVIEW_REQUIRED")):
        result[name] = journey(lines, applicability)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run_smoke()
    except SmokeFailure as exc:
        result = dict(passed=False, code=exc.code, product_accepted=False, **exc.diagnostics)
    except Exception:
        result = dict(passed=False, code="visual_smoke_failed", product_accepted=False)
    raw = json.dumps(result, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
