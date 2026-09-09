import React from "react";
import {Composition} from "remotion";
import data from "./data/electricity-magnetism.lesson.json";
import type {Lesson} from "./types";
import {LessonComposition} from "./LessonComposition";
import {SceneComposition} from "./SceneComposition";

const lesson=data as Lesson;
const totalFrames=lesson.scenes.reduce((n,s)=>n+s.duration_frames,0);

export const Root=()=> <><Composition id="ElectricityMagnetismLesson"
 component={()=> <LessonComposition lesson={lesson}/>}
 durationInFrames={totalFrames} fps={30} width={1920} height={1080}/>
 {lesson.scenes.map((scene,index)=>
  <Composition key={scene.scene_id} id={scene.scene_id}
   component={()=> <SceneComposition scene={scene} index={index} total={lesson.scenes.length}/>}
   durationInFrames={scene.duration_frames} fps={30} width={1920} height={1080}/>
 )}</>;
