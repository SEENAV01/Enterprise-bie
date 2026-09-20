import React from "react";
import {interpolate, useCurrentFrame, useVideoConfig} from "remotion";
export const evaluateTrackStyle = (frame: number, fps: number): React.CSSProperties => {
  if (!Number.isInteger(frame) || frame < 0 || !Number.isInteger(fps) || fps < 1 || fps > 240) throw new Error("ANIMATION_FRAME_INVALID");
  const startFrame = Math.round((0 / 1000) * fps);
  const endFrame = Math.round((1000 / 1000) * fps) - 1;
  if (endFrame <= startFrame) throw new Error("ANIMATION_FRAME_RANGE_COLLAPSES");
  
  const rawProgress = interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const progress = rawProgress;
  const points = [[0.0, 0.0], [20.0, 0.0], [20.0, 80.0]]; const lengths = [20.0, 80.0];
  const distance = progress * 100.0; let covered = 0;
  for (let i=0; i<lengths.length; i++) {
    if (distance <= covered+lengths[i] || i===lengths.length-1) {
      const ratio = Math.min(1, Math.max(0, (distance-covered)/lengths[i]));
      const x = points[i][0]+(points[i+1][0]-points[i][0])*ratio;
      const y = points[i][1]+(points[i+1][1]-points[i][1])*ratio;
      return {translate: x + "px " + y + "px"};
    } covered += lengths[i];
  } throw new Error("ANIMATION_PATH_INVALID");
};
export const Track_h2_track_26ec4418: React.FC<React.PropsWithChildren> = ({children}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const style = evaluateTrackStyle(frame, fps);
  return <div data-bie-track-id={"h2-track"} data-bie-element-id={"e0"} data-bie-action={"path_follow"}
    style={{width: "100%", height: "100%", ...style}}>{children}</div>;
};
