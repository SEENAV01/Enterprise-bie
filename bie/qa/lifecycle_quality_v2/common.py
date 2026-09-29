"""H6 immutable local contracts. None of these APIs grants release approval."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from ..native_quality_v2.common import (Binding, Finding, Report, report, require, fields,
    items, unique, approved, SnapshotStore, ArtifactRef, Review, ReviewVerifier,
    ContractError, canonical_bytes, digest, integer, token, text, binding_matches)
from ..release_v2.contracts import safe_relative_path, sha256
from ..publication_v2.contracts import strict_json
from ..media_runtime_v2.common import q
from ..repair_v2.worker import validator_digest

SCHEMA='bie.qa.lifecycle-quality/1'

def read(root, ref):
    require(type(ref) is ArtifactRef, 'H6_ARTIFACT_TYPE')
    with SnapshotStore(root) as store:
        return store.read(ref)

def load(root, ref):
    result=strict_json(read(root,ref))
    require(type(result) is dict,'H6_JSON_OBJECT')
    return result

def ids(values, name, minimum=1, maximum=4096):
    require(type(values) in (tuple,list) and minimum<=len(values)<=maximum,name+'_COUNT')
    for x in values: token(x,name)
    require(len(set(values))==len(values),name+'_DUPLICATE')
    return tuple(values)

def result(task,binding,findings,details,inspected=()):
    fs=list(findings)+[Finding('NATIVE_AND_INDEPENDENT_REVIEW_REQUIRED',task)]
    r=report(task,binding,fs,inspected,details)
    return dict(schema_version=SCHEMA,report=r.to_dict(),details=details,
                technical_checks_clear=not any(f.severity=='BLOCKER' for f in fs),
                production_authorized=False,product_accepted=False)

def blocker(findings,code,subject='candidate'):
    findings.append(Finding(code,subject,'BLOCKER'))

def bind(binding,policy):
    require(type(binding) is Binding and binding.policy_digest==policy.content_digest,'H6_POLICY_BINDING')

@dataclass(frozen=True)
class RepairScope:
    """Authoritative owner/check/descendant scope, provisioned outside source text."""
    owner: str
    mutable_paths: tuple[str,...]
    protected_paths: tuple[str,...]
    required_checks: tuple[str,...]
    invalidates: tuple[str,...]
    generator_group: str
    max_replacement_bytes: int=2*1024*1024
    timeout_seconds: int=10
    def __post_init__(self):
        token(self.owner,'owner');token(self.generator_group,'generator')
        for k in ('required_checks','invalidates'):
            ids(getattr(self,k),k)
        for k in ('mutable_paths','protected_paths'):
            v=getattr(self,k)
            require(type(v) is tuple and len(v)<=4096 and len(v)==len(set(v)), 'H6_PATH_CENSUS')
        require(bool(self.mutable_paths),'H6_MUTABLE_PATHS_EMPTY')
        for p in self.mutable_paths+self.protected_paths:
            safe_relative_path(p)
        require(not set(self.mutable_paths)&set(self.protected_paths),'H6_PROTECTED_MUTATION')
        for p in self.mutable_paths:
            require(p.startswith(('generated/','derived/')),'H6_NON_GENERATED_TARGET')
        integer(self.max_replacement_bytes,'replacement',1,8*1024*1024)
        integer(self.timeout_seconds,'timeout',1,60)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True)
class Change:
    task_id: str
    binding: Binding
    target: ArtifactRef
    payload: bytes
    scope_digest: str
    input_refs: tuple[ArtifactRef,...]
    required_checks: tuple[str,...]
    invalidates: tuple[str,...]
    witness: dict
    def __post_init__(self):
        require(type(self.payload) is bytes and self.payload,'H6_REPLACEMENT_BYTES')
        require(type(self.target) is ArtifactRef and type(self.binding) is Binding,'H6_CHANGE_TYPE')
        sha256(self.scope_digest,'scope')
        require(type(self.input_refs) is tuple and all(type(r) is ArtifactRef for r in self.input_refs),'H6_CHANGE_INPUTS')
        ids(self.required_checks,'checks');ids(self.invalidates,'invalidates')
        canonical_bytes(self.witness)
    @property
    def payload_sha256(self):
        import hashlib
        return hashlib.sha256(self.payload).hexdigest()
    @property
    def content_digest(self):
        return digest(dict(task_id=self.task_id,binding=asdict(self.binding),target=asdict(self.target),
            payload_sha256=self.payload_sha256,payload_bytes=len(self.payload),scope_digest=self.scope_digest,
            inputs=[asdict(r) for r in self.input_refs],checks=self.required_checks,invalidates=self.invalidates,witness=self.witness))
    def receipt(self):
        return dict(schema_version='bie.qa.h6-change/1',change_digest=self.content_digest,task_id=self.task_id,
          binding=asdict(self.binding),target=asdict(self.target),replacement_sha256=self.payload_sha256,
          replacement_bytes=len(self.payload),required_checks=self.required_checks,invalidates=self.invalidates,
          witness=self.witness,status='PROPOSAL_ONLY',old_assessments_reusable=False,product_accepted=False)

def make_change(task,binding,root,target,payload,scope,inputs,witness):
    bind(binding,scope)
    require(target.path in scope.mutable_paths and target.path not in scope.protected_paths,'H6_TARGET_OWNERSHIP')
    require(type(payload) is bytes and 0<len(payload)<=scope.max_replacement_bytes,'H6_REPLACEMENT_LIMIT')
    before=read(root,target)
    require(before!=payload,'H6_NO_CHANGE')
    refs=tuple({r.path:r for r in (target,)+tuple(inputs)}.values())
    require(len(refs)==len({r.artifact_id for r in refs}),'H6_ARTIFACT_ID_ALIAS')
    for r in refs:read(root,r)
    return Change(task,binding,target,payload,scope.content_digest,refs,scope.required_checks,scope.invalidates,witness)

def authorize(change,scope,review,verifier,now):
    require(type(change) is Change and type(scope) is RepairScope,'H6_AUTH_INPUT')
    require(change.scope_digest==scope.content_digest and change.binding.policy_digest==scope.content_digest,'H6_AUTH_SCOPE')
    require(change.required_checks==scope.required_checks and change.invalidates==scope.invalidates,'H6_AUTH_CHECK_SCOPE')
    require(type(review) is Review,'H6_FRESH_REVIEW_REQUIRED')
    status=approved(review,verifier,subject=change.target.artifact_id,purpose='inference',
       request_digest=change.content_digest,policy_digest=scope.content_digest,now=now,
       evidence_ids=tuple(r.artifact_id for r in change.input_refs))
    require(status=='VERIFIED','H6_FRESH_REVIEW_REQUIRED')
    auth=verifier.verify_bound(review,change.content_digest,scope.content_digest,86400,now)
    require(auth.independence_group!=scope.generator_group,'H6_SELF_APPROVAL')
    return True
