import React from "react";
import {Composition} from "remotion";
import {ElectricChargeLesson} from "./ElectricChargeLesson";

export const Root: React.FC = () => (
  <Composition
    id="ElectricChargeLesson"
    component={ElectricChargeLesson}
    durationInFrames={2980}
    fps={30}
    width={1920}
    height={1080}
  />
);
