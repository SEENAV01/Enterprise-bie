"""Real native-PDF Task033 journeys through the hardened Director assembly.

Protocol providers require the explicit technical-test child flag. Uploaded
receipts contain safe identities/counts only, never source or generated speech.
"""
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
    def __init__(self, phase, code, **diagnostics):
        self.phase, self.code = phase, code
        self.diagnostics = diagnostics


def require(condition, phase, code):
    if not condition:
        raise SmokeFailure(phase, code)


def decoded_strings(value):
    """Inspect private fragments after decoding, including Windows paths."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from decoded_strings(key)
            yield from decoded_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from decoded_strings(item)


def excludes_private(value, fragments):
    return all(fragment not in field for field in decoded_strings(value)
               for fragment in fragments)


def journey(lines, applicability):
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.director_producer import DirectorProducerControlPlane
    from apps.operator.process_supervision import supervise, child_environment
    from apps.operator.process_limits import PdfProcessBudget
    from bie.productization.director_contract import PROFILE, profile_config
    from bie.productization.director_slice import STAGES
    sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
    sys.path.insert(0, str(ROOT / "tests/productization/director"))
    from structural_pdf_fixtures import positioned_text_pdf
    from protocol_support import config_for_stack

    credentials = Credentials()
    token = secrets.token_urlsafe(40)
    principal = Principal("smoke", "local", frozenset({"read", "source", "create", "worker"}),
                          time.time() + 180)
    credentials.grant(token, principal)
    # The process smoke is the smallest bounded native composition journey.
    # Multi-unit dependency coverage belongs to authored preservation tests.
    source_lines = ("Birds.",) + tuple(lines)
    raw = positioned_text_pdf([[(72, 740 - 40 * index, text)
                                for index, text in enumerate(source_lines)]])
    config = profile_config(director=config_for_stack())
    with tempfile.TemporaryDirectory(prefix="bie-prod033-") as temporary:
        root = Path(temporary)
        operator = Service(root, credentials)
        port = DirectorProducerControlPlane(operator, enabled_profiles={PROFILE})
        source = operator.import_pdf(principal, raw)
        run = port.admit(principal, source["source_id"], "smoke", producer_config=config)["run_id"]
        environment = child_environment()
        environment["BIE_OPERATOR_TOKEN"] = token
        command = [sys.executable, "-I", "-B", str(ROOT / "apps/operator/director_worker_child.py"),
                   "--data-root", str(root), "--run-id", run, "--tenant", "local",
                   "--technical-test-providers"]
        started = time.monotonic()
        child = supervise(command, environment, PdfProcessBudget())
        child_elapsed = round(time.monotonic() - started, 3)
        if not child.completed:
            diagnostics = dict(child_wall_seconds=child_elapsed, child_exit_code=child.exit_code,
                               child_output_bytes=len(child.output))
            # Read only committed outer state after supervision has stopped;
            # never decode private/native Director output to diagnose a limit.
            try:
                with port.native(principal, run, "read") as stopped:
                    saved = stopped.persistence.load_run_state(run)
                    diagnostics["persisted_stage_states"] = {
                        stage: saved["stages"][stage]["attempts"][-1]["state"] for stage in STAGES}
                    diagnostics["queue_counts"] = stopped.queue.stats()
                    diagnostics["state_readback"] = "AVAILABLE"
            except Exception:
                diagnostics["state_readback"] = "UNAVAILABLE"
            raise SmokeFailure(applicability, "child_supervision_incomplete",
                               **diagnostics)
        require(child.exit_code == 0, applicability, "child_execution_failed")
        initial = json.loads(child.output)
        started = time.monotonic()
        reopened = supervise(command + ["--verify-only"], environment, PdfProcessBudget())
        restart_elapsed = round(time.monotonic() - started, 3)
        require(reopened.completed and reopened.exit_code == 0, applicability, "restart_failed")
        final = json.loads(reopened.output)["result"]
        require(initial["result"] == final, applicability, "restart_identity_failed")
        require(port.admit(principal, source["source_id"], "smoke", producer_config=config) == final,
                applicability, "idempotent_replay_failed")
        blocked = applicability == "REVIEW_REQUIRED"
        expected = {stage: "SUCCEEDED" for stage in STAGES}
        if blocked:
            expected.update(MATH="BLOCKED", REASONING="PENDING", PEDAGOGY="PENDING", DIRECTOR="PENDING")
        require(final["stages"] == expected, applicability, "stage_scope_failed")
        require(final["math"]["applicability"] == applicability, applicability, "math_applicability_failed")
        require(all(state == "NOT_RUN" for state in final["downstream"].values()),
                applicability, "downstream_execution_forbidden")
        require(final["source_sha256"] == source["sha256"], applicability, "source_identity_failed")
        with port.native(principal, run, "read") as native:
            snapshot = native.persistence.load_run_state(run)
            for stage in STAGES:
                attempt = snapshot["stages"][stage]["attempts"][-1]
                if blocked and stage in ("REASONING", "PEDAGOGY", "DIRECTOR"):
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
                    if stage not in ("SOURCE", "DIRECTOR"):
                        require(set(attempt["input_artifact_refs"]) <= set(record.parent_artifact_ids),
                                applicability, "artifact_ancestry_failed")
                for reference in attempt["evidence_refs"]:
                    safe_evidence = native.read(run, reference)
                    require(excludes_private(safe_evidence, source_lines + (str(root), token)),
                            applicability, "safe_evidence_leakage")
            if not blocked:
                output, receipt = native.verified_director(run, principal.tenant)
                request, components, _ = native.request(run, principal.tenant)
                require({request.reasoning_ref, request.pedagogy_ref} <= set(output.parent_refs),
                        applicability, "exact_native_input_binding_failed")
                require(output.artifact_type == "director.plan" and
                        output.payload["schema_version"] == "bie.dir.annotated_plan/1.0.0",
                        applicability, "native_director_schema_failed")
                require(output.metadata["requires_review"] is True and
                        output.metadata["accepted"] is False and output.metadata["release_ready"] is False,
                        applicability, "review_boundary_failed")
                require(all(receipt[name] > 0 for name in
                            ("generation_attempt_count", "critic_attempt_count", "annotation_attempt_count", "review_attempt_count")),
                        applicability, "actual_provider_invocation_missing")
                require(receipt["math_artifact_id"] == final["math"]["artifact_id"] and
                        receipt["math_sha256"] == final["math"]["sha256"],
                        applicability, "director_math_binding_failed")
                require(native.queue.stats()["ACKED"] == 8, applicability, "eight_acks_required")
                require(final["slice_complete"] and final["director"]["director_executed"],
                        applicability, "director_completion_failed")
            else:
                require(final["director"] is None and final["pedagogy"] is None and final["reasoning"] is None
                        and not final["slice_complete"], applicability, "unsupported_math_false_success")
                require(not any(native.persistence.load_artifact(aid).stage_id == "DIRECTOR"
                                for aid in native.persistence.artifacts_for_run(run)),
                        applicability, "blocked_director_output_forbidden")
        require(excludes_private(final, source_lines + (str(root), token)),
                applicability, "safe_projection_leakage")
        # Reap closed-scope fixture references before temporary cleanup on
        # Windows. This changes no worker/process/resource or recovery policy;
        # it does not attribute a platform cleanup failure to a native store.
        gc.collect()
        return dict(passed=True, evidence_kind="SYNTHETIC_TEST", source_sha256=source["sha256"],
                    stages=final["stages"], math=final["math"], reasoning=final["reasoning"],
                    pedagogy=final["pedagogy"], director=final["director"], native_pdf=True,
                    real_child_process=True, actual_production_assembly_executed=not blocked,
                    restart_in_second_process=True, artifact_identity_preserved=True,
                    queue_terminal_states_verified=True, enforcement=initial["enforcement"],
                    child_wall_seconds=child_elapsed, restart_wall_seconds=restart_elapsed,
                    child_output_bytes=len(child.output),
                    idempotent_replay=True, director_executed=not blocked, visual_executed=False,
                    downstream_not_run=True, audio_complete=False, academic_acceptance=False,
                    learner_outcome_evidence=False, product_accepted=False, live_provider_executed=False)


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
        result = dict(passed=False, phase=error.phase, code=error.code,
                      product_accepted=False, **error.diagnostics)
    except Exception:
        result = dict(passed=False, code="director_process_smoke_failed", product_accepted=False)
    raw = json.dumps(result, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
