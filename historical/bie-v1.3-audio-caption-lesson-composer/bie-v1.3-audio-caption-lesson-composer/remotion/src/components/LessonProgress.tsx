import React from "react";
import {interpolate, useCurrentFrame} from "remotion";

export const LessonProgress:React.FC<{current:number;total:number}>=({current,total})=>{
 const p=total?current/total:0;
 return <div style={{position:"absolute",top:0,left:0,right:0,height:7}}>
   <div style={{width:`${p*100}%`,height:7}}/>
 </div>;
};
