from .attention_contracts import *

def build_attention_model(targets, *, decision_id="ani-attn-model", max_secondary=2, salience_penalty=.25):
    targets=tuple(targets)
    if not targets:
        raise AttentionError("attention model requires targets")
    if len({t.target_id for t in targets})!=len(targets):
        raise AttentionError("duplicate target ids")
    if isinstance(max_secondary,bool) or not isinstance(max_secondary,int) or max_secondary<0:
        raise AttentionError("max_secondary invalid")
    salience_penalty=unit(salience_penalty,"salience_penalty")
    active=[t for t in targets if t.active]
    if not active:
        return make_decision(decision_id,status="UNSUPPORTED",primary_target=None,
                             blockers=("no_active_targets",),
                             evidence_refs=tuple(sorted({e for t in targets for e in t.evidence_refs})),
                             reasoning_refs=tuple(sorted({r for t in targets for r in t.reasoning_refs})))
    scored=[]
    for t in active:
        score=t.importance + .20*t.visual_salience + .15*t.motion_salience
        if t.motion_salience>.8 and t.importance<.5:
            score-=salience_penalty
        scored.append((score,t.target_id,t))
    scored.sort(key=lambda x:(-x[0],x[1]))
    primary=scored[0][2]
    secondary=tuple(x[2].target_id for x in scored[1:1+max_secondary] if x[0]>=.55)
    warnings=[]
    if primary.motion_salience>.8 and primary.importance<.6:
        warnings.append("motion_salience_may_dominate_semantic_importance")
    ev=tuple(sorted({e for t in targets for e in t.evidence_refs}))
    rr=tuple(sorted({r for t in targets for r in t.reasoning_refs}))
    return make_decision(decision_id,status="REVIEW" if warnings else "PASS",
                         primary_target=primary.target_id,secondary_targets=secondary,
                         warnings=warnings,evidence_refs=ev,reasoning_refs=rr)
