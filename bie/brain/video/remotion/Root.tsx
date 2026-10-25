// The bridge to real Remotion (Task 046a): the same VideoSpec and the same blocks (core + toolbox) as a Remotion
// composition. render.mjs bundles this entry with @remotion/bundler and renders it with @remotion/renderer, so a clip
// made by the preview path (remotion-lite) can be made again by Remotion itself and compared frame by frame.
import React from "react";
import { Composition, registerRoot } from "remotion";
import { Video, VideoSpec, totalFrames } from "../blocks/Video";
import "../blocks/toolbox";

const empty: VideoSpec = { fps: 30, width: 1920, height: 1080, scenes: [{ id: "empty", duration: 1, layers: [], camera: [] }] };

const Root: React.FC = () => (
  <Composition id="BieVideo" component={Video as React.FC<any>} defaultProps={{ spec: empty }}
    durationInFrames={1} fps={30} width={1920} height={1080}
    calculateMetadata={({ props }: { props: { spec: VideoSpec } }) => ({
      durationInFrames: totalFrames(props.spec), fps: props.spec.fps, width: props.spec.width, height: props.spec.height,
    })} />
);

registerRoot(Root);
