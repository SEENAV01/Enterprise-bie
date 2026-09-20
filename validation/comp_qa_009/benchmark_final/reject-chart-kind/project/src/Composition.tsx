import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQA32f7458ea6000486"}
      component={Scene}
      width={640}
      height={360}
      fps={24}
      durationInFrames={48}
      defaultProps={{...defaultProps}}
    />
  );
};
