import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const EquationLayer:React.FC<{equations?:string[]}>=({equations=[]})=>{
 const f=useCurrentFrame();
 const opacity=interpolate(f,[0,15],[0,1],{extrapolateRight:"clamp"});
 return <div style={{fontSize:56,opacity}}>{equations.join("   ")}</div>;
};

export const DiagramLayer:React.FC<{description?:string;labels?:string[]}>=({description,labels=[]})=>
 <div style={{fontSize:34}}><div>{description}</div>{labels.map((x,i)=><div key={i}>{x}</div>)}</div>;

export const ChartLayer:React.FC<{label?:string}>=({label})=>
 <div style={{fontSize:36}}>{label||"Chart layer"}</div>;

export const TableLayer:React.FC<{rows?:string[]}>=({rows=[]})=>
 <div style={{fontSize:32}}>{rows.map((x,i)=><div key={i}>{x}</div>)}</div>;
