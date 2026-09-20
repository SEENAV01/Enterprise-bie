import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import {QALayer_e0_5c88e7a2} from "./qa-layers/QALayer_e0_5c88e7a2";
import {QALayer_h2e1_eeb4664e} from "./qa-layers/QALayer_h2e1_eeb4664e";
import {QALayer_h2e2_16d7da70} from "./qa-layers/QALayer_h2e2_16d7da70";

export const Scene: React.FC = () => {
  return (
    <AbsoluteFill name="Scene" style={{backgroundColor: "white"}}>
      <Sequence name={"e0"} from={0} durationInFrames={72}>
        <QALayer_e0_5c88e7a2 {...({})} />
      </Sequence>
      <Sequence name={"h2e1"} from={0} durationInFrames={72}>
        <QALayer_h2e1_eeb4664e {...({})} />
      </Sequence>
      <Sequence name={"h2e2"} from={0} durationInFrames={72}>
        <QALayer_h2e2_16d7da70 {...({})} />
      </Sequence>
    </AbsoluteFill>
  );
};
