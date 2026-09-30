"""METRIC-012: bounded actual file decode, stream/time/frame-count fidelity."""
from fractions import Fraction
from ..models import BenchmarkError,digest_string,text
from ..domains.structured import record,sequence,amount
from .common import indexed,weight
from .delivery_common import integer,boolean,unknown,result_unit,observation,used_artifacts

def measure(reference,candidate,artifacts):
    record(reference,{'targets'});record(candidate,{'artifacts'})
    refs=indexed(reference['targets'],{'id','width','height','fps','frame_count','audio_required','pts_tolerance_seconds','weight'},lower=1)
    actual=indexed(candidate['artifacts'],{'id','observation_id','media_sha256'});unknown(actual,refs)
    units=[];used=[]
    for k,r in sorted(refs.items()):
        w=integer(r['width'],1,320);h=integer(r['height'],1,180);fps=amount(r['fps'],positive=True,maximum=120)
        n=integer(r['frame_count'],1,300);audio=boolean(r['audio_required']);tol=amount(r['pts_tolerance_seconds'],maximum=1)
        if tol>=1/fps:raise BenchmarkError('TIMESTAMP_TOLERANCE_TOO_LARGE')
        reasons=[]
        if k not in actual:reasons.append('REQUIRED_RENDER_MISSING')
        else:
            a=actual[k];o=observation(artifacts,a['observation_id'],'media',a['media_sha256']);used.append(a['observation_id']);f=o['facts']
            record(f,{'width','height','fps','container_duration','decoded_frames','video_streams','audio_streams','pts_seconds','frame_sha256','decoded_sha256','decoder_version','decode_exit_code','codec'})
            integer(f['width'],1,320);integer(f['height'],1,180);integer(f['decoded_frames'],1,300);integer(f['video_streams'],1,8);integer(f['audio_streams'],0,8)
            integer(f['decode_exit_code'],-255,255);actualfps=amount(f['fps'],positive=True,maximum=120);dur=amount(f['container_duration'],positive=True,maximum=20)
            text(f['decoder_version']);text(f['codec']);digest_string(f['decoded_sha256'])
            pts=[amount(v,signed=True,maximum=60) for v in sequence(f['pts_seconds'],upper=300)]
            hashes=[digest_string(x) for x in sequence(f['frame_sha256'],upper=300)]
            if len(pts)!=f['decoded_frames'] or len(hashes)!=len(pts):raise BenchmarkError('MEDIA_OBSERVATION_INCONSISTENT')
            if f['decode_exit_code']!=0:reasons.append('ACTUAL_DECODE_FAILED')
            if (f['width'],f['height'])!=(w,h):reasons.append('RENDER_DIMENSIONS_MISMATCH')
            if actualfps!=fps:reasons.append('RENDER_FRAME_RATE_MISMATCH')
            if f['decoded_frames']!=n:reasons.append('RENDER_FRAME_COUNT_MISMATCH')
            if f['video_streams']!=1:reasons.append('UNEXPECTED_VIDEO_STREAMS')
            if audio and not f['audio_streams']:reasons.append('REQUIRED_AUDIO_STREAM_MISSING')
            if any(a>=b for a,b in zip(pts,pts[1:])) or any(abs(t-Fraction(i,1)/fps)>tol for i,t in enumerate(pts)):
                reasons.append('RENDER_TIMESTAMPS_MISMATCH')
            if abs(dur-Fraction(n,1)/fps)>tol:reasons.append('RENDER_DURATION_MISMATCH')
        units.append(result_unit(k,reasons,weight(r)))
    if len(set(used))!=len(used):raise BenchmarkError('OBSERVATION_REUSED_FOR_MULTIPLE_TARGETS')
    used_artifacts(artifacts,used)
    return units,[],{'assessment_scope':'ACTUALLY_DECODED_BOUNDED_VIDEO','audio_content_decoded':False,'native_bie_render_verified':False}
