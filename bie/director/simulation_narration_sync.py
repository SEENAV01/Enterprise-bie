"""BIE-DIR-SYNC-005: deterministic declared-state simulation cue schedules.

Model fingerprints/seeds describe a future runtime input. No code is executed,
and declared state values are not passed off as observed simulation outputs.
"""
from dataclasses import dataclass
from .demonstration_narration import DemoNarrationStep
from .timing_contract import ordered, nonblank, number, integer, digest_id, fingerprint
from .sync_contract import (IntentBinding, SyncCue, SyncIndex, SyncIssue, unique_inputs,
    immutable_ids, parameters, finish_plan, require_target, _immutable, SyncPlan, same_plan)
from .narration_visual_sync import validate_visual_sync


@dataclass(frozen=True)
class SimulationParameter:
    parameter_id: str
    unit: str
    minimum: float
    maximum: float


@dataclass(frozen=True)
class ParameterValue:
    parameter_id: str
    value: float


@dataclass(frozen=True)
class SimulationState:
    state_id: str
    values: tuple[ParameterValue, ...]


@dataclass(frozen=True)
class SimulationTransition:
    transition_id: str
    from_state_id: str
    to_state_id: str
    changed_parameter_ids: tuple[str, ...]
    minimum_duration_ms: int = 1


@dataclass(frozen=True)
class SimulationDefinition:
    simulation_id: str
    scene_id: str
    element_id: str
    revision: str
    model_fingerprint: str
    seed: int
    parameters: tuple[SimulationParameter, ...]
    states: tuple[SimulationState, ...]
    transitions: tuple[SimulationTransition, ...]
    initial_state_id: str
    evidence_ids: tuple[str, ...]

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class SimulationIntent:
    binding: IntentBinding
    visual_intent_id: str
    simulation_id: str
    simulation_fingerprint: str
    narration_step: DemoNarrationStep
    state_id: str
    transition_id: str | None = None


def _validate_simulation(spec):
    if not isinstance(spec,SimulationDefinition): raise ValueError("expected SimulationDefinition")
    _immutable(spec)
    for field in ("simulation_id","scene_id","element_id","revision","initial_state_id"):
        nonblank(getattr(spec,field),field)
    digest_id(spec.model_fingerprint,"simulation model fingerprint")
    integer(spec.seed,"simulation seed")
    immutable_ids(spec.evidence_ids,"simulation evidence")
    params={}
    for p in spec.parameters:
        if not isinstance(p,SimulationParameter): raise ValueError("expected SimulationParameter")
        nonblank(p.parameter_id,"parameter id"); nonblank(p.unit,"parameter unit")
        number(p.minimum,"parameter minimum",low=-float("inf"))
        number(p.maximum,"parameter maximum",p.minimum)
        if p.parameter_id in params: raise ValueError("duplicate simulation parameter")
        params[p.parameter_id]=p
    if not params: raise ValueError("simulation must declare its parameter schema")
    states={}
    for s in spec.states:
        if not isinstance(s,SimulationState): raise ValueError("expected SimulationState")
        nonblank(s.state_id,"state id")
        if s.state_id in states: raise ValueError("duplicate simulation state")
        values={}
        for v in s.values:
            if not isinstance(v,ParameterValue) or v.parameter_id not in params or v.parameter_id in values:
                raise ValueError("unknown, duplicate or invalid state parameter")
            p=params[v.parameter_id]
            number(v.value,"state parameter value",p.minimum,p.maximum)
            values[v.parameter_id]=v.value
        if set(values)!=set(params): raise ValueError("state must supply every declared parameter")
        states[s.state_id]=values
    if spec.initial_state_id not in states: raise ValueError("unknown initial simulation state")
    seen=set()
    for t in spec.transitions:
        if not isinstance(t,SimulationTransition): raise ValueError("expected SimulationTransition")
        nonblank(t.transition_id,"transition id")
        integer(t.minimum_duration_ms,"transition minimum duration",1)
        immutable_ids(t.changed_parameter_ids,"changed parameter IDs",empty=True)
        if t.transition_id in seen or t.from_state_id not in states or t.to_state_id not in states:
            raise ValueError("duplicate transition or unknown state endpoint")
        seen.add(t.transition_id)
        changed={p for p in params if states[t.from_state_id][p]!=states[t.to_state_id][p]}
        if set(t.changed_parameter_ids)!=changed:
            raise ValueError("transition changed-parameter declaration does not match its states")


