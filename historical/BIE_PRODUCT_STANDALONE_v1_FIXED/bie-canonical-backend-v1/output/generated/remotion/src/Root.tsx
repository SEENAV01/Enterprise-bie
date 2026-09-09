import React from "react";
import { Composition } from "remotion";
import { BIELesson } from "./BIELesson";

export const Root: React.FC = () => (
  <Composition
    id="BIELesson"
    component={BIELesson}
    durationInFrames={87}
    fps={30}
    width={1920}
    height={1080}
  />
);
