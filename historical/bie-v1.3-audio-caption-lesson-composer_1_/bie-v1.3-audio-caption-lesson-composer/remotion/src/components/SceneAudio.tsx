import React from "react";
import {Audio} from "remotion";

export const SceneAudio:React.FC<{src?:string|null}>=({src})=>{
  if(!src) return null;
  return <Audio src={src} />;
};
