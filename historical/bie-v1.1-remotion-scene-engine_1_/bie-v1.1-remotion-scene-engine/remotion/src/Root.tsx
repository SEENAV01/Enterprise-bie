import React from "react";
import { Composition } from "remotion";
import sceneData from "../../examples/electricity-magnetism.scene.json";
import { SceneRenderer } from "./SceneRenderer";
import type { Scene } from "./types";

export const Root: React.FC = () => (
  <>
    {sceneData.scenes.map((scene:Scene) => (
      <Composition key={scene.scene_id} id={scene.scene_id}
        component={()=><SceneRenderer scene={scene}/>}
        durationInFrames={scene.duration_frames} fps={30} width={1920} height={1080}/>
    ))}
  </>
);
