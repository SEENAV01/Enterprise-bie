import React from "react";
import {Interactive} from "remotion";

const initialState = {"x": 0};

export const Simulation_e0_5c88e7a2: React.FC = () => {
  return (
    <Interactive.Div name={"e0"} role="region" aria-label={"Synthetic simulation compiler fixture"}>
      <pre data-model-ref={"fixture:toy-model"} data-execution-class={"conceptual"}>
        {JSON.stringify(initialState, null, 2)}
      </pre>
    </Interactive.Div>
  );
};
