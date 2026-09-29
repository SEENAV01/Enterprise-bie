"""Independent finite-oracle game QA over actual inspected artifacts.

This evaluator never executes candidate code. Browser capture is a separate
explicit diagnostic/worker action. Hashes and screenshots need external producer
attestation; they cannot prove their own provenance or educational effectiveness.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from urllib.parse import urlparse
from io import BytesIO
import hashlib,re
from PIL import Image
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.evaluator import evaluate as evaluate_source,EvaluationPair
from ..source_v2.models import Finding,Report
from ..source_v2.io import SnapshotStore
from ..reasoning_v2.attestation import Review,ReviewVerifier
from ..video_v2.evaluator import decode_log
from .models import GameRequest,GamePolicy,inventory,all_refs,validate_aliases
from .codec import load_build,load_runtime
AREAS=('build','runtime','interaction','learning')
TASKS={k:f'BIE-QA-GAME-{i:03}' for i,k in enumerate(AREAS,1)}
LIMITATIONS=(
 'Finite operator-enumerated state/transition/path oracle; not exhaustive exploration of arbitrary game code or all possible action sequences.',
 'Observed DOM values and screenshots cover specified checkpoints only. Internal telemetry cannot certify behavior. Canvas/3D gameplay needs a separate observable adapter and independently calibrated visual evaluation.',
 'Build and runtime identity/authentication do not establish producer honesty, actual isolation or scientific correctness. Unsigned/authored diagnostic receipts cannot authorize a native production gate.',
 'Learning alignment requires exact source-linked prompt/feedback and independently provisioned contextual review. Correct gameplay/score transitions do not prove human learning or mastery.',
 'No native Section15 acceptance, real learner study, live calibrated assessor, complete accessibility/security certification, full-repository integration or real-book end-to-end acceptance.')

@dataclass(frozen=True,slots=True)
class GameResult:
    source:EvaluationPair
    reports:tuple[Report,...]
    inspected_artifact_ids:tuple[str,...]
    observed_cases:int
    covered_transition_ids:tuple[str,...]
    @property
    def status(self):
        s={r.status for r in self.reports}|{self.source.grounding.status,self.source.provenance.status}
        return 'BLOCKED' if 'BLOCKED' in s else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in s else 'CHECKS_PASSED'
    @property
    def product_accepted(self):return False
    def to_dict(self):
        return dict(source=self.source.to_dict(),reports={k:r.to_dict() for k,r in zip(AREAS,self.reports)},inspected_artifact_ids=self.inspected_artifact_ids,observed_cases=self.observed_cases,covered_transition_ids=self.covered_transition_ids,status=self.status,product_accepted=False,native_game_acceptance=False,learner_mastery_proven=False)
    @property
    def content_digest(self):return digest(self.to_dict())

def review_targets(r,p):
    targets={('calibration','game-build'):(r.build_receipt.artifact_id,),('calibration','game-runtime'):(r.runtime_receipt.artifact_id,),('inventory','game-scope'):tuple(sorted(c.claim_id for c in r.source.claims))}
    for t in p.learning:targets[('teaching',t.challenge_id)]=tuple(sorted({r.runtime_receipt.artifact_id,t.prompt_claim_id,t.correct_claim_id,t.incorrect_claim_id}))
    return targets

def oracle_paths(policy):
    """Validate all required routes without executing untrusted candidate code."""
    edges={(t.before,t.action_id):t for t in policy.transitions};seen={policy.initial_state};q=deque(seen)
    while q:
        current=q.popleft()
        for t in policy.transitions:
            if t.before==current and t.after not in seen:seen.add(t.after);q.append(t.after)
    all_states={s.state_id for s in policy.states}
    if seen!=all_states:raise ContractError('GAME_UNREACHABLE_ORACLE_STATE')
    if not any(s.successful and s.state_id in seen for s in policy.states):raise ContractError('GAME_NO_REACHABLE_SUCCESS')
    paths={};covered=set()
    for c in policy.scenarios:
        state=policy.initial_state;route=[]
        for action in c.action_ids:
            if (state,action) not in edges:raise ContractError('GAME_UNDEFINED_ORACLE_TRANSITION')
            t=edges[state,action];route.append(t);covered.add(t.transition_id);state=t.after
        paths[c.scenario_id]=tuple(route)
    if covered!={t.transition_id for t in policy.transitions}:raise ContractError('GAME_ORACLE_ROUTE_COVERAGE')
    return paths

def png_check(data,width,height):
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format!='PNG' or im.size!=(width,height) or getattr(im,'n_frames',1)!=1:raise ContractError('GAME_SCREENSHOT_SHAPE')
            im.verify()
    except (OSError,ValueError,Image.DecompressionBombError) as e:
        if isinstance(e,ContractError):raise
        raise ContractError('GAME_SCREENSHOT_INVALID') from e

def evaluate(request,artifact_root,policy,*,as_of,reviews=(),verifier=None,source_assessments=(),source_verifier=None):
    if type(request) is not GameRequest or type(policy) is not GamePolicy:raise ContractError('GAME_EVALUATION_TYPE')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>512 or any(type(x) is not Review for x in reviews):raise ContractError('GAME_REVIEW_TYPE')
    if len({r.review_id for r in reviews})!=len(reviews) or len({(r.purpose,r.subject_id,r.evaluator_id) for r in reviews})!=len(reviews):raise ContractError('GAME_DUPLICATE_REVIEW')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('GAME_VERIFIER_TYPE')
    source=evaluate_source(request.source,artifact_root,policy.source,as_of=as_of,assessments=source_assessments,verifier=source_verifier)
    groups={a:[] for a in ('common',)+AREAS};groups['learning'].extend(source.provenance.findings+source.grounding.findings)
    metrics={a:{} for a in AREAS};cache={};inspected=set(source.provenance.inspected_artifact_ids)|set(source.grounding.inspected_artifact_ids)
    seen_refs=list(all_refs(request));covered=set();observed_cases=0
    def add(area,code,subject,detail,severity='BLOCKER'):
        f=Finding(code,severity,subject,'QA.GAME',detail)
        if f not in groups[area]:groups[area].append(f)
    if request.game_id!=policy.game_id:add('common','GAME_SCOPE_MISMATCH','game','Candidate game differs from operator-approved scope.')
    if inventory(request.inputs)!=policy.expected_input_digest:add('common','GAME_INPUT_INVENTORY','game','Input/source/lock digest differs from operator-controlled inventory.')
    targets=review_targets(request,policy);votes={};tainted=set()
    def area_for(t):return 'build' if t[1]=='game-build' else 'runtime' if t[1]=='game-runtime' else 'learning'
    for r in reviews:
        target=(r.purpose,r.subject_id);area=area_for(target)
        if target not in targets:add('common','GAME_UNKNOWN_REVIEW_TARGET',r.subject_id,'Review is outside current scope.');continue
        if set(r.evidence_ids)!=set(targets[target]):add(area,'GAME_REVIEW_EVIDENCE',r.subject_id,'Exact required evidence identities are missing.');tainted.add(target);continue
        a=verifier.verify_bound(r,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,as_of)
        if not a.authenticated:add(area,'GAME_'+a.code,r.subject_id,'Review signature/binding is invalid.');tainted.add(target)
        elif not a.operational:add(area,'GAME_TEST_ONLY_REVIEW',r.subject_id,'Diagnostic key cannot establish production review.','REVIEW');tainted.add(target)
        elif r.verdict=='REJECTED':add(area,'GAME_REVIEW_REJECTED',r.subject_id,'A rejection cannot be outvoted.');tainted.add(target)
        elif r.verdict!='VERIFIED' or r.confidence_ppm<policy.minimum_review_confidence_ppm:add(area,'GAME_REVIEW_UNCERTAIN',r.subject_id,'Current assessment remains uncertain.','REVIEW');tainted.add(target)
        else:votes.setdefault(target,set()).add(a.independence_group)
    for t in sorted(targets):
        if t in tainted or len(votes.get(t,()))<policy.minimum_independent_assessors:add(area_for(t),'GAME_AUTHORIZED_REVIEW_REQUIRED',t[1],'Execution/scope/learning review remains required.','REVIEW')
    try:paths=oracle_paths(policy)
    except ContractError as e:paths={};add('interaction',e.code,'oracle','Operator oracle has incomplete/ambiguous required coverage.')
    states={s.state_id:s for s in policy.states};observables={o.key for o in policy.observables};matched=[];observed_states=[];runtime=None;build=None
    try:
        with SnapshotStore(artifact_root) as store:
            def read(ref):
                seen_refs.append(ref);validate_aliases(seen_refs)
                if ref.artifact_id not in cache:cache[ref.artifact_id]=store.read(ref);inspected.add(ref.artifact_id)
                return cache[ref.artifact_id]
            for ref in request.inputs+request.outputs:
                try:read(ref)
                except ContractError as e:add('common',e.code,ref.artifact_id,'Actual source/build artifact failed byte verification.')
            try:
                build=load_build(read(request.build_receipt));stdout=decode_log(read(build.stdout));stderr=decode_log(read(build.stderr))
                if (build.run_id,build.revision,build.game_id)!=(request.run_id,request.revision,request.game_id):add('build','GAME_BUILD_BINDING','build','Build receipt belongs to another run/revision/game.')
                if build.issued_at>as_of or as_of-build.issued_at>policy.max_receipt_age_seconds:add('build','GAME_BUILD_STALE','build','Build receipt is future dated or expired.')
                if not build.started or build.timed_out or build.exit_code!=0:add('build','GAME_BUILD_EXECUTION_FAILED','build','Compiler did not complete successfully.')
                if (build.inputs_digest,build.outputs_digest)!=(inventory(request.inputs),inventory(request.outputs)):add('build','GAME_BUILD_ARTIFACT_LINK','build','Receipt does not bind inspected source/output inventories.')
                if build.entrypoint!=policy.entrypoint or policy.entrypoint not in {x.path for x in request.outputs}:add('build','GAME_BUILD_ENTRYPOINT','build','Required actual HTML entrypoint is missing or changed.')
                if build.tool_id not in policy.compile_tools:add('build','GAME_BUILD_TOOL','build','Compiler not approved by operator.')
                if build.tool_id=='tsc' and re.search(rb'error TS\d+',stdout+stderr):add('build','GAME_COMPILER_DIAGNOSTIC','build','Compiler error remains despite claimed success.')
                if stderr.strip():add('build','GAME_BUILD_STDERR','build','Compiler stderr needs tool-specific review.','REVIEW')
                if build.execution_kind!='native':add('build','GAME_NON_NATIVE_BUILD','build','Authored/reported build cannot prove canonical native game compilation.','REVIEW')
            except ContractError as e:add('build',e.code,'build','Build receipt/logs failed byte/schema inspection.')
            try:runtime=load_runtime(read(request.runtime_receipt))
            except ContractError as e:add('common',e.code,'runtime','Runtime evidence failed byte/schema inspection.')
            if runtime is not None:
                if (runtime.run_id,runtime.revision,runtime.game_id)!=(request.run_id,request.revision,request.game_id):add('runtime','GAME_RUNTIME_BINDING','runtime','Runtime belongs to another run/revision/game.')
                if runtime.build_receipt_sha256!=request.build_receipt.sha256 or runtime.outputs_digest!=inventory(request.outputs):add('runtime','GAME_RUNTIME_ARTIFACT_LINK','runtime','Observed game is not bound to exact inspected build.')
                if runtime.oracle_digest!=policy.oracle_digest:add('interaction','GAME_RUNTIME_ORACLE_LINK','runtime','Capture was made for a different action/observable policy.')
                if runtime.issued_at>as_of or as_of-runtime.issued_at>policy.max_receipt_age_seconds:add('runtime','GAME_RUNTIME_STALE','runtime','Runtime receipt is expired/future dated.')
                if build is not None and runtime.issued_at<build.issued_at:add('runtime','GAME_CAUSAL_TIME','runtime','Runtime predates its build evidence.')
                origin=urlparse(runtime.origin)
                if runtime.method!='http_entrypoint' or origin.scheme not in ('http','https') or not origin.netloc or origin.username or origin.password or origin.query or origin.fragment or origin.path not in ('','/') or runtime.entrypoint!=policy.entrypoint:add('runtime','GAME_NOT_ENTRYPOINT_EXECUTION','runtime','Injected/about:blank or wrong-entry runs do not establish native-origin loading.')
                if runtime.execution_kind!='native':add('runtime','GAME_NON_NATIVE_RUNTIME','runtime','Authored diagnostics are not native Section15 runtime acceptance.','REVIEW')
                if not runtime.sandbox_verified:add('runtime','GAME_SANDBOX_UNPROVEN','runtime','No verified production worker isolation.','REVIEW')
                if runtime.page_errors:add('runtime','GAME_RUNTIME_EXCEPTION','runtime','Browser exception observed.')
                if runtime.console_errors:add('runtime','GAME_CONSOLE_ERROR','runtime','Browser console errors observed.')
                if runtime.network_violations:add('runtime','GAME_NETWORK_VIOLATION','runtime','Unapproved request/navigation/worker activity observed.')
                outputs={x.path:x for x in request.outputs};loaded={x.path:x for x in runtime.loaded}
                for path,x in loaded.items():
                    if path not in outputs or (x.sha256,x.size)!=(outputs[path].sha256,outputs[path].size):add('runtime','GAME_LOADED_ASSET_MISMATCH','runtime','Browser loaded unexpected or altered executable/asset bytes.')
                if not set(policy.required_loaded_paths)<=set(loaded):add('runtime','GAME_REQUIRED_ASSET_NOT_LOADED','runtime','Required entrypoint/modules were not loaded.')
                expected={(c.scenario_id,i) for c in policy.scenarios for i in range(policy.replays)}
                actual={(t.scenario_id,t.replay) for t in runtime.traces}
                if actual!=expected:add('interaction','GAME_TRACE_COVERAGE','runtime','Every required path, viewport and independent replay must be captured.')
                cidx={c.scenario_id:c for c in policy.scenarios};normalized={}
                for trace in runtime.traces:
                    c=cidx.get(trace.scenario_id)
                    if c is None:continue
                    observed_cases+=1;subject=trace.scenario_id
                    if not set(policy.required_loaded_paths)<=set(trace.loaded_paths) or not set(trace.loaded_paths)<=set(loaded):add('runtime','GAME_TRACE_LOADED_COVERAGE',subject,'Every path/replay must load required bound assets.')
                    if (trace.width,trace.height)!=(c.width,c.height):add('runtime','GAME_VIEWPORT_SCOPE',subject,'Required viewport changed.')
                    expected_actions=('boot',)+c.action_ids
                    if tuple(s.action_id for s in trace.steps)!=expected_actions:add('interaction','GAME_ACTION_SEQUENCE',subject,'Omitted/reordered/duplicated actions or initial snapshot.');continue
                    route=paths.get(subject)
                    if route is None:continue
                    previous_end=0;case_values=[];expected_state_ids=(policy.initial_state,)+tuple(t.after for t in route);step_ok=[]
                    for index,(step,state_id) in enumerate(zip(trace.steps,expected_state_ids)):
                        ok=True
                        if step.start_ms<previous_end:add('interaction','GAME_ACTION_CLOCK_ORDER',subject,'Actions overlap or timestamps regress.');ok=False
                        previous_end=step.end_ms
                        if step.end_ms-step.start_ms>policy.max_action_ms:add('interaction','GAME_ACTION_TIMEOUT',subject,'Observed action latency exceeds operator budget.');ok=False
                        if not step.succeeded or step.error:add('interaction','GAME_ACTION_FAILED',subject,'Real UI action/observation failed.');ok=False
                        try:png_check(read(step.screenshot),trace.width,trace.height)
                        except ContractError as e:add('runtime',e.code,subject,'Screenshot bytes do not match required checkpoint.');ok=False
                        if {v.key for v in step.values}!=observables:add('interaction','GAME_OBSERVABLE_COVERAGE',subject,'Required independent observables missing/added.');ok=False
                        if any(v.count!=1 or not v.visible for v in step.values):add('interaction','GAME_HIDDEN_OR_AMBIGUOUS_STATE',subject,'Expected output is hidden, missing or duplicated.');ok=False
                        values=tuple(sorted((v.key,v.text) for v in step.values));want=tuple(sorted((v.key,v.text) for v in states[state_id].values))
                        if values!=want:add('interaction','GAME_STATE_TRANSITION_MISMATCH',subject,'Visible score/feedback/state does not match independent transition oracle.');ok=False
                        case_values.append(values);step_ok.append(ok)
                        if ok:observed_states.append((state_id,dict(values)))
                        if index and ok and step_ok[index-1]:
                            t=route[index-1];covered.add(t.transition_id)
                            matched.append((t,dict(case_values[index-1]),dict(values),subject,trace.replay))
                    normalized.setdefault(subject,[]).append(tuple(case_values))
                for key,vals in normalized.items():
                    if any(v!=vals[0] for v in vals[1:]):add('interaction','GAME_REPLAY_DIVERGENCE',key,'Identical approved UI paths produce different observed states.')
                if covered!={t.transition_id for t in policy.transitions}:add('interaction','GAME_OBSERVED_TRANSITION_COVERAGE','runtime','Not every required transition was observed correctly.')
                metrics['runtime']['traces']=observed_cases;metrics['runtime']['loaded_assets']=len(loaded)
                metrics['interaction']['covered_transitions']=len(covered);metrics['interaction']['required_transitions']=len(policy.transitions)
    except ContractError as e:add('common',e.code,'game','Artifact store/identity violation blocks verification.')
    claims={c.claim_id:c for c in request.source.claims};used=set();opportunities=set()
    for target in policy.learning:
        ids={target.prompt_claim_id,target.correct_claim_id,target.incorrect_claim_id};used|=ids
        if not ids<=set(claims):add('learning','GAME_LEARNING_CLAIM_MISSING',target.challenge_id,'Required source-linked prompt/feedback claim is missing.');continue
        success=False;failure=False
        for t,before,after,case,replay in matched:
            if t.action_id not in target.response_action_ids:continue
            if before.get(target.prompt_key)!=claims[target.prompt_claim_id].text:add('learning','GAME_PROMPT_NOT_PRESENTED',target.challenge_id,'Source-linked challenge must actually be visible before response.');continue
            if t.after==target.success_state:
                if after.get(target.feedback_key)!=claims[target.correct_claim_id].text:add('learning','GAME_CORRECT_FEEDBACK_MISMATCH',target.challenge_id,'Actual correct-response feedback differs from source-linked claim.')
                else:success=True;opportunities.add((target.challenge_id,'success'))
            if t.after==target.failure_state:
                if after.get(target.feedback_key)!=claims[target.incorrect_claim_id].text:add('learning','GAME_INCORRECT_FEEDBACK_MISMATCH',target.challenge_id,'Incorrect-response feedback differs from source-linked claim.')
                else:failure=True;opportunities.add((target.challenge_id,'failure'))
        if not success or not failure:add('learning','GAME_LEARNING_RESPONSE_COVERAGE',target.challenge_id,'Both successful and misconception/error response branches need actual observed evidence.')
        if claims[target.correct_claim_id].text==claims[target.incorrect_claim_id].text:add('learning','GAME_UNDIFFERENTIATED_FEEDBACK',target.challenge_id,'Success and error feedback are identical; contextual repair required.')
    for b in policy.text_bindings:
        used.add(b.claim_id)
        if b.claim_id not in claims:add('learning','GAME_BOUND_CLAIM_MISSING',b.claim_id,'Additional hint/instruction text has no source-linked claim.');continue
        for sid in b.state_ids:
            rows=[v for s,v in observed_states if s==sid]
            if not rows or any(v.get(b.key)!=claims[b.claim_id].text for v in rows):add('learning','GAME_BOUND_TEXT_MISMATCH',b.claim_id,'Hint/instruction is not observed as the reviewed source-linked text.')
    if used!=set(claims):add('learning','GAME_LEARNING_CLAIM_SCOPE','game','Declared prompt/feedback source inventory is not fully mapped.')
    metrics['learning']['observed_response_classes']=len(opportunities);metrics['learning']['required_challenges']=len(policy.learning)
    ed=digest(dict(inspected=sorted(inspected),artifacts=[(k,hashlib.sha256(v).hexdigest()) for k,v in sorted(cache.items())],reviews=[r.signing_bytes().hex()+r.signature for r in sorted(reviews,key=lambda r:r.review_id)],verifier=verifier.configuration_digest,source=source.to_dict()))
    reports=tuple(Report(TASKS[k],request.content_digest,policy.content_digest,ed,as_of,tuple(sorted(set(groups['common']+groups[k]),key=lambda x:(x.severity,x.code,x.subject_id,x.detail))),tuple(sorted(metrics[k].items())),tuple(sorted(inspected)),LIMITATIONS) for k in AREAS)
    return GameResult(source,reports,tuple(sorted(inspected)),observed_cases,tuple(sorted(covered)))
