"""H10-003: repair-owned downstream invalidation planning.

This creates a canonical-semantics-compatible invalidation receipt. It does not
replace the enterprise orchestrator and does not mutate the canonical repository.
"""
from __future__ import annotations
from .common import AudioError, fingerprint

SCHEMA='bie.audio.repair-invalidation/1'
GRAPH={
 'AUDIO_TTS_CACHE':(),
 'AUDIO_SYNC':('AUDIO_TTS_CACHE',),
 'AUDIO_MIX':('AUDIO_SYNC',),
 'CAPTIONS':('AUDIO_SYNC',),
 'ANIMATION_CLOCKS':('AUDIO_SYNC',),
 'AUDIO_QA':('AUDIO_MIX','CAPTIONS','ANIMATION_CLOCKS'),
 'COMP_NARRATION_PLAN':('AUDIO_MIX','CAPTIONS','ANIMATION_CLOCKS'),
 'COMP_GENERATED_SOURCE':('COMP_NARRATION_PLAN',),
 'RENDER':('COMP_GENERATED_SOURCE','AUDIO_QA'),
}
REQUIRED=('AUDIO_TTS_CACHE','AUDIO_SYNC','AUDIO_MIX','CAPTIONS','ANIMATION_CLOCKS','AUDIO_QA','COMP_NARRATION_PLAN','COMP_GENERATED_SOURCE','RENDER')
CANONICAL_MAIN='dfc1ef9b59bf7d3a8f099a8ad2fb4a93895257e8'
CANONICAL_INVALIDATION_BLOB='da5f108ebd50dded37a3a95a5b7fb340f3535fc7'
CANONICAL_DEPENDENCY_BLOB='f6f0b5fbd1d7bcf19b1a01d87c85c5d3f9d1e56b'

def _dependents(graph):
    out={k:[] for k in graph}
    for k,deps in graph.items():
        for d in deps:out[d].append(k)
    for v in out.values():v.sort()
    return out

def invalidation_plan(repair_intent, statuses, *, source_task_id='AUDIO/VO'):
    if type(repair_intent)is not dict or repair_intent.get('action')!='RESYNTHESIZE_UNCHANGED_READING' or repair_intent.get('dispatch_performed') is not False:raise AudioError('REPAIR_DISPATCH_INPUT')
    if not repair_intent.get('expected_spoken') or not repair_intent.get('source_refs'):raise AudioError('REPAIR_DISPATCH_SOURCE')
    declared=set(repair_intent.get('invalidates',[]))
    if not {'AUDIO_TTS_CACHE','AUDIO_SYNC','AUDIO_MIX','CAPTIONS','ANIMATION_CLOCKS','AUDIO_QA','RENDER'}<=declared:raise AudioError('REPAIR_DISPATCH_DECLARATION')
    if type(statuses)is not dict or set(statuses)!=set(GRAPH):raise AudioError('REPAIR_STATUS_COVERAGE')
    if any(v=='INVALIDATED' for v in statuses.values()):raise AudioError('REPAIR_ALREADY_INVALIDATED')
    dep=_dependents(GRAPH);seen=set();stack=['AUDIO_TTS_CACHE']
    while stack:
        n=stack.pop()
        if n in seen:continue
        seen.add(n);stack.extend(dep[n])
    if seen!=set(GRAPH):raise AudioError('REPAIR_GRAPH_INCOMPLETE')
    rows=[]
    for task_id in REQUIRED:
        rows.append({'task_id':task_id,'reason':'UPSTREAM_AUDIO_REPAIR:'+repair_intent['repair_fingerprint'],
                     'source_task_id':source_task_id,'previous_status':statuses[task_id],'new_status':'INVALIDATED'})
    receipt={'schema_version':SCHEMA,'canonical_main':CANONICAL_MAIN,
      'canonical_semantics':{'task_invalidation_blob':CANONICAL_INVALIDATION_BLOB,'dependency_resolver_blob':CANONICAL_DEPENDENCY_BLOB},
      'repair_fingerprint':repair_intent['repair_fingerprint'],'action':'RESYNTHESIZE_UNCHANGED_READING',
      'source_text_mutated':False,'reading_mutated':False,'invalidations':rows,
      'dispatch_performed':True,'repository_mutated':False,'product_accepted':False}
    receipt['fingerprint']=fingerprint(receipt);return receipt

def validate_invalidation_plan(receipt,repair_intent,statuses):
    expected=invalidation_plan(repair_intent,statuses)
    if receipt!=expected:raise AudioError('REPAIR_INVALIDATION_RECEIPT_MISMATCH')
    return receipt
