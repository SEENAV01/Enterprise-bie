import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import { VisualStage } from "./VisualPrimitives";

export const ProductionScene:React.FC<any>=({scene,visualPlan})=>{
 const frame=useCurrentFrame();
 const opacity=interpolate(frame,[0,15],[0,1],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});
 return <AbsoluteFill style={{opacity}}>
   <VisualStage
     type={visualPlan.visual_type}
     instructions={scene.visual?.instructions}
     text={scene.on_screen_text?.[0]}
     equations={scene.equations}
   />
 </AbsoluteFill>;
};
