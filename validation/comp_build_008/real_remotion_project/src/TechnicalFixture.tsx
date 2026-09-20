import React from "react";
import {useCurrentFrame, interpolate} from "remotion";
import {BieReveal} from "./primitives";

export const TechnicalFixture: React.FC = () => {
  const frame = useCurrentFrame();
  const x = interpolate(frame, [0, 47], [50, 490], {extrapolateRight: "clamp"});
  return <BieReveal durationInFrames={12}>
    <div style={{fontFamily: "sans-serif", padding: 24, color: "black"}}>
      <h2>BIE compiler execution fixture</h2>
      <p>Technical test only — not an accepted learning video.</p>
      <div style={{position: "absolute", left: x, top: 195, width: 64, height: 64,
                   border: "4px solid black", transform: `rotate(${frame * 3}deg)`}} />
      <p style={{position: "absolute", bottom: 20}}>Frame {frame} / 47</p>
    </div>
  </BieReveal>;
};
