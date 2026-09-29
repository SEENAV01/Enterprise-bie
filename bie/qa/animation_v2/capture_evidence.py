"""Byte-bound paused-browser samples. No claim about unsampled intermediate frames."""
from fractions import Fraction
from io import BytesIO
import warnings
from ..release_v2.contracts import ContractError,integer
from ..source_v2.codec import loads
from .metrics import value_at,frame_time_ms,SUPPORTED

FIELDS={'schema_version','mode','plan_digest','policy_digest','mode_id','html_sha256','renderer','viewport','frames','unsupported'}
FRAME_FIELDS={'frame_index','time_numerator','time_denominator','screenshot_sha256','objects'}
OBJECT_FIELDS={'object_id','x_mpx','y_mpx','width_mpx','height_mpx','opacity_ppm','displayed'}

def expected_value(request,mode_id,oid,prop,time):
    ts=sorted((t for t in request.tracks if (t.mode_id,t.object_id,t.property)==(mode_id,oid,prop)),key=lambda t:(t.start_ms,t.track_id))
    if not ts:return None
    for t in ts:
        if t.start_ms<=time<=t.end_ms:return value_at(t,time)
        if time<t.start_ms:return Fraction(ts[0].keyframes[0].value) if t is ts[0] else Fraction(previous.keyframes[-1].value)
        previous=t
    return Fraction(ts[-1].keyframes[-1].value)

def validate_png(data,width,height):
    try:
        from PIL import Image
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as im:
                if im.format!='PNG' or im.size!=(width,height) or getattr(im,'n_frames',1)!=1:raise ContractError('ANI_CAPTURE_IMAGE_DIMENSIONS')
                im.verify()
            with Image.open(BytesIO(data)) as im:im.load()
    except ImportError as exc:raise ContractError('ANI_IMAGE_DECODER_UNAVAILABLE') from exc
    except (OSError,ValueError,Warning) as exc:
        if isinstance(exc,ContractError):raise
        raise ContractError('ANI_CAPTURE_IMAGE_INVALID') from exc

def verify_capture(capture,request,policy,store):
    modes={m.mode_id:m for m in policy.modes};specs={s.mode_id:s for s in policy.captures}
    if capture.mode_id not in modes or capture.mode_id not in specs:raise ContractError('ANI_CAPTURE_UNAPPROVED_MODE')
    m=modes[capture.mode_id];spec=specs[capture.mode_id]
    html=store.read(capture.html);raw=store.read(capture.observations);d=loads(raw)
    if not html.strip():raise ContractError('ANI_CAPTURE_EMPTY_HTML')
    if type(d) is not dict or set(d)!=FIELDS:raise ContractError('ANI_CAPTURE_FIELDS')
    if d['schema_version']!='1.0.0' or d['mode']!='paused-css-samples':raise ContractError('ANI_CAPTURE_KIND')
    if d['plan_digest']!=request.plan_digest or d['policy_digest']!=policy.content_digest:raise ContractError('ANI_CAPTURE_CONTEXT')
    if d['mode_id']!=m.mode_id or d['viewport']!=[m.width_px,m.height_px]:raise ContractError('ANI_CAPTURE_VIEW')
    if d['html_sha256']!=capture.html.sha256:raise ContractError('ANI_CAPTURE_HTML_BINDING')
    if type(d['renderer']) is not str or not 1<=len(d['renderer'])<=200:raise ContractError('ANI_CAPTURE_RENDERER')
    if type(d['unsupported']) is not list or len(d['unsupported'])>128 or any(type(x) is not str or len(x)>200 for x in d['unsupported']):raise ContractError('ANI_CAPTURE_UNSUPPORTED_FIELDS')
    frames=d['frames']
    if type(frames) is not list or len(frames)!=len(spec.frame_indices) or len(capture.screenshots)!=len(frames):raise ContractError('ANI_CAPTURE_SAMPLE_COUNT')
    ids={o.object_id for o in policy.objects};violations=[]
    for row,frame,shot in zip(frames,spec.frame_indices,capture.screenshots):
        if type(row) is not dict or set(row)!=FRAME_FIELDS:raise ContractError('ANI_CAPTURE_FRAME_FIELDS')
        for n in ('frame_index','time_numerator','time_denominator'):integer(row[n],n,0 if n!='time_denominator' else 1,10**15)
        tm=frame_time_ms(frame,m.fps)
        if row['frame_index']!=frame or (row['time_numerator'],row['time_denominator'])!=(tm.numerator,tm.denominator):raise ContractError('ANI_CAPTURE_CLOCK_OR_ORDER')
        if row['screenshot_sha256']!=shot.sha256:raise ContractError('ANI_CAPTURE_SCREENSHOT_BINDING')
        validate_png(store.read(shot),m.width_px,m.height_px)
        obs=row['objects']
        if type(obs) is not list or len(obs)>128:raise ContractError('ANI_CAPTURE_OBJECT_LIST')
        for x in obs:
            if type(x) is not dict or set(x)!=OBJECT_FIELDS:raise ContractError('ANI_CAPTURE_OBJECT_FIELDS')
            if type(x['object_id']) is not str or type(x['displayed']) is not bool:raise ContractError('ANI_CAPTURE_OBJECT_TYPE')
            for n in ('x_mpx','y_mpx','width_mpx','height_mpx','opacity_ppm'):integer(x[n],n,-1_000_000_000 if n in ('x_mpx','y_mpx') else 0,1_000_000 if n=='opacity_ppm' else 1_000_000_000)
        if len({x['object_id'] for x in obs})!=len(obs):raise ContractError('ANI_CAPTURE_DUPLICATE_OBJECT')
        if {x['object_id'] for x in obs}!=ids:violations.append(('ANI_CAPTURE_OBJECT_INVENTORY',m.mode_id,frame))
        for x in obs:
            if x['object_id'] not in ids:continue
            oid=x['object_id'];obj=next(o for o in policy.objects if o.object_id==oid)
            if obj.start_ms<=tm<obj.end_ms and not x['displayed']:violations.append(('ANI_CAPTURE_HIDDEN_OBJECT',oid,frame))
            for prop in ('x_mpx','y_mpx','opacity_ppm'):
                try:expected=expected_value(request,m.mode_id,oid,prop,tm)
                except ContractError:continue  # unsupported interpolation is an explicit REVIEW elsewhere
                if expected is None:continue
                tol=spec.opacity_tolerance_ppm if prop=='opacity_ppm' else spec.tolerance_mpx
                if abs(x[prop]-expected)>tol:violations.append(('ANI_CAPTURE_TRAJECTORY_MISMATCH',oid+':'+prop,frame))
    unsupported=set(d['unsupported'])
    if any(t.mode_id==m.mode_id and t.property not in ('x_mpx','y_mpx','opacity_ppm') for t in request.tracks):unsupported.add('UNMEASURED_CHANNELS')
    return tuple(sorted(set(violations))),tuple(sorted(unsupported)),len(frames)
