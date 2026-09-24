"""H2-004: source-preserving owned repair intents and fresh-media rechecks.

This is not a second orchestrator. Kernel dispatch and durable invalidation are
owned by pending F03/F04, and are explicitly never asserted as executed here.
"""
from __future__ import annotations
from .common import AudioError, fingerprint
from .acoustic_contract import BOUNDARIES, plain, fields, validate_job
from .acoustic_assessment import assess_receipt


def immutable_source(job):
    validate_job(job)
    return fingerprint([{'segment_id':s['segment_id'],'spoken_text':s['spoken_text'],
        'languages':s['languages'],'source_spans':s['source_spans']} for s in job['segments']])


def plan_repairs(job,receipt,trust,*,now=None):
    assessment=assess_receipt(receipt,job,trust,now=now);items=[]
    for f in assessment['findings']:
        if f['code']=='ACOUSTIC_CALIBRATION_AND_LISTENING_REQUIRED':continue
        action=(('REMIX_UNCHANGED_READING' if f['owner']=='AUDIO/MIX' else 'RESYNTHESIZE_UNCHANGED_READING') if f['code']=='ACOUSTIC_DELIVERED_SEGMENT_SILENT'
                else 'REVIEW_INDEPENDENT_TIMING' if f['owner']=='AUDIO/SYNC'
                else 'REVIEW_ACOUSTIC_EVIDENCE')
        item={'finding_fingerprint':fingerprint(f),'code':f['code'],'severity':f['severity'],
              'owner':f['owner'],'segment_id':f['path'],'action':action,
              'source_refs':f['source_refs'],'automatic_execution_authorized':False}
        item['repair_id']=fingerprint({'job':job['fingerprint'],'item':item});items.append(item)
    invalidations=[{'kind':key,'fingerprint':job['binding'][key]} for key in
        ('source_sync_fingerprint','mix_receipt_fingerprint','clock_fingerprint')]
    invalidations += [{'kind':'speech_request_fingerprint','fingerprint':s['request_fingerprint']} for s in job['segments']]
    out={'schema_version':'bie.audio.acoustic-repair-plan/1',
         'job_fingerprint':job['fingerprint'],'immutable_source_fingerprint':immutable_source(job),
         'previous_media_sha256':job['binding']['media_sha256'],'receipt_fingerprint':fingerprint(receipt),
         'assessment_fingerprint':assessment['fingerprint'],'items':items,
         'requires_invalidation':invalidations,
         'downstream_rebuild_required':['word_clock','captions','pause_clock','scene_animation_clock','mixed_audio','audio_qa','rendered_av'],
         'kernel_dispatch_performed':False,'durable_invalidation_performed':False,
         'source_or_reading_mutated':False,**BOUNDARIES}
    out['fingerprint']=fingerprint(out);return plain(out)


def recheck_repair(plan,old_job,old_receipt,new_job,new_receipt,trust,*,now=None):
    # Old evidence is checked as history, never represented as a fresh evaluation.
    history_time=old_receipt['payload']['issued_at']
    expected=plan_repairs(old_job,old_receipt,trust,now=history_time)
    if plan!=expected:raise AudioError('ACOUSTIC_REPAIR_PLAN_TAMPER')
    validate_job(new_job)
    if immutable_source(new_job)!=plan['immutable_source_fingerprint']:
        raise AudioError('ACOUSTIC_REPAIR_SOURCE_OR_READING_CHANGED')
    if new_job['binding']['media_sha256']==plan['previous_media_sha256']:
        raise AudioError('ACOUSTIC_REPAIR_REQUIRES_NEW_MEDIA')
    if new_job['policy']!=old_job['policy']:raise AudioError('ACOUSTIC_REPAIR_POLICY_CHANGED')
    if new_receipt['payload']['issued_at']<old_receipt['payload']['issued_at']:
        raise AudioError('ACOUSTIC_REPAIR_EVIDENCE_PRECEDES_FAILURE')
    current=assess_receipt(new_receipt,new_job,trust,now=now)
    remaining={(f['code'],f['path']) for f in current['findings']}
    measured={s['segment_id'] for s in new_receipt['payload']['measurement']['segments'] if s['status']=='MEASURED'}
    resolved=[item['repair_id'] for item in plan['items'] if item['segment_id'] in measured and (item['code'],item['segment_id']) not in remaining]
    out={'schema_version':'bie.audio.acoustic-repair-recheck/1','repair_plan_fingerprint':plan['fingerprint'],
         'new_job_fingerprint':new_job['fingerprint'],'new_receipt_fingerprint':fingerprint(new_receipt),
         'new_assessment_fingerprint':current['fingerprint'],'resolved_diagnostic_items':resolved,
         'remaining_diagnostic_items':[i['repair_id'] for i in plan['items'] if i['repair_id'] not in resolved],
         'status':'RECHECKED_DIAGNOSTIC_NOT_ACCEPTED','source_and_reading_preserved':True,
         'kernel_dispatch_performed':False,'durable_invalidation_performed':False,
         'product_repair_accepted':False,**BOUNDARIES}
    out['fingerprint']=fingerprint(out);return out
