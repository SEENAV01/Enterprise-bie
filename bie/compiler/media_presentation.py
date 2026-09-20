"""H11 source-faithful static crop and finite video schedules.

Crop units and time quantization are explicit. No heuristic focus crop, silent
retiming, playback loop, sound suppression, or inference of captions is applied.
"""
from fractions import Fraction
import math
from .visual_assets import fail, plan_visual_assets, integer
from .qa_common import digest

IMAGE_KEYS={'asset_ref','rights_ref','resolved_asset_path','crop','crop_space','fit'}
VIDEO_KEYS={'asset_ref','rights_ref','resolved_asset_path','trim_start_ms','trim_end_ms','captions_ref',
            'timeline_start_ms','audio_policy','audio_reason_ref','fit'}

def image_geometry(element, asset, target):
    p=element['props'];unknown=set(p)-IMAGE_KEYS
    if unknown:fail('MEDIA_IMAGE_PROPERTY_UNCONSUMED',','.join(sorted(unknown)))
    if p.get('fit','contain')!='contain':fail('MEDIA_FIT_UNSUPPORTED','contain preserves the source aspect ratio')
    w=asset['media']['width'];h=asset['media']['height'];crop=p.get('crop')
    if crop is None:
        if 'crop_space' in p:fail('MEDIA_CROP_WITHOUT_RECT')
        x=y=0.;cw=float(w);ch=float(h)
    else:
        if not isinstance(crop,(list,tuple)) or len(crop)!=4 or any(type(v)not in (int,float) or not math.isfinite(v) for v in crop):fail('MEDIA_CROP_INVALID')
        space=p.get('crop_space')
        if space not in {'normalized-xywh','source-pixels-xywh'}:fail('MEDIA_CROP_SPACE_REQUIRED')
        x,y,cw,ch=map(float,crop)
        if space=='normalized-xywh':x*=w;cw*=w;y*=h;ch*=h
        if x<0 or y<0 or cw<=0 or ch<=0 or x+cw>w or y+ch>h:fail('MEDIA_CROP_OUT_OF_BOUNDS')
    box=element.get('normalized_box')
    if not box:fail('MEDIA_VIEWPORT_REQUIRED')
    bw=box['width']*target.width;bh=box['height']*target.height
    if bw<=0 or bh<=0:fail('MEDIA_VIEWPORT_REQUIRED')
    scale=min(bw/cw,bh/ch)
    return {'element_id':element['element_id'],'source_size':[w,h],'source_crop':[x,y,cw,ch],
            'viewport':[bw,bh],'crop_viewport':[cw*scale,ch*scale],
            'image_size':[w*scale,h*scale],'image_offset':[-x*scale,-y*scale],
            'viewport_offset':[(bw-cw*scale)/2,(bh-ch*scale)/2],'scale':scale,
            'intent':'EXPLICIT_CROP_CONTAIN_NO_SOURCE_BYTE_CHANGE','accepted':False}

def _exact_frame(ms, fps, code):
    integer(ms,0,24*3600*1000,code)
    n=ms*fps
    if n%1000:fail('MEDIA_TIME_NOT_FRAME_ALIGNED',code+' requires an exact composition-frame boundary')
    return n//1000

def video_schedule(element, asset, target, duration_ms):
    p=element['props'];unknown=set(p)-VIDEO_KEYS
    if unknown:fail('MEDIA_VIDEO_PROPERTY_UNCONSUMED',','.join(sorted(unknown)))
    if p.get('fit','contain')!='contain':fail('MEDIA_FIT_UNSUPPORTED')
    if p.get('captions_ref') is not None:
        fail('MEDIA_CAPTIONS_BINDING_REQUIRED','resolve into the existing source-bound H6 caption timeline; no external reference is silently treated as rendered captions')
    m=asset['media'];duration=Fraction(m['frame_count']*m['fps_den'],m['fps_num'])
    start=_exact_frame(p.get('timeline_start_ms',0),target.fps,'timeline_start_ms')
    before=_exact_frame(p.get('trim_start_ms',0),target.fps,'trim_start_ms')
    after_ms=p.get('trim_end_ms')
    if after_ms is None:
        last=duration*target.fps
        if last.denominator!=1:fail('MEDIA_END_NOT_FRAME_ALIGNED','declare a trim_end_ms')
        after=last.numerator
    else:after=_exact_frame(after_ms,target.fps,'trim_end_ms')
    if before>=after or Fraction(after,target.fps)>duration:fail('MEDIA_TRIM_RANGE')
    end=start+after-before;n=(duration_ms*target.fps+999)//1000
    if start<0 or end>n:fail('MEDIA_CLIP_EXCEEDS_SCENE')
    policy=p.get('audio_policy')
    if policy not in {'preserve','muted'}:fail('MEDIA_AUDIO_POLICY_REQUIRED')
    if policy=='muted':
        if p.get('audio_reason_ref') not in element['reasoning_refs']:fail('MEDIA_MUTE_REASON_UNBOUND')
    elif 'audio_reason_ref' in p:fail('MEDIA_UNUSED_AUDIO_REASON')
    return {'element_id':element['element_id'],'asset_id':asset['asset_id'],'public_path':asset['public_path'],
            'composition_fps':target.fps,'display_start_frame':start,'display_end_frame_exclusive':end,
            'trim_before_composition_frames':before,'trim_after_composition_frames':after,
            'source_fps_num':m['fps_num'],'source_fps_den':m['fps_den'],'source_frame_count':m['frame_count'],
            'audio_policy':policy,'audio_streams':m['audio_streams'],'fit':'contain',
            'clock_policy':'EXACT_COMPOSITION_FRAMES_SOURCE_SAMPLE_FLOOR_NO_LOOP','accepted':False}

def source_video_frame(schedule, frame):
    integer(frame,0,10000000,'MEDIA_FRAME_INVALID')
    a,b=schedule['display_start_frame'],schedule['display_end_frame_exclusive']
    if not a<=frame<b:return None
    # Independent observable CFR timeline reference; Remotion runtime remains a
    # required separate validation gate, not certified by this arithmetic alone.
    return ((frame-a+schedule['trim_before_composition_frames'])*schedule['source_fps_num'])//(schedule['composition_fps']*schedule['source_fps_den'])

def media_presentations(raw,target,*,required=True):
    plan=plan_visual_assets(raw,required=required)
    if plan is None:return None
    byid={a['asset_id']:a for a in plan['assets']};elements={e['element_id']:e for e in raw['elements']}
    rows=[]
    for b in plan['bindings']:
        e=elements[b['element_id']];a=byid[b['asset_id']]
        c=image_geometry(e,a,target) if e['element_type']=='image' else video_schedule(e,a,target,raw['duration_ms'])
        if e['element_type']=='video' and c['audio_streams'] and c['audio_policy']=='preserve' and raw.get('narration_cues'):
            fail('MEDIA_AUDIO_MIX_POLICY_REQUIRED','embedded audio plus narration needs an explicitly verified mix, not implicit summation')
        rows.append({'element_id':e['element_id'],'kind':e['element_type'],'asset':a,'presentation':c})
    out={'schema_version':'bie.media-presentations.v1','asset_plan_sha256':plan['plan_sha256'],'rows':rows,'accepted':False}
    out['identity_sha256']=digest(out);return out

def media_visibility(raw,target,frame):
    p=media_presentations(raw,target,required=False)
    if p is None:return {}
    return {r['element_id']:source_video_frame(r['presentation'],frame) is not None for r in p['rows'] if r['kind']=='video'}
