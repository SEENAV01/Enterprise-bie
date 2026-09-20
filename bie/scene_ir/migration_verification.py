from __future__ import annotations
from dataclasses import dataclass
from .legacy_scenedsl_adapter import adapt_legacy_scenedsl
from .five_pane_adapter import adapt_five_pane
from .migration_common import require_lossless_lineage
from .unified_scene_ir_codec import decode_scene_ir
from .scene_ir_registry import default_registry
from .dsl_orchestrator import validate_scene_ir_document

@dataclass(frozen=True)
class MigrationValidationReceipt:
    adapter_id:str
    canonical_fingerprint:str
    migration_input_fingerprint:str
    migration_output_fingerprint:str
    dsl_gate_passed:bool
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    passed:bool
    accepted:bool=False

def _canonicalize_adapter_output(raw):
    raw=dict(raw)
    raw.pop("ir_fingerprint",None)
    raw.setdefault("layout",{})
    raw.setdefault("events",())
    raw.setdefault("narration_cues",())
    raw.setdefault("interaction_cues",())
    raw.setdefault("interaction_bindings",())
    raw.setdefault("state_bindings",())
    raw.setdefault("simulation_controls",())
    raw.setdefault("accessibility_metadata",())
    raw.setdefault("capability_requests",())
    raw.setdefault("planned_fallbacks",())
    raw.setdefault("metadata",{})
    raw.setdefault("upstream_revision",1)
    raw["accepted"]=False
    raw["review_required"]=True
    return raw

def verify_migration(source_document, adapter):
    if adapter=="legacy-scenedsl":
        raw,evidence=adapt_legacy_scenedsl(source_document)
    elif adapter=="five-pane":
        raw,evidence=adapt_five_pane(source_document)
    else:
        raise ValueError("unsupported migration adapter")
    blockers=[];warnings=[]
    try:
        require_lossless_lineage(evidence)
    except Exception as exc:
        blockers.append("migration_lineage:"+str(exc))
    canonical=decode_scene_ir(_canonicalize_adapter_output(raw))
    try:
        default_registry().normalize_document(canonical)
    except Exception as exc:
        blockers.append("registry:"+str(exc))
    gate=validate_scene_ir_document(canonical)
    blockers.extend(gate.blockers)
    warnings.extend(gate.warnings)
    passed=not blockers and gate.passed
    return canonical,MigrationValidationReceipt(
        evidence.adapter_id,
        canonical.fingerprint,
        evidence.input_fingerprint,
        evidence.output_fingerprint,
        gate.passed,
        tuple(sorted(set(blockers))),
        tuple(sorted(set(warnings))),
        passed,
        False
    )

def require_verified_migration(receipt):
    if not receipt.passed:
        raise ValueError("migration verification failed")
    return True
