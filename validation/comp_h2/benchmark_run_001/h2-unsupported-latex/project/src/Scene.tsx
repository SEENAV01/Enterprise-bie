import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import {QALayer_e0_5c88e7a2} from "./qa-layers/QALayer_e0_5c88e7a2";

export const Scene: React.FC = () => {
  return (
    <AbsoluteFill name="Scene" style={{backgroundColor: "white"}}>
      <Sequence name={"e0"} from={0} durationInFrames={72}>
        <QALayer_e0_5c88e7a2 {...({})} />
      </Sequence>
    </AbsoluteFill>
  );
};
