"""H7 frame-complete bounded text-paint checks; no fake universal visual/learning score."""
from __future__ import annotations
import math
from .qa_common import CompilerQAError, digest


def inspect_paint_quality(records, *, element_ids, frame_count, min_contrast=4.5):
    if type(frame_count) is not int or not 1<=frame_count<=2400:raise CompilerQAError('PAINT_FRAME_BUDGET')
    if type(min_contrast) not in (float,int) or not math.isfinite(min_contrast) or not 1<=min_contrast<=21:raise CompilerQAError('PAINT_CONTRAST_POLICY')
    if not isinstance(element_ids,(list,tuple)) or not element_ids or any(not isinstance(e,str) or not e for e in element_ids) or len(set(element_ids))!=len(element_ids):raise CompilerQAError('PAINT_ELEMENT_IDENTITY')
    ids=set(element_ids); expected={(e,f) for e in ids for f in range(frame_count)}
    if not isinstance(records,list) or len(records)!=len(expected):raise CompilerQAError('PAINT_COVERAGE_INCOMPLETE')
    seen=set();findings=[];text_count=0
    def note(code,e,f):findings.append({'code':code,'element_id':e,'frame':f})
    for row in records:
        if not isinstance(row,dict):raise CompilerQAError('PAINT_RECORD_INVALID')
        e,f=row.get('element_id'),row.get('frame')
        if not isinstance(e,str):raise CompilerQAError('PAINT_FRAME_IDENTITY')
        key=(e,f)
        if type(f) is not int or key not in expected or key in seen:raise CompilerQAError('PAINT_FRAME_IDENTITY')
        seen.add(key);texts=row.get('text')
        if not isinstance(texts,list) or len(texts)>4096:raise CompilerQAError('PAINT_TEXT_BUDGET')
        ink=row.get('ink',[])
        if not isinstance(ink,list) or len(ink)>20000:raise CompilerQAError('PAINT_INK_BUDGET')
        ink_ids=set()
        for shape in ink:
            if not isinstance(shape,dict) or not isinstance(shape.get('shape_id'),str) or shape['shape_id'] in ink_ids:raise CompilerQAError('PAINT_INK_IDENTITY')
            ink_ids.add(shape['shape_id'])
            if shape.get('error') is not None:note('PAINT_INK_MEASUREMENT_ERROR',e,f)
            else:
                box=shape.get('box')
                if not isinstance(box,list) or len(box)!=4 or any(type(v) not in (float,int) or not math.isfinite(v) or abs(v)>1e7 for v in box) or box[2]<0 or box[3]<0:raise CompilerQAError('PAINT_INK_BOX_INVALID')
            if type(shape.get('clipped'))is not bool or type(shape.get('unsupported_effect'))is not bool:raise CompilerQAError('PAINT_INK_FLAGS')
            if shape['clipped']:note('PAINT_VECTOR_INK_CLIPPED',e,f)
            if shape['unsupported_effect']:note('PAINT_VECTOR_EFFECT_UNVERIFIED',e,f)
        text_ids=set()
        for t in texts:
            if not isinstance(t,dict):raise CompilerQAError('PAINT_TEXT_INVALID')
            text_count+=1
            if text_count>1000000:raise CompilerQAError('PAINT_TOTAL_BUDGET')
            tid=t.get('text_id')
            if not isinstance(tid,str) or tid in text_ids:raise CompilerQAError('PAINT_TEXT_IDENTITY')
            text_ids.add(tid)
            if not isinstance(t.get('text'),str) or len(t['text'])>100000:raise CompilerQAError('PAINT_TEXT_INVALID')
            if t.get('font_ready') is not True:note('PAINT_FONT_NOT_READY',e,f)
            contrast=t.get('contrast')
            if contrast is None:note('PAINT_CONTRAST_UNRESOLVED',e,f)
            elif type(contrast) not in (int,float) or not math.isfinite(contrast) or not 1<=contrast<=21.0001:raise CompilerQAError('PAINT_CONTRAST_INVALID')
            elif contrast<min_contrast:note('PAINT_TEXT_LOW_CONTRAST',e,f)
            boxes=t.get('boxes')
            if not isinstance(boxes,list) or len(boxes)>4096:raise CompilerQAError('PAINT_BOX_BUDGET')
            if t['text'].strip() and not boxes:note('PAINT_TEXT_NO_INK_BOX',e,f)
            for b in boxes:
                if not isinstance(b,dict):raise CompilerQAError('PAINT_BOX_INVALID')
                xy=b.get('box')
                if not isinstance(xy,list) or len(xy)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e7 for v in xy) or xy[2]<=0 or xy[3]<=0:raise CompilerQAError('PAINT_BOX_INVALID')
                n,k=b.get('tested_points'),b.get('occluded_points')
                if type(n) is not int or type(k) is not int or not 0<=k<=n<=3:raise CompilerQAError('PAINT_OCCLUSION_INVALID')
                if k:note('PAINT_TEXT_OCCLUDED',e,f)
                if type(b.get('ancestor_clip')) is not bool:raise CompilerQAError('PAINT_CLIP_INVALID')
                if b['ancestor_clip']:note('PAINT_ANCESTOR_CLIPPING',e,f)
    return {'schema_version':'bie.paint-quality.v1','passed':not findings,'findings':findings,'records_checked':len(seen),
            'text_records':text_count,'min_contrast':min_contrast,'measurement_sha256':digest(records),
            'limits':'Computed solid-color contrast, vector path envelopes and text-range occlusion probes; not universal raster ink segmentation, map meaning or instructional legibility.',
            'accepted':False}
