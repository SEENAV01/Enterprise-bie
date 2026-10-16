"""Eleven real stages in two bounded children, then separate reopen; no rendering."""
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
from scripts.smoke_bie_animation import SmokeFailure, check


def _read_checkpoint(root):
    try:
        from tests.productization.scene_ir.positive_process_observations import read
        return read(root)
    except BaseException:
        return "UNAVAILABLE", None


def _partition_reply(reply, segment, stages, blocked, run_id):
    """Validate an actual reaped child's declared cut, never infer execution from ACKs alone."""
    from apps.operator.scene_ir_worker_child import _split_expected
    check(type(reply) is dict and set(reply) == {"enforcement", "run_id", "status_sha256",
        "stages", "scene_ir", "product_accepted", "partition"}, "split_reply_shape")
    check(reply["run_id"] == run_id and reply["product_accepted"] is False and
          reply["enforcement"] in ("LINUX_RLIMIT", "WINDOWS_JOB_OBJECT"), "split_reply_identity")
    partition = reply["partition"]
    check(type(partition) is dict and set(partition) == {"segment", "executed_stages",
        "input_prefix_sha256", "output_prefix_sha256"}, "split_partition_shape")
    expected = list(stages[:5] if blocked else stages[:10]) if segment == "through-animation" else ([] if blocked else ["SCENE_IR"])
    check(partition["segment"] == segment and partition["executed_stages"] == expected, "split_execution_inventory")
    check(reply["stages"] == _split_expected(stages, 10 if segment == "through-animation" else 11, blocked),
          "split_terminal_states")
    for value in (reply["status_sha256"], partition["input_prefix_sha256"], partition["output_prefix_sha256"]):
        check(type(value) is str and len(value) == 64 and set(value) <= set("0123456789abcdef"), "split_identity_shape")
    if segment == "scene-ir":
        check(partition["input_prefix_sha256"] == partition["output_prefix_sha256"], "split_upstream_changed")
    return {k: v for k, v in reply.items() if k != "partition"}, partition


def _child_passed(outcome):
    return outcome.completed is True and type(outcome.exit_code) is int and outcome.exit_code == 0


