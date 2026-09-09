import React from "react";
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from "remotion";
import type {Scene} from "./types";
import {SceneAudio} from "./components/SceneAudio";
import {Captions} from "./components/Captions";
import {LessonProgress} from "./components/LessonProgress";

function captionWords(script:string, duration:number){
 const words=script.trim().split(/\s+/).filter(Boolean);
 if(!words.length) return [];
 const step=Math.max(2, Math.floor(duration/words.length));
 return words.map((text,i)=>({text,startFrame:i*step,endFrame:Math.min(duration,(i+1)*step+2)}));
}

export const SceneComposition:React.FC<{scene:Scene;index:number;total:number}>=({scene,index,total})=>{
 const f=useCurrentFrame();
 const opacity=interpolate(f,[0,18],[0,1],{extrapolateRight:"clamp",easing:Easing.bezier(.16,1,.3,1)});
 const script=scene.narration.script ?? scene.narration.key_points.join(" ");
 const captionDuration=Math.min(scene.duration_frames,scene.narration.estimated_duration_frames ?? scene.duration_frames);
 const words=captionWords(script,captionDuration);
 return <AbsoluteFill style={{opacity,padding:70,display:"flex",flexDirection:"column"}}>
   <LessonProgress current={index+1} total={total}/>
   <div style={{fontSize:46,fontWeight:700}}>{scene.title ?? scene.visual.type}</div>
   <div style={{flex:1,display:"flex",alignItems:"center",justifyContent:"center"}}>
     <div style={{fontSize:42,maxWidth:1500,textAlign:"center"}}>{scene.visual.formula ?? scene.visual.type.replaceAll("_"," ")}</div>
   </div>
   <Captions words={words}/>
   <SceneAudio src={scene.narration.audio_asset}/>
 </AbsoluteFill>;
};
