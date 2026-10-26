// A whole video: scenes one after another, each with its own frame clock, plus the narration track.
import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { H, Scene, SceneSpec, W } from "./index";

export type VideoSpec = { fps: number; width: number; height: number; scenes: SceneSpec[]; audio?: string; captions?: boolean };

export const totalFrames = (v: VideoSpec) => v.scenes.reduce((n, s) => n + s.duration, 0);

/** The scenes compose at W × H (1920 × 1080); a smaller or larger output (a 720p review copy, a demo clip) is the same
 *  picture scaled as a whole, so every block, label and caption keeps its proportions (Task 046). */
export const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width, height } = useVideoConfig();
  const scale = Math.min(width / W, height / H);
  if (Math.abs(scale - 1) < 1e-6) return <>{children}</>;
  return (
    <div style={{ position: "absolute", left: (width - W * scale) / 2, top: (height - H * scale) / 2, width: W, height: H,
      transformOrigin: "0 0", transform: `scale(${scale})` }}>{children}</div>
  );
};

export const Video: React.FC<{ spec: VideoSpec }> = ({ spec }) => {
  let from = 0;
  return (
    <AbsoluteFill style={{ background: "#06121c" }}>
      {spec.audio ? <Audio src={staticFile(spec.audio)} /> : null}
      <Stage>
        {spec.scenes.map((s) => {
          const start = from;
          from += s.duration;
          return (
            <Sequence key={s.id} from={start} durationInFrames={s.duration}>
              <Scene spec={s} showCaptions={spec.captions !== false} />
            </Sequence>
          );
        })}
      </Stage>
    </AbsoluteFill>
  );
};
