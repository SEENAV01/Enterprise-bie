import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import {QALayer_e0_5c88e7a2} from "./qa-layers/QALayer_e0_5c88e7a2";
import {QALayer_label_1aca80e8} from "./qa-layers/QALayer_label_1aca80e8";
import {QALayer_sim_507a9a8b} from "./qa-layers/QALayer_sim_507a9a8b";

export const Scene: React.FC = () => {
  return (
    <AbsoluteFill name="Scene" style={{backgroundColor: "white"}}>
      <Sequence name={"e0"} from={0} durationInFrames={72}>
        <QALayer_e0_5c88e7a2 {...({})} />
      </Sequence>
      <Sequence name={"label"} from={0} durationInFrames={72}>
        <QALayer_label_1aca80e8 {...({})} />
      </Sequence>
      <Sequence name={"sim"} from={0} durationInFrames={72}>
        <QALayer_sim_507a9a8b {...({})} />
      </Sequence>
    </AbsoluteFill>
  );
};
