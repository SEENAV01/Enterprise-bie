from __future__ import annotations
from .contracts import *
from ..canonical import fingerprint
from ..errors import GameContractError
from ..learning import LearningTarget
from ..state import StateVariableSpec,StateModel
from ..expressions import ValueType,Literal,Variable,Compare,CompareOp
from ..interaction import ActionSpec,ActionKind,EffectSpec,EffectKind,RuleSpec,InteractionContract
from ..visual import VisualEntity,VisualExperienceContract,MotionCue,MotionKind,CameraCue,CameraKind
from ..audio import AudioExperienceContract
from ..feedback import FeedbackContract
from ..adaptation import AdaptationContract,AdaptationRule as DSLAdaptationRule,AdaptAction as DSLAdaptAction
from ..quality_intent import ExperienceMode,ExperienceQualityIntent
from ..document import ChallengeContract,GameLevelContract,GameExperienceContract,GameDocument
from ..compiler_engine.contracts import ScoringPolicy,MasteryPolicy,CompilerContext,CompilerSecurityPolicy
from ..director_engine.contracts import MechanicKind,AdaptAction

MODE={MechanicKind.RETRIEVAL:ExperienceMode.RETRIEVAL,MechanicKind.MANIPULATE:ExperienceMode.MANIPULATION,MechanicKind.SIMULATION:ExperienceMode.SIMULATION,MechanicKind.PREDICT:ExperienceMode.PREDICTION,MechanicKind.DIAGNOSE:ExperienceMode.DIAGNOSIS,MechanicKind.TIMELINE:ExperienceMode.TIMELINE,MechanicKind.MAP:ExperienceMode.MAP,MechanicKind.EQUATION:ExperienceMode.EQUATION,MechanicKind.CAUSAL:ExperienceMode.CAUSAL_SYSTEM}
ACTION={MechanicKind.RETRIEVAL:ActionKind.SELECT,MechanicKind.MANIPULATE:ActionKind.ADJUST,MechanicKind.SIMULATION:ActionKind.ADJUST,MechanicKind.PREDICT:ActionKind.PREDICT,MechanicKind.DIAGNOSE:ActionKind.SELECT,MechanicKind.TIMELINE:ActionKind.ORDER,MechanicKind.MAP:ActionKind.PLACE,MechanicKind.EQUATION:ActionKind.ADJUST,MechanicKind.CAUSAL:ActionKind.SELECT}
DYNAMIC={MechanicKind.MANIPULATE,MechanicKind.SIMULATION,MechanicKind.PREDICT,MechanicKind.CAUSAL}

def _token(value):return fingerprint(value)[7:19]
def _text_ref(oid,kind):return f'text:{_token(oid)}:{kind}'
def _entity_id(oid):return f'entity:{_token(oid)}'
def _progress_id(oid):return f'progress:{_token(oid)}'

