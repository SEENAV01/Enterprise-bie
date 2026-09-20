import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
const contract = {"accepted": false, "assumptions": "Constant acceleration in a Cartesian plane; no collision or boundary dynamics.", "axes": ["x (m)", "y (m)"], "duration_ms": 2000, "execution_class": "analytic_model", "initial_state": {"vx": 2.0, "vy": 4.0, "x": 0.0, "y": 0.0}, "model_ref": "bie.sim.constant-acceleration-2d@1", "parameters": {"ax": 0.0, "ay": -2.0}, "solver": "closed-form.v1", "start_ms": 0, "title": "Synthetic acceleration model", "trajectory_samples": 65, "units": {"ax": "m/s^2", "ay": "m/s^2", "t": "s", "vx": "m/s", "vy": "m/s", "x": "m", "y": "m"}, "view": [-1.0, 5.0, -1.0, 5.0]};
const initialState: Record<string, number> = {"vx": 2.0, "vy": 4.0, "x": 0.0, "y": 0.0};
const parameters: Record<string, number> = {"ax": 0.0, "ay": -2.0};
const units: Record<string, string> = {"ax": "m/s^2", "ay": "m/s^2", "t": "s", "vx": "m/s", "vy": "m/s", "x": "m", "y": "m"};
const trajectory = [[213.33333333333331, 255.0], [222.29166666666669, 250.6591796875], [231.25, 246.38671875], [240.20833333333331, 242.1826171875], [249.16666666666669, 238.046875], [258.125, 233.9794921875], [267.0833333333333, 229.98046875], [276.0416666666667, 226.0498046875], [285.0, 222.1875], [293.95833333333337, 218.3935546875], [302.91666666666663, 214.66796875], [311.875, 211.0107421875], [320.83333333333337, 207.421875], [329.79166666666663, 203.9013671875], [338.75, 200.44921875], [347.70833333333337, 197.0654296875], [356.66666666666663, 193.75], [365.625, 190.5029296875], [374.58333333333337, 187.32421875], [383.54166666666663, 184.2138671875], [392.5, 181.171875], [401.45833333333337, 178.1982421875], [410.41666666666663, 175.29296875], [419.375, 172.4560546875], [428.33333333333337, 169.6875], [437.29166666666663, 166.9873046875], [446.25, 164.35546875], [455.20833333333337, 161.7919921875], [464.16666666666663, 159.296875], [473.125, 156.8701171875], [482.08333333333337, 154.51171875], [491.04166666666663, 152.2216796875], [500.0, 150.0], [508.9583333333333, 147.8466796875], [517.9166666666667, 145.76171875], [526.875, 143.7451171875], [535.8333333333333, 141.796875], [544.7916666666667, 139.9169921875], [553.75, 138.10546875], [562.7083333333333, 136.3623046875], [571.6666666666667, 134.6875], [580.625, 133.0810546875], [589.5833333333333, 131.54296875], [598.5416666666667, 130.0732421875], [607.5, 128.671875], [616.4583333333333, 127.3388671875], [625.4166666666667, 126.07421875], [634.375, 124.8779296875], [643.3333333333333, 123.75], [652.2916666666667, 122.6904296875], [661.25, 121.69921875], [670.2083333333333, 120.7763671875], [679.1666666666667, 119.921875], [688.125, 119.1357421875], [697.0833333333333, 118.41796875], [706.0416666666667, 117.7685546875], [715.0, 117.1875], [723.9583333333333, 116.6748046875], [732.9166666666667, 116.23046875], [741.875, 115.8544921875], [750.8333333333333, 115.546875], [759.7916666666667, 115.3076171875], [768.75, 115.13671875], [777.7083333333333, 115.0341796875], [786.6666666666667, 115.0]];
export const evaluateSimulation = (t: number): Record<string, number> => {
  if (!Number.isFinite(t) || t < 0 || t > contract.duration_ms/1000) throw new Error("SIMULATION_TIME_OUT_OF_RANGE");
  const s = initialState; const p = parameters;
  const x = s.x + s.vx*t + 0.5*p.ax*t*t; const y = s.y + s.vy*t + 0.5*p.ay*t*t; return {t, x, y, vx: s.vx+p.ax*t, vy: s.vy+p.ay*t, plot_x: x, plot_y: y};
};
export const Simulation_e0_5c88e7a2: React.FC = () => {
  const frame = 48; const {fps} = useVideoConfig();
  const time = Math.min(contract.duration_ms/1000, Math.max(0, frame/fps-contract.start_ms/1000));
  const state = evaluateSimulation(time);
  const cx = 70 + (state.plot_x - -1.0) / 6.0 * 860;
  const cy = 290 - (state.plot_y - -1.0) / 6.0 * 210;
  return <svg viewBox="0 0 1000 400" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label={"Synthetic simulation compiler fixture"} data-model-ref={"bie.sim.constant-acceleration-2d@1"} data-execution-class="analytic_model">
    <title>{contract.title + ": " + contract.assumptions}</title>
    <text x={70} y={28} fontSize={20}>{contract.title}</text>
    <path d="M 70 80 L 70 290 L 930 290" fill="none" stroke="currentColor" />
    <polyline points={trajectory.map(p => p.join(",")).join(" ")} fill="none" stroke="currentColor" strokeWidth={2} strokeDasharray="4 4" />
    <circle data-bie-sim-marker="state" cx={cx} cy={cy} r={7} fill="currentColor" />
    <text x={70} y={55} fontSize={16}>{contract.axes[1] + " [" + contract.view[2] + ", " + contract.view[3] + "]"}</text>
    <text x={70} y={315} fontSize={16}>{contract.axes[0] + " [" + contract.view[0] + ", " + contract.view[1] + "]"}</text>
    <text x={70} y={343} fontSize={14}>{Object.entries(state).filter(([k]) => k !== "plot_x" && k !== "plot_y").map(([k,v]) => k + "=" + v.toPrecision(6) + " " + units[k]).join("; ")}</text>
    <text x={70} y={375} fontSize={13}>Analytic model; not an observed measurement. Dashed curve: full model trajectory.</text>
  </svg>;
};
