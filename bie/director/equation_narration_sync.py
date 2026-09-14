"""BIE-DIR-SYNC-003: source-step and token-bound equation narration sync."""
from dataclasses import dataclass, replace
from .derivation_narration import DerivationNarrationStep
from .timing_contract import ordered, nonblank, integer, fingerprint
from .sync_contract import (IntentBinding, SyncCue, SyncIndex, SyncIssue, unique_inputs,
    immutable_ids, parameters, finish_plan, require_target, _immutable, SyncPlan, same_plan)
from .narration_visual_sync import validate_visual_sync


@dataclass(frozen=True)
class EquationToken:
    token_id: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class EquationState:
    state_id: str
    scene_id: str
    element_id: str
    step: DerivationNarrationStep
    tokens: tuple[EquationToken, ...] = ()

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class EquationIntent:
    binding: IntentBinding
    visual_intent_id: str
    state_id: str
    state_fingerprint: str
    action: str
    token_ids: tuple[str, ...] = ()
    allow_revisit: bool = False


def sync_equation_narration(context, visuals, states, intents, policy_version="bie-dir-equation-sync/1.0.0"):
    validate_visual_sync(context,visuals)
    index=SyncIndex(context)
    definitions=ordered(states,"equation states")
    by_state,indices={},set()
    for state in definitions:
        if not isinstance(state,EquationState) or not isinstance(state.step,DerivationNarrationStep):
            raise ValueError("expected equation state with original DerivationNarrationStep")
        _immutable(state)
        for field in ("state_id","scene_id","element_id"):
            nonblank(getattr(state,field),field)
        integer(state.step.index,"derivation index",1)
        nonblank(state.step.expression,"expression")
        nonblank(state.step.narration,"derivation narration")
        immutable_ids(state.step.evidence_ids,"derivation evidence")
        key=(state.scene_id,state.element_id,state.step.index)
        if state.state_id in by_state or key in indices:
            raise ValueError("duplicate equation state or step index within target")
        if state.scene_id not in index.scenes:
            raise ValueError("equation state refers to an unknown scene")
        indices.add(key); by_state[state.state_id]=state
        seen=set()
        for token in state.tokens:
            if not isinstance(token,EquationToken): raise ValueError("expected EquationToken")
            nonblank(token.token_id,"equation token id")
            integer(token.start_char,"token start")
            integer(token.end_char,"token end",1)
            if token.token_id in seen or not token.start_char<token.end_char<=len(state.step.expression):
                raise ValueError("duplicate or out-of-expression token anchor")
            if not state.step.expression[token.start_char:token.end_char].strip():
                raise ValueError("equation token cannot bind whitespace only")
            seen.add(token.token_id)
    rows=unique_inputs(intents,EquationIntent)
    by_visual={c.binding.intent_id:c for c in visuals.cues}
    cues,issues=[],list(visuals.issues)
    for row in rows:
        if row.action not in ("SHOW_STEP","HIGHLIGHT_TOKEN") or type(row.allow_revisit) is not bool:
            raise ValueError("unknown equation action or invalid revisit flag")
        immutable_ids(row.token_ids,"equation token ids",empty=True)
        if row.state_id not in by_state or row.visual_intent_id not in by_visual:
            raise ValueError("unknown equation state or visual intent")
        state=by_state[row.state_id]
        if row.state_fingerprint!=state.fingerprint():
            raise ValueError("stale equation expression, tokens or source-step revision")
        w=index.resolve(row.binding)
        if (state.scene_id,state.element_id)!=(w.scene_id,row.binding.target_id):
            raise ValueError("equation state target does not match narration binding")
        u=index.utterances[row.binding.anchor.utterance_id].utterance
        if u.text != state.step.narration:
            raise ValueError("equation step narration is not the exact timed utterance")
        if not set(state.step.evidence_ids)<=set(row.binding.evidence_ids):
            raise ValueError("equation step evidence missing from binding")
        tokens={t.token_id:t for t in state.tokens}
        if any(t not in tokens for t in row.token_ids):
            raise ValueError("unknown token in this exact equation revision")
        if row.action=="HIGHLIGHT_TOKEN" and (not row.token_ids or row.allow_revisit):
            raise ValueError("token highlight needs tokens and cannot change equation state")
        if row.action=="SHOW_STEP" and row.token_ids:
            raise ValueError("SHOW_STEP displays the whole state; use a separate token highlight")
        spans=tuple((tid,tokens[tid].start_char,tokens[tid].end_char,
                     state.step.expression[tokens[tid].start_char:tokens[tid].end_char]) for tid in row.token_ids)
        cue=SyncCue(row.binding,row.action,w,parameters(state_id=row.state_id,
            expression=state.step.expression,step_index=state.step.index,token_spans=spans,
            source_step_fingerprint=fingerprint(state.step)))
        issues.extend(require_target(cue,by_visual[row.visual_intent_id],"equation"))
        cues.append(cue)
    by_intent={r.binding.intent_id:r for r in rows}
    shows={}
    for cue in cues:
        if cue.kind=="SHOW_STEP":
            shows.setdefault((cue.window.scene_id,cue.binding.target_id),[]).append(cue)
    active_ends={}
    for group in shows.values():
        group.sort(key=lambda c:(c.window.start_ms,c.binding.intent_id))
        for i,cue in enumerate(group):
            row=by_intent[cue.binding.intent_id]
            state=by_state[row.state_id]
            until=by_visual[row.visual_intent_id].window.end_ms
            if i+1<len(group):
                until=min(until,group[i+1].window.start_ms)
                if group[i+1].window.start_ms<cue.window.end_ms:
                    issues.append(SyncIssue("EQUATION_STATE_OVERLAP",group[i+1].binding.intent_id,
                        "Next equation state begins before the current step narration ends.","DIR_SYNC_EQUATION"))
            active_ends[cue.binding.intent_id]=until
            if i:
                prev=by_state[by_intent[group[i-1].binding.intent_id].state_id]
                if state.step.index<=prev.step.index and not row.allow_revisit:
                    issues.append(SyncIssue("EQUATION_STEP_ORDER",row.binding.intent_id,
                        "A backward/repeated step needs an explicit revisit intent.","DIR_SCRIPT"))
    shown={by_intent[c.binding.intent_id].state_id for group in shows.values() for c in group}
    for state in definitions:
        if state.state_id not in shown:
            issues.append(SyncIssue("MISSING_EQUATION_DISPLAY",state.state_id,
                "A declared equation state has no SHOW_STEP cue.","DIR_SYNC_EQUATION"))
    for cue in cues:
        if cue.kind=="HIGHLIGHT_TOKEN":
            group=shows.get((cue.window.scene_id,cue.binding.target_id),[])
            active=[s for s in group if s.window.start_ms<=cue.window.start_ms and active_ends[s.binding.intent_id]>=cue.window.end_ms]
            row=by_intent[cue.binding.intent_id]
            if not active or by_intent[active[-1].binding.intent_id].state_id!=row.state_id:
                issues.append(SyncIssue("TOKEN_HIGHLIGHT_WITHOUT_ACTIVE_STATE",row.binding.intent_id,
                    "The referenced equation state is not active for the whole highlight.","DIR_SYNC_EQUATION"))
    cues=tuple(replace(c,parameters=tuple(sorted(c.parameters+(("active_until_ms",active_ends[c.binding.intent_id]),))))
               if c.kind=="SHOW_STEP" else c for c in cues)
    return finish_plan(index,"BIE-DIR-SYNC-003",policy_version,rows,
        tuple(sorted(definitions,key=lambda s:s.state_id)),cues,issues,visuals.fingerprint(),
        visuals.review_reasons+("EQUATION_SEMANTICS_NOT_PROVEN_BY_SYNCHRONIZATION",))


def validate_equation_sync(context, visuals, plan):
    if not isinstance(plan,SyncPlan) or plan.task_id!="BIE-DIR-SYNC-003":
        raise ValueError("expected equation sync plan")
    return same_plan(plan,sync_equation_narration(context,visuals,plan.definitions,plan.inputs,plan.policy_version))
