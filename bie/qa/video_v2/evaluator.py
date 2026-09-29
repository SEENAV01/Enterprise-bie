"""Actual-byte technical video QA; no receipts/fixture flags alone certify execution."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import base64,hashlib,re
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer
from ..source_v2.io import SnapshotStore
from ..source_v2.models import Finding,Report
from ..reasoning_v2.attestation import Review,ReviewVerifier
from .codec import loads,load_receipt
from .models import VideoRequest,VideoPolicy,all_refs,artifact_digest
from .media import inspect_bytes
from .metrics import sample_indices,image,error_ppm,blank_metrics,region_error,clock_errors

AREAS=('compile','render','sampling','blank','crop','continuity','duration')
TASKS={a:f'BIE-QA-VIDEO-{i:03}' for i,a in enumerate(AREAS,1)}
LIMITATIONS=(
 'Bounded local MP4/constant-frame-rate technical inspection. All decoded RGB frames are checked, but semantic correctness, educational quality and native Remotion provenance are separate obligations.',
 'Compile/render receipts require separately provisioned execution attestation. Logs, hashes, process flags and a successfully decoded file cannot prove their own producer or source-to-output correspondence.',
 'Blank/abrupt/frozen metrics are operator-defined diagnostics, not universal aesthetic, clinical safety or learning measures. Approved cuts, blank intervals and required movement must be set outside the candidate.',
 'Crop checks compare only operator-required frame/region PNG templates plus screen bounds; they do not locate arbitrary missing text or prove full-object/3D/occlusion semantics.',
 'No final audiovisual synchronization, player/device testing, production hostile-input sandbox, real-book E2E or product acceptance is established. Long media must use a governed chunked worker; this bounded lane rejects over-budget input.')

@dataclass(frozen=True,slots=True)
class VideoResult:
    reports:tuple[Report,...]
    sampled_frames:tuple[tuple[int,str],...]
    decoded_frame_count:int
    observation_digest:str
    inspected_artifact_ids:tuple[str,...]
    @property
    def status(self):
        statuses={r.status for r in self.reports}
        return 'BLOCKED' if 'BLOCKED' in statuses else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in statuses else 'CHECKS_PASSED'
    @property
    def product_accepted(self):return False
    def to_dict(self):return dict(reports={a:r.to_dict() for a,r in zip(AREAS,self.reports)},sampled_frames=self.sampled_frames,decoded_frame_count=self.decoded_frame_count,observation_digest=self.observation_digest,inspected_artifact_ids=self.inspected_artifact_ids,status=self.status,product_accepted=False,full_media_quality_verified=False)
    @property
    def content_digest(self):return digest(self.to_dict())

def review_targets(request,policy):
    return {('calibration','compile-execution'):(request.compile_receipt.artifact_id,),
            ('calibration','render-execution'):(request.render_receipt.artifact_id,),
            ('inventory','video-coverage'):tuple(sorted({request.video.artifact_id,*(r.reference.artifact_id for r in policy.regions)}))}

def decode_log(data):
    obj=loads(data)
    if type(obj) is not dict or set(obj)!= {'encoding','data','byte_count','sha256'} or obj['encoding']!='base64' or type(obj['data']) is not str or type(obj['byte_count']) is not int:raise ContractError('VIDEO_LOG_FORMAT')
    try:b=base64.b64decode(obj['data'],validate=True)
    except (ValueError,TypeError) as exc:raise ContractError('VIDEO_LOG_BASE64') from exc
    if len(b)!=obj['byte_count'] or hashlib.sha256(b).hexdigest()!=obj['sha256']:raise ContractError('VIDEO_LOG_IDENTITY')
    return b

def encode_log(data):
    if type(data) is not bytes:raise ContractError('VIDEO_LOG_BYTES')
    return canonical_bytes(dict(encoding='base64',data=base64.b64encode(data).decode(),byte_count=len(data),sha256=hashlib.sha256(data).hexdigest()))

def evaluate(request,artifact_root,policy,*,as_of,reviews=(),verifier=None,tools=None):
    if type(request) is not VideoRequest or type(policy) is not VideoPolicy:raise ContractError('VIDEO_EVALUATION_TYPE')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>256 or any(type(r) is not Review for r in reviews):raise ContractError('VIDEO_REVIEW_TYPE')
    if len({r.review_id for r in reviews})!=len(reviews) or len({(r.evaluator_id,r.purpose,r.subject_id) for r in reviews})!=len(reviews):raise ContractError('VIDEO_DUPLICATE_REVIEW')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('VIDEO_VERIFIER_TYPE')
    groups={a:[] for a in ('common',)+AREAS};measures={a:{} for a in AREAS};inspected=set();cache={};by_id={};by_path={}
    def add(area,code,subject,detail,severity='BLOCKER'):
        finding=Finding(code,severity,subject,'COMP' if area in ('compile','render') else 'QA.VIDEO',detail)
        if finding not in groups[area]:groups[area].append(finding)
    targets=review_targets(request,policy);votes={};tainted=set()
    for r in reviews:
        key=(r.purpose,r.subject_id)
        if key not in targets:add('common','VIDEO_UNKNOWN_REVIEW',r.subject_id,'Review target is not in this policy.');continue
        area='compile' if r.subject_id=='compile-execution' else 'render' if r.subject_id=='render-execution' else 'common'
        if set(r.evidence_ids)!=set(targets[key]):add(area,'VIDEO_REVIEW_EVIDENCE',r.subject_id,'Review does not reference exact required evidence.');tainted.add(key);continue
        auth=verifier.verify_bound(r,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,as_of)
        if not auth.authenticated:add(area,'VIDEO_'+auth.code,r.subject_id,'Review authentication failed.');tainted.add(key)
        elif not auth.operational:add(area,'VIDEO_TEST_ONLY_REVIEW',r.subject_id,'Diagnostic trust cannot attest production execution.','REVIEW');tainted.add(key)
        elif r.verdict=='REJECTED':add(area,'VIDEO_REVIEW_REJECTED',r.subject_id,'Authenticated rejection cannot be outvoted.');tainted.add(key)
        elif r.verdict!='VERIFIED' or r.confidence_ppm<policy.minimum_review_confidence_ppm:add(area,'VIDEO_REVIEW_UNCERTAIN',r.subject_id,'Review remains uncertain.','REVIEW');tainted.add(key)
        else:votes.setdefault(key,set()).add(auth.independence_group)
    for key in targets:
        if key in tainted or len(votes.get(key,()))<policy.minimum_independent_assessors:
            area='compile' if key[1]=='compile-execution' else 'render' if key[1]=='render-execution' else 'common'
            add(area,'VIDEO_EXECUTION_OR_SCOPE_REVIEW_REQUIRED',key[1],'Current authorized execution/scope review required.','REVIEW')
    if request.composition_id!=policy.composition_id:add('common','VIDEO_COMPOSITION_SCOPE','video','Candidate changed the operator-approved composition.')
    if artifact_digest(request.inputs)!=policy.expected_input_digest:add('common','VIDEO_INPUT_INVENTORY','video','Code, assets and lock inventory does not match operator-approved input digest.')
    observation=None;samples=();observation_digest='0'*64;receipt_values={}
    try:
        with SnapshotStore(artifact_root) as store:
            def read(ref):
                if (ref.artifact_id in by_id and by_id[ref.artifact_id]!=ref) or (ref.path in by_path and by_path[ref.path]!=ref):raise ContractError('VIDEO_ARTIFACT_ALIAS')
                by_id[ref.artifact_id]=ref;by_path[ref.path]=ref
                if ref.artifact_id not in cache:
                    cache[ref.artifact_id]=store.read(ref);inspected.add(ref.artifact_id)
                return cache[ref.artifact_id]
            for ref in request.inputs+request.build_outputs:
                try:read(ref)
                except ContractError as exc:add('common',exc.code,ref.artifact_id,'Input or build artifact failed actual-byte verification.')
            for stage,ref in (('compile',request.compile_receipt),('render',request.render_receipt)):
                try:
                    receipt=load_receipt(read(ref));receipt_values[stage]=receipt
                    stdout=decode_log(read(receipt.stdout));stderr=decode_log(read(receipt.stderr))
                except ContractError as exc:add(stage,exc.code,ref.artifact_id,'Receipt/log bytes or schema could not be verified.');continue
                if (receipt.stage,receipt.run_id,receipt.revision,receipt.composition_id)!=(stage,request.run_id,request.revision,request.composition_id):add(stage,'VIDEO_RECEIPT_BINDING',stage,'Receipt belongs to another stage/run/revision/composition.')
                if receipt.issued_at>as_of or as_of-receipt.issued_at>policy.max_receipt_age_seconds:add(stage,'VIDEO_RECEIPT_STALE',stage,'Execution receipt is future-dated or expired.')
                if not receipt.started or receipt.timed_out or receipt.exit_code!=0:add(stage,'VIDEO_EXECUTION_FAILED',stage,'Process did not finish successfully.')
                allowed=policy.compile_tools if stage=='compile' else policy.render_tools
                if receipt.tool_id not in allowed:add(stage,'VIDEO_TOOL_POLICY',stage,'Execution tool is not operator-approved.')
                if receipt.execution_kind!='native':add(stage,'VIDEO_NON_NATIVE_RECEIPT',stage,'Diagnostic or reported execution is not native pipeline proof.','REVIEW')
                if stage=='compile':
                    if receipt.inputs_digest!=artifact_digest(request.inputs) or receipt.outputs_digest!=artifact_digest(request.build_outputs):add(stage,'VIDEO_COMPILE_ARTIFACT_LINK',stage,'Compile receipt not bound to exact inspected input/output inventory.')
                    if receipt.parent_receipt_sha256!='0'*64 or receipt.mode!='compile' or receipt.first_frame!=0 or receipt.frame_count!=0:add(stage,'VIDEO_COMPILE_SCOPE',stage,'Invalid compilation stage scope.')
                    if receipt.tool_id=='tsc' and re.search(rb'error TS\d+',stdout+stderr):add(stage,'VIDEO_COMPILER_DIAGNOSTICS',stage,'TypeScript error diagnostics remain despite claimed exit status.')
                else:
                    if receipt.inputs_digest!=artifact_digest(request.build_outputs) or receipt.outputs_digest!=artifact_digest((request.video,)) or receipt.parent_receipt_sha256!=request.compile_receipt.sha256:add(stage,'VIDEO_RENDER_ARTIFACT_LINK',stage,'Render output or compile lineage differs from inspected bytes.')
                    if receipt.mode!='full' or receipt.first_frame!=0 or receipt.frame_count!=policy.expected_frames:add(stage,'VIDEO_PARTIAL_RENDER',stage,'Smoke/subset render cannot establish complete render evidence.')
                if stderr.strip():add(stage,'VIDEO_STDERR_REVIEW',stage,'Nonempty process stderr requires tool-aware review.','REVIEW')
            try:
                observation=inspect_bytes(read(request.video),policy,tools)
                observation_digest=digest(dict(probe=observation.probe_sha256,decoded=observation.decode_sha256,tools=observation.tools_digest))
            except ContractError as exc:add('common',exc.code,'video','Actual media bytes could not be fully inspected within the supported profile.')
            if observation is not None:
                n=observation.frames_count;measures['render']['decoded_frames']=n;measures['render']['audio_streams']=observation.audio_streams
                if policy.require_audio and not observation.audio_streams:add('render','VIDEO_REQUIRED_AUDIO_MISSING','video','Required audio stream is absent; presence alone never proves synchronization.')
                for code in clock_errors(observation,policy):add('duration',code,'video','Decoded presentation clock/count differs from operator-approved output.')
                measures['duration']['decoded_frames']=n
                try:
                    selected=sample_indices(policy)
                    if any(i>=n for i in selected):raise ContractError('VIDEO_REQUIRED_SAMPLE_MISSING')
                    samples=tuple((i,hashlib.sha256(observation.frames[i]).hexdigest()) for i in selected)
                    measures['sampling']['sample_count']=len(samples)
                except ContractError as exc:add('sampling',exc.code,'video','Required boundary/interval samples cannot be satisfied.')
                previous=None;frozen=0;blank_count=0;max_diff=0;max_freeze=0
                for i,frame in enumerate(observation.frames):
                    img=image(frame,observation.width,observation.height);bm=blank_metrics(img,policy.black_level)
                    suspicious=bm['black_fraction_ppm']>=policy.black_fraction_ppm or bm['max_channel_span']<=policy.uniform_channel_span
                    if suspicious and not any(w.contains(i) for w in policy.blank_allowances):
                        blank_count+=1
                        # Summarize later; no unbounded per-frame finding explosion.
                    if previous is not None:
                        delta=error_ppm(previous,img);max_diff=max(max_diff,delta)
                        if delta>policy.abrupt_change_ppm and i not in policy.cuts:add('continuity','VIDEO_UNAPPROVED_DISCONTINUITY','video','At least one adjacent-frame pixel jump exceeds the approved bound.')
                        active=any(w.contains(i) and w.contains(i-1) for w in policy.expected_motion)
                        frozen=frozen+1 if active and delta<=policy.frozen_change_ppm and i not in policy.cuts else 0
                        max_freeze=max(max_freeze,frozen)
                        if frozen>=policy.max_repeated_frames:add('continuity','VIDEO_FROZEN_REQUIRED_MOTION','video','A required-motion interval contains too many unchanged adjacent frames.')
                    previous=img
                if blank_count:add('blank','VIDEO_UNAPPROVED_BLANK','video','Near-black or uniform frames appear outside approved blank intervals.')
                measures['blank']['flagged_frames']=blank_count;measures['continuity'].update(max_change_ppm=max_diff,max_repeated_transitions=max_freeze)
                if not policy.expected_motion:add('continuity','VIDEO_MOTION_EXPECTATIONS_ABSENT','video','Freeze detection cannot infer which educational objects must move.','REVIEW')
                if not policy.regions:add('crop','VIDEO_CROP_COVERAGE_MISSING','video','No independent required-content templates provided.','REVIEW')
                checked=0
                for region in policy.regions:
                    try:
                        if region.frame>=n:raise ContractError('VIDEO_REGION_FRAME_MISSING')
                        diff=region_error(image(observation.frames[region.frame],observation.width,observation.height),region,read(region.reference));checked+=1
                        if diff>region.max_error_ppm:add('crop','VIDEO_REQUIRED_REGION_MISMATCH',region.region_id,'Decoded content differs from complete operator reference; crop/omission/paint changes require repair.')
                    except ContractError as exc:add('crop',exc.code,region.region_id,'Required complete content could not be verified in output frame.')
                measures['crop']['regions_checked']=checked
    except ContractError as exc:add('common',exc.code,'video','Artifact store unavailable; no successful inspection is assumed.')
    evidence_digest=digest(dict(inspected=sorted(inspected),artifacts=[(k,hashlib.sha256(v).hexdigest()) for k,v in sorted(cache.items())],observation=observation_digest,reviews=[r.signing_bytes().hex()+r.signature for r in sorted(reviews,key=lambda r:r.review_id)],verifier=verifier.configuration_digest))
    reports=[]
    for a in AREAS:
        fs=tuple(sorted(groups['common']+groups[a],key=lambda f:(f.severity,f.code,f.subject_id,f.detail)))
        reports.append(Report(TASKS[a],request.content_digest,policy.content_digest,evidence_digest,as_of,fs,tuple(sorted(measures[a].items())),tuple(sorted(inspected)),LIMITATIONS))
    return VideoResult(tuple(reports),samples,0 if observation is None else observation.frames_count,observation_digest,tuple(sorted(inspected)))
