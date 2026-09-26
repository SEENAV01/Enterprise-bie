from __future__ import annotations
from .provenance_adapter import all_refs
import json
from .contracts import *
from ..state_engine.action_router import compile_action_routes

def compile_interactions(ctx:CompilerContext):
    ctx.validate();rows=[]
    for exp in ctx.document.experiences:
      for level in exp.levels:
        routes={r.action_id:r for r in compile_action_routes(level)};challenge_ids=[c.challenge_id for c in level.challenges];objective_ids=[c.learning.objective_id for c in level.challenges]
        for a in level.interaction.actions:
            route=routes[a.action_id]
            rows.append({'game_id':exp.game_id,'level_id':level.level_id,'action_id':a.action_id,'kind':a.kind.value,'target':a.target_entity_id,'accessible_label':a.accessible_label,'keyboard_equivalent':a.keyboard_equivalent,'mechanic_id':route.mechanic_id,'rule_id':route.rule_id,'state_bindings':list(route.state_bindings),'route_fingerprint':route.route_fingerprint,'challenge_ids':challenge_ids,'objective_ids':objective_ids})
    for e in ctx.mechanic_events:
        rows.append({'semantic_event_id':e.event_id,'mechanic_id':e.mechanic_id,'receipt_id':e.receipt_id,'motion_ids':list(e.motion_ids),'state_before':e.state_before,'state_after':e.state_after,'pedagogical_purpose':e.pedagogical_purpose,'causal':e.causal})
    data={'schema_version':'bie.game.interaction-program/2','actions_and_events':rows,'keyboard_parity_required':True,'decorative_only_forbidden':True,'authoritative_state_router':True,'product_accepted':False}
    ts='export const interactionProgram = '+json.dumps(data,sort_keys=True,separators=(',',':'))+' as const;\n'
    return artifact(ArtifactKind.INTERACTION_PROGRAM,'runtime/interactions.ts','text/typescript',ts,all_refs(ctx.document.provenance))
