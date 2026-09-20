import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQA819f9f77b5e272ca"}
      component={Scene}
      width={640}
      height={360}
      fps={24}
      durationInFrames={48}
      defaultProps={{...defaultProps}}
    />
  );
};
