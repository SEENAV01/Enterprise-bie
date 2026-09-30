"""METRIC-009: scene-semantic labels, directed relations and geometric visibility.
The input is scene metadata, NOT proof of what a renderer actually drew.
"""
from ..models import BenchmarkError,ident,text
from ..domains.structured import record,sequence,amount
from .common import indexed,weight
from .delivery_common import integer,unknown,result_unit

def box(value):
    record(value,{'x','y','width','height'})
    return (amount(value['x'],signed=True),amount(value['y'],signed=True),
            amount(value['width'],positive=True),amount(value['height'],positive=True))
def measure(reference,candidate,artifacts):
    record(reference,{'viewport','objects','relations','nonoverlap_pairs'})
    record(candidate,{'objects','relations'})
    record(reference['viewport'],{'width','height'})
    width=integer(reference['viewport']['width'],1,16384);height=integer(reference['viewport']['height'],1,16384)
    expected=indexed(reference['objects'],{'id','concept_id','label','kind','weight'},lower=1)
    er=indexed(reference['relations'],{'id','from','to','kind','weight'})
    for r in expected.values(): ident(r['concept_id']);text(r['label']);ident(r['kind']);weight(r)
    for r in er.values():
        weight(r);ident(r['kind'])
        if ident(r['from']) not in expected or ident(r['to']) not in expected: raise BenchmarkError('REFERENCE_RELATION_ENDPOINT_MISSING')
    actual=indexed(candidate['objects'],{'id','concept_id','label','kind','box','alt_text'});unknown(actual,expected)
    relations=indexed(candidate['relations'],{'id','from','to','kind'});unknown(relations,er)
    boxes={}
    for k,r in actual.items():
        ident(r['concept_id']);text(r['label']);ident(r['kind']);text(r['alt_text']);boxes[k]=box(r['box'])
    for r in relations.values(): ident(r['from']);ident(r['to']);ident(r['kind'])
    reasons={k:[] for k in expected}
    for k,r in expected.items():
        if k not in actual: reasons[k].append('REQUIRED_OBJECT_MISSING');continue
        a=actual[k]
        if any(a[f]!=r[f] for f in ('concept_id','label','kind')): reasons[k].append('SEMANTIC_REPRESENTATION_MISMATCH')
        x,y,w,h=boxes[k]
        if x<0 or y<0 or x+w>width or y+h>height: reasons[k].append('OBJECT_OUTSIDE_VIEWPORT')
    pairs=set()
    for p in sequence(reference['nonoverlap_pairs'],lower=0,upper=128):
        record(p,{'first','second'});a=ident(p['first']);b=ident(p['second'])
        if a not in expected or b not in expected or a==b: raise BenchmarkError('INVALID_NONOVERLAP_PAIR')
        pair=tuple(sorted((a,b)))
        if pair in pairs: raise BenchmarkError('DUPLICATE_NONOVERLAP_PAIR')
        pairs.add(pair)
        if a in boxes and b in boxes:
            x,y,w,h=boxes[a];xx,yy,ww,hh=boxes[b]
            if max(x,xx)<min(x+w,xx+ww) and max(y,yy)<min(y+h,yy+hh):
                reasons[a].append('REQUIRED_ELEMENTS_OCCLUDED');reasons[b].append('REQUIRED_ELEMENTS_OCCLUDED')
    units=[result_unit(k,reasons[k],weight(r)) for k,r in sorted(expected.items())]
    for k,r in sorted(er.items()):
        why=[]
        if k not in relations: why.append('REQUIRED_RELATION_MISSING')
        elif any(relations[k][f]!=r[f] for f in ('from','to','kind')): why.append('RELATION_DIRECTION_OR_KIND_MISMATCH')
        elif r['from'] not in actual or r['to'] not in actual: why.append('RELATION_ENDPOINT_NOT_RENDERABLE')
        units.append(result_unit('relation:'+k,why,weight(r)))
    return units,[],{'assessment_scope':'TYPED_SCENE_SEMANTICS_AND_BOXES','rendered_pixels_verified':False}
