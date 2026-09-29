"""Byte-backed supported-module drift report, not compilation/runtime evidence."""
import hashlib
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.models import Report,Finding
from ..source_v2.io import SnapshotStore
from .service import preview

def inspect_generated(task,request,root,policy,*,as_of):
    integer(as_of,'as_of')
    if task not in ('BIE-QA-REPAIR-010','BIE-QA-REPAIR-011'):raise ContractError('MEDIA_REPAIR_INSPECTION_TASK')
    expected,_=preview(task,request,root,policy,as_of=as_of)
    with SnapshotStore(root) as store:actual=store.read(request.module)
    owner='COMP' if task.endswith('010') else 'GAME'
    findings=[]
    if actual!=expected:findings.append(Finding('MEDIA_REPAIR_MODULE_DRIFT','BLOCKER',request.module.artifact_id,owner,'Generated module differs from the separately approved closed grammar/specification.'))
    findings.append(Finding('MEDIA_REPAIR_COMPILE_RUNTIME_REVIEW','REVIEW',request.module.artifact_id,owner,'Module identity is not actual compile, full runtime, source meaning or learner verification.'))
    qa=policy.qa if hasattr(policy,'qa') else policy
    return Report(task,request.content_digest,qa.content_digest,digest(dict(actual=request.module.sha256,expected=hashlib.sha256(expected).hexdigest())),as_of,tuple(findings),
        (('module_bytes',len(actual)),),(request.module.artifact_id,),('Supported deterministic emitter only; not arbitrary TypeScript/game repair or complete native execution.',))
