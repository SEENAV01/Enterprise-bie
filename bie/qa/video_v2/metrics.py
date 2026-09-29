"""Exact deterministic diagnostics; thresholds are operator policy, not pedagogy."""
from fractions import Fraction
from io import BytesIO
from PIL import Image,ImageChops
from ..release_v2.contracts import ContractError

def sample_indices(policy):
    n=policy.expected_frames
    selected={0,n-1,*range(0,n,policy.sample_stride),*(r.frame for r in policy.regions)}
    for b in policy.boundaries+policy.cuts:
        selected.update(i for i in (b-1,b,b+1) if 0<=i<n)
    for w in policy.blank_allowances+policy.expected_motion:
        selected.update(i for i in (w.start-1,w.start,w.end-1,w.end) if 0<=i<n)
    if len(selected)>policy.max_samples:raise ContractError('VIDEO_SAMPLE_BUDGET')
    return tuple(sorted(selected))

def image(frame,width,height):
    if type(frame) is not bytes or len(frame)!=width*height*3:raise ContractError('VIDEO_RGB_SIZE')
    return Image.frombytes('RGB',(width,height),frame)

def error_ppm(a,b):
    if a.mode!='RGB' or b.mode!='RGB' or a.size!=b.size:raise ContractError('VIDEO_COMPARE_SHAPE')
    hist=ImageChops.difference(a,b).histogram();total=sum((i%256)*v for i,v in enumerate(hist))
    return total*1000000//(a.width*a.height*3*255)

def blank_metrics(img,black_level):
    if img.mode!='RGB':raise ContractError('VIDEO_RGB_REQUIRED')
    channels=img.split();hist=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]).histogram()
    return {'black_fraction_ppm':sum(hist[:black_level+1])*1000000//(img.width*img.height),'max_channel_span':max(hi-lo for lo,hi in img.getextrema())}

def region_error(img,region,reference_bytes):
    if region.x<0 or region.y<0 or region.x+region.width>img.width or region.y+region.height>img.height:raise ContractError('VIDEO_REGION_OVERFLOW')
    try:
        with Image.open(BytesIO(reference_bytes)) as im:
            if im.format!='PNG' or im.size!=(region.width,region.height) or im.mode!='RGB' or getattr(im,'n_frames',1)!=1:raise ContractError('VIDEO_REGION_IMAGE_PROFILE')
            im.load();ref=im.copy()
    except (OSError,ValueError,Image.DecompressionBombError) as exc:
        if isinstance(exc,ContractError):raise
        raise ContractError('VIDEO_REGION_IMAGE_INVALID') from exc
    actual=img.crop((region.x,region.y,region.x+region.width,region.y+region.height))
    return error_ppm(actual,ref)

def clock_errors(observation,policy):
    codes=[];tb=observation.time_base;n=len(observation.pts);step=1/policy.fps
    tolerance=min(step/4,max(tb,Fraction(1,1000000)))
    if observation.frames_count!=policy.expected_frames:codes.append('VIDEO_FRAME_COUNT')
    if abs(observation.fps-policy.fps)>Fraction(1,100000):codes.append('VIDEO_FPS')
    if abs(observation.pts[0]*tb)>tolerance:codes.append('VIDEO_START_TIME')
    for i,(a,b) in enumerate(zip(observation.pts,observation.pts[1:])):
        if b<=a:codes.append('VIDEO_NONMONOTONIC_PTS')
        elif abs((b-a)*tb-step)>tolerance:codes.append('VIDEO_FRAME_CADENCE')
        if abs(observation.durations[i]*tb-(b-a)*tb)>tolerance:codes.append('VIDEO_FRAME_DURATION_GAP')
    if any(abs(d*tb-step)>tolerance for d in observation.durations):codes.append('VIDEO_PACKET_DURATION')
    end=(observation.pts[-1]+observation.durations[-1])*tb
    expected=Fraction(policy.expected_frames,1)/policy.fps
    if abs(end-expected)>max(tolerance,Fraction(policy.duration_tolerance_us,1000000)):codes.append('VIDEO_RENDER_DURATION')
    return tuple(sorted(set(codes)))
