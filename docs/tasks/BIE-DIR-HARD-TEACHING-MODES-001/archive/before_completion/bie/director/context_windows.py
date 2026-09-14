"""BIE-DIR-HARD-WINDOWS-001: source-preserving views of actual PED decisions.

A window is an execution view, never a replacement upstream artifact. Complete
cited pages, actual RE ancestry, prerequisite definitions and math chains stay
intact. An indivisible context that cannot fit fails; it is never truncated.
"""
from dataclasses import asdict, dataclass, replace
import heapq
from .contract_validation import acyclic, ids
from .director_artifacts import canonical, fingerprint
from .director_model import DirectingPolicy, ResourceLimit, request_material


@dataclass(frozen=True)
class WindowedDirectingPolicy(DirectingPolicy):
    window_version: str = 'bie-dir-decision-windows/1.0.0'
    maximum_windows: int = 128
    continuity_reserve_characters: int = 12000
    prior_scene_count: int = 1

    def validate(self):
        super().validate()
        if self.window_version != 'bie-dir-decision-windows/1.0.0':
            raise ValueError('unsupported directing window policy')
        if type(self.maximum_windows) is not int or self.maximum_windows < 1:
            raise ValueError('positive window resource budget required')
        if (type(self.continuity_reserve_characters) is not int
                or not 0 <= self.continuity_reserve_characters < self.maximum_request_characters):
            raise ValueError('continuity reserve must fit inside the request budget')
        if type(self.prior_scene_count) is not int or self.prior_scene_count < 1:
            raise ValueError('at least the previous complete scene is required for continuity')


def decision_dependencies(inputs):
    owned={b.decision_id for b in inputs.bindings}
    deps={d.decision_id:set(d.parent_decision_ids) for d in inputs.pedagogy.decisions if d.decision_id in owned}
    if inputs.teaching_context is not None:
        for child,parents in inputs.teaching_context.decision_dependencies:
            if child not in deps:
                raise ValueError('windowing requires the complete selected prerequisite bridge scope')
            deps[child].update(parents)
    if set(deps)!=owned or any(not parents <= owned for parents in deps.values()):
        raise ValueError('windowing requires the complete selected prerequisite bridge scope')
    acyclic(deps)
    return {d:tuple(sorted(parents)) for d,parents in deps.items()}


def ordered_decisions(inputs):
    deps=decision_dependencies(inputs); rank={b.decision_id:i for i,b in enumerate(inputs.bindings)}
    children={d:set() for d in deps}; counts={d:len(parents) for d,parents in deps.items()}
    for d,parents in deps.items():
        for parent in parents: children[parent].add(d)
    ready=[(rank[d],d) for d,n in counts.items() if n==0]; heapq.heapify(ready); result=[]
    while ready:
        _,d=heapq.heappop(ready); result.append(d)
        for child in sorted(children[d]):
            counts[child]-=1
            if counts[child]==0: heapq.heappush(ready,(rank[child],child))
    if len(result)!=len(deps): raise ValueError('cyclic window decision order')
    return tuple(result)


def supporting_decisions(inputs, selected):
    deps=decision_dependencies(inputs); closure=set(selected); pending=list(selected)
    while pending:
        for parent in deps[pending.pop()]:
            if parent not in closure: closure.add(parent); pending.append(parent)
    return tuple(d for d in ordered_decisions(inputs) if d in closure and d not in selected)


