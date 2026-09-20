import React from "react";
import {interpolate, useCurrentFrame, useVideoConfig} from "remotion";
export const evaluateTrackStyle = (frame: number, fps: number): React.CSSProperties => {
  if (!Number.isInteger(frame) || frame < 0 || !Number.isInteger(fps) || fps < 1 || fps > 240) throw new Error("ANIMATION_FRAME_INVALID");
  const startFrame = Math.round((0 / 1000) * fps);
  const endFrame = Math.round((40 / 1000) * fps) - 1;
  if (endFrame <= startFrame) throw new Error("ANIMATION_FRAME_RANGE_COLLAPSES");
  
  const rawProgress = interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const progress = rawProgress;
  return {opacity: 0.0 + (1.0-0.0)*progress};
};
export const Track_h2_track_26ec4418: React.FC<React.PropsWithChildren> = ({children}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const style = evaluateTrackStyle(frame, fps);
  return <div data-bie-track-id={"h2-track"} data-bie-element-id={"e0"} data-bie-action={"enter"}
    style={{width: "100%", height: "100%", ...style}}>{children}</div>;
};
