import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import type { CaptionWord } from "../types";

export const Captions:React.FC<{words:CaptionWord[]}>=({words})=>{
  const f=useCurrentFrame();
  const active=words.filter(w=>f>=w.startFrame && f<=w.endFrame);
  const text=active.map(w=>w.text).join(" ");
  const opacity=interpolate(f,[0,8],[0,1],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});
  if(!text) return null;
  return <div style={{
    position:"absolute",bottom:55,left:120,right:120,textAlign:"center",
    fontSize:34,fontWeight:700,opacity,
    textShadow:"0 2px 8px rgba(0,0,0,.7)"
  }}>{text}</div>;
};
