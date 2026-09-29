"""Bounded translation-only repair of DECLARED geometry, never captured evidence."""
from dataclasses import replace,asdict
from ..release_v2.contracts import ContractError,canonical_bytes
from ..visual_v2.models import Rect
from ..visual_v2.geometry import contains,intersection,gap_squared
from ..visual_v2.evaluator import evaluate
from ..domain_repair_v2.common import exact_inputs

def repair(r,root,p,limits,as_of):
    exact_inputs(r,root)
    if r.captures or any(s.geometry_mode!='static' or s.capture_id!='none' for s in r.states):raise ContractError('MEDIA_REPAIR_OBSERVATIONS_IMMUTABLE')
    if r.elements!=p.qa.elements or r.relations!=p.qa.relations:raise ContractError('MEDIA_REPAIR_SEMANTIC_INVENTORY')
    states={s.state_id:s for s in r.states};specs={s.state_id:s for s in p.qa.states};views={v.view_id:v for v in p.qa.views}
    if set(states)!=set(specs):raise ContractError('MEDIA_REPAIR_VIS_STATE_SCOPE')
    permissions={(a.state_id,a.object_id):a for a in p.permissions};visits=0;changed=[];out=[]
    for state in r.states:
        spec=specs[state.state_id]
        if (state.scene_id,state.view_id,state.start_ms,state.end_ms)!=(spec.scene_id,spec.view_id,spec.start_ms,spec.end_ms):raise ContractError('MEDIA_REPAIR_VIS_STATE_CONTEXT')
        ms={m.object_id:m for m in state.measurements}
        if set(ms)!=set(spec.object_ids):raise ContractError('MEDIA_REPAIR_VIS_OBJECT_SCOPE')
        if any(not m.displayed or m.unsupported for m in ms.values()):raise ContractError('MEDIA_REPAIR_VIS_UNSUPPORTED')
        view=views[state.view_id];editable=[m.object_id for m in state.measurements if (state.state_id,m.object_id) in permissions]
        if len(editable)>32:raise ContractError('MEDIA_REPAIR_LAYOUT_OBJECT_LIMIT')
        chosen={m.object_id:m for m in state.measurements if m.object_id not in editable}
        rels=[x for x in p.qa.relations if x.relation_id in spec.relation_ids]
        def good_relations():
            for rel in rels:
                if rel.from_id not in chosen or rel.to_id not in chosen:continue
                a=chosen[rel.from_id].box;b=chosen[rel.to_id].box
                if rel.kind=='above' and a.bottom>b.y:return False
                if rel.kind=='left_of' and a.right>b.x:return False
                if rel.kind=='contains' and not contains(a,b,0):return False
                if rel.kind=='label_for' and gap_squared(a,b)>p.qa.limits.label_distance_mpx**2:return False
            return True
        def solve(index):
            nonlocal visits
            if index==len(editable):return good_relations()
            oid=editable[index];m=ms[oid];permit=permissions[state.state_id,oid];b=m.box
            # Only geometry is translated. Glyph extents, font, text, durations,
            # opacity, flags and the clipping rectangle are all preserved.
            region=intersection(permit.region,view.safe)
            if region:region=intersection(region,m.clip)
            if region is None or b.width>region.width or b.height>region.height:return False
            obstacles=[x.box for x in chosen.values()]+list(view.subtitle_regions)
            xs={b.x,region.x,region.right-b.width};ys={b.y,region.y,region.bottom-b.height}
            for box in obstacles:
                xs.update((box.right+p.gap_mpx,box.x-b.width-p.gap_mpx));ys.update((box.bottom+p.gap_mpx,box.y-b.height-p.gap_mpx))
            positions=sorted(((x,y) for x in xs for y in ys),key=lambda q:(abs(q[0]-b.x)+abs(q[1]-b.y),q[1],q[0]))
            # A deterministic search frontier limit is an explicit escalation,
            # not a claim to have exhaustively solved arbitrary layout.
            tried=0
            for x,y in positions:
                tried+=1;visits+=1
                if visits>limits.max_layout_visits or tried>limits.max_positions_per_object:raise ContractError('MEDIA_REPAIR_LAYOUT_BUDGET')
                if abs(x-b.x)+abs(y-b.y)>permit.max_shift_mpx:continue
                nb=Rect(x,y,b.width,b.height)
                if not contains(region,nb,0) or any(intersection(nb,o) for o in obstacles):continue
                dx,dy=x-b.x,y-b.y
                nm=replace(m,box=nb,line_boxes=tuple(replace(t,x=t.x+dx,y=t.y+dy) for t in m.line_boxes))
                chosen[oid]=nm
                if good_relations() and solve(index+1):return True
                chosen.pop(oid)
            return False
        if not solve(0):raise ContractError('MEDIA_REPAIR_LAYOUT_UNSAT_OR_UNSUPPORTED')
        new=replace(state,measurements=tuple(chosen[m.object_id] for m in state.measurements))
        for a,b in zip(state.measurements,new.measurements):
            if a!=b:changed.append(dict(state_id=state.state_id,object_id=a.object_id,dx=b.box.x-a.box.x,dy=b.box.y-a.box.y))
        out.append(new)
    after=replace(r,states=tuple(out));result=evaluate(after,root,p.qa,as_of=as_of)
    for area in ('layout','clutter','readability','alignment'):
        if getattr(result,area).status=='BLOCKED':raise ContractError('MEDIA_REPAIR_VIS_POSTCHECK_BLOCKED',area)
    return canonical_bytes(asdict(after)),dict(changes=changed,layout_visits=visits,unsigned_postcheck=result.to_dict(),observations_rewritten=False,actual_render_verified=False)
