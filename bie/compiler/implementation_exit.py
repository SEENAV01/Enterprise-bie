"""COMP implementation-scope exit decision.

This deliberately does not weaken the historical runtime gate in
:mod:`bie.compiler.section_closure`.  The v1 gate answers whether every required
runtime verification has completed.  This adapter answers the separate roadmap
question: whether material COMP implementation work is closed so development may
continue to the next section while blocked execution/acceptance gates remain
explicitly open.

It cannot authorize a render or product release and it never marks acceptance.
"""
from __future__ import annotations

from .section_closure import evaluate_section_closure


def evaluate_implementation_scope_exit(findings):
    """Return a fail-closed implementation-exit receipt over the v1 register.

    ``evaluate_section_closure`` remains the schema/identity validator and the
    strict runtime-verification gate.  Environment blockers do not become
    implementation gaps, but any ``OPEN_IMPLEMENTATION`` capability still blocks
    moving to the next development section.
    """
    runtime_gate = evaluate_section_closure(findings)
    implementation_complete = bool(runtime_gate["implementation_complete"])
    runtime_verified = bool(runtime_gate["section_exit_permitted"])
    blocked_execution = tuple(runtime_gate["blocked_execution"])
    open_implementation = tuple(runtime_gate["open_implementation"])

    if open_implementation:
        status = "OPEN_IMPLEMENTATION"
    elif runtime_verified:
        status = "IMPLEMENTATION_SCOPE_COMPLETE_RUNTIME_VERIFIED_NOT_PRODUCT_ACCEPTED"
    else:
        status = "IMPLEMENTATION_SCOPE_COMPLETE_RUNTIME_VERIFICATION_PENDING"

    return {
        "schema_version": "bie.comp-implementation-scope-exit.v2",
        "register_sha256": runtime_gate["register_sha256"],
        "implementation_scope_complete": implementation_complete,
        "implementation_scope_exit_permitted": implementation_complete,
        "open_implementation": list(open_implementation),
        "runtime_verification_complete": runtime_verified,
        "blocked_execution": list(blocked_execution),
        "runtime_gate_status": runtime_gate["status"],
        "status": status,
        "actual_render_authorization": False,
        "product_accepted": False,
        "accepted": False,
        "note": (
            "Development exit is distinct from runtime/product acceptance. "
            "Blocked execution must be re-run when the required environment is "
            "available; any resulting compiler defect reopens COMP narrowly."
        ),
    }
