"""METRIC-015: explicit sRGB contrast, caption alignment and focus-graph checks.
Uses WCAG contrast math, but does not certify WCAG conformance or live browsers.
"""
import math
from ..models import BenchmarkError,ident,text
from ..domains.structured import record,sequence
from .common import ids,indexed,weight
from .delivery_common import integer,boolean,interval,unknown,result_unit,covered

def color(value):return [integer(v,0,255)/255 for v in sequence(value,lower=3,upper=3)]
def luminance(rgb):
    channels=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in color(rgb)]
    return sum(a*b for a,b in zip(channels,(0.2126,0.7152,0.0722)))
def contrast(fg,bg):
    a,b=sorted((luminance(fg),luminance(bg)))
    return (b+0.05)/(a+0.05)
def normalized(t):return ' '.join(text(t).split())

def measure(reference,candidate,artifacts):
    record(reference,{'duration_ms','speech','controls','text_labels','alt_ids','caption_tolerance_ms'})
    record(candidate,{'captions','controls','text_styles','alts'})
    duration=integer(reference['duration_ms'],1,3600000);tol=integer(reference['caption_tolerance_ms'],0,1000)
    speech=indexed(reference['speech'],{'id','start','end','transcript','weight'})
    rc=indexed(reference['controls'],{'id','key','role','weight'})
    rt=indexed(reference['text_labels'],{'id','large_text','weight'});alt=ids(reference['alt_ids'])
    if not any((speech,rc,rt,alt)):raise BenchmarkError('EMPTY_ACCESSIBILITY_REFERENCE')
    for r in speech.values():interval(r,duration);text(r['transcript']);weight(r)
    for r in rc.values():text(r['key']);ident(r['role']);weight(r)
    for r in rt.values():boolean(r['large_text']);weight(r)
    caps=indexed(candidate['captions'],{'id','speech_id','start','end','text'})
    controls=indexed(candidate['controls'],{'id','key','role','accessible_name','next_id'})
    styles=indexed(candidate['text_styles'],{'id','foreground','background'})
    alts=indexed(candidate['alts'],{'id','text'});unknown(controls,rc);unknown(styles,rt);unknown(alts,alt)
    mapped={k:[] for k in speech}
    for c in caps.values():
        if ident(c['speech_id']) not in speech:raise BenchmarkError('UNKNOWN_CAPTION_SPEECH')
        interval(c,duration);text(c['text']);mapped[c['speech_id']].append(c)
    for c in controls.values():
        text(c['key']);ident(c['role']);text(c['accessible_name']);ident(c['next_id'])
        if c['next_id']!='EXIT' and c['next_id'] not in controls:raise BenchmarkError('BROKEN_FOCUS_REFERENCE')
    for s in styles.values():color(s['foreground']);color(s['background'])
    for a in alts.values():text(a['text'])
    units=[];ratios={}
    for k,r in sorted(speech.items()):
        why=[];rows=sorted(mapped[k],key=lambda c:(c['start'],c['id']))
        if not rows:why.append('CAPTION_MISSING')
        else:
            spans=[(c['start'],c['end']) for c in rows]
            if not covered(r['start'],r['end'],spans,tol) or abs(rows[0]['start']-r['start'])>tol or abs(rows[-1]['end']-r['end'])>tol:
                why.append('CAPTION_TIMING_MISMATCH')
            if any(a['end']>b['start'] for a,b in zip(rows,rows[1:])):why.append('OVERLAPPING_CAPTION_CUES')
            if normalized(' '.join(c['text'] for c in rows))!=normalized(r['transcript']):why.append('CAPTION_TRANSCRIPT_MISMATCH')
        units.append(result_unit('caption:'+k,why,weight(r)))
    for k,r in sorted(rc.items()):
        why=[]
        if k not in controls:why.append('KEYBOARD_CONTROL_MISSING')
        else:
            c=controls[k]
            if (c['key'],c['role'])!=(r['key'],r['role']):why.append('KEYBOARD_SEMANTICS_MISMATCH')
            visit=set();cur=k
            while cur!='EXIT' and cur not in visit:
                visit.add(cur);cur=controls[cur]['next_id']
            if cur!='EXIT':why.append('KEYBOARD_FOCUS_TRAP')
        units.append(result_unit('control:'+k,why,weight(r)))
    for k,r in sorted(rt.items()):
        why=[]
        if k not in styles:why.append('TEXT_STYLE_MISSING')
        else:
            ratio=contrast(styles[k]['foreground'],styles[k]['background']);ratios[k]=ratio
            if ratio < (3 if r['large_text'] else 4.5):why.append('TEXT_CONTRAST_BELOW_FLOOR')
        units.append(result_unit('contrast:'+k,why,weight(r)))
    for k in alt:units.append(result_unit('alt:'+k,[] if k in alts else ['ALT_TEXT_MISSING']))
    return units,[],{'assessment_scope':'STATIC_METADATA_ACCESSIBILITY_SUBSET','contrast_ratios_unrounded':ratios,
                     'wcag_conformance_certified':False,'browser_keyboard_trace_verified':False,'caption_audio_alignment_verified':False}
