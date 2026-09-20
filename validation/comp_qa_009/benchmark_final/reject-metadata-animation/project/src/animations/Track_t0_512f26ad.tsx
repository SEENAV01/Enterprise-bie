import React from "react";
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from "remotion";

export const Track_t0_512f26ad: React.FC<React.PropsWithChildren> = ({children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const startFrame = Math.round((0 / 1000) * fps);
  const endFrame = Math.round((1000 / 1000) * fps);
  const progress = interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <div
      data-bie-track-id={"t0"}
      data-bie-element-id={"e0"}
      data-bie-action={"reveal"}
      data-bie-progress={progress}
    >
      {children}
    </div>
  );
};
