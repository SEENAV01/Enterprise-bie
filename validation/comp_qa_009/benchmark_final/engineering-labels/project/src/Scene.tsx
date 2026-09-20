import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import {QALayer_e0_5c88e7a2} from "./qa-layers/QALayer_e0_5c88e7a2";
import {QALayer_e1_8b5cc4df} from "./qa-layers/QALayer_e1_8b5cc4df";

export const Scene: React.FC = () => {
  return (
    <AbsoluteFill name="Scene" style={{backgroundColor: "white"}}>
      <Sequence name={"e0"} from={0} durationInFrames={48}>
        <QALayer_e0_5c88e7a2 {...({})} />
      </Sequence>
      <Sequence name={"e1"} from={0} durationInFrames={48}>
        <QALayer_e1_8b5cc4df {...({})} />
      </Sequence>
    </AbsoluteFill>
  );
};
