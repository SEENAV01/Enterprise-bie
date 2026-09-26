from __future__ import annotations
from ..provenance import ProvenanceBundle

def all_refs(bundle:ProvenanceBundle):
    bundle.validate(('source','reasoning'))
    return tuple(sorted({r.artifact_id for r in bundle.refs}))

def refs_by_role(bundle:ProvenanceBundle, role:str):
    bundle.validate(('source','reasoning'))
    return tuple(sorted({r.artifact_id for r in bundle.refs if r.role==role}))
