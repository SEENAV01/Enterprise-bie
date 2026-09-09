import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import type {Lesson} from "./types";
import {SceneComposition} from "./SceneComposition";

export const LessonComposition:React.FC<{lesson:Lesson}>=({lesson})=>{
 let cursor=0;
 return <AbsoluteFill>
   {lesson.scenes.map((scene,index)=>{
     const from=cursor; cursor+=scene.duration_frames;
     return <Sequence key={scene.scene_id} from={from} durationInFrames={scene.duration_frames}>
       <SceneComposition scene={scene} index={index} total={lesson.scenes.length}/>
     </Sequence>
   })}
 </AbsoluteFill>;
};
