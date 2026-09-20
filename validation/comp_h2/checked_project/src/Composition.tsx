import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQA34a0e4e252d23787"}
      component={Scene}
      width={640}
      height={360}
      fps={24}
      durationInFrames={72}
      defaultProps={{...defaultProps}}
    />
  );
};
