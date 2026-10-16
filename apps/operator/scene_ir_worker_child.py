"""Real Task036 child; existing supervisor/resource contract, no rendering."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _checkpoints(args):
    if not args.technical_test_providers: return None
    try:
        from tests.productization.scene_ir.positive_process_observations import Checkpoints
        return Checkpoints(args.data_root, "VERIFY" if args.verify_only else "RUN")
    except BaseException:
        return None  # Optional test evidence cannot prevent the native journey.


def _mark(observer, *args):
    if observer is not None:
        try: observer.mark(*args)
        except BaseException: pass


def _checkpoint_fault(observer):
    def fault(boundary):
        try: observer.fault(boundary)
        except BaseException: pass
    return fault


def _split_expected(stages, completed, blocked=False):
    """Only the two owner-approved cut points; no arbitrary stage selection."""
    if blocked:
        return {s: ("SUCCEEDED" if i < 4 else "BLOCKED" if i == 4 else "PENDING")
                for i, s in enumerate(stages)}
    return {s: ("SUCCEEDED" if i < completed else "READY" if i == completed else "PENDING")
            for i, s in enumerate(stages)}


def _partition_inventory(port, principal, run_id, expected):
    """Read-only durable cut validation, not a substitute for native status admission.

    Native status still reopens and validates the current full upstream chain.
    This extra smoke guard rejects preseeded stages, fake ACKs, missing records,
    orphan publications and retries at either supervised-process cut.
    """
    from bie.productization.contracts import digest, require
    with port.native(principal, run_id, "read") as service:
        saved = service.persistence.load_run_state(run_id)
        require(set(saved["stages"]) == set(expected), "scene_ir_split_inventory")
        admitted = {run_id + "-config", run_id + "-source"}
        for stage, state in expected.items():
            attempts = saved["stages"][stage]["attempts"]
            require(len(attempts) == 1, "scene_ir_split_attempt")
            attempt = attempts[0]
            require(attempt["state"] == state, "scene_ir_split_state")
            refs = attempt["output_artifact_refs"] + attempt["evidence_refs"]
            if state in ("PENDING", "READY"):
                require(not refs, "scene_ir_split_preseeded")
                continue
            require(state in ("SUCCEEDED", "BLOCKED"), "scene_ir_split_state")
            message = service.queue.get(service.task_id(run_id, stage, attempt["attempt"]))
            require(message is not None and message.state == ("ACKED" if state == "SUCCEEDED" else "DEAD_LETTER"),
                    "scene_ir_split_queue")
            if state == "SUCCEEDED":
                require(bool(attempt["output_artifact_refs"]), "scene_ir_split_missing_output")
            require(len(refs) == len(set(refs)), "scene_ir_split_duplicate_output")
            for ref in refs:
                record = service.record(run_id, ref)  # Reopen and authenticate the actual CAS bytes.
                require(record.stage_id == stage, "scene_ir_split_foreign_output")
        inventory = []
        for ref in service.persistence.artifacts_for_run(run_id):
            record = service.record(run_id, ref)
            # Private supporting artifacts need not be stage output refs. Keep
            # them, but never admit any publication by a stage not yet executed.
            require(ref in admitted or expected.get(record.stage_id) in ("SUCCEEDED", "BLOCKED"),
                    "scene_ir_split_preseeded")
            if record.stage_id != "SCENE_IR":
                inventory.append([ref, record.blob_digest])
        require(admitted <= set(service.persistence.artifacts_for_run(run_id)), "scene_ir_split_missing_input")
        counts = service.queue.stats()
        require(counts.get("ACKED", 0) == sum(s == "SUCCEEDED" for s in expected.values()) and
                counts.get("DEAD_LETTER", 0) == sum(s == "BLOCKED" for s in expected.values()),
                "scene_ir_split_queue")
        # The first ten committed identities must survive the Scene child unchanged.
        return digest(sorted(inventory))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--technical-test-providers", action="store_true")
    parser.add_argument("--segment", choices=("through-animation", "scene-ir"))
    args = parser.parse_args()
    if args.segment and (not args.technical_test_providers or args.verify_only):
        parser.error("segment requires technical providers and cannot replace restart verification")
    from apps.operator.process_limits import PdfProcessBudget, enforce_current_process
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.scene_ir_producer import SceneIRProducerControlPlane
    from bie.productization.scene_ir_contract import PROFILE
    from bie.productization.contracts import digest
    enforcement = enforce_current_process(PdfProcessBudget())
    credentials = Credentials()
    principal = Principal("local-producer", args.tenant, frozenset({"read", "worker"}), time.time() + 60)
    credentials.grant(os.environ.get("BIE_OPERATOR_TOKEN", ""), principal)
    port = SceneIRProducerControlPlane(Service(args.data_root, credentials), enabled_profiles={PROFILE})
    stack = None
    checkpoints = _checkpoints(args)
    if args.technical_test_providers and not args.verify_only and args.segment != "scene-ir":
        sys.path.insert(0, str(ROOT / "tests/productization/director"))
        from protocol_support import make_stack
        stack = make_stack()
    _mark(checkpoints, "INITIAL_STATUS")
    result = port.status(principal, args.run_id)
    stages = tuple(port.native_service.stages)
    executed = []
    before = None
    blocked = result.get("safe_diagnostics") == {"MATH": ["math_review_required"]}
    if args.segment:
        from bie.productization.contracts import require
        require(len(stages) == 11 and stages[-2:] == ("ANIMATION", "SCENE_IR"), "scene_ir_split_profile")
        expected = _split_expected(stages, 0 if args.segment == "through-animation" else 10,
                                   blocked=blocked and args.segment == "scene-ir")
        require(result["stages"] == expected, "scene_ir_split_entry")
        before = _partition_inventory(port, principal, args.run_id, expected)
    selected = stages[:10] if args.segment == "through-animation" else stages[-1:] if args.segment else stages
    if args.segment == "scene-ir" and blocked:
        selected = ()  # Authenticated blocked-Math control: never schedule Scene IR.
    if not args.verify_only:
        for stage in selected:
            index = stages.index(stage) + 1
            _mark(checkpoints, "BEFORE_WORK", stage, index)
            options = dict(director_stack=stack)
            if checkpoints is not None: options["fault"] = _checkpoint_fault(checkpoints)
            result = port.work_once(principal, args.run_id, **options)
            executed.append(stage)
            if args.segment:
                blocked = result.get("safe_diagnostics") == {"MATH": ["math_review_required"]}
                require(result["stages"] == _split_expected(stages, index, blocked), "scene_ir_split_progress")
            _mark(checkpoints, "AFTER_WORK", stage, index)
            if result["slice_complete"] or any(s in ("FAILED", "BLOCKED") for s in result["stages"].values()):
                break
    _mark(checkpoints, "RETURN")
    reply = dict(enforcement=enforcement, run_id=args.run_id, status_sha256=digest(result),
        stages=result["stages"], scene_ir=result.get("scene_ir"), product_accepted=False)
    if args.segment:
        expected = _split_expected(stages, 10 if args.segment == "through-animation" else 11, blocked)
        require(result["stages"] == expected, "scene_ir_split_exit")
        after = _partition_inventory(port, principal, args.run_id, expected)
        if args.segment == "scene-ir":
            require(before == after, "scene_ir_split_upstream_changed")
        reply["partition"] = dict(segment=args.segment, executed_stages=executed,
                                  input_prefix_sha256=before, output_prefix_sha256=after)
    print(json.dumps(reply, sort_keys=True, separators=(",", ":")))
    return 0 if args.segment or result["slice_complete"] or result.get("safe_diagnostics") == {"MATH": ["math_review_required"]} else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"code":"scene_ir_worker_failed","product_accepted":false}')
        raise SystemExit(2) from None
