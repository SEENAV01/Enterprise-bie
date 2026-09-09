import React from "react"; import {interpolate,useCurrentFrame} from "remotion";
export const ParticleFlow:React.FC=()=>{const f=useCurrentFrame();return <div style={{display:"flex",gap:36}}>{Array.from({length:10},(_,i)=>{const x=interpolate((f+i*24)%240,[0,239],[-20,900]);return <div key={i} style={{fontSize:22,translate:`${x}px 0px`}}>●</div>})}</div>};
