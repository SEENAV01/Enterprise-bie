"""HARD022/023: consume externally built native games; never rebuild Section15.

No about:blank/inline fallback exists in this collector entrypoint. Managed
browser navigation failure is retained. Finite scenario/property checks are not
exhaustive game verification, actual-device touch proof or measured learning.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from urllib.parse import urlsplit
import json,hashlib
from .common import *
from ..game_v2.models import GameRequest,GamePolicy,inventory
from ..game_v2.codec import load_runtime
from ..game_v2.evaluator import evaluate as evaluate_game
from ..game_v2.capture import collect

DEPLOYMENT_FIELDS={'static_origin_verified','native_esm_loader_verified','exact_module_count',
 'module_graph_fingerprint','entry_source_sha256','browser_origin_navigation_verified','origin_block_reason','sandbox_evidence','product_accepted'}

@dataclass(frozen=True)
class NativeGamePolicy:
    game_id:str
    entrypoint:str
    entry_module:str
    module_paths:tuple[str,...]
    module_graph_fingerprint:str
    package_revision:str
    max_age:int=86400
    def __post_init__(self):
        from ..release_v2.contracts import revision
        token(self.game_id,'game');safe_relative_path(self.entrypoint);safe_relative_path(self.entry_module)
        require(type(self.module_paths)is tuple and 2<=len(self.module_paths)<=512 and len(set(self.module_paths))==len(self.module_paths),'H5_MODULE_INVENTORY')
        for p in self.module_paths:
            safe_relative_path(p);require(p.endswith(('.js','.mjs')),'H5_NATIVE_MODULE_EXTENSION')
        require(self.entry_module in self.module_paths,'H5_GAME_ENTRY_MODULE')
        require(type(self.module_graph_fingerprint)is str and self.module_graph_fingerprint.startswith('sha256:'),'H5_MODULE_GRAPH_HASH')
        sha256(self.module_graph_fingerprint[7:],'module_graph');revision(self.package_revision)
        integer(self.max_age,'age',1,604800)


def inspect_native_game(root,deployment_ref,runtime_ref,outputs,binding,policy,*,review=None,verifier=ReviewVerifier(),now=0):
    policy_binding(binding,policy);integer(now,'now');findings=[]
    require(type(outputs)is tuple and outputs and all(type(x)is ArtifactRef for x in outputs),'H5_GAME_OUTPUTS')
    require(len({x.path for x in outputs})==len(outputs) and len({x.artifact_id for x in outputs})==len(outputs),'H5_GAME_OUTPUT_ALIAS')
    refs=(deployment_ref,runtime_ref)+outputs
    require(all(type(r)is ArtifactRef for r in refs) and len({r.artifact_id for r in refs})==len(refs) and len({r.path for r in refs})==len(refs),'H5_GAME_ALL_REF_ALIAS')
    require(binding.revision==policy.package_revision,'H5_GAME_POLICY_REVISION')
    with SnapshotStore(root) as store:
        d=strict_json(store.read(deployment_ref));runtime=load_runtime(store.read(runtime_ref))
        payload={x.path:store.read(x) for x in outputs}
        for t in runtime.traces:
            for step in t.steps:store.read(step.screenshot)
    fields(d,DEPLOYMENT_FIELDS,'H5_DEPLOYMENT_FIELDS')
    require(d['product_accepted'] is False,'H5_NATIVE_GAME_ACCEPTANCE_CLAIM')
    for field in ('static_origin_verified','native_esm_loader_verified','browser_origin_navigation_verified'):
        require(type(d[field])is bool,'H5_DEPLOYMENT_BOOLEAN')
        if not d[field]:fail(findings,'H5_NATIVE_'+field.upper())
    if d['origin_block_reason'] is not None:fail(findings,'H5_NATIVE_ORIGIN_BLOCKED')
    if set(policy.module_paths)-set(payload) or policy.entrypoint not in payload:fail(findings,'H5_NATIVE_MODULE_MISSING')
    if policy.entry_module in payload and hashlib.sha256(payload[policy.entry_module]).hexdigest()!=d['entry_source_sha256']:fail(findings,'H5_NATIVE_MODULE_CHANGED')
    if d['exact_module_count']!=len(policy.module_paths) or d['module_graph_fingerprint']!=policy.module_graph_fingerprint:fail(findings,'H5_NATIVE_MODULE_GRAPH')
    if (runtime.game_id,runtime.run_id,runtime.revision)!=(policy.game_id,binding.run_id,policy.package_revision):fail(findings,'H5_NATIVE_GAME_BINDING')
    u=urlsplit(runtime.origin)
    if runtime.method!='http_entrypoint' or u.scheme not in ('http','https') or not u.netloc or u.username or u.password or u.path not in ('','/') or u.query or u.fragment:fail(findings,'H5_GAME_NATIVE_ORIGIN_REQUIRED')
    if runtime.entrypoint!=policy.entrypoint or runtime.outputs_digest!=inventory(outputs):fail(findings,'H5_NATIVE_GAME_PACKAGE_IDENTITY')
    if runtime.issued_at>now or now-runtime.issued_at>policy.max_age:fail(findings,'H5_NATIVE_GAME_FRESHNESS')
    loaded={a.path:a for a in runtime.loaded};required=set(policy.module_paths)|{policy.entrypoint}
    if not required<=set(loaded):fail(findings,'H5_NATIVE_GAME_LOAD_COVERAGE')
    for path,a in loaded.items():
        if path not in payload or len(payload[path])!=a.size or hashlib.sha256(payload[path]).hexdigest()!=a.sha256:fail(findings,'H5_NATIVE_GAME_RESPONSE_HASH',path)
    if not runtime.traces:fail(findings,'H5_NATIVE_GAME_TRACE_EMPTY')
    for t in runtime.traces:
        if not required<=set(t.loaded_paths):fail(findings,'H5_NATIVE_GAME_ROUTE_LOAD',t.scenario_id)
        if any(not s.succeeded or s.error for s in t.steps):fail(findings,'H5_NATIVE_GAME_ACTION_FAILED',t.scenario_id)
    if runtime.page_errors or runtime.console_errors or runtime.network_violations:fail(findings,'H5_NATIVE_GAME_BROWSER_ERROR')
    if runtime.execution_kind!='native' or not runtime.sandbox_verified:findings.append(Finding('H5_NATIVE_GAME_EXECUTION_AUTHORITY_REQUIRED',policy.game_id))
    refs=(deployment_ref,runtime_ref)+outputs
    request_digest=digest({'binding':asdict(binding),'refs':[r.to_dict() for r in refs]})
    auth=approved(review,verifier,subject=policy.game_id,purpose='support',request_digest=request_digest,policy_digest=binding.policy_digest,now=now,evidence_ids=tuple(x.artifact_id for x in refs),max_age=policy.max_age)
    if auth=='BLOCKED':fail(findings,'H5_NATIVE_GAME_REVIEW_INVALID')
    elif auth!='VERIFIED':findings.append(Finding('H5_NATIVE_GAME_REVIEW_REQUIRED',policy.game_id))
    return findings_report('BIE-QA-HARD-022',binding,findings,{'request_digest':request_digest,'review':auth,
        'runtime_method':runtime.method,'origin':runtime.origin,'module_count':len(policy.module_paths),
        'rendered_touch_or_learning_verified':False},refs)


def collect_native_game(outputs,build_receipt,game_policy,root,*,run_id,code_revision,issued_at,output_prefix,chromium='/usr/bin/chromium',allow_trusted_execution=False):
    """The original collector runs the supplied real entrypoint, never substitutes JS.

    External code must be operator-trusted; production sandbox integration stays
    separate. The result is captured evidence, not automatic native certification.
    """
    require(allow_trusted_execution is True,'H5_GAME_CAPTURE_OPT_IN')
    require(type(game_policy)is GamePolicy,'H5_GAME_NATIVE_POLICY')
    try:
        ref,receipt,screens=collect(outputs,build_receipt,game_policy,root,run_id=run_id,code_revision=code_revision,
            issued_at=issued_at,output_prefix=output_prefix,chromium=chromium,
            allow_trusted_diagnostic=True,diagnostic_inline=False)
        blocked=receipt.method!='http_entrypoint' or any(not s.succeeded for t in receipt.traces for s in t.steps)
        return {'status':'BLOCKED' if blocked else 'CAPTURED_REVIEW_REQUIRED','receipt':asdict(receipt),
                'receipt_ref':ref.to_dict(),'screenshots':[s.to_dict() for s in screens],
                'injected_fallback_used':False,'native_acceptance':False}
    except Exception as exc:
        message=str(exc)
        code='BROWSER_POLICY_BLOCKED' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in message else getattr(exc,'code','H5_NATIVE_GAME_CAPTURE_FAILED')
        return {'status':'BLOCKED','code':code,'error':message[:2000],'injected_fallback_used':False,'native_acceptance':False}


@dataclass(frozen=True)
class StateConstraint:
    observable:str
    minimum:str
    maximum:str
    def __post_init__(self):
        token(self.observable,'observable');require(q(self.minimum)<=q(self.maximum),'H5_GAME_RANGE')

@dataclass(frozen=True)
class ExtendedGamePolicy:
    game_policy_digest:str
    required_scenarios:tuple[str,...]
    required_mechanics:tuple[tuple[str,str],...]
    state_ranges:tuple[StateConstraint,...]
    conserved_groups:tuple[tuple[tuple[str,...],str],...]=()
    actual_touch_required:bool=False
    def __post_init__(self):
        sha256(self.game_policy_digest,'game_policy');checked_ids(self.required_scenarios,'SCENARIOS')
        require(type(self.required_mechanics)is tuple and 1<=len(self.required_mechanics)<=512,'H5_MECHANIC_INVENTORY')
        seen=set()
        for action,kind in self.required_mechanics:
            token(action,'action');require(kind in ('manipulation','simulation','prediction','branch','reset','reload','keyboard','touch'),'H5_MECHANIC_KIND')
            require(action not in seen,'H5_MECHANIC_DUPLICATE');seen.add(action)
        require(type(self.state_ranges)is tuple and len(self.state_ranges)<=64 and all(type(r)is StateConstraint for r in self.state_ranges),'H5_STATE_RANGES')
        require(len({r.observable for r in self.state_ranges})==len(self.state_ranges),'H5_STATE_RANGE_DUPLICATE')
        require(type(self.conserved_groups)is tuple and len(self.conserved_groups)<=64,'H5_CONSERVATION_BUDGET')
        for names,total in self.conserved_groups:checked_ids(names,'CONSERVATION',2);q(total)
        require(type(self.actual_touch_required)is bool,'H5_TOUCH_FLAG')


def inspect_extended_game(root,request,game_policy,binding,policy,*,as_of,reviews=(),verifier=None,source_assessments=(),source_verifier=None):
    """Run existing full GAME QA, then additional observed-state invariants.

    Mechanic intent comes from independent policy; actions do not prove learning.
    No synthetic state transitions are executed in place of browser observations.
    """
    policy_binding(binding,policy);require(type(request)is GameRequest and type(game_policy)is GamePolicy,'H5_GAME_REQUEST')
    require(game_policy.content_digest==policy.game_policy_digest,'H5_GAME_POLICY_DIGEST')
    inherited=evaluate_game(request,root,game_policy,as_of=as_of,reviews=reviews,verifier=verifier,
                            source_assessments=source_assessments,source_verifier=source_verifier)
    findings=[]
    if inherited.status=='BLOCKED':fail(findings,'H5_INHERITED_GAME_QA_BLOCKED')
    require(set(policy.required_scenarios)=={s.scenario_id for s in game_policy.scenarios},'H5_GAME_BRANCH_INVENTORY')
    actions={a.action_id:a for a in game_policy.actions}
    for action,kind in policy.required_mechanics:
        require(action in actions,'H5_REQUIRED_MECHANIC_ACTION')
        if kind=='keyboard' and actions[action].kind!='press':fail(findings,'H5_KEYBOARD_MECHANIC_UNTESTED',action)
        if kind=='reload' and actions[action].kind!='reload':fail(findings,'H5_RELOAD_MECHANIC_UNTESTED',action)
    with SnapshotStore(root) as store:runtime=load_runtime(store.read(request.runtime_receipt))
    observed_actions={s.action_id for t in runtime.traces for s in t.steps if s.succeeded}
    if not {a for a,_ in policy.required_mechanics}<=observed_actions:fail(findings,'H5_MECHANIC_COVERAGE')
    checked=0
    for t in runtime.traces:
        for s in t.steps:
            state={v.key:v.text for v in s.values}
            for r in policy.state_ranges:
                if r.observable not in state:fail(findings,'H5_GAME_STATE_MISSING',r.observable);continue
                try:value=q(state[r.observable])
                except ContractError:fail(findings,'H5_GAME_STATE_NOT_QUANTITATIVE',r.observable);continue
                if not q(r.minimum)<=value<=q(r.maximum):fail(findings,'H5_GAME_IMPOSSIBLE_STATE',r.observable)
            for names,total in policy.conserved_groups:
                try:value=sum(q(state[n]) for n in names)
                except (KeyError,ContractError):fail(findings,'H5_GAME_CONSERVATION_MISSING');continue
                if value!=q(total):fail(findings,'H5_GAME_CONSERVATION_BROKEN')
            checked+=1
    if policy.actual_touch_required or any(k=='touch' for _,k in policy.required_mechanics):
        findings.append(Finding('H5_ACTUAL_DEVICE_TOUCH_EVIDENCE_REQUIRED',request.game_id))
    return findings_report('BIE-QA-HARD-023',binding,findings,{'inherited_report':inherited.to_dict(),
        'checked_checkpoints':checked,'reported_native_origin':runtime.method=='http_entrypoint',
        'finite_observed_paths_only':True,'learner_mastery_verified':False})
