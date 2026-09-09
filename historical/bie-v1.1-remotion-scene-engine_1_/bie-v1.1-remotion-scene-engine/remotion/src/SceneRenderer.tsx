import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Scene } from "./types";

export const SceneRenderer: React.FC<{scene:Scene}> = ({scene}) => {
  const frame=useCurrentFrame();
  const opacity=interpolate(frame,[0,20],[0,1],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});
  return (
    <AbsoluteFill style={{justifyContent:"center",alignItems:"center",padding:80,opacity}}>
      <div style={{fontSize:52,fontWeight:700}}>{scene.title ?? scene.visual.type}</div>
      {scene.visual.formula && <div style={{fontSize:64,marginTop:40}}>{scene.visual.formula}</div>}
      <div style={{fontSize:28,marginTop:40,maxWidth:1300}}>
        {scene.narration.key_points.join(" • ")}
      </div>
    </AbsoluteFill>
  );
};