def materialize(inputs:MaterializationInputs)->MaterializedGame:
    inputs.validate();plan=inputs.plan;texts={};levels=[];runtime={'typescript','html','state_machine','semantic_motion','keyboard_input','deterministic_replay'};prov=inputs.provenance
    objective_by={x.objective_id:x for x in plan.objective_assignments};mech_by={x.objective_id:x for x in plan.mechanic_assignments};feedback_by={x.objective_id:x for x in plan.feedback};mastery_by={x.objective_id:x for x in plan.mastery_targets}
    misconceptions={}
    for m in plan.misconception_assignments:misconceptions.setdefault(m.objective_id,[]).append(m.misconception_id)
    for level_node in plan.levels:
        state_vars=[];actions=[];rules=[];entities=[];motions=[];cameras=[];challenges=[];adapt_rules=[]
        state_vars.append(StateVariableSpec('attempts',ValueType.INTEGER,0,0,99,semantic_role='attempt_count'))
        for oid in level_node.objective_ids:
            if oid not in objective_by or oid not in mech_by:raise GameContractError('GAME_MAT_PLAN_REFERENCE_MISSING',oid)
            tm=inputs.texts[oid];vm=inputs.visuals[oid];mech=mech_by[oid];runtime.update(mech.required_runtime_capabilities)
            pid=_progress_id(oid);eid=_entity_id(oid);aid='action:'+_token((oid,mech.mechanic.value));rid='rule:'+_token((oid,mech.mechanic.value));cid='challenge:'+_token(oid)
            state_vars.append(StateVariableSpec(pid,ValueType.NUMBER,0.0,0.0,1.0,semantic_role='objective_progress'))
            kb='Enter or Space' if ACTION[mech.mechanic] in {ActionKind.SELECT,ActionKind.PREDICT} else 'Arrow keys and Enter'
            actions.append(ActionSpec(aid,ACTION[mech.mechanic],eid,tm.accessible_description,kb))
            rules.append(RuleSpec(rid,Compare(CompareOp.LT,Variable(pid),Literal(1.0)),(EffectSpec(pid,EffectKind.SET,1.0),EffectSpec('attempts',EffectKind.ADD,1)),mech.rationale,10,tuple(r.artifact_id for r in mech.provenance.refs)))
            entities.append(VisualEntity(eid,vm.kind,vm.semantic_role,vm.source_ref,(pid,),vm.accessible_description))
            if mech.mechanic in DYNAMIC:
                motions.append(MotionCue('motion:'+_token(oid),eid,MotionKind.STATE_CHANGE,0,min(level_node.estimated_seconds*1000,1200),'Make learner-caused state change visually explicit'))
                cameras.append(CameraCue('camera:'+_token(oid),CameraKind.FOCUS,0,min(level_node.estimated_seconds*1000,1200),'Keep attention on the learner-controlled semantic entity',eid))
            elif mech.motion_requirements:
                motions.append(MotionCue('motion:'+_token(oid),eid,MotionKind.HIGHLIGHT,0,700,'Reveal the interaction consequence without decorative motion'))
            lt=LearningTarget(oid,objective_by[oid].concept_ids,(),tuple(misconceptions.get(oid,())),mastery_by[oid].target,objective_by[oid].provenance).validate()
            success=_text_ref(oid,'success');failure=_text_ref(oid,'failure');explain=_text_ref(oid,'explanation');mission=_text_ref(oid,'mission')
            texts.update({success:tm.success_message,failure:tm.failure_message,explain:tm.explanation,mission:tm.mission_prompt})
            fb=FeedbackContract(success,failure,tuple((m,'text:'+_token((oid,m))+':mis') for m in misconceptions.get(oid,())),explain,False)
            for m in misconceptions.get(oid,()):texts['text:'+_token((oid,m))+':mis']='Re-examine the evidence for '+m
            challenges.append(ChallengeContract(cid,tm.challenge_title,mission,MODE[mech.mechanic],lt,Compare(CompareOp.EQ,Variable(pid),Literal(1.0)),(Compare(CompareOp.GE,Variable('attempts'),Literal(3)),),fb,next(x.difficulty for x in plan.difficulty if x.level_id==level_node.level_id),1.0))
            # Convert Director adaptation only when it has a target required by DSL; otherwise governed repeat/advance is represented by compiler/runtime policy rather than fabricated target.
            for a in plan.adaptations:
                if a.objective_id!=oid:continue
                amap={AdaptAction.ADVANCE:DSLAdaptAction.ADVANCE,AdaptAction.REPEAT:DSLAdaptAction.REPEAT,AdaptAction.REMEDIATE:DSLAdaptAction.REMEDIATE,AdaptAction.EASIER:DSLAdaptAction.EASIER,AdaptAction.HARDER:DSLAdaptAction.HARDER,AdaptAction.UNLOCK_HINT:DSLAdaptAction.UNLOCK_HINT,AdaptAction.BRANCH:DSLAdaptAction.BRANCH}
                target=a.target_level_id
                if amap[a.action] in {DSLAdaptAction.UNLOCK_HINT,DSLAdaptAction.BRANCH,DSLAdaptAction.REMEDIATE} and not target:raise GameContractError('GAME_MAT_ADAPT_TARGET_REQUIRED',a.rule_id)
                priority=len(adapt_rules);adapt_rules.append(DSLAdaptationRule(a.rule_id,Compare(CompareOp.GE,Variable('attempts'),Literal(max(1,a.priority+1))),amap[a.action],priority,target))
        state=StateModel(tuple(state_vars),'level').validate();interaction=InteractionContract(tuple(actions),tuple(rules)).validate(state)
        visual=VisualExperienceContract(tuple(entities),tuple(motions),tuple(cameras),'supportive').validate();audio=AudioExperienceContract(()).validate();adapt=AdaptationContract(tuple(sorted(adapt_rules,key=lambda x:x.priority))).validate(state)
        title=' / '.join(inputs.texts[o].level_title for o in level_node.objective_ids);purpose=level_node.pedagogical_purpose
        levels.append(GameLevelContract(level_node.level_id,title,purpose,state,interaction,visual,audio,adapt,tuple(challenges)).validate())
    game_id='game:'+_token(plan.plan_id);doc_id='game-doc:'+_token((plan.plan_fingerprint,tuple(sorted(inputs.texts))))
    exp=GameExperienceContract(game_id,'Studio revision experience',tuple(levels),inputs.policy.scoring_policy_id,inputs.policy.mastery_policy_id,ExperienceQualityIntent()).validate()
    doc=GameDocument(inputs.policy.game_ir_version,doc_id,(exp,),prov,False).validate()
    sp=plan.scoring;score=ScoringPolicy(inputs.policy.scoring_policy_id,float(sp.correct_points),float(sp.incorrect_points),float(max((c for _,c in sp.hint_costs),default=0)),float(sp.floor),sp.mastery_weighted,sp.speed_bonus_enabled).validate()
    threshold=max(x.target for x in plan.mastery_targets);mastery=MasteryPolicy(inputs.policy.mastery_policy_id,float(threshold),1).validate()
    material={'plan':plan.plan_fingerprint,'signals':fingerprint(inputs.signals),'document':doc.fingerprint(),'texts':dict(sorted(texts.items())),'runtime':sorted(runtime),'telemetry':inputs.policy.telemetry_allowlist}
    refs=tuple(sorted({r.artifact_id for r in prov.refs}));out_fp=fingerprint(material);receipt=MaterializationReceipt('materialize:'+out_fp[7:23],plan.plan_fingerprint,doc.fingerprint(),fingerprint(inputs),out_fp,refs,True,(),False).validate()
    return MaterializedGame(doc,dict(sorted(texts.items())),{score.policy_id:score},{mastery.policy_id:mastery},tuple(sorted(runtime)),inputs.policy.telemetry_allowlist,receipt,False).validate()

def to_compiler_context(game:MaterializedGame,*,assets=None,mechanic_events=()):
    game.validate();return CompilerContext(game.document,game.text_catalog,game.scoring_policies,game.mastery_policies,dict(assets or {}),tuple(mechanic_events),game.runtime_capabilities,game.telemetry_allowlist,CompilerSecurityPolicy(), 'studio-enterprise-v1',False).validate()
