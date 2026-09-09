import React from "react";
import { AbsoluteFill, Audio, Sequence, useCurrentFrame } from "remotion";

export type RenderSpec = {
  fps: number;
  duration_frames: number;
  scenes: Array<{
    scene_id: string;
    start_frame: number;
    end_frame: number;
    components: Array<{
      component: string;
      props: Record<string, unknown>;
      lifecycle: Array<Record<string, unknown>>;
      z: number;
    }>;
  }>;
};

export const RendererAdapter: React.FC<{spec: RenderSpec; audioSrc?: string}> = ({spec, audioSrc}) => (
  <AbsoluteFill>
    {audioSrc ? <Audio src={audioSrc} /> : null}
    {spec.scenes.map(scene => (
      <Sequence
        key={scene.scene_id}
        from={scene.start_frame}
        durationInFrames={scene.end_frame - scene.start_frame}
      >
        <AbsoluteFill>
          {/* Production implementation resolves each component through the registry. */}
        </AbsoluteFill>
      </Sequence>
    ))}
  </AbsoluteFill>
);
