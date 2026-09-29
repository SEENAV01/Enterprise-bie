"""Restore supported generated modules, never policies/observations/test oracles."""
from ..release_v2.contracts import ContractError
from ..source_v2.io import SnapshotStore
from ..domain_repair_v2.common import exact_inputs
from .emitter import emit_constants,emit_reducer,code_header,game_header,validate_oracle

def read_original(r,root,header):
    exact_inputs(r,root)
    with SnapshotStore(root) as store:b=store.read(r.module)
    if not b.startswith(header.encode('utf-8')):raise ContractError('MEDIA_REPAIR_UNOWNED_GENERATOR_GRAMMAR')
    return b

def code(r,root,p,limits,as_of):
    if r.module_id!=p.module_id:raise ContractError('MEDIA_REPAIR_MODULE_IDENTITY')
    read_original(r,root,code_header(p.module_id))
    claims={c.claim_id for c in r.source.claims}
    if not set(p.source_claim_ids)<=claims:raise ContractError('MEDIA_REPAIR_CODE_SOURCE_SCOPE')
    return emit_constants(p),dict(emitter='closed-constants-v1',source_claim_ids=p.source_claim_ids,
        compile_required=True,arbitrary_code_repair=False,semantic_correctness_verified=False)

def game(r,root,p,limits,as_of):
    if r.game_id!=p.qa.game_id:raise ContractError('MEDIA_REPAIR_GAME_IDENTITY')
    read_original(r,root,game_header(r.game_id));validate_oracle(p.qa)
    claims={c.claim_id:c for c in r.source.claims};states={s.state_id:s for s in p.qa.states}
    # Ground every policy-declared learning presentation. Prompt/feedback credit
    # cannot come from IDs that refer to other output text.
    bindings=[(b.claim_id,b.key,b.state_ids) for b in p.qa.text_bindings]
    for target in p.qa.learning:
        if target.prompt_claim_id not in claims:raise ContractError('MEDIA_REPAIR_GAME_SOURCE_SCOPE')
        if not any(any(v.key==target.prompt_key and v.text==claims[target.prompt_claim_id].text for v in s.values) for s in p.qa.states):raise ContractError('MEDIA_REPAIR_GAME_PROMPT_NOT_PRESENT')
        responding=[t for t in p.qa.transitions if t.action_id in target.response_action_ids]
        if {t.action_id for t in responding}!=set(target.response_action_ids):raise ContractError('MEDIA_REPAIR_GAME_RESPONSE_NOT_COVERED')
        for t in responding:
            if dict((v.key,v.text) for v in states[t.before].values).get(target.prompt_key)!=claims[target.prompt_claim_id].text:raise ContractError('MEDIA_REPAIR_GAME_PROMPT_NOT_AT_RESPONSE')
        bindings.extend(((target.correct_claim_id,target.feedback_key,(target.success_state,)),(target.incorrect_claim_id,target.feedback_key,(target.failure_state,))))
    for claim,key,state_ids in bindings:
        if claim not in claims:raise ContractError('MEDIA_REPAIR_GAME_SOURCE_SCOPE')
        for sid in state_ids:
            if dict((v.key,v.text) for v in states[sid].values).get(key)!=claims[claim].text:raise ContractError('MEDIA_REPAIR_GAME_FEEDBACK_SOURCE_MISMATCH')
    return emit_reducer(p.qa),dict(emitter='closed-finite-reducer-v1',oracle_digest=p.qa.oracle_digest,
        state_count=len(p.qa.states),transition_count=len(p.qa.transitions),scenario_count=len(p.qa.scenarios),
        native_ui_verified=False,browser_interaction_verified=False,learner_mastery_observed=False,compile_and_replay_required=True)
