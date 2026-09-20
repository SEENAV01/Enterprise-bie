from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .unified_scene_ir_contract import _fp

@dataclass(frozen=True)
class IntegrityReceipt:
    scene_id:str
    stored_fingerprint:str
    recomputed_fingerprint:str
    deep_immutable:bool
    blockers:tuple[str,...]
    passed:bool
    accepted:bool=False

def _immutable(v):
    if isinstance(v, MappingProxyType):
        return all(_immutable(x) for x in v.values())
    if isinstance(v, tuple):
        return all(_immutable(x) for x in v)
    if isinstance(v, (dict,list,set)):
        return False
    return True

def inspect_document_integrity(document):
    blockers=[]
    recomputed=_fp(document.to_dict(include_fingerprint=False))
    if recomputed!=document.fingerprint:
        blockers.append("fingerprint_mismatch")
    deep=True
    for e in document.elements:
        deep=deep and _immutable(e.props) and _immutable(e.accessibility)
        if e.normalized_box is not None:
            deep=deep and _immutable(e.normalized_box)
    for t in document.tracks:
        deep=deep and _immutable(t.parameters)
    deep=deep and _immutable(document.layout) and _immutable(document.metadata)
    for name in (
        "events","narration_cues","interaction_cues","interaction_bindings",
        "state_bindings","simulation_controls","accessibility_metadata",
        "capability_requests","planned_fallbacks"
    ):
        deep=deep and _immutable(getattr(document,name))
    if not deep:
        blockers.append("mutable_nested_payload_detected")
    return IntegrityReceipt(
        document.scene_id,document.fingerprint,recomputed,deep,
        tuple(sorted(set(blockers))),not blockers,False
    )

def require_integrity(receipt):
    if not receipt.passed:
        raise ValueError("SceneIR integrity failed")
    return True
