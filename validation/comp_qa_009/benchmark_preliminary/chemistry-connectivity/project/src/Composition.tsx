import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQA5390384aff2bbd0d"}
      component={Scene}
      width={640}
      height={360}
      fps={24}
      durationInFrames={48}
      defaultProps={{...defaultProps}}
    />
  );
};
