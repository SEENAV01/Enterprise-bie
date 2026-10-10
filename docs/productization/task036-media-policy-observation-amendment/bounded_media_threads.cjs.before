'use strict';
// Explicit governed-M1 media policy. Never change a legacy request by inference.
// Only the pinned source-parser/renderMedia callback contract is admitted.
const SCHEMA='bie.comp-m1.media-threads/1';
const PROFILE='producer-motion-v1';
function fail(){throw new Error('M1_MEDIA_THREAD_POLICY_REJECTED');}
function validatePolicy(value){
 if(!value||Object.getPrototypeOf(value)!==Object.prototype||
  JSON.stringify(Object.keys(value).sort())!==JSON.stringify(['admission_id','decoder_threads','encoder_threads','filter_threads','profile','remotion_version','schema'].sort()))fail();
 if(value.schema!==SCHEMA||value.profile!==PROFILE||value.remotion_version!=='4.0.506'||
  typeof value.admission_id!=='string'||!(/^[a-f0-9]{64}$/).test(value.admission_id)||
  value.decoder_threads!==1||value.encoder_threads!==1||value.filter_threads!==1)fail();
 return Object.freeze({...value});
}
function lowerArguments(type,args){
 if(type!=='pre-stitcher'&&type!=='stitcher')fail();
 if(!Array.isArray(args)||args.length<8||args.length>256||
  args.some((v,i)=>typeof v==='number' ? !(Number.isFinite(v)&&v===24&&i>0&&args[i-1]==='-r') :
   typeof v!=='string'||v.length>16384||v.includes('\0'))||
  args.reduce((n,v)=>n+(typeof v==='string'?v.length:2),0)>65536)fail();
 // Ambiguous or already-thread-configured calls cannot silently override policy.
 if(args.some(v=>typeof v==='string'&&/^-(?:threads|filter_threads|filter_complex_threads)(?::|=|$)/.test(v)))fail();
 const inputs=[];for(let i=0;i<args.length;i++)if(args[i]==='-i')inputs.push(i);
 if(inputs.length!==1||inputs[0]+1>=args.length-2||
  args[args.length-2]!=='-y'||args[args.length-1].startsWith('-'))fail();
 const codec=args.indexOf('-c:v');
 if(codec<0||codec+1>=args.length||!['libx264','copy'].includes(args[codec+1]))fail();
 if(type==='pre-stitcher'&&(args[inputs[0]+1]!=='-'||args[codec+1]!=='libx264'))fail();
 // FFmpeg applies codec options to the next input/output. Keep every original
 // token in its original order; add only explicit decoder/encoder/filter bounds.
 // No codec, quality, pixel format, geometry, frame, timing or media change.
 return ['-filter_threads','1','-filter_complex_threads','1',
  ...args.slice(0,inputs[0]),'-threads','1',...args.slice(inputs[0],args.length-2),
  '-threads','1',...args.slice(args.length-2)];
}
function createOverride(value){
 const policy=validatePolicy(value),calls={'pre-stitcher':0,stitcher:0};
 function override(request){
  if(!request||Object.getPrototypeOf(request)!==Object.prototype||
   JSON.stringify(Object.keys(request).sort())!==JSON.stringify(['args','type']))fail();
  const result=lowerArguments(request.type,request.args);
  if(++calls[request.type]!==1)fail();
  return result;
 }
 function completed(){
  // The pinned native renderer may omit pre-stitching after its memory test.
  // Record what actually ran; the final stitcher remains mandatory exactly once.
  if(calls.stitcher!==1||!Number.isInteger(calls['pre-stitcher'])||calls['pre-stitcher']<0||calls['pre-stitcher']>1)fail();
  return {...policy,pre_stitcher_calls:calls['pre-stitcher'],stitcher_calls:1};
 }
 return Object.freeze({override,completed});
}
module.exports=Object.freeze({SCHEMA,validatePolicy,lowerArguments,createOverride});
