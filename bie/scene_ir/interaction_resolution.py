from dataclasses import dataclass
@dataclass(frozen=True)
class InteractionResolutionReceipt:
    scene_id:str;binding_ids:tuple[str,...];state_paths:tuple[str,...];control_ids:tuple[str,...];cue_ids:tuple[str,...];blockers:tuple[str,...];warnings:tuple[str,...];passed:bool;accepted:bool=False
def resolve_interactions(document):
    elem_type={e.element_id:e.element_type for e in document.elements};meta=dict(document.metadata);handlers=set(meta.get("handler_refs",()));states=set(meta.get("state_paths",()))
    bindings=[dict(x) for x in document.interaction_bindings];state_bindings=[dict(x) for x in document.state_bindings];controls=[dict(x) for x in document.simulation_controls];cues=[dict(x) for x in document.interaction_cues]
    blockers=[];warnings=[]
    def unique(items,key,label):
        vals=[x.get(key) for x in items]
        if any(not v for v in vals):blockers.append("missing_"+label+"_id")
        if len(vals)!=len(set(vals)):blockers.append("duplicate_"+label+"_id")
    unique(bindings,"binding_id","binding");unique(state_bindings,"binding_id","state_binding");unique(controls,"control_id","control");unique(cues,"cue_id","interaction_cue")
    interaction_ids=set()
    for b in bindings:
        bid=str(b.get("binding_id","?"));iid=b.get("interaction_id")
        if not iid:blockers.append("binding_missing_interaction_id:"+bid)
        else:interaction_ids.add(iid)
        for target in b.get("target_ids",()):
            if target not in elem_type:blockers.append("binding_unknown_target:"+bid+":"+str(target))
        h=b.get("handler_ref")
        if not h:blockers.append("binding_missing_handler:"+bid)
        elif handlers and h not in handlers:blockers.append("binding_unknown_handler:"+bid)
        if b.get("state_path") and b["state_path"] not in states:blockers.append("binding_unknown_state_path:"+bid)
    for b in state_bindings:
        bid=str(b.get("binding_id","?"))
        if b.get("target_id") not in elem_type:blockers.append("state_binding_unknown_target:"+bid)
        if b.get("state_path") not in states:blockers.append("state_binding_unknown_state_path:"+bid)
    for c in controls:
        cid=str(c.get("control_id","?"));sim=c.get("simulation_element_id")
        if sim not in elem_type:blockers.append("control_unknown_simulation:"+cid)
        elif elem_type[sim]!="simulation":blockers.append("control_target_not_simulation:"+cid)
        if c.get("state_path") not in states:blockers.append("control_unknown_state_path:"+cid)
        if c.get("requires_verified_execution"):
            e=next((x for x in document.elements if x.element_id==sim),None);execution=None if e is None else e.props.get("execution_class")
            if execution!="verified_observed_execution":blockers.append("verified_execution_required:"+cid)
    for c in cues:
        cid=str(c.get("cue_id","?"));iid=c.get("interaction_id")
        if iid and iid not in interaction_ids:blockers.append("cue_unknown_interaction:"+cid)
        for target in c.get("target_ids",()):
            if target not in elem_type:blockers.append("cue_unknown_target:"+cid+":"+str(target))
    return InteractionResolutionReceipt(document.scene_id,tuple(sorted(str(x.get("binding_id","")) for x in bindings)),tuple(sorted(states)),tuple(sorted(str(x.get("control_id","")) for x in controls)),tuple(sorted(str(x.get("cue_id","")) for x in cues)),tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),not blockers,False)
