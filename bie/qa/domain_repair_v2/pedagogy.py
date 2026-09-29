"""Content-preserving finite-route scheduling and planned response-gate restoration.

Never lower a learning criterion, invent teaching, mark mastery, or remove a route.
A metadata response gate still requires actual game-runtime enforcement evidence.
"""
from dataclasses import replace
from ..release_v2.contracts import ContractError
from ..pedagogy_v2.models import PedagogyRequest,PedagogyPolicy
from .contracts import Limits
from .common import exact_inputs,stable_topology,finish

def repair(request,root,policy,limits=Limits()):
    if type(request) is not PedagogyRequest or type(policy) is not PedagogyPolicy:raise ContractError('DOMAIN_REPAIR_PEDAGOGY_TYPE')
    exact_inputs(request,root)
    if (request.audience_id,request.language)!=(policy.audience_id,policy.language):raise ContractError('DOMAIN_REPAIR_AUDIENCE')
    specs={o.objective_id:o for o in policy.objectives};segments={s.segment_id:s for s in request.segments};events={e.event_id:e for e in request.events}
    if set(segments)!=set(policy.expected_segment_ids) or set(specs)!={o.objective_id for o in request.objectives}:raise ContractError('DOMAIN_REPAIR_PED_SCOPE')
    teaching={oid:set() for oid in specs}
    for t in request.teachings:
        if t.objective_id not in specs or any(e not in events for e in t.event_ids):raise ContractError('DOMAIN_REPAIR_TEACHING_REFERENCE')
        if t.mode in ('explanation','worked_example'):
            teaching[t.objective_id].update(events[e].segment_id for e in t.event_ids)
    if any(not ts for ts in teaching.values()):raise ContractError('DOMAIN_REPAIR_TEACHING_REQUIRED')
    edges={(c.before_segment_id,c.after_segment_id) for c in policy.order_constraints}
    for oid,spec in specs.items():
        for pre in spec.prerequisites:
            for a in teaching[pre]:
                for b in teaching[oid]:
                    if a==b:raise ContractError('DOMAIN_REPAIR_INTRASEGMENT_PREREQUISITE_REVIEW')
                    edges.add((a,b))
    updates=dict(events);changed_gates=[]
    for item in request.items:
        spec=specs.get(item.objective_id)
        if spec is None or any(e not in events for e in (item.prompt_event_id,item.solution_event_id,item.feedback_event_id)):raise ContractError('DOMAIN_REPAIR_ASSESSMENT_REFERENCE')
        prompt,solution,feedback=(events[e] for e in (item.prompt_event_id,item.solution_event_id,item.feedback_event_id))
        if len({prompt.segment_id,solution.segment_id,feedback.segment_id})!=1:raise ContractError('DOMAIN_REPAIR_CROSS_SEGMENT_RESPONSE')
        if (prompt.kind,solution.kind,feedback.kind)!=('prompt','solution','feedback'):raise ContractError('DOMAIN_REPAIR_RESPONSE_ROLE')
        if item.purpose!='diagnostic':
            for a in teaching[item.objective_id]:
                if a==prompt.segment_id:raise ContractError('DOMAIN_REPAIR_INTRASEGMENT_ASSESSMENT_REVIEW')
                edges.add((a,prompt.segment_id))
        for old in (solution,feedback):
            # Shared answer events would couple two questions; require redesign.
            if sum(old.event_id in (i.solution_event_id,i.feedback_event_id) for i in request.items)!=1:raise ContractError('DOMAIN_REPAIR_SHARED_RESPONSE_EVENT')
        start=max(solution.start_ms,prompt.end_ms+spec.minimum_response_ms)
        new_sol=replace(solution,start_ms=start,end_ms=start+(solution.end_ms-solution.start_ms),wait_for_response=True)
        start=max(feedback.start_ms,new_sol.end_ms)
        new_feedback=replace(feedback,start_ms=start,end_ms=start+(feedback.end_ms-feedback.start_ms),wait_for_response=True)
        updates[solution.event_id]=new_sol;updates[feedback.event_id]=new_feedback
        changed_gates.extend(e.event_id for e,old in ((new_sol,solution),(new_feedback,feedback)) if e!=old)
    new_segments=[]
    for s in request.segments:
        end=max([s.duration_ms]+[e.end_ms for e in updates.values() if e.segment_id==s.segment_id])
        new_segments.append(replace(s,duration_ms=end))
    if any(e.segment_id not in segments for e in events.values()):raise ContractError('DOMAIN_REPAIR_EVENT_SEGMENT')
    durations={s.segment_id:s.duration_ms for s in new_segments}
    added=sum(s.duration_ms-segments[s.segment_id].duration_ms for s in new_segments)
    if added>limits.max_added_ms:raise ContractError('DOMAIN_REPAIR_TIME_BUDGET')
    expected={r.route_id:r for r in policy.routes}
    if set(expected)!={r.route_id for r in request.routes}:raise ContractError('DOMAIN_REPAIR_ROUTE_SCOPE')
    routes=[];orders=[]
    for route in request.routes:
        spec=expected[route.route_id]
        if set(route.segment_ids)!=set(spec.segment_ids):raise ContractError('DOMAIN_REPAIR_ROUTE_MEMBERSHIP')
        members=set(route.segment_ids)
        for oid in spec.objective_ids:
            if not teaching[oid]<=members or any(not teaching[p]<=members for p in specs[oid].prerequisites):raise ContractError('DOMAIN_REPAIR_ROUTE_TEACHING_MISSING')
        local={(a,b) for a,b in edges if a in members and b in members}
        order=stable_topology(route.segment_ids,local)
        if sum(durations[s] for s in order)>spec.max_duration_ms:raise ContractError('DOMAIN_REPAIR_ROUTE_DURATION')
        offsets={};cursor=0
        for sid in order:offsets[sid]=cursor;cursor+=durations[sid]
        for c in policy.order_constraints:
            if c.before_segment_id in members and c.after_segment_id in members:
                gap=offsets[c.after_segment_id]-offsets[c.before_segment_id]-durations[c.before_segment_id]
                if gap<c.minimum_gap_ms:raise ContractError('DOMAIN_REPAIR_REVIEW_SPACING_UNSATISFIED')
        routes.append(replace(route,segment_ids=order));orders.append(dict(route_id=route.route_id,before=route.segment_ids,after=order))
    after=replace(request,routes=tuple(routes),events=tuple(updates[e.event_id] for e in request.events),segments=tuple(new_segments))
    return finish(request,after,dict(worker='finite-route-and-response-window-restoration',routes=orders,
        changed_response_events=changed_gates,added_duration_ms=added,learning_criteria_changed=False,
        content_changed=False,empirical_mastery_proven=False,runtime_response_gate_proven=False),limits)
