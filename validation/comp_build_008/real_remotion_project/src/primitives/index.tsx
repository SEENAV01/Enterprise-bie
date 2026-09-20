import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const BieAbsoluteScene: React.FC<React.PropsWithChildren<{
  backgroundColor?: string;
}>> = ({backgroundColor = "white", children}) => {
  return (
    <AbsoluteFill style={{backgroundColor}}>
      {children}
    </AbsoluteFill>
  );
};

export const BieReveal: React.FC<React.PropsWithChildren<{
  fromFrame?: number;
  durationInFrames?: number;
}>> = ({fromFrame = 0, durationInFrames = 15, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const safeDuration = Math.max(1, durationInFrames);

  return (
    <div
      style={{
        opacity: interpolate(
          frame,
          [fromFrame, fromFrame + safeDuration],
          [0, 1],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          },
        ),
      }}
      data-bie-fps={fps}
    >
      {children}
    </div>
  );
};
