// Test-only UI. Loaded alongside, never included in, the production game bundle.
import {React, reactDomVersion} from './react-vendor.js';
const events=[];
window.__BIE_GAME_TELEMETRY_CONFIG__={enabled:true,policy_id:'policy:probe',session_id:'session:1'};
window.__BIE_GAME_TELEMETRY_SINK__=event=>events.push(event);
const audio={calls:0,playing:0,ended:0,errors:[]};
const originalPlay=HTMLMediaElement.prototype.play;
HTMLMediaElement.prototype.play=function(...args){
  audio.calls++;
  this.addEventListener('playing',()=>audio.playing++,{once:true});
  this.addEventListener('ended',()=>audio.ended++,{once:true});
  const result=originalPlay.apply(this,args);
  result.catch(error=>audio.errors.push(error.name));
  return result;
};
const errors=[];
window.addEventListener('error',event=>errors.push(event.message));
window.addEventListener('unhandledrejection',event=>errors.push(String(event.reason)));
const entry=await import('./entry.js');
const initial=window.__BIE_GAME_RUNTIME__.getState();
const result=document.querySelector('#h6-probe-result');
const report={schema_version:'bie.game.h6.ui-proof/1',checks:{},passed:false,
  platform:navigator.platform,react:React.version,reactDOM:reactDomVersion,
  linux_sandbox_verified:false,product_accepted:false,
  input_scope:'Native keyboard/audio activation followed by a test-only lifecycle harness'};
const check=(key,condition,detail=true)=>{
  if(!condition)throw new Error('FAILED:'+key);
  report.checks[key]=detail;
};
document.querySelector('#h6-probe-check').addEventListener('click',async()=>{
  try{
    const api=window.__BIE_GAME_RUNTIME__;
    const after=api.getState();
    check('real_react_exports',React.version==='19.3.0'&&reactDomVersion==='19.3.0'&&React.isValidElement(React.createElement('span')));
    check('single_application',document.querySelectorAll('main[role="application"]').length===1);
    check('native_keyboard_changed_state',initial.x===1&&after.x===2,{initial,after});
    check('score',api.getScore()===10,api.getScore());
    check('one_telemetry_event',events.length===1&&events[0].sequence_id===1&&events[0].session_id==='session:1'&&!('raw_text' in events[0]),events.slice());
    check('actual_audio_completed',audio.calls>0&&audio.playing>0&&audio.ended>0&&audio.errors.length===0,{...audio});
    check('caption_present',document.querySelector('#bie-game-captions').textContent.length>0);
    let unknown=false;try{api.dispatch('unknown:action');}catch(e){unknown=e.message==='GAME_RUNTIME_ACTION_UNKNOWN';}
    check('unknown_action_no_mutation',unknown&&JSON.stringify(after)===JSON.stringify(api.getState()));
    let duplicate=false;try{entry.startGameRuntime();}catch(e){duplicate=e.message==='GAME_REACT_ALREADY_MOUNTED';}
    check('duplicate_mount_rejected',duplicate);
    const oldTarget=document.querySelector('button[data-entity-id]');
    api.dispose();api.dispose();
    oldTarget.click();
    let disposed=false;try{api.dispatch('drag:mover');}catch(e){disposed=e.message==='GAME_RUNTIME_DISPOSED';}
    check('dispose_unmounts_removes_handlers',!api.booted&&disposed&&events.length===1&&document.querySelectorAll('main[role="application"]').length===0);
    window.__BIE_GAME_TELEMETRY_CONFIG__.session_id='session:2';
    const next=entry.startGameRuntime();
    check('remount_restores_initial_state',JSON.stringify(initial)===JSON.stringify(next.getState()));
    document.querySelector('button[data-entity-id]').click();
    check('replay_same_state_score',JSON.stringify(after)===JSON.stringify(next.getState())&&next.getScore()===10);
    check('new_session_resets_sequence',events.length===2&&events[1].session_id==='session:2'&&events[1].sequence_id===1);
    check('no_page_errors',errors.length===0,errors);
    report.passed=true;
  }catch(error){report.failure=String(error.stack||error);}
  result.textContent=JSON.stringify(report,null,2);
  document.querySelector('#h6-probe-check').disabled=true;
});