def journey(lines, applicability):
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.scene_ir_producer import SceneIRProducerControlPlane
    from apps.operator.process_supervision import supervise, child_environment
    from apps.operator.process_limits import PdfProcessBudget
    from bie.productization.scene_ir_contract import PROFILE, profile_config, scene_ir_config, strict_document
    from bie.productization.animation_contract import animation_config
    from bie.productization.visual_contract import visual_config
    from bie.productization.scene_ir_slice import STAGES
    from bie.productization.contracts import digest
    from bie.compiler.scene_ir_loader import load_scene_ir_payload
    from bie.infrastructure.artifact_store import BlobRef
    from scripts.smoke_bie_visual import target
    from scripts.smoke_bie_director import excludes_private
    sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
    sys.path.insert(0, str(ROOT / "tests/productization/director"))
    from structural_pdf_fixtures import positioned_text_pdf
    from protocol_support import config_for_stack
    raw = positioned_text_pdf([[(72, 740 - 40*i, text) for i, text in enumerate(lines)]])
    budget = dict(profile_id=target()["profile_id"], max_score=20, split_score=35,
        max_particles=0, max_3d_objects=0, max_asset_bytes=0)
    config = profile_config(director=config_for_stack(), visual=visual_config(target()),
        animation=animation_config(reduced_motion_required=True, budget=budget), scene_ir=scene_ir_config())
    credentials = Credentials()
    token = secrets.token_urlsafe(40)
    principal = Principal("smoke036", "local", frozenset({"read", "source", "create", "worker"}), time.time()+240)
    credentials.grant(token, principal)
    with tempfile.TemporaryDirectory(prefix="bie-prod036-") as temporary:
        root = Path(temporary)
        operator = Service(root, credentials)
        port = SceneIRProducerControlPlane(operator, enabled_profiles={PROFILE})
        source = operator.import_pdf(principal, raw)
        run = port.admit(principal, source["source_id"], "smoke", producer_config=config)["run_id"]
        env = child_environment(); env["BIE_OPERATOR_TOKEN"] = token
        command = [sys.executable, "-I", "-B", str(ROOT / "apps/operator/scene_ir_worker_child.py"),
            "--data-root", str(root), "--run-id", run, "--tenant", "local", "--technical-test-providers"]
        children = {}
        def execute(label, arguments):
            started = time.monotonic()
            outcome = supervise(command + arguments, env, PdfProcessBudget())
            elapsed = round(time.monotonic() - started, 3)
            children[label] = dict(wall_seconds=elapsed, exit_code=outcome.exit_code,
                completed=outcome.completed, output_bytes=len(outcome.output))
            if not _child_passed(outcome):
                checkpoint_state, checkpoint = _read_checkpoint(root)
                with port.native(principal, run, "read") as service:
                    saved = service.persistence.load_run_state(run)
                    states = {s: a["attempts"][-1]["state"] for s, a in saved["stages"].items()}
                    safe = {s: a["attempts"][-1]["diagnostics"] for s, a in saved["stages"].items()
                        if a["attempts"][-1]["diagnostics"]}
                    queues = service.queue.stats()
                raise SmokeFailure("child_execution_failed" if outcome.completed else "child_supervision_incomplete",
                    dict(safe_diagnostics=safe, persisted_stage_states=states, queue_counts=queues,
                        child_checkpoint_state=checkpoint_state, child_checkpoint=checkpoint,
                        exit_code=outcome.exit_code, child_wall_seconds=elapsed, child_output_bytes=len(outcome.output),
                        child_phase=label, child_processes=children))
            return json.loads(outcome.output)
        blocked = applicability == "REVIEW_REQUIRED"
        _, first_partition = _partition_reply(execute("through-animation", ["--segment", "through-animation"]),
            "through-animation", STAGES, blocked, run)
        original, scene_partition = _partition_reply(execute("scene-ir", ["--segment", "scene-ir"]),
            "scene-ir", STAGES, blocked, run)
        check(first_partition["output_prefix_sha256"] == scene_partition["input_prefix_sha256"], "split_handoff_identity")
        reopened = execute("reopen-replay", ["--verify-only"])
        check(original == reopened, "restart_identity_failed")
        final = port.status(principal, run)
        check(reopened["status_sha256"] == digest(final), "full_projection_binding_failed")
        check(port.admit(principal, source["source_id"], "smoke", producer_config=config) == final, "idempotent_replay_failed")
        expected = dict.fromkeys(STAGES, "SUCCEEDED")
        if blocked:
            expected.update(MATH="BLOCKED", REASONING="PENDING", PEDAGOGY="PENDING", DIRECTOR="PENDING",
                VISUAL="PENDING", ANIMATION="PENDING", SCENE_IR="PENDING")
        check(final["stages"] == expected, "stage_states_failed")
        check(final["math"]["applicability"] == applicability, "math_applicability_failed")
        check(all(v == "NOT_RUN" for v in final["downstream"].values()), "downstream_execution_forbidden")
        identities = {}
        with port.native(principal, run, "read") as service:
            saved = service.persistence.load_run_state(run)
            for stage in STAGES:
                attempt = saved["stages"][stage]["attempts"][-1]
                if final["stages"][stage] == "PENDING":
                    check(not attempt["output_artifact_refs"] and not attempt["evidence_refs"], "blocked_output_forbidden")
                    continue
                message = service.queue.get(service.task_id(run, stage, attempt["attempt"]))
                check(message.state == ("DEAD_LETTER" if stage == "MATH" and blocked else "ACKED"), "queue_terminal_failed")
                identities[stage] = [dict(artifact_id=ref, sha256=service.record(run, ref).blob_digest)
                    for ref in attempt["output_artifact_refs"] + attempt["evidence_refs"]]
                for ref in attempt["evidence_refs"]:
                    check(excludes_private(service.read(run, ref), tuple(lines)+(str(root), token)), "safe_evidence_leakage")
            if not blocked:
                doc, receipt = service.verified_scene_ir(run, "local")
                check(receipt["requires_review"] and not doc["accepted"] and not receipt["release_ready"], "review_contract")
                check(not receipt["audio_complete"] and receipt["audio_reconciliation_open"], "audio_boundary_failed")
                check(service.queue.stats()["ACKED"] == 11, "eleven_acks_required")
                check(receipt["input_artifact_ids"] == [service.stage_ref(run, s)[0]
                    for s in ("VISUAL", "ANIMATION", "DIRECTOR")], "exact_ordered_inputs_failed")
                row = service.record(run, receipt["output_artifact_id"])
                persisted = service.cas.get_bytes(BlobRef(row.blob_algorithm, row.blob_digest, row.blob_size))
                parsed = strict_document(persisted)
                loaded = load_scene_ir_payload(persisted.decode())
                check(parsed.to_dict() == doc and parsed.fingerprint == loaded.scene_fingerprint and
                    loaded.source_sha256 == row.blob_digest and loaded.validation_passed, "persisted_native_admission_failed")
            else:
                check(final["scene_ir"] is None and final["animation"] is None, "false_scene_success")
                check(not any(service.persistence.load_artifact(a).stage_id in ("DIRECTOR", "VISUAL", "ANIMATION", "SCENE_IR")
                    for a in service.persistence.artifacts_for_run(run)), "blocked_execution_forbidden")
        check(excludes_private(final, tuple(lines)+(str(root), token)), "safe_projection_leakage")
        gc.collect()
        return dict(passed=True, stages=final["stages"], source_sha256=source["sha256"], identities=identities,
            math_applicability=applicability, scene_ir=final["scene_ir"], real_native_pdf=True,
            real_child_process=True, second_process_restart=True, idempotent_replay=True,
            child_wall_seconds=children["through-animation"]["wall_seconds"],
            child_output_bytes=children["through-animation"]["output_bytes"],
            child_processes=children, execution_layout="SOURCE_TO_ANIMATION_THEN_SCENE_IR_THEN_REOPEN",
            queue_terminal_verified=True,
            evidence_kind="SYNTHETIC_TEST", downstream_not_run=True, video_code_executed=False,
            audio_complete=False, audio_reconciliation_open=True, product_accepted=False)


def run_smoke():
    result = dict(passed=True, product_accepted=False)
    for name, lines, applicability in (
        ("quantitative_nonmath", ("Chart B x A y B: C 2; D 3.",), "NOT_REQUIRED"),
        ("chronology", ("Timeline: A at 1810; B at 1820.",), "NOT_REQUIRED"),
        ("cellular", ("Cell: A C; B C.",), "NOT_REQUIRED"),
        ("unsupported_math", ("Chart B x A y B: C 2; D 3.", "Compute the matrix inverse."), "REVIEW_REQUIRED")):
        try:
            result[name] = journey(lines, applicability)
        except SmokeFailure as exc:
            result[name] = dict(passed=False, code=exc.code, **exc.diagnostics)
            result["passed"] = False
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run_smoke()
    except Exception:
        result = dict(passed=False, code="scene_ir_smoke_failed", product_accepted=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
