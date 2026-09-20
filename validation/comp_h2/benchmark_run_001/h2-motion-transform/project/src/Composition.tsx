import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQAb8e2599f7c263501"}
      component={Scene}
      width={640}
      height={360}
      fps={24}
      durationInFrames={72}
      defaultProps={{...defaultProps}}
    />
  );
};
