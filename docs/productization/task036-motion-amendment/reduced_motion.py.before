"""H3-003 explicit source-bound accessibility variants, not silent motion removal."""
from __future__ import annotations
from copy import deepcopy
from .frame_layout import h3_metadata, dimensions, fail
from .animation_behavior import motion_contract
from .qa_common import digest, token

DERIVATION_KEY = '_bie_h3_derivation'


def resolve_reduced_motion(raw, target, preference='standard'):
    if preference not in {'standard','reduced'}:
        fail('MOTION_PREFERENCE_INVALID','standard or reduced is required')
    if DERIVATION_KEY in raw.get('metadata',{}):
        fail('MOTION_DERIVATION_RESERVED','input may not impersonate compiler derivation metadata')
    from .specialized_motion import is_specialized
    from .motion_milestones import prepare_specialized_variants
    prepared, specialized_variants = prepare_specialized_variants(raw,target,preference)
    registry=h3_metadata(raw).get('reduced_motion_variants',{})
    if not isinstance(registry,dict) or len(registry)>256:
        fail('REDUCED_VARIANT_REGISTRY_INVALID','bounded variant registry required')
    for key,val in registry.items():
        token(key,'variant reference')
        if not isinstance(val,dict) or set(val)-{'element_id','track_replacements','freeze_frame','reason','source_refs','reasoning_refs'}:
            fail('REDUCED_VARIANT_UNCONSUMED','unknown variant fields')
    count=dimensions(raw,target)
    effective=deepcopy(prepared)
    # Original fingerprint is retained in lineage; the derived document must
    # receive a fresh fingerprint rather than carrying a stale input identity.
    effective.pop('fingerprint',None)
    original_identity=digest(raw)
    selection=[];frozen={};replacements={};referenced=[]
    for e in raw['elements']:
        eid=e['element_id'];kind=e['element_type']
        from .registered_actions import ACTIONS as REGISTERED_ACTIONS
        safe_registered=REGISTERED_ACTIONS-{'simulation_state'}
        tracks=[t for t in raw.get('tracks',[]) if t['element_id']==eid and not is_specialized(t) and t['action'] not in safe_registered]
        ref=e.get('accessibility',{}).get('reduced_motion_variant')
        if ref:referenced.append(ref)
        registered_snapshots=any(t['element_id']==eid and t['action']=='state_snapshots' for t in raw.get('tracks',[]))
        needs=bool(tracks) or kind in {'simulation','particle_system','video'} and not registered_snapshots
        if preference=='standard' or not needs:continue
        if not isinstance(ref,str) or ref not in registry:
            fail('REDUCED_VARIANT_UNRESOLVED','missing explicit variant for '+eid)
        variant=registry[ref]
        required={'element_id','track_replacements','reason','source_refs','reasoning_refs'}
        if not required<=set(variant) or variant['element_id']!=eid:
            fail('REDUCED_VARIANT_TARGET_MISMATCH','variant must bind exactly its element')
        token(variant['reason'],'variant reason')
        if len(variant['reason'])>2000:fail('REDUCED_VARIANT_INVALID','rationale exceeds budget')
        for field in ('source_refs','reasoning_refs'):
            refs=variant[field]
            if not isinstance(refs,list) or not refs or any(not isinstance(v,str) for v in refs) or len(refs)!=len(set(refs)) or not set(refs)<=set(e.get(field,[])):
                fail('REDUCED_VARIANT_PROVENANCE_UNBOUND',field+' must be nonempty existing element provenance')
        mapping=variant['track_replacements']
        if not isinstance(mapping,dict) or set(mapping)!={t['track_id'] for t in tracks}:
            fail('REDUCED_VARIANT_TRACK_COVERAGE','each original track needs exactly one explicit replacement')
        for t in tracks:
            row=mapping[t['track_id']]
            if not isinstance(row,dict) or set(row)!={'action','parameters'} or row['action'] not in {'enter','exit'}:
                fail('REDUCED_VARIANT_MOTION_UNSUPPORTED','only explicit opacity enter/exit tracks are supported')
            new={**deepcopy(t),'action':row['action'],'parameters':deepcopy(row['parameters'])}
            c=motion_contract(new)
            if c.owned_properties!=('opacity',):fail('REDUCED_VARIANT_MOTION_UNSUPPORTED','variant is not opacity-only')
            replacements[t['track_id']]=new
        if kind=='simulation':
            f=variant.get('freeze_frame')
            if type(f) is not int or not 0<=f<count:
                fail('REDUCED_SIMULATION_FRAME_REQUIRED','simulation variant needs a rendered frame index')
            frozen[eid]=f
        elif 'freeze_frame' in variant:
            fail('REDUCED_VARIANT_UNCONSUMED','freeze_frame only applies to the analytic simulation adapter')
        if kind in {'particle_system','video'}:
            fail('REDUCED_DYNAMIC_FAMILY_UNSUPPORTED','no static adapter for '+kind)
        selection.append({'element_id':eid,'reference':ref,'definition_sha256':digest(variant),
                          'replaced_track_ids':sorted(mapping),'freeze_frame':frozen.get(eid),
                          'reason':variant['reason'],'source_refs':variant['source_refs'],
                          'reasoning_refs':variant['reasoning_refs']})
    effective['tracks']=[replacements.get(t['track_id'],t) for t in effective.get('tracks',[])]
    receipt={'schema_version':'bie.motion-variant.v1','preference':preference,'original_document_identity':original_identity,
             'selected':selection,'frozen_simulation_frames':frozen,
             'standard_unresolved_references':sorted(set(referenced)-set(registry)) if preference=='standard' else [],
             'learning_equivalence':'NOT_EVALUATED','accepted':False}
    if specialized_variants:receipt['specialized_milestones']=specialized_variants
    effective.setdefault('metadata',{})[DERIVATION_KEY]=deepcopy(receipt)
    receipt['effective_document_identity']=digest(effective)
    return effective,receipt
