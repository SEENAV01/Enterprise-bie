"""Native-PDF Task032 journeys, real process restart and Director input checks."""
import argparse
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class SmokeFailure(Exception):
    def __init__(self, phase, code):
        self.phase, self.code = phase, code


def require(condition, phase, code):
    if not condition:
        raise SmokeFailure(phase, code)


def journey(lines, applicability):
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.pedagogy_producer import PedagogyProducerControlPlane
    from apps.operator.process_supervision import supervise, child_environment
    from apps.operator.process_limits import PdfProcessBudget
    from bie.productization.pedagogy_plan import PROFILE
    from bie.productization.pedagogy_slice import STAGES
    sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
    from structural_pdf_fixtures import positioned_text_pdf

    credentials = Credentials()
    token = secrets.token_urlsafe(40)
    principal = Principal("smoke", "local", frozenset({"read", "source", "create", "worker"}),
                          time.time() + 180)
    credentials.grant(token, principal)
    raw = positioned_text_pdf([[(72, 740 - 40 * index, text) for index, text in enumerate(
        ("Birds requires Flight.",) + tuple(lines))]])
    with tempfile.TemporaryDirectory(prefix="bie-prod032-") as temporary:
        root = Path(temporary)
        operator = Service(root, credentials)
        port = PedagogyProducerControlPlane(operator, enabled_profiles={PROFILE})
        source = operator.import_pdf(principal, raw)
        run = port.admit(principal, source["source_id"], "smoke")["run_id"]
        environment = child_environment()
        environment["BIE_OPERATOR_TOKEN"] = token
        command = [sys.executable, "-I", "-B", str(ROOT / "apps/operator/pedagogy_worker_child.py"),
                   "--data-root", str(root), "--run-id", run, "--tenant", "local"]
        child = supervise(command, environment, PdfProcessBudget())
        require(child.completed, applicability, "child_supervision_incomplete")
        require(child.exit_code == 0, applicability, "child_execution_failed")
        initial = json.loads(child.output)
        reopened = supervise(command + ["--verify-only"], environment, PdfProcessBudget())
        require(reopened.completed and reopened.exit_code == 0, applicability, "restart_failed")
        final = json.loads(reopened.output)["result"]
        require(initial["result"] == final, applicability, "restart_identity_failed")
        require(port.admit(principal, source["source_id"], "smoke") == final,
                applicability, "idempotent_replay_failed")
        blocked = applicability == "REVIEW_REQUIRED"
        expected = {stage: "SUCCEEDED" for stage in STAGES}
        if blocked:
            expected.update(MATH="BLOCKED", REASONING="PENDING", PEDAGOGY="PENDING")
        require(final["stages"] == expected, applicability, "stage_scope_failed")
        require(final["math"]["applicability"] == applicability,
                applicability, "math_applicability_failed")
        require(all(state == "NOT_RUN" for state in final["downstream"].values()),
                applicability, "downstream_execution_forbidden")
        require(final["source_sha256"] == source["sha256"], applicability, "source_identity_failed")

        director_compatible = False
        with port.native(principal, run, "read") as native:
            snapshot = native.persistence.load_run_state(run)
            for stage in STAGES:
                attempt = snapshot["stages"][stage]["attempts"][-1]
                if blocked and stage in ("REASONING", "PEDAGOGY"):
                    require(not attempt["output_artifact_refs"] and not attempt["evidence_refs"],
                            applicability, "blocked_downstream_output_forbidden")
                    continue
                terminal = "DEAD_LETTER" if blocked and stage == "MATH" else "ACKED"
                task = native.queue.get(native.task_id(run, stage, attempt["attempt"]))
                require(task.state == terminal, applicability, "queue_terminal_failed")
                require(bool(attempt["evidence_refs"]), applicability, "stage_evidence_missing")
                for reference in attempt["output_artifact_refs"] + attempt["evidence_refs"]:
                    record = native.record(run, reference)
                    require(record.run_id == run, applicability, "artifact_identity_failed")
                    if stage != "SOURCE":
                        require(set(attempt["input_artifact_refs"]) <= set(record.parent_artifact_ids),
                                applicability, "artifact_ancestry_failed")
                for reference in attempt["evidence_refs"]:
                    evidence = json.dumps(native.read(run, reference), sort_keys=True)
                    require(all(fragment not in evidence for fragment in
                                ("Birds", "Flight", "2 + 3", str(root), token)),
                            applicability, "safe_evidence_leakage")
            if not blocked:
                # The actual canonical loader validates inputs; no Director stage executes.
                native.director_inputs(run, principal.tenant)
                director_compatible = True
                require(native.queue.stats()["ACKED"] == 7, applicability, "seven_acks_required")
        if not blocked:
            require(final["slice_complete"] and final["pedagogy"]["director_compatible"],
                    applicability, "pedagogy_completion_failed")
            require(final["reasoning"]["math_artifact_id"] == final["math"]["artifact_id"]
                    and final["reasoning"]["math_sha256"] == final["math"]["sha256"],
                    applicability, "reasoning_math_binding_failed")
        else:
            require(final["pedagogy"] is None and final["reasoning"] is None
                    and not final["slice_complete"], applicability, "unsupported_math_false_success")
        safe = json.dumps(final, sort_keys=True)
        require(all(fragment not in safe for fragment in ("Birds", "Flight", "2 + 3", str(root), token)),
                applicability, "safe_projection_leakage")
        return dict(passed=True, evidence_kind="SYNTHETIC_TEST",
                    technical_evidence="TECHNICAL_SOURCE_DERIVED", source_sha256=source["sha256"],
                    stages=final["stages"], math=final["math"], reasoning=final["reasoning"],
                    pedagogy=final["pedagogy"], native_pdf=True, real_child_process=True,
                    restart_in_second_process=True, artifact_identity_preserved=True,
                    queue_terminal_states_verified=True, enforcement=initial["enforcement"],
                    idempotent_replay=True, director_input_compatibility=director_compatible,
                    director_executed=False, downstream_not_run=True,
                    academic_acceptance=False, product_accepted=False, live_provider_executed=False)


def run_smoke():
    result = dict(passed=True, product_accepted=False)
    for label, lines, applicability in (
            ("supported_math", ("2 + 3 = 5",), "REQUIRED"),
            ("non_math", (), "NOT_REQUIRED"),
            ("unsupported_math", ("Compute the matrix inverse.",), "REVIEW_REQUIRED")):
        try:
            result[label] = journey(lines, applicability)
        except SmokeFailure:
            raise
        except Exception:
            raise SmokeFailure(label, "journey_verification_failed") from None
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run_smoke()
    except SmokeFailure as error:
        result = dict(passed=False, phase=error.phase, code=error.code, product_accepted=False)
    except Exception:
        result = dict(passed=False, code="pedagogy_process_smoke_failed", product_accepted=False)
    raw = json.dumps(result, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
