import React from "react";
import {AbsoluteFill, Sequence, useCurrentFrame} from "remotion";

const Scene = ({title, body}: {title: string; body: string}) => {
  const frame = useCurrentFrame();
  const opacity = Math.min(1, frame / 15);
  return (
    <AbsoluteFill style={{
      justifyContent: "center",
      alignItems: "center",
      padding: 100,
      fontFamily: "Arial",
      opacity
    }}>
      <div>
        <h1 style={{fontSize: 72, marginBottom: 30}}>{title}</h1>
        <p style={{fontSize: 42, maxWidth: 1500}}>{body}</p>
      </div>
    </AbsoluteFill>
  );
};

export const BIELesson: React.FC = () => (
  <AbsoluteFill>
    <Sequence from={0} durationInFrames={90}>
      <Scene title="Electric Charge" body="Electric charge is a property of matter." />
    </Sequence>
    <Sequence from={90} durationInFrames={90}>
      <Scene title="Interaction" body="Like charges repel and unlike charges attract." />
    </Sequence>
  </AbsoluteFill>
);
