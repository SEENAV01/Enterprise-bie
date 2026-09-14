"""BIE-DIR-HARD-CONTEXT-001: actual upstream prerequisite bridges for one lesson.

Adds existing PED decisions/objectives/assessments to a lesson's bridge scope.
Never fabricates objectives or waives a prerequisite from a reported score.
"""
from dataclasses import asdict, dataclass, replace
from .director_artifacts import canonical, fingerprint
from .contract_validation import acyclic
from .teaching_context import TeachingContext
from bie.pedagogy.remedial_bridge_planner import MissingPrerequisite, plan_remedial_bridge, BridgePlan
from bie.pedagogy.bridge_content_scope import scope_bridge_content


@dataclass(frozen=True)
class TeachingObligation:
    obligation_id: str
    kind: str
    decision_id: str
    concept_id: str
    objective_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    required_texts: tuple[str, ...]
    source_reason: str
    predecessor_obligation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class LessonTeachingContext:
    profile: TeachingContext
    selected_concept_ids: tuple[str, ...]
    bridge_decision_ids: tuple[str, ...]
    decision_dependencies: tuple[tuple[str, tuple[str, ...]], ...]
    bridge_plan: BridgePlan
    obligations: tuple[TeachingObligation, ...]

    def model_data(self):
        data = self.profile.model_data()
        relevant = set(self.selected_concept_ids)
        data['knowledge_graph']['nodes'] = {k:v for k,v in data['knowledge_graph']['nodes'].items() if k in relevant}
        data['knowledge_graph']['edges'] = [e for e in data['knowledge_graph']['edges'] if e['source'] in relevant and e['target'] in relevant]
        data['prerequisite_order'] = [c for c in data['prerequisite_order'] if c in relevant]
        data['mastery_states'] = [s for s in data['mastery_states'] if s['concept_id'] in relevant]
        data['math'] = [m for m in data['math'] if m['derivation']['concept_id'] in relevant]
        if 'rich_teaching' in data:
            data['rich_teaching']['strategies'] = [row for row in data['rich_teaching']['strategies'] if row['concept_id'] in relevant]
            data['rich_teaching']['obligations'] = [row for row in data['rich_teaching']['obligations'] if row['concept_id'] in relevant]
            data['rich_teaching']['coverage'] = {key:value for key,value in data['rich_teaching']['coverage'].items() if key in relevant}
        return {**data, 'context_ref': asdict(self.profile.context_ref),
                'bridge_decision_ids': self.bridge_decision_ids, 'bridge_plan': asdict(self.bridge_plan),
                'decision_dependencies': self.decision_dependencies,
                'teaching_obligations': [asdict(o) for o in self.obligations]}

    def evidence_ids(self):
        out = {e for o in self.obligations for e in o.evidence_ids}
        for c in self.profile.concepts:
            if c.concept_id in self.selected_concept_ids:
                out.update(d.evidence_id for d in c.definitions + c.conditions)
        for p in self.profile.prerequisites:
            if p.edge.dependent in self.selected_concept_ids: out.update(p.evidence_ids)
        return tuple(sorted(out))


def derivation_decision_value(derivation):
    """Exact structured binding expected in the existing RE selected_option."""
    return canonical({'schema_version':'bie.dir.source_derivation/1.0.0', 'derivation':asdict(derivation)})