@dataclass(frozen=True)
class ContextSlice:
    full: object
    decision_ids: tuple[str,...]
    selected_concept_ids: tuple[str,...]

    @property
    def obligations(self): return tuple(o for o in self.full.obligations if o.decision_id in self.decision_ids)
    @property
    def decision_dependencies(self):
        return tuple((d,tuple(p for p in parents if p in self.decision_ids))
            for d,parents in self.full.decision_dependencies if d in self.decision_ids)

    def model_data(self):
        data=self.full.model_data(); selected=set(self.selected_concept_ids)
        data['knowledge_graph']['nodes']={k:v for k,v in data['knowledge_graph']['nodes'].items() if k in selected}
        data['knowledge_graph']['edges']=[e for e in data['knowledge_graph']['edges'] if e['source'] in selected and e['target'] in selected]
        data['prerequisite_order']=[c for c in data['prerequisite_order'] if c in selected]
        data['mastery_states']=[s for s in data['mastery_states'] if s['concept_id'] in selected]
        data['math']=[m for m in data['math'] if m['derivation']['concept_id'] in selected]
        data['bridge_decision_ids']=[d for d in data['bridge_decision_ids'] if d in self.decision_ids]
        bridge_concepts={o.concept_id for o in self.obligations if o.kind=='PREREQUISITE_BRIDGE'}
        data['bridge_plan']['steps']=[s for s in data['bridge_plan']['steps'] if s['concept_id'] in bridge_concepts]
        data['bridge_plan']['requires_bridge']=bool(bridge_concepts)
        data['decision_dependencies']=[(d,parents) for d,parents in self.full.decision_dependencies if d in self.decision_ids]
        data['teaching_obligations']=[asdict(o) for o in self.obligations]
        data['scope']='CURRENT_DECISIONS_WITH_COMPLETE_PREREQUISITE_SUPPORT; NOT_A_NEW_UPSTREAM_ARTIFACT'
        return data

    def evidence_ids(self):
        selected=set(self.selected_concept_ids); evidence={e for o in self.obligations for e in o.evidence_ids}
        for concept in self.full.profile.concepts:
            if concept.concept_id in selected: evidence.update(x.evidence_id for x in concept.definitions+concept.conditions)
        for row in self.full.profile.prerequisites:
            if row.edge.dependent in selected: evidence.update(row.evidence_ids)
        for derivation in self.full.profile.derivations:
            if derivation.concept_id in selected: evidence.update(s.source for s in derivation.steps)
        return tuple(sorted(evidence))


@dataclass(frozen=True)
class WindowInputView:
    """A distinct type so it cannot masquerade as load_director_inputs output."""
    full: object
    decision_ids: tuple[str,...]
    support_decision_ids: tuple[str,...]

    def __getattr__(self,name):
        if name in ('lesson_id','title','language','catalog','reasoning','inferences','evidence_artifacts','review_reasons'):
            return getattr(self.full,name)
        raise AttributeError(name)
    @property
    def bindings(self):
        by_id={b.decision_id:b for b in self.full.bindings}
        return tuple(by_id[d] for d in self.decision_ids)
    @property
    def prerequisite_support(self):
        selected=set(self.support_decision_ids)
        bindings=tuple(b for b in self.full.bindings if b.decision_id in selected)
        objectives={o for b in bindings for o in b.objective_ids}
        return {'scope':'SUPPORT_ONLY; OWNED_TEACHING_BINDINGS_REMAIN_SEPARATE',
            'teaching_bindings':[asdict(b) for b in bindings],
            'objectives':[asdict(o) for o in self.full.objectives if o.objective_id in objectives],
            'decisions':[asdict(d) for d in self.full.pedagogy.decisions if d.decision_id in selected]}
    @property
    def objectives(self):
        selected={o for b in self.bindings for o in b.objective_ids}
        return tuple(o for o in self.full.objectives if o.objective_id in selected)
    @property
    def pedagogy(self):
        return replace(self.full.pedagogy, objective_ids=tuple(o.objective_id for o in self.objectives),
            lesson_ids=(self.lesson_id,), decisions=tuple(replace(d,parent_decision_ids=tuple(p for p in d.parent_decision_ids if p in self.decision_ids))
                for d in self.full.pedagogy.decisions if d.decision_id in self.decision_ids))
    @property
    def teaching_context(self):
        if self.full.teaching_context is None: return None
        support=set(self.decision_ids+self.support_decision_ids)
        objective_ids={o for b in self.full.bindings if b.decision_id in support for o in b.objective_ids}
        concepts=tuple(sorted({o.concept_id for o in self.full.objectives if o.objective_id in objective_ids}))
        return ContextSlice(self.full.teaching_context,self.decision_ids,concepts)
    def fingerprint(self):
        return fingerprint({'schema_version':'bie.dir.window_view/1.0.0','full_input_fingerprint':self.full.fingerprint(),
            'decision_ids':self.decision_ids,'support_decision_ids':self.support_decision_ids})


@dataclass(frozen=True)
class ContextWindow:
    window_id: str
    decision_ids: tuple[str,...]
    support_decision_ids: tuple[str,...]
    evidence_ids: tuple[str,...]
    page_fingerprints: tuple[str,...]
    view_fingerprint: str
    context_fingerprint: str

    def fingerprint(self): return fingerprint(asdict(self))


def outline(inputs):
    by_objective={o.objective_id:o for o in inputs.objectives}; by_binding={b.decision_id:b for b in inputs.bindings}
    deps=decision_dependencies(inputs)
    return [{'decision_id':d,'parent_decision_ids':deps[d],'teaching_mode':by_binding[d].mode.mode,
        'objectives':[{'objective_id':o,'concept_id':by_objective[o].concept_id,'statement':by_objective[o].statement}
            for o in by_binding[d].objective_ids]} for d in ordered_decisions(inputs)]


