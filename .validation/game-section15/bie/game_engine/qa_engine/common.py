from __future__ import annotations
from ..provenance import ProvenanceBundle
from .contracts import QualityFinding,Severity

def provenance_refs(bundle:ProvenanceBundle):
    bundle.validate(('source','reasoning'));return tuple(sorted({r.artifact_id for r in bundle.refs}))
def finding(task,idx,code,message,*,severity=Severity.ERROR,blocking=True,refs=()):return QualityFinding(f'{task}:finding:{idx}',severity,code,message,tuple(refs),blocking).validate()
def ratio(n,d):return 1.0 if d==0 else n/d
