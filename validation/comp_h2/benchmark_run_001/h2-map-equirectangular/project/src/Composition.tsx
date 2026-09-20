import React from "react";
import {Composition} from "remotion";
import {Scene} from "./Scene";

const defaultProps = {} as const;

export const BieComposition: React.FC = () => {
  return (
    <Composition
      id={"BieQAc2d2b9afc6bd4807"}
      component={Scene}
      width={640}
      height={360}
      fps={24}
      durationInFrames={72}
      defaultProps={{...defaultProps}}
    />
  );
};
