'use strict';
// Explicit governed-M1 media policy. Never change a legacy request by inference.
// Only the pinned source-parser/renderMedia callback contract is admitted.
const SCHEMA='bie.comp-m1.media-threads/1';
const PROFILE='producer-motion-v1';
function fail(guard){
 // Fixed failure-only category, never a private value or a render verdict.
 const error=new Error('M1_MEDIA_THREAD_POLICY_REJECTED');
 Object.defineProperty(error,'m1_media_guard',{value:guard});
 throw error;
}
function validatePolicy(value){
 if(!value||Object.getPrototypeOf(value)!==Object.prototype||
  JSON.stringify(Object.keys(value).sort())!==JSON.stringify(['admission_id','decoder_threads','encoder_threads','filter_threads','profile','remotion_version','schema'].sort()))fail('POLICY_SHAPE');
 if(value.schema!==SCHEMA||value.profile!==PROFILE||value.remotion_version!=='4.0.506'||
  typeof value.admission_id!=='string'||!(/^[a-f0-9]{64}$/).test(value.admission_id)||
  value.decoder_threads!==1||value.encoder_threads!==1||value.filter_threads!==1)fail('POLICY_IDENTITY');
 return Object.freeze({...value});
}
function lowerArguments(type,args){
 if(type!=='pre-stitcher'&&type!=='stitcher')fail('CALLBACK_KIND');
 if(!Array.isArray(args)||args.length<8||args.length>256||
  args.some((v,i)=>typeof v==='number' ? !(Number.isFinite(v)&&v===24&&i>0&&args[i-1]==='-r') :
   typeof v!=='string'||v.length>16384||v.includes('\0'))||
  args.reduce((n,v)=>n+(typeof v==='string'?v.length:2),0)>65536)fail('ARGUMENT_SHAPE');
 // Ambiguous or already-thread-configured calls cannot silently override policy.
 if(args.some(v=>typeof v==='string'&&/^-(?:threads|filter_threads|filter_complex_threads)(?::|=|$)/.test(v)))fail('ARGUMENT_THREADS');
 const inputs=[];for(let i=0;i<args.length;i++)if(args[i]==='-i')inputs.push(i);
 // Pinned renderMedia may normalize a silent audio stream even when the
 // per-frame media arrays are empty. Admit only that final video/audio pair,
 // never a generic multi-input request. Pre-stitching remains one PNG pipe.
 if((type==='pre-stitcher'&&inputs.length!==1)||
  (type==='stitcher'&&inputs.length!==1&&inputs.length!==2)||
  inputs.some(i=>i+1>=args.length-2))fail('ARGUMENT_INPUT');
 if(inputs.length===2){
  const video=inputs[0],audio=inputs[1];
  const audioCodecs=args.filter(v=>v==='-c:a').length;
  if(audio!==video+2||args[audio+2]!=='-c:a'||args[audio+3]!=='copy'||
   audioCodecs!==1||args.includes('-an')||
   inputs.some(i=>typeof args[i+1]!=='string'||!args[i+1].length||args[i+1].startsWith('-'))||
   args[video+1]===args[audio+1])fail('ARGUMENT_INPUT');
 }
 if(args[args.length-2]!=='-y'||args[args.length-1].startsWith('-'))fail('ARGUMENT_OUTPUT');
 const codec=args.indexOf('-c:v');
 if(codec<0||codec+1>=args.length||!['libx264','copy'].includes(args[codec+1]))fail('ARGUMENT_CODEC');
 if(inputs.length===2&&codec<=inputs[1]+3)fail('ARGUMENT_INPUT');
 if(type==='pre-stitcher'&&(args[inputs[0]+1]!=='-'||args[codec+1]!=='libx264'))fail('ARGUMENT_PIPE');
 // FFmpeg applies codec options to the next input/output. Keep every original
 // token in its original order; add only explicit decoder/encoder/filter bounds.
 // No codec, quality, pixel format, geometry, frame, timing or media change.
 const lowered=['-filter_threads','1','-filter_complex_threads','1'];
 for(let i=0;i<args.length;i++){
  if(inputs.includes(i)||i===args.length-2)lowered.push('-threads','1');
  lowered.push(args[i]);
 }
 return lowered;
}
function createOverride(value){
 const policy=validatePolicy(value),calls={'pre-stitcher':0,stitcher:0};
 function override(request){
  if(!request||Object.getPrototypeOf(request)!==Object.prototype||
   JSON.stringify(Object.keys(request).sort())!==JSON.stringify(['args','type']))fail('REQUEST_SHAPE');
  const result=lowerArguments(request.type,request.args);
  if(++calls[request.type]!==1)fail('CALLBACK_DUPLICATE');
  return result;
 }
 function completed(){
  // The pinned native renderer may omit pre-stitching after its memory test.
  // Record what actually ran; the final stitcher remains mandatory exactly once.
  if(calls.stitcher!==1||!Number.isInteger(calls['pre-stitcher'])||calls['pre-stitcher']<0||calls['pre-stitcher']>1)fail('COMPLETION_COUNTS');
  return {...policy,pre_stitcher_calls:calls['pre-stitcher'],stitcher_calls:1};
 }
 return Object.freeze({override,completed});
}
module.exports=Object.freeze({SCHEMA,validatePolicy,lowerArguments,createOverride});
