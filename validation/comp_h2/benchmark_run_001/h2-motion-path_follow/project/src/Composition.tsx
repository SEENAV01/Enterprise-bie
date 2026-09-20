import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQA6f4ac74b0dca6d6a"}
      component={Scene}
      width={640}
      height={360}
      fps={24}
      durationInFrames={72}
      defaultProps={{...defaultProps}}
    />
  );
};
