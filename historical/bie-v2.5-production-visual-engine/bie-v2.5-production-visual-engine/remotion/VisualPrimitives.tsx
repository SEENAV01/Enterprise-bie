import React from "react";
import { AbsoluteFill } from "remotion";

export const TextPrimitive:React.FC<{text:string}>=({text})=>
  <div style={{fontSize:54,fontWeight:700}}>{text}</div>;

export const DiagramPrimitive:React.FC<{instructions?:string}>=({instructions})=>
  <div style={{fontSize:34}}>[DIAGRAM] {instructions}</div>;

export const EquationPrimitive:React.FC<{equations?:string[]}>=({equations=[]})=>
  <div style={{fontSize:48}}>{equations.join("   ")}</div>;

export const ProcessPrimitive:React.FC<{instructions?:string}>=({instructions})=>
  <div style={{fontSize:38}}>[PROCESS] {instructions}</div>;

export const ChartPrimitive:React.FC<{instructions?:string}>=({instructions})=>
  <div style={{fontSize:38}}>[CHART] {instructions}</div>;

export const TablePrimitive:React.FC<{instructions?:string}>=({instructions})=>
  <div style={{fontSize:38}}>[TABLE] {instructions}</div>;

export const RealWorldPrimitive:React.FC<{instructions?:string}>=({instructions})=>
  <div style={{fontSize:38}}>[REAL WORLD] {instructions}</div>;

export const VisualStage:React.FC<{type:string;instructions?:string;text?:string;equations?:string[]}>=
({type,instructions,text,equations})=>
<AbsoluteFill style={{display:"flex",alignItems:"center",justifyContent:"center",padding:80}}>
 {type==="diagram" && <DiagramPrimitive instructions={instructions}/>}
 {type==="equation" && <EquationPrimitive equations={equations}/>}
 {type==="process" && <ProcessPrimitive instructions={instructions}/>}
 {type==="chart" && <ChartPrimitive instructions={instructions}/>}
 {type==="table" && <TablePrimitive instructions={instructions}/>}
 {type==="real_world" && <RealWorldPrimitive instructions={instructions}/>}
 {type==="text" && <TextPrimitive text={text||instructions||""}/>}
 {type==="mixed" && <TextPrimitive text={text||instructions||""}/>}
</AbsoluteFill>;