def sync_simulation_narration(context, visuals, simulations, intents, policy_version="bie-dir-simulation-sync/1.0.0"):
    validate_visual_sync(context,visuals)
    index=SyncIndex(context)
    definitions=ordered(simulations,"simulation definitions")
    by_sim,targets={},set()
    for spec in definitions:
        _validate_simulation(spec)
        key=(spec.scene_id,spec.element_id)
        if spec.simulation_id in by_sim or key in targets or spec.scene_id not in index.scenes:
            raise ValueError("duplicate simulation revision/target or unknown scene")
        by_sim[spec.simulation_id]=spec; targets.add(key)
    rows=unique_inputs(intents,SimulationIntent)
    by_visual={c.binding.intent_id:c for c in visuals.cues}
    cues,issues=[],list(visuals.issues)
    for row in rows:
        if row.simulation_id not in by_sim or row.visual_intent_id not in by_visual:
            raise ValueError("unknown simulation or visual intent")
        spec=by_sim[row.simulation_id]
        if row.simulation_fingerprint!=spec.fingerprint(): raise ValueError("stale simulation schema/model/seed revision")
        step=row.narration_step
        if not isinstance(step,DemoNarrationStep) or step.phase not in ("SETUP","ACTION","OBSERVE","INTERPRET"):
            raise ValueError("expected original demonstration narration step")
        immutable_ids(step.evidence_ids,"demonstration evidence")
        w=index.resolve(row.binding)
        if (spec.scene_id,spec.element_id)!=(w.scene_id,row.binding.target_id): raise ValueError("simulation target mismatch")
        if step.narration!=index.utterances[row.binding.anchor.utterance_id].utterance.text:
            raise ValueError("demonstration narration differs from exact timed utterance")
        if not set(step.evidence_ids)<=set(row.binding.evidence_ids) or not set(row.binding.evidence_ids)<=set(spec.evidence_ids):
            raise ValueError("simulation/demo evidence is inconsistent with narration binding")
        state=next((s for s in spec.states if s.state_id==row.state_id),None)
        if state is None: raise ValueError("unknown declared simulation state")
        transition=next((t for t in spec.transitions if t.transition_id==row.transition_id),None)
        if step.phase=="ACTION":
            if transition is None or transition.to_state_id!=state.state_id:
                raise ValueError("action must name an existing transition and its exact destination")
            if transition.minimum_duration_ms>w.end_ms-w.start_ms:
                issues.append(SyncIssue("SIMULATION_ACTION_TOO_SHORT",row.binding.intent_id,
                    "Declared transition duration exceeds the narration window.","DIR_TIME"))
        elif row.transition_id is not None: raise ValueError("only ACTION may execute a declared transition")
        if step.phase=="SETUP" and state.state_id!=spec.initial_state_id:
            raise ValueError("SETUP must initialize the declared initial state")
        cue=SyncCue(row.binding,step.phase,w,parameters(simulation_id=spec.simulation_id,
            simulation_fingerprint=spec.fingerprint(),model_fingerprint=spec.model_fingerprint,seed=spec.seed,
            declared_state_id=state.state_id,declared_values=tuple((v.parameter_id,v.value) for v in state.values),
            transition_id=row.transition_id,execution_status="DECLARED_NOT_EXECUTED",
            source_narration_fingerprint=fingerprint(step)))
        issues.extend(require_target(cue,by_visual[row.visual_intent_id],"simulation")); cues.append(cue)
    by_row={r.binding.intent_id:r for r in rows}
    for spec in definitions:
        group=sorted((c for c in cues if by_row[c.binding.intent_id].simulation_id==spec.simulation_id),
                     key=lambda c:(c.window.start_ms,c.binding.intent_id))
        current=None; action_done=False; observed=False; interpreted=False; previous_end=0
        if not group:
            issues.append(SyncIssue("UNBOUND_SIMULATION",spec.simulation_id,"No narration cycle supplied.","DIR_SCRIPT"))
        for cue in group:
            row=by_row[cue.binding.intent_id]
            if cue.window.start_ms<previous_end:
                issues.append(SyncIssue("SIMULATION_PHASE_OVERLAP",row.binding.intent_id,
                    "Simulation narration phases overlap in the same state machine.","DIR_SCRIPT"))
            previous_end=max(previous_end,cue.window.end_ms)
            phase=cue.kind
            if phase=="SETUP":
                if action_done and not interpreted:
                    issues.append(SyncIssue("UNFINISHED_SIMULATION_CYCLE",row.binding.intent_id,
                        "A new setup interrupts an uninterpreted action.","DIR_SCRIPT"))
                current=row.state_id; action_done=observed=interpreted=False
            elif phase=="ACTION":
                transition=next(t for t in spec.transitions if t.transition_id==row.transition_id)
                if current!=transition.from_state_id:
                    issues.append(SyncIssue("SIMULATION_STATE_PRECONDITION",row.binding.intent_id,
                        "Action source state is not the currently established state.","DIR_SCRIPT"))
                if action_done and not interpreted:
                    issues.append(SyncIssue("UNFINISHED_SIMULATION_CYCLE",row.binding.intent_id,
                        "Observe and interpret the preceding action before another action.","DIR_SCRIPT"))
                current=row.state_id; action_done=True; observed=interpreted=False
            elif phase=="OBSERVE":
                if not action_done or current!=row.state_id:
                    issues.append(SyncIssue("OBSERVATION_WITHOUT_ACTION",row.binding.intent_id,
                        "Observation must follow an action in its destination state.","DIR_SCRIPT"))
                else: observed=True
            elif phase=="INTERPRET":
                if not observed or current!=row.state_id:
                    issues.append(SyncIssue("INTERPRETATION_WITHOUT_OBSERVATION",row.binding.intent_id,
                        "Interpretation must follow observation of the same state.","DIR_SCRIPT"))
                else: interpreted=True
        if group and not interpreted:
            issues.append(SyncIssue("INCOMPLETE_SIMULATION_CYCLE",spec.simulation_id,
                "Complete SETUP/ACTION/OBSERVE/INTERPRET for the declared example.","DIR_SCRIPT"))
    return finish_plan(index,"BIE-DIR-SYNC-005",policy_version,rows,tuple(sorted(definitions,key=lambda s:s.simulation_id)),
        tuple(cues),issues,visuals.fingerprint(),visuals.review_reasons+("SIMULATION_STATES_ARE_DECLARED_NOT_OBSERVED",))


def validate_simulation_sync(context, visuals, plan):
    if not isinstance(plan,SyncPlan) or plan.task_id!="BIE-DIR-SYNC-005":
        raise ValueError("expected simulation sync plan")
    return same_plan(plan,sync_simulation_narration(context,visuals,plan.definitions,plan.inputs,plan.policy_version))