def window_view(inputs, window):
    return WindowInputView(inputs,window.decision_ids,window.support_decision_ids)


def make_window(inputs, decision_ids, index):
    from .grounded_directing import model_context
    selected=ids(tuple(decision_ids),'window decisions'); view=WindowInputView(inputs,selected,supporting_decisions(inputs,selected))
    context=model_context(view); pages={p.page_id:p for p in inputs.catalog.pages}
    return ContextWindow('window:'+str(index),selected,view.support_decision_ids,
        tuple(p['evidence_id'] for p in context['source_passages']),
        tuple(pages[p['page_id']].fingerprint() for p in context['source_pages']),view.fingerprint(),fingerprint(context))


def planning_contract(inputs, window, completed_scenes=()):
    from .grounded_directing import model_context, PLAN_INSTRUCTION, _schema, TEXT
    from .contextual_teaching import plan_schema, instruction_suffix
    view=window_view(inputs,window)
    payload={'operation':'PLAN_WINDOW','inputs':model_context(view),'global_input_fingerprint':inputs.fingerprint(),
        'window':asdict(window),'window_fingerprint':window.fingerprint(),'global_teaching_outline':outline(inputs),
        'completed_plan_ledger':[{'scene_id':s.scene_id,'title':s.title,'teaching_goal':s.teaching_goal,
            'pedagogy_decision_ids':s.pedagogy_decision_ids,'objective_ids':s.objective_ids} for s in completed_scenes],
        'scene_id_prefix':window.window_id+':'}
    schema=_schema({**plan_schema(view)['properties'],'global_input_fingerprint':TEXT,'window_fingerprint':TEXT})
    instruction=PLAN_INSTRUCTION+instruction_suffix(view)+'''
This is one source-preserving execution window of the same lesson. The global teaching outline and
completed_plan_ledger are host records, not evidence of learner mastery. Plan exactly the owned PED
decisions and obligations; prerequisite support is context, not a request to reteach completed units.
Use the supplied scene_id_prefix for every scene ID. Parent scenes in this response belong to this
window; global prerequisite ordering is checked again after assembly. Do not invent new objectives or
assessments. Choose as many substantively justified scenes as this teaching requires; no universal layout.
Echo both the global_input_fingerprint and window_fingerprint along with the input-view binding.'''
    return payload,schema,instruction


def build_windows(inputs, policy, identity):
    from .director_inputs import DirectorInputs
    if not isinstance(inputs,DirectorInputs): raise ValueError('full upstream DirectorInputs required')
    if not isinstance(policy,WindowedDirectingPolicy): raise ValueError('explicit windowed directing policy required')
    policy.validate(); ordered=ordered_decisions(inputs); windows=[]; pending=[]
    # Reserve capacity for completed scene contracts and bounded retry feedback.
    budget=replace(policy,maximum_request_characters=policy.maximum_request_characters-policy.continuity_reserve_characters)
    def fits(selected):
        window=make_window(inputs,selected,len(windows)+1); payload,schema,prompt=planning_contract(inputs,window)
        try: request_material(identity,budget,'PLAN_WINDOW',window.window_id,prompt,payload,schema,
                              policy.maximum_attempts,'RESPONSE_CONTRACT_REJECTED')
        except ResourceLimit: return None
        return window
    for decision in ordered:
        trial=fits((*pending,decision))
        if trial is not None: pending.append(decision); continue
        if pending:
            windows.append(make_window(inputs,tuple(pending),len(windows)+1)); pending=[]
        if fits((decision,)) is None:
            raise ResourceLimit('complete indivisible PED/source/RE/prerequisite/math context exceeds window budget: '+decision)
        pending=[decision]
    if pending: windows.append(make_window(inputs,tuple(pending),len(windows)+1))
    if not windows or len(windows)>policy.maximum_windows:
        raise ResourceLimit('window count exceeds the configured execution resource budget')
    if tuple(d for w in windows for d in w.decision_ids)!=ordered:
        raise ValueError('window schedule lost or repeated a teaching decision')
    from .grounded_directing import model_context
    required={p['evidence_id'] for p in model_context(inputs)['source_passages']}
    if required != {e for w in windows for e in w.evidence_ids}:
        raise ValueError('source coverage lost by the context-window schedule')
    return tuple(windows)
