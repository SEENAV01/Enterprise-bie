import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import {TechnicalFixture} from "./TechnicalFixture";

export const Scene: React.FC = () => {
  return (
    <AbsoluteFill name="Scene" style={{backgroundColor: "white"}}>
      <Sequence name={"technical"} from={0} durationInFrames={48}>
        <TechnicalFixture {...({})} />
      </Sequence>
    </AbsoluteFill>
  );
};
