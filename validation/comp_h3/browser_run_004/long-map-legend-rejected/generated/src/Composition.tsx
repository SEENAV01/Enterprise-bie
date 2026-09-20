import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQA9780e3ed9667e463"}
      component={Scene}
      width={1280}
      height={720}
      fps={24}
      durationInFrames={24}
      defaultProps={{...defaultProps}}
    />
  );
};
