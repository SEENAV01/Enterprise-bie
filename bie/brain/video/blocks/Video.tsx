// A whole video: scenes one after another, each with its own frame clock, plus the narration track.
import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Scene, SceneSpec } from "./index";

export type VideoSpec = { fps: number; width: number; height: number; scenes: SceneSpec[]; audio?: string; captions?: boolean };

export const totalFrames = (v: VideoSpec) => v.scenes.reduce((n, s) => n + s.duration, 0);

export const Video: React.FC<{ spec: VideoSpec }> = ({ spec }) => {
  let from = 0;
  return (
    <AbsoluteFill style={{ background: "#06121c" }}>
      {spec.audio ? <Audio src={staticFile(spec.audio)} /> : null}
      {spec.scenes.map((s) => {
        const start = from;
        from += s.duration;
        return (
          <Sequence key={s.id} from={start} durationInFrames={s.duration}>
            <Scene spec={s} showCaptions={spec.captions !== false} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
