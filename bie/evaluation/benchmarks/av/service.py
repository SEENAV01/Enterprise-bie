"""H2-008: artifact-bound streaming AV evaluation, no self-reported PASS admission."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib
from ..models import BenchmarkError,digest,digest_string,canonical_json,strict_loads,ident
from .custody import Limits,frozen_artifact,regular_path,exact_fields,finite,integer
from .process import Deadline,capture,executable
from .probe import inspect,fraction
from .video import decode_video
from .audio import decode_audio
from .timeline import decode_timeline,consistency
from .captions import parse,intervals,alignment

POLICY_FIELDS={'schema_version','width','height','expected_frames','fps','require_audio','require_captions',
 'caption_text_sha256','narration_intervals_s','max_dark_fraction','max_identical_run_s',
 'max_silent_fraction','max_clipped_fraction','min_caption_coverage','min_narration_activity','sync_tolerance_s'}

def validate_policy(value):
    r=strict_loads(canonical_json(value));exact_fields(r,POLICY_FIELDS)
    if r['schema_version']!='av-policy-2':raise BenchmarkError('UNSUPPORTED_AV_POLICY')
    integer(r['width'],1,7680);integer(r['height'],1,4320);integer(r['expected_frames'],1,864000)
    if type(r['fps']) is not str:raise BenchmarkError('FPS_MUST_BE_RATIONAL_TEXT')
    fps=fraction(r['fps'])
    if not 0<fps<=120:raise BenchmarkError('POLICY_FPS_LIMIT')
    duration=r['expected_frames']/float(fps)
    if not 0<duration<=7200:raise BenchmarkError('POLICY_DURATION_LIMIT')
    for k in ('require_audio','require_captions'):
        if type(r[k]) is not bool:raise BenchmarkError('POLICY_BOOLEAN_REQUIRED')
    if r['require_captions']:
        digest_string(r['caption_text_sha256'])
    elif r['caption_text_sha256'] is not None:raise BenchmarkError('UNEXPECTED_CAPTION_TEXT_PIN')
    for k in ('max_dark_fraction','max_silent_fraction','max_clipped_fraction','min_caption_coverage','min_narration_activity'):
        finite(r[k],0,1)
    finite(r['max_identical_run_s'],0,7200);finite(r['sync_tolerance_s'],0,1)
    intervals(r['narration_intervals_s'],duration) # validate without changing canonical input types
    if r['require_audio'] and not r['narration_intervals_s']:raise BenchmarkError('NARRATION_EXPECTATION_REQUIRED')
    if r['require_captions'] and not r['require_audio']:raise BenchmarkError('CAPTION_AUDIO_POLICY_INCONSISTENT')
    return r

def code_sha256():
    base=Path(__file__).parent
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.glob('*.py'))}
    # Bind reused canonicalization implementation as well as this extension.
    for name in ('models.py','storage.py'):
        files['../'+name]=hashlib.sha256((base.parent/name).read_bytes()).hexdigest()
    return digest(files)

def tool_identity():
    from .custody import sha_file
    result={}
    for name in ('ffmpeg','ffprobe'):
        path=executable(name);sha,size=sha_file(path,maximum=1_000_000_000)
        result[name]={'path':path,'sha256':sha,'bytes':size}
    return result

def _grade(policy,observed):
    m=observed['metadata'];v=observed['video'];a=observed['audio'];vt=observed['video_timing'];at=observed['audio_timing']
    reasons=consistency(m,v,vt,a,at,tolerance_s=policy['sync_tolerance_s'])
    if (m['width'],m['height'])!=(policy['width'],policy['height']):reasons.append('REFERENCE_DIMENSIONS_MISMATCH')
    if fraction(m['fps'])!=fraction(policy['fps']):reasons.append('REFERENCE_FPS_MISMATCH')
    if v['decoded_frames']!=policy['expected_frames']:reasons.append('REFERENCE_FRAME_COUNT_MISMATCH')
    expected_duration=policy['expected_frames']/float(fraction(policy['fps']))
    if abs((vt['end_s']-vt['start_s'])-expected_duration)>max(policy['sync_tolerance_s'],0.002):reasons.append('REFERENCE_DURATION_MISMATCH')
    if v['dark_frames']/v['decoded_frames']>policy['max_dark_fraction']:reasons.append('DARK_FRAME_FLOOR')
    if v['max_same_run_transitions']/float(fraction(policy['fps']))>policy['max_identical_run_s']:reasons.append('IDENTICAL_FRAME_RUN_FLOOR')
    if policy['require_audio'] and a is None:reasons.append('REQUIRED_AUDIO_MISSING')
    if a is not None:
        n=a['samples_per_channel']
        if any(x/n>policy['max_silent_fraction'] for x in a['silent_samples_per_channel']):reasons.append('SILENT_CHANNEL_FLOOR')
        if any(x/n>policy['max_clipped_fraction'] for x in a['clipped_samples_per_channel']):reasons.append('CLIPPED_AUDIO_FLOOR')
    captions=observed['captions'];al=observed['alignment']
    if policy['require_captions']:
        if captions is None:reasons.append('REQUIRED_CAPTIONS_MISSING')
        elif captions['text_sha256']!=policy['caption_text_sha256']:reasons.append('CAPTION_TEXT_REFERENCE_MISMATCH')
        value=al['caption_coverage_of_declared_narration']
        if value is None or value<policy['min_caption_coverage']:reasons.append('CAPTION_COVERAGE_FLOOR')
    if policy['require_audio']:
        value=al['decoded_activity_coverage_of_declared_narration']
        if value is None or value<policy['min_narration_activity']:reasons.append('NARRATION_ACTIVITY_FLOOR')
    return sorted(set(reasons))

def collect_and_evaluate(*,media_path,media_sha256,policy,policy_sha256,run_id,
                         caption_path=None,caption_sha256=None,caption_format='srt',limits=Limits()):
    """Run local tools on verified private bytes. No acceptance or native claim.

    Invalid admission inputs raise BenchmarkError. Failures after admitted inputs
    return BLOCKED without a score. The ledger reserves attempts BEFORE this call.
    """
    ident(run_id);digest_string(media_sha256);digest_string(policy_sha256)
    p=validate_policy(policy)
    if digest(p)!=policy_sha256:raise BenchmarkError('REFERENCE_POLICY_HASH_MISMATCH')
    if type(limits) is not Limits:raise BenchmarkError('INVALID_LIMITS_TYPE')
    if (caption_path is None)!=(caption_sha256 is None):raise BenchmarkError('CAPTION_HASH_REQUIRED')
    if caption_sha256 is not None:digest_string(caption_sha256)
    if caption_format not in ('srt','vtt'):raise BenchmarkError('UNSUPPORTED_CAPTION_FORMAT')
    identity={'media_sha256':media_sha256,'caption_sha256':caption_sha256,'caption_format':caption_format if caption_path is not None else None}
    result={'schema_version':'av-result-2','run_id':run_id,'candidate_sha256':digest(identity),
            'candidate_identity':identity,'reference_sha256':policy_sha256,'evaluator_code_sha256':code_sha256(),
            'limits_sha256':digest(asdict(limits)),'status':'BLOCKED','reasons':[],
            'release_authorized':False,'product_accepted':False,'native_execution_verified':False,
            'semantic_speech_verified':False,'observations':None,'commands':[]}
    deadline=Deadline(limits.deadline_s)
    try:
        with frozen_artifact(media_path,media_sha256,limits) as (f,artifact):
            tools=tool_identity()
            parsed=None
            if caption_path is not None:
                cp=regular_path(caption_path)
                with cp.open('rb') as stream:raw=stream.read(1_000_001)
                if len(raw)>1_000_000:raise BenchmarkError('CAPTION_BYTE_LIMIT')
                if hashlib.sha256(raw).hexdigest()!=caption_sha256:raise BenchmarkError('CAPTION_HASH_MISMATCH')
                parsed=parse(raw,caption_format,p['expected_frames']/float(fraction(p['fps'])))
            m,cmd=inspect(f,limits,deadline);result['commands'].append(cmd)
            v,cmd=decode_video(f,m,limits,deadline);result['commands'].append(cmd)
            vt,cmd=decode_timeline(f,'video',m,limits,deadline);result['commands'].append(cmd)
            a,cmd=decode_audio(f,m,limits,deadline)
            at=None
            if a is not None:
                result['commands'].append(cmd);at,cmd=decode_timeline(f,'audio',m,limits,deadline);result['commands'].append(cmd)
            version,cmd=capture([executable('ffmpeg'),'-version'],f.parent,deadline,20000)
            result['commands'].append(cmd)
            if tool_identity()!=tools:raise BenchmarkError('AV_TOOLCHAIN_CHANGED_DURING_RUN')
            observed={'tool_binary_identity':tools,'artifact':artifact,'metadata':m,'video':v,'video_timing':vt,'audio':a,'audio_timing':at,
                      'captions':parsed,'alignment':alignment(parsed,p['narration_intervals_s'],a,at['start_s'] if at else 0),
                      'decoder_version':version.decode('utf-8').splitlines()[0]}
            result['observations']=observed;result['reasons']=_grade(p,observed)
            result['status']='FAIL' if result['reasons'] else 'DIAGNOSTIC_PASS'
    except BenchmarkError as exc:
        result['status']='BLOCKED';result['reasons']=[exc.code]
    except Exception as exc:
        # Redacted infrastructure error; never convert into a numeric pass.
        result['status']='BLOCKED';result['reasons']=['AV_EXECUTION_ERROR'];result['observations']=None
    # Commands pin profiles but not temporary-path noise. Media hash binds bytes.
    for cmd in result['commands']:
        cmd['argv']=['<PRIVATE_INPUT>' if x.endswith('/input.media') else x for x in cmd['argv']]
    result['receipt_sha256']=digest(result)
    return result

def verify_receipt(report):
    if type(report) is not dict:raise BenchmarkError('AV_RECEIPT_INTEGRITY')
    body=dict(report);claimed=body.pop('receipt_sha256',None)
    if claimed!=digest(body) or report.get('release_authorized') is not False or report.get('product_accepted') is not False:
        raise BenchmarkError('AV_RECEIPT_INTEGRITY')
    if report.get('native_execution_verified') is not False or report.get('semantic_speech_verified',False) is not False:raise BenchmarkError('AV_RECEIPT_INTEGRITY')
    if report.get('status') not in ('DIAGNOSTIC_PASS','FAIL','BLOCKED'):raise BenchmarkError('AV_RECEIPT_INTEGRITY')
    if report.get('recovery') is True:
        if report.get('status')!='BLOCKED' or report.get('candidate_identity') is not None or report.get('observations') is not None or 'OPERATOR_RECOVERED_ABANDONED_RUN' not in report.get('reasons',[]):raise BenchmarkError('AV_RECEIPT_INTEGRITY')
    elif report.get('candidate_sha256')!=digest(report.get('candidate_identity')):raise BenchmarkError('AV_RECEIPT_INTEGRITY')
    if report['status']=='DIAGNOSTIC_PASS' and (report.get('reasons') or report.get('observations') is None):raise BenchmarkError('AV_RECEIPT_INTEGRITY')
    return report
