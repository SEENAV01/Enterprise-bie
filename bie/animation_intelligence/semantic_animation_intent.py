from .contracts import *
def build_semantic_animation_intent(ctx, *, target_ids, semantic_change, preferred_actions=()):
    targets=ids(target_ids,"target_ids")
    change=tok(semantic_change,"semantic_change")
    actions=tuple(tok(a,"preferred_action") for a in preferred_actions)
    if any(a not in ACTIONS for a in actions):
        raise AnimationSemanticError("unsupported preferred action")
    if ctx.uncertainty>=.8:
        return make_decision(ctx,":semantic",None,"ABSTAIN",1-ctx.uncertainty,
                             rationale=("high_uncertainty_abstention",),
                             payload={"targets":targets,"semantic_change":change})
    return make_decision(ctx,":semantic",actions[0] if actions else None,
                         "REVIEW" if ctx.uncertainty>=.45 else "PASS",
                         1-ctx.uncertainty*.6,
                         rationale=("animation_exists_only_for_declared_semantic_change",),
                         payload={"targets":targets,"semantic_change":change,"preferred_actions":actions})
