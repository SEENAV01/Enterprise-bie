"""Exercise the pinned native layout builder; never use its accepted flags."""
from ...visual_intelligence.layout_contracts import Box, LayoutNode, make_layout_plan
from ...visual_intelligence.collision_avoidance import detect_collisions


def to_native(request, state, view):
    elements={e.object_id:e for e in request.elements}
    refs=tuple(sorted({c.claim_id for c in request.source.claims}|{s.source_id for s in request.source.sources}))
    fallback=refs[0]
    nodes=[]
    for m in sorted(state.measurements,key=lambda x:x.object_id):
        e=elements[m.object_id]
        nodes.append(LayoutNode(m.object_id,e.role,Box(m.box.x/(view.width_px*1000),m.box.y/(view.height_px*1000),
                               m.box.width/(view.width_px*1000),m.box.height/(view.height_px*1000)),
                               e.claim_ids or (fallback,),payload={'state_id':state.state_id}))
    plan=make_layout_plan(evidence_refs=refs,reasoning_refs=(request.lesson_id,),nodes=tuple(nodes))
    return plan,detect_collisions(plan,ignore_same_group=False)
