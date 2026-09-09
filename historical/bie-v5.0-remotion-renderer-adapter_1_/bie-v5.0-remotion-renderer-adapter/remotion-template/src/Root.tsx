import React from "react";
import { Composition } from "remotion";

export const Root: React.FC = () => {
  return (
    <Composition
      id="BookLesson"
      component={() => <div />}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
