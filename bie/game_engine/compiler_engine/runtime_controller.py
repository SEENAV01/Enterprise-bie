from __future__ import annotations
from .provenance_adapter import all_refs
from .contracts import *
from .security import validate_generated_source

def compile_runtime_controller(ctx:CompilerContext):
    ctx.validate()
    ts=r'''import {stateMachine, cloneState, type RuntimeState} from "./state-machine";
import {ruleMetadata, ruleFunctions, challengeFunctions} from "./rules";
import {interactionProgram} from "./interactions";
import {scoringProgram} from "./scoring";
import {feedbackProgram} from "./feedback";
import {adaptationMetadata, adaptationFunctions} from "./adaptation";
import {telemetryProgram, sanitizeTelemetry} from "./telemetry";
import {applySemanticState,studioLevels,runtimeExperience,resolveStudioLevel} from "./react-runtime";
type DispatchResult={applied:boolean;action_id:string;rule_id:string|null;mechanic_id:string;state:RuntimeState;score:number;feedback:string;adaptations:readonly string[];telemetry:Record<string,unknown>};
declare global { interface Window { __BIE_GAME_ASSETS__?:Record<string,string>; __BIE_GAME_TELEMETRY_SINK__?:(event:Record<string,unknown>)=>void; __BIE_GAME_TELEMETRY_CONFIG__?:{enabled:boolean;policy_id:string;session_id:string}; } }
function levelState(levelId:string,gameId:string):RuntimeState {const levels=(stateMachine.games as readonly any[]).filter((g:any)=>g.game_id===gameId).flatMap((g:any)=>g.levels);const level=levels.find((x:any)=>x.level_id===levelId);if(!level)throw new Error("GAME_RUNTIME_LEVEL_STATE_MISSING");const out:RuntimeState={};for(const v of level.variables)out[v.id]=v.initial;return out;}
function numericEffectValue(value:unknown):number {if(typeof value!=="number"||!Number.isFinite(value))throw new Error("GAME_RUNTIME_EFFECT_NUMERIC");return value;}
function applyEffects(levelId:string,gameId:string,state:RuntimeState,effects:readonly any[]):RuntimeState {const next=cloneState(state);for(const e of effects){const cur:any=next[e.target];if(e.kind==="set")next[e.target]=e.value;else if(e.kind==="add")next[e.target]=numericEffectValue(cur)+numericEffectValue(e.value);else if(e.kind==="sub")next[e.target]=numericEffectValue(cur)-numericEffectValue(e.value);else if(e.kind==="mul")next[e.target]=numericEffectValue(cur)*numericEffectValue(e.value);else if(e.kind==="div"){if(numericEffectValue(e.value)===0)throw new Error("GAME_RUNTIME_DIV_ZERO");next[e.target]=numericEffectValue(cur)/numericEffectValue(e.value);}else if(e.kind==="toggle"){if(typeof cur!=="boolean")throw new Error("GAME_RUNTIME_EFFECT_TOGGLE_BOOL");next[e.target]=!cur;}else throw new Error("GAME_RUNTIME_EFFECT_UNSUPPORTED");validateState(levelId,gameId,next);}return next;}
function validateState(levelId:string,gameId:string,state:RuntimeState):void {
 const level=(stateMachine.games as readonly any[]).filter((g:any)=>g.game_id===gameId).flatMap((g:any)=>g.levels).find((l:any)=>l.level_id===levelId);
 if(!level)throw new Error("GAME_RUNTIME_LEVEL_STATE_MISSING");
 if(Object.keys(state).length!==level.variables.length)throw new Error("GAME_RUNTIME_STATE_COVERAGE");
 for(const spec of level.variables){const value=state[spec.id];
  if(!Object.prototype.hasOwnProperty.call(state,spec.id))throw new Error("GAME_RUNTIME_STATE_COVERAGE");
  if(spec.type==="number"||spec.type==="integer"){
   if(typeof value!=="number"||!Number.isFinite(value)||(spec.type==="integer"&&!Number.isSafeInteger(value)))throw new Error("GAME_RUNTIME_STATE_TYPE");
   if((spec.min!==null&&value<spec.min)||(spec.max!==null&&value>spec.max))throw new Error("GAME_RUNTIME_STATE_RANGE");
  }else if(spec.type==="boolean"&&typeof value!=="boolean"||spec.type==="string"&&typeof value!=="string")throw new Error("GAME_RUNTIME_STATE_TYPE");
  else if(spec.type==="enum"&&!spec.enum_values.includes(value))throw new Error("GAME_RUNTIME_STATE_ENUM");
 }
}
export function createRuntimeController(levelId:string,requestedGameId?:string){const gameId=resolveStudioLevel(levelId,requestedGameId).game_id;let boundRoot:HTMLElement|null=null;function cueRows(levelId:string):readonly any[]{return (studioLevels.find((x:any)=>x.level_id===levelId&&x.game_id===gameId) as any)?.audio||[];}
let activeNarration:HTMLAudioElement|null=null;const playingAudio=new Set<HTMLAudioElement>();function playCue(levelId:string,trigger:string):boolean{if(disposed)throw new Error("GAME_RUNTIME_DISPOSED");const cue=cueRows(levelId).find((x:any)=>x.trigger_event===trigger||x.trigger_event==="mechanic_completed");if(!cue)return false;const caption=(boundRoot?.querySelector("#bie-game-captions")||null) as HTMLElement|null;if(caption){caption.textContent=cue.caption||"";caption.dataset.cueId=cue.cue_id;caption.dataset.expectedStartMs=String(cue.start_ms||0);caption.dataset.expectedEndMs=String(cue.end_ms||0);}if(!cue.asset_ref)return true;const url=(globalThis as any).__BIE_GAME_ASSETS__?.[cue.asset_ref];if(!url)return false;const audio=new Audio(url);playingAudio.add(audio);audio.addEventListener("ended",()=>playingAudio.delete(audio),{once:true});audio.preload="auto";const expected=Math.max(0,Number(cue.end_ms||0)-Number(cue.start_ms||0));audio.addEventListener("loadedmetadata",()=>{if(expected>0&&Number.isFinite(audio.duration)){const drift=Math.abs(audio.duration*1000-expected);audio.dataset.syncDriftMs=String(drift);if(drift>Number((runtimeExperience as any).audio_max_sync_drift_ms||120))throw new Error("GAME_AUDIO_SYNC_DRIFT");}});if(cue.kind==="narration")activeNarration=audio;const prior=activeNarration&&activeNarration!==audio?activeNarration:null;if(cue.duck_narration&&prior){prior.volume=.35;audio.addEventListener("ended",()=>{prior.volume=1;},{once:true});}void audio.play().catch(()=>{});return true;}
let disposed=false,bound=false,telemetrySequence=0;const disposers:(()=>void)[]=[];function on(target:HTMLElement,type:string,listener:any){target.addEventListener(type,listener);disposers.push(()=>target.removeEventListener(type,listener));}function dispose(){if(disposed)return;disposed=true;for(const remove of disposers)remove();disposers.length=0;for(const audio of playingAudio)audio.pause();playingAudio.clear();activeNarration=null;}let state=levelState(levelId,gameId),score=0,attempts=0,lastFeedback="Ready";const completedChallenges=new Set<string>();validateState(levelId,gameId,state);const telemetry:Record<string,unknown>[]=[];const actions=(interactionProgram.actions_and_events as readonly any[]).filter((x:any)=>x.level_id===levelId&&x.game_id===gameId&&x.action_id);
 function dispatch(actionId:string,payload:Record<string,unknown>={}):DispatchResult{if(disposed)throw new Error("GAME_RUNTIME_DISPOSED");const action=actions.find((x:any)=>x.action_id===actionId);if(!action)throw new Error("GAME_RUNTIME_ACTION_UNKNOWN");if(action.mechanic_id==="reset"){state=levelState(levelId,gameId);applySemanticState(state,levelId,gameId,boundRoot||document);return{applied:true,action_id:actionId,rule_id:null,mechanic_id:action.mechanic_id,state:cloneState(state),score,feedback:"Reset",adaptations:[],telemetry:{}};}const meta=(ruleMetadata.rules as readonly any[]).find((x:any)=>x.rule_id===action.rule_id&&x.level_id===levelId&&x.game_id===gameId);if(!meta)throw new Error("GAME_RUNTIME_RULE_ROUTE_MISSING");const predicate=ruleFunctions[meta.function_name];if(!predicate)throw new Error("GAME_RUNTIME_RULE_FUNCTION_MISSING");if(!predicate(state))return{applied:false,action_id:actionId,rule_id:action.rule_id,mechanic_id:action.mechanic_id,state:cloneState(state),score,feedback:lastFeedback,adaptations:[],telemetry:{}};const ids=action.challenge_ids||[];const selected=payload.challenge_id;
 const challengeId=typeof selected==="string"&&ids.includes(selected)?selected:ids.length===1&&selected===undefined?ids[0]:null;
 if(!challengeId)throw new Error("GAME_RUNTIME_CHALLENGE_ROUTE_AMBIGUOUS");
 const challenge=challengeFunctions[JSON.stringify([gameId,levelId,challengeId])];if(!challenge)throw new Error("GAME_RUNTIME_CHALLENGE_MISSING");
 const nextState=applyEffects(levelId,gameId,state,meta.effects);const failed=challenge.failure(nextState);const succeeded=!failed&&challenge.success(nextState);
 const scoring=(scoringProgram.games as any)[gameId];let nextScore=score;if(scoring){const points=succeeded&&!completedChallenges.has(challengeId)?Number(scoring.correct_points):failed?Number(scoring.incorrect_points):0;nextScore=Math.max(Number(scoring.floor),score+points);}if(!Number.isFinite(nextScore))throw new Error("GAME_RUNTIME_SCORE_NONFINITE");
 const fired:string[]=[];for(const a of adaptationMetadata.rules as readonly any[]){if(a.level_id!==levelId||a.game_id!==gameId)continue;const fn=adaptationFunctions[a.function_name];if(fn&&fn(nextState))fired.push(a.action+":"+(a.target_id||""));}
 state=nextState;score=nextScore;attempts++;if(succeeded)completedChallenges.add(challengeId);const fb=(feedbackProgram.feedback as readonly any[]).find((x:any)=>x.challenge_id===challengeId&&x.level_id===levelId&&x.game_id===gameId);lastFeedback=succeeded?(fb?.success||"Correct"):failed?(fb?.failure||"Not yet"):"In progress";
 const event=sanitizeTelemetry({event:"mechanic_completed",game_id:gameId,level_id:levelId,challenge_id:challengeId,attempt_number:attempts,outcome_code:succeeded?"succeeded":failed?"failed":"in_progress",mechanic_id:action.mechanic_id,objective_id:(action.objective_ids||[])[(action.challenge_ids||[]).indexOf(challengeId)]||"",adaptation_id:fired[0]||""});if((telemetryProgram.events as readonly string[]).includes("mechanic_completed")){telemetry.push({...event});const cfg=window.__BIE_GAME_TELEMETRY_CONFIG__;if(cfg?.enabled&&window.__BIE_GAME_TELEMETRY_SINK__){telemetrySequence++;window.__BIE_GAME_TELEMETRY_SINK__({...event,session_id:cfg.session_id,sequence_id:telemetrySequence,policy_id:cfg.policy_id});}}playCue(levelId,"mechanic_completed");applySemanticState(state,levelId,gameId,boundRoot||document);const out=boundRoot?.querySelector("#bie-game-feedback");if(out)out.textContent=lastFeedback;return{applied:true,action_id:actionId,rule_id:action.rule_id,mechanic_id:action.mechanic_id,state:cloneState(state),score,feedback:lastFeedback,adaptations:fired,telemetry:event};}
 function bind(root:HTMLElement){
  if(disposed||bound)throw new Error("GAME_RUNTIME_BIND_LIFECYCLE");
  const targets=actions.map((action:any)=>{const node=root.querySelector(`[data-action-id="${action.action_id}"]`) as HTMLElement|null;if(!node)throw new Error("GAME_RUNTIME_ACTION_TARGET_MISSING");return{action,node};});
  const chooser=root.querySelector('[data-challenge-control="select"]') as HTMLSelectElement|null;
  bound=true;boundRoot=root;
  const audioControl=root.querySelector('[data-audio-control="play"]') as HTMLElement|null;if(audioControl)on(audioControl,"click",()=>playCue(levelId,"level_start"));
  for(const {action,node} of targets){
   let suppressPointerClick=false;
   const invoke=(payload:Record<string,unknown>={})=>dispatch(action.action_id,chooser?{...payload,challenge_id:chooser.value}:payload);
   on(node,"click",(ev:MouseEvent)=>{if(suppressPointerClick&&ev.detail>0){suppressPointerClick=false;return;}suppressPointerClick=false;invoke({});});
   on(node,"keydown",(ev:KeyboardEvent)=>{if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();suppressPointerClick=false;invoke({});}else if(action.kind==="adjust"&&(ev.key==="ArrowRight"||ev.key==="ArrowUp")){ev.preventDefault();invoke({delta:1});}else if(action.kind==="adjust"&&(ev.key==="ArrowLeft"||ev.key==="ArrowDown")){ev.preventDefault();invoke({delta:-1});}});
   if(action.kind==="drag"||action.kind==="drop"||action.kind==="place")on(node,"pointerup",(ev:PointerEvent)=>{if(ev.button!==0)return;suppressPointerClick=true;invoke({x:ev.clientX,y:ev.clientY});});
  }
 }

 return Object.freeze({dispatch,bind,dispose,playNarration:()=>playCue(levelId,"level_start"),getState:()=>cloneState(state),getScore:()=>score,getFeedback:()=>lastFeedback,getTelemetry:()=>telemetry.map(event=>({...event})),actionIds:()=>actions.map((x:any)=>x.action_id),audioRuntimeAvailable:true,reducedMotionSupported:true});}
'''
    validate_generated_source(ts,allow_imports=True);return artifact(ArtifactKind.RUNTIME_CONTROLLER,'runtime/runtime-controller.ts','text/typescript',ts,all_refs(ctx.document.provenance))
