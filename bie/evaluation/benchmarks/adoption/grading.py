"""H3-003/004/005: full-decode technical, exact-frame, hybrid a11y profiles.

Signal and exact RGB checks do not measure cinematic or semantic teaching quality.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError,digest
from ..metrics.common import unit
from ..metrics.accessibility import measure as accessibility_measure
from ..av.service import verify_receipt,_grade
from .contracts import METRICS

def grade(metric_id,reference,candidate,av_receipt):
    r=verify_receipt(av_receipt)
    if r['status']=='BLOCKED':raise BenchmarkError('AV_COLLECTION_BLOCKED')
    obs=r.get('observations')
    if type(obs) is not dict:raise BenchmarkError('AV_OBSERVATIONS_REQUIRED')
    # Recompute every AV policy decision; never treat a stored status as proof.
    reasons=_grade(reference['av_policy'],obs)
    if reasons!=r['reasons'] or (r['status']=='DIAGNOSTIC_PASS')!= (not reasons):
        raise BenchmarkError('AV_DECISION_INCONSISTENT')
    units=[unit('full_av_policy',1,0 if reasons else 1,reasons)]
    details={'scope':'ALL_FRAME_AUDIO_SIGNAL_AND_TIMING',
             'semantic_teaching_quality_verified':False,'perceptual_quality_certified':False,
             'browser_runtime_verified':False}
    if metric_id==METRICS[1]:
        f=reference['frame_reference'];v=obs['video'];tool=obs['tool_binary_identity']['ffmpeg']['sha256']
        if tool!=f['ffmpeg_sha256']:raise BenchmarkError('FRAME_ORACLE_DECODER_CHANGED')
        for key in ('decoded_sha256','frame_chain_sha256'):
            why=[] if v[key]==f[key] else ['REFERENCE_FRAME_CONTENT_MISMATCH']
            units.append(unit(key,1,0 if why else 1,why))
        details['scope']='FULL_RGB_SEQUENCE_EXACT_REFERENCE_PLUS_AV_POLICY'
    if metric_id==METRICS[2]:
        more,defects,sub=accessibility_measure(reference['a11y_reference'],candidate['a11y_candidate'],{})
        if defects:raise BenchmarkError('STATIC_ACCESSIBILITY_UNHANDLED_DEFECT')
        if not more:raise BenchmarkError('STATIC_ACCESSIBILITY_EMPTY')
        # Keep the existing controls, contrast, alt text and authored caption checks.
        for row in more:units.append({**row,'id':'static:'+row['id']})
        observed_caps=obs['captions']
        actual=[] if observed_caps is None else [(round(x['start_s']*1000),round(x['end_s']*1000),' '.join(x['text'].split())) for x in observed_caps['cues']]
        declared=sorted([(x['start'],x['end'],' '.join(x['text'].split())) for x in candidate['a11y_candidate']['captions']])
        mismatch=[] if actual==declared else ['CAPTION_METADATA_MEDIA_MISMATCH']
        units.append(unit('observed_caption_metadata',1,0 if mismatch else 1,mismatch))
        details['scope']='FULL_AV_CAPTION_SIGNAL_PLUS_STATIC_ACCESSIBILITY'
        details['static_accessibility']=sub
        duration=reference['av_policy']['expected_frames']/float(Fraction(reference['av_policy']['fps']))
        if abs(reference['a11y_reference']['duration_ms']/1000-duration)>0.001:
            raise BenchmarkError('ACCESSIBILITY_DURATION_BINDING_MISMATCH')
    return units,details
