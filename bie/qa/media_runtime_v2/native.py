"""HARD020 native compiler execution and exact final-media binding.

The existing canonical scripts are invoked unchanged only from an explicitly
registered local checkout. No npm installs, injected renderers or generated
replacement implementations. Missing files/toolchain stop before native success.
This module does NOT provide a sandbox for untrusted code.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,os,tempfile,time
from .common import *
from .storage import hash_file,StreamArtifact,snapshot
from .process import pipe
from .stream import StreamPolicy,inspect,validate_coverage
from ..video_v2.adapters import from_native_render


@dataclass(frozen=True)
class NativeProfile:
    revision:str
    files:tuple[tuple[str,str],...]
    python:Tool
    timeout_s:int=300
    def __post_init__(self):
        from ..release_v2.contracts import revision
        revision(self.revision);integer(self.timeout_s,'timeout',1,3600)
        require(type(self.files)is tuple and 2<=len(self.files)<=20000,'H5_NATIVE_FILE_INVENTORY')
        paths=[]
        for path,h in self.files:safe_relative_path(path);sha256(h,'native_file');paths.append(path)
        require(len(set(paths))==len(paths),'H5_NATIVE_DUPLICATE_FILE')
        require({'scripts/compile_scene_checked.py','scripts/run_comp_render.py'}<=set(paths),'H5_NATIVE_ENTRYPOINTS')
        require(type(self.python)is Tool,'H5_NATIVE_PYTHON')
    @property
    def content_digest(self):return digest(asdict(self))


def verify_checkout(root,profile):
    require(type(profile)is NativeProfile,'H5_NATIVE_PROFILE')
    profile.python.verify();rows=[]
    for path,h in profile.files:
        actual,size=hash_file(Path(root)/path,max_bytes=256*1024**2)
        require(actual==h,'H5_NATIVE_CHECKOUT_DRIFT')
        rows.append({'path':path,'sha256':h,'bytes':size})
    return {'revision':profile.revision,'files':rows,'profile_digest':profile.content_digest,
            'dependency_closure_asserted_by_operator_not_discovered':True}


def preflight(root,profile):
    """Nonexecuting readiness probe, useful even when the full checkout is absent."""
    try:return {'status':'READY_FOR_TRUSTED_INVOCATION','checkout':verify_checkout(root,profile),'native_executed':False}
    except (ContractError,OSError) as e:
        return {'status':'BLOCKED','code':getattr(e,'code','H5_NATIVE_FILES_UNAVAILABLE'),'native_executed':False}


def _run(argv,cwd,timeout):
    start=time.time_ns();monotonic=time.monotonic_ns()
    with pipe(argv,timeout=timeout,cwd=cwd,allow_nonzero=True) as handle:
        stdout=handle['read'](4*1024**2+1);require(len(stdout)<=4*1024**2,'H5_NATIVE_LOG_BUDGET')
    return {'argv':argv,'exit_code':handle['exit_code'],'started_ns':start,
            'elapsed_ns':time.monotonic_ns()-monotonic,'stdout':stdout.decode('utf-8',errors='strict'),
            'stderr':bytes(handle['stderr']).decode('utf-8',errors='replace'),'pid':handle['pid']}


def run_native_pipeline(checkout,profile,scene_path,destination,render_request,*,allow_trusted_execution=False,asset_root=None,motion_preference='standard'):
    """Execute approved native scripts; returned execution records remain unsigned.

    Destination must be new. Inputs/checkout are hash rechecked after invocation.
    The operator supplies a provisioned native dependency environment; unsupported
    setup is not repaired by downloading, patching source or injecting a renderer.
    """
    require(allow_trusted_execution is True,'H5_NATIVE_EXECUTION_OPT_IN')
    before=verify_checkout(checkout,profile);source_hash,_=hash_file(scene_path)
    dest=Path(destination).absolute();require(not dest.exists() and not dest.is_symlink(),'H5_NATIVE_OUTPUT_EXISTS')
    require(type(render_request)is dict and 'composition' in render_request,'H5_NATIVE_RENDER_REQUEST')
    forbidden={'runner','mode','first_frame','frame_count'}
    require(not forbidden & set(render_request),'H5_NATIVE_INJECTED_OR_PARTIAL_REQUEST')
    py=profile.python.verify();root=Path(checkout).absolute()
    stages=[];status='BLOCKED';code='H5_NATIVE_COMPILE_FAILED'
    composition=render_request['composition'];require(type(composition)is dict,'H5_NATIVE_COMPOSITION')
    target=[]
    for name,maximum in (('width',4096),('height',2160),('fps',240)):
        integer(composition.get(name),name,1,maximum);target.extend(['--'+name,str(composition[name])])
    require(motion_preference in ('standard','reduced'),'H5_NATIVE_MOTION_MODE')
    target.extend(['--motion-preference',motion_preference])
    if asset_root is not None:
        ar=Path(asset_root).absolute();require(ar.is_dir() and not ar.is_symlink(),'H5_NATIVE_ASSET_ROOT');target.extend(['--asset-root',str(ar)])
    compiled=_run([py,'-B',str(root/'scripts/compile_scene_checked.py'),str(Path(scene_path).absolute()),str(dest)]+target,root,profile.timeout_s)
    stages.append(compiled)
    if compiled['exit_code']==0:
        request={**render_request,'workspace':str(dest)}
        with tempfile.TemporaryDirectory(prefix='bie-h5-native-request-') as td:
            req=Path(td)/'request.json';req.write_bytes(canonical_bytes(request))
            rendered=_run([py,'-B',str(root/'scripts/run_comp_render.py'),str(req),'--mode','full'],root,profile.timeout_s)
            stages.append(rendered)
        if rendered['exit_code']==0:status='NATIVE_COMMANDS_COMPLETED_REDECODE_REQUIRED';code='H5_NATIVE_DECODE_REQUIRED'
        else:code='H5_NATIVE_RENDER_FAILED'
    require(verify_checkout(checkout,profile)==before,'H5_NATIVE_CHECKOUT_DRIFT')
    require(hash_file(scene_path)[0]==source_hash,'H5_NATIVE_SOURCE_DRIFT')
    return {'schema_version':'bie.qa.native-av-execution/1','profile':asdict(profile),
            'source_sha256':source_hash,'checkout':before,'stages':stages,'status':status,'code':code,
            'native_scripts_invoked':True,'native_pipeline_success':False,'release_authorized':False}


@dataclass(frozen=True)
class AVPolicy:
    composition_id:str
    scene_sha256:str
    native_revision:str
    required_evidence:tuple[str,...]
    max_age:int=86400
    def __post_init__(self):
        from ..release_v2.contracts import revision
        token(self.composition_id,'composition');sha256(self.scene_sha256,'scene');revision(self.native_revision)
        checked_ids(self.required_evidence,'NATIVE_EVIDENCE');require({'source-scene','checked-scene','input-manifest','render-recipe','toolchain','isolation','render-log'}<=set(self.required_evidence),'H5_NATIVE_REQUIRED_LINEAGE');integer(self.max_age,'age',1,604800)


def inspect_native_av(root,receipt_ref,video:StreamArtifact,stream_report,binding,policy,*,evidence_refs,stream_policy=None,ffmpeg=None,ffprobe=None,review=None,verifier=ReviewVerifier(),now=0):
    policy_binding(binding,policy);integer(now,'now');findings=[]
    require(type(receipt_ref)is ArtifactRef and type(evidence_refs)is tuple,'H5_AV_EVIDENCE_TYPES')
    refs=(receipt_ref,)+evidence_refs
    require(len({r.artifact_id for r in refs})==len(refs) and len({r.path for r in refs})==len(refs),'H5_AV_EVIDENCE_ALIAS')
    with SnapshotStore(root) as store:
        raw=json.loads(store.read(receipt_ref))
        payload={r.artifact_id:store.read(r) for r in evidence_refs}
    if set(payload)!=set(policy.required_evidence):fail(findings,'H5_AV_EVIDENCE_INVENTORY')
    if hashlib.sha256(payload.get('source-scene',b'')).hexdigest()!=policy.scene_sha256:fail(findings,'H5_AV_SCENE_BYTES')
    require(binding.revision==policy.native_revision,'H5_AV_REVISION')
    # Native adapter has a bounded ArtifactRef; larger media cannot silently bypass
    # its current public contract. Long-form streaming remains separately usable.
    vref=ArtifactRef(video.artifact_id,video.path,video.sha256,video.size,'video')
    native=from_native_render(raw,vref,run_id=binding.run_id,composition_id=policy.composition_id)
    # A stream receipt alone is replayable metadata. Re-run the actual decoder
    # when tools/profile are provisioned; otherwise no technical-clear verdict.
    redecoded=False
    if stream_policy is None or ffmpeg is None or ffprobe is None:
        fail(findings,'H5_AV_FRESH_REDECODE_REQUIRED')
    else:
        require(type(stream_policy)is StreamPolicy and type(ffmpeg)is Tool and type(ffprobe)is Tool,'H5_AV_DECODER_PROFILE')
        sb=Binding(binding.run_id,binding.revision,binding.candidate_digest,stream_policy.content_digest)
        with tempfile.TemporaryDirectory(prefix='bie-h5-av-redecode-') as td:
            materialized=any('png_sha256' in s for s in stream_report.get('details',{}).get('samples',[]))
            fresh=inspect(root,video,sb,stream_policy,ffmpeg=ffmpeg,ffprobe=ffprobe,samples_dir=Path(td)/'samples' if materialized else None)
        # JSON arrays and the corresponding typed tuples have one canonical byte
        # representation. Do not ignore any actual report field or sample hash.
        require(canonical_bytes(fresh)==canonical_bytes(stream_report),'H5_AV_STREAM_REPLAY_MISMATCH')
        validate_coverage(fresh['details'],stream_policy);redecoded=True
    if not raw['passed'] or raw['mode']!='full' or raw['execution_kind']!='LOCAL_REMOTION_CLI':fail(findings,'H5_NATIVE_FULL_RENDER_REQUIRED')
    require(type(stream_report)is dict and stream_report.get('schema_version')==SCHEMA,'H5_AV_STREAM_REPORT')
    sr=stream_report['report'];sd=stream_report['details']
    if sr['binding']['candidate_digest']!=binding.candidate_digest or sr['binding']['run_id']!=binding.run_id or sr['binding']['revision']!=binding.revision:fail(findings,'H5_AV_FOREIGN_STREAM_REPORT')
    if sd.get('artifact')!=asdict(video) or sd.get('full_frame_coverage') is not True or sd.get('frames')!=raw['expected_frames']:fail(findings,'H5_AV_STREAM_IDENTITY')
    if stream_report.get('technical_checks_clear') is not True or any(f['severity']=='BLOCKER' for f in sr['findings']):fail(findings,'H5_AV_STREAM_FAILED')
    # The independently supplied, byte-bound lineage record is not assumed correct.
    # A current scoped review must authenticate the entire receipt+capture+evidence.
    request_digest=digest({'binding':asdict(binding),'native_receipt':receipt_ref.to_dict(),
                           'stream_report_digest':digest(stream_report),'evidence':[r.to_dict() for r in evidence_refs],
                           'scene_sha256':policy.scene_sha256,'native_revision':policy.native_revision})
    auth=approved(review,verifier,subject=policy.composition_id,purpose='support',request_digest=request_digest,
                  policy_digest=binding.policy_digest,now=now,evidence_ids=tuple(r.artifact_id for r in refs),max_age=policy.max_age)
    if auth=='BLOCKED':fail(findings,'H5_AV_EXECUTION_REVIEW_INVALID')
    elif auth!='VERIFIED':findings.append(Finding('H5_AV_EXECUTION_REVIEW_REQUIRED',policy.composition_id))
    # Reopen final media even if an older streaming receipt claimed a matching hash.
    with snapshot(root,video) as (_,manifest):pass
    return findings_report('BIE-QA-HARD-020',binding,findings,{'native':native,'actual_media_bytes':manifest,
            'request_digest':request_digest,'review':auth,'native_provenance_authenticated':auth=='VERIFIED',
            'actual_media_redecoded':redecoded,'final_acoustic_sync_verified':False},refs)