def bind_lesson_context(context, plan, objectives, bindings, reasoning, lesson_id):
    by_binding = {b.decision_id: b for b in bindings}; by_decision = {d.decision_id: d for d in plan.decisions}
    by_objective = {o.objective_id:o for o in objectives}; concepts = {c.concept_id:c for c in context.concepts}
    by_re = {d.decision_id:d for d in reasoning}
    binding_concepts = {b.decision_id:{by_objective[o].concept_id for o in b.objective_ids} for b in bindings}
    selected = {b.decision_id for b in bindings if b.lesson_id == lesson_id}; initial = set(selected)
    if not selected:
        raise ValueError('unknown lesson')
    incoming = {c: set() for c in concepts}
    for p in context.prerequisites: incoming[p.edge.dependent].add(p.edge.prerequisite)
    # Compute the complete decision + source prerequisite closure. An absent or
    # ambiguous upstream PED bridge is an explicit error, not generated mastery.
    while True:
        previous = set(selected)
        selected.update(p for d in tuple(selected) for p in by_decision[d].parent_decision_ids)
        active_concepts = {c for d in selected for c in binding_concepts[d]}
        if not active_concepts <= concepts.keys():
            raise ValueError('selected PED concept absent from grounded knowledge context')
        needed = {p for c in active_concepts for p in incoming[c]} - active_concepts
        for concept_id in sorted(needed):
            choices = [b.decision_id for b in bindings if concept_id in binding_concepts[b.decision_id]]
            if len(choices) != 1:
                raise ValueError('missing or ambiguous explicit PED prerequisite bridge')
            selected.add(choices[0])
        if selected == previous: break
    active_concepts = {c for d in selected for c in binding_concepts[d]}
    dependencies = {d:set(by_decision[d].parent_decision_ids) for d in selected}
    for row in context.prerequisites:
        if row.edge.dependent not in active_concepts: continue
        parents = {d for d in selected if row.edge.prerequisite in binding_concepts[d]}
        children = {d for d in selected if row.edge.dependent in binding_concepts[d]}
        for child in children: dependencies[child].update(parents - {child})
    acyclic(dependencies)
    bridge_ids = selected - initial; bridge_concepts = {c for d in bridge_ids for c in binding_concepts[d]}
    states = {s['concept_id']:s for s in context.model_data()['mastery_states']}
    missing = tuple(MissingPrerequisite(c, concepts[c].label,
        max(.35, 1-states[c]['lower_bound']), tuple(sorted({x.evidence_id for x in concepts[c].definitions})),
        tuple(sorted(incoming[c]))) for c in sorted(bridge_concepts))
    proposed = plan_remedial_bridge(missing)
    # The original bridge planner ranks urgency; dependency order comes from the
    # actual prerequisite tool, so urgency cannot put a child before its parent.
    order = {c:i for i,c in enumerate(context.model_data()['prerequisite_order'])}
    bridge = replace(proposed, steps=tuple(replace(s, order=i+1) for i,s in enumerate(sorted(proposed.steps,key=lambda s:order[s.concept_id]))))
    if bridge_concepts:
        scope_bridge_content(tuple(sorted(bridge_concepts)), {c:tuple(v) for c,v in incoming.items()}, concepts,
                             max_support_depth=len(concepts))
    obligations = []
    for d in sorted(bridge_ids):
        for c in sorted(binding_concepts[d]):
            concept = concepts[c]
            objectives_for_c = tuple(o for o in by_binding[d].objective_ids if by_objective[o].concept_id == c)
            obligations.append(TeachingObligation('bridge:'+d+':'+c, 'PREREQUISITE_BRIDGE', d, c, objectives_for_c,
                tuple(sorted({q.evidence_id for q in concept.definitions})), (concept.label,),
                'Explain the prerequisite in this lesson and retain its original assessment; mastery is not presumed.'))
    for derivation in context.derivations:
        decision = by_re.get(derivation.reasoning_decision_id)
        if decision is None or decision.decision_type != 'mathematical_derivation' or decision.subject_id != derivation.concept_id:
            raise ValueError('derivation not bound to actual RE decision')
        if decision.selected_option != derivation_decision_value(derivation):
            raise ValueError('RE derivation differs from source-bound math context')
        relevant = [b for b in bindings if b.decision_id in selected and derivation.reasoning_decision_id in b.reasoning_decision_ids]
        if not relevant: continue
        if len(relevant) != 1:
            raise ValueError('derivation needs an unambiguous PED teaching binding')
        binding = relevant[0]
        if binding.mode.mode != 'DERIVATION' or derivation.concept_id not in binding_concepts[binding.decision_id]:
            raise ValueError('math context does not match selected PED derivation mode/concept')
        preceding = ()
        for i,step in enumerate(derivation.steps):
            oid = 'math:'+derivation.derivation_id+':'+str(i+1)
            obligations.append(TeachingObligation(oid, 'DERIVATION_STEP', binding.decision_id, derivation.concept_id,
                tuple(o for o in binding.objective_ids if by_objective[o].concept_id==derivation.concept_id),
                (step.source,), (step.before,step.after), step.rule+': '+step.justification, preceding))
            preceding = (oid,)
    covered_math = {o.decision_id for o in obligations if o.kind=='DERIVATION_STEP'}
    if any(by_binding[d].mode.mode=='DERIVATION' and d not in covered_math for d in selected):
        raise ValueError('rich derivation mode needs actual source-bound steps')
    rich = context.model_data().get('rich_teaching', {})
    rich_rows = rich.get('obligations', [])
    rich_ids = {row['obligation_id'] for row in rich_rows}
    if len(rich_ids) != len(rich_rows):
        raise ValueError('duplicate rich teaching obligation')
    for row in rich_rows:
        concept_id = row['concept_id']
        if concept_id not in active_concepts:
            continue
        choices = [b for b in bindings if b.decision_id in selected and concept_id in binding_concepts[b.decision_id]]
        if len(choices) != 1:
            raise ValueError('rich teaching needs one explicit PED decision binding')
        binding = choices[0]
        objective_ids = tuple(o for o in binding.objective_ids if by_objective[o].concept_id == concept_id)
        permitted_evidence = {e for oid in objective_ids for e in by_objective[oid].evidence_ids}
        if not set(row['evidence_ids']) <= permitted_evidence:
            raise ValueError('rich teaching evidence outside bound objective')
        predecessors = list(row['predecessor_obligation_ids'])
        if not predecessors:
            predecessors.extend(o.obligation_id for o in obligations if o.concept_id == concept_id)
        if not set(predecessors) <= ({o.obligation_id for o in obligations} | rich_ids):
            raise ValueError('rich teaching predecessor outside lesson context')
        obligations.append(TeachingObligation(row['obligation_id'], row['kind'], binding.decision_id,
            concept_id, objective_ids, tuple(row['evidence_ids']), tuple(row['required_texts']),
            row['source_reason'], tuple(dict.fromkeys(predecessors))))
    selected_bindings = tuple(replace(b, lesson_id=lesson_id) for b in bindings if b.decision_id in selected)
    selected_objectives = tuple(o for o in objectives if o.objective_id in {o for b in selected_bindings for o in b.objective_ids})
    lesson_context = LessonTeachingContext(context, tuple(sorted(active_concepts)), tuple(sorted(bridge_ids)),
        tuple((d,tuple(sorted(dependencies[d]))) for d in sorted(dependencies)), bridge, tuple(obligations))
    return selected_bindings, selected_objectives, lesson_context
