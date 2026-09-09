import React from "react";
import { Composition } from "remotion";
import { RenderTimeline, SceneSpec } from "./SceneRegistry";
import contract from "../examples/renderer-contract.json";

export const Root: React.FC = () => {
  const scenes = contract.scene_dsl.scenes as SceneSpec[];
  return (
    <Composition
      id="BIECourse"
      component={() => <RenderTimeline scenes={scenes}/>}
      durationInFrames={contract.remotion_manifest.duration_in_frames}
      fps={contract.remotion_manifest.fps}
      width={contract.remotion_manifest.width}
      height={contract.remotion_manifest.height}
    />
  );
};
