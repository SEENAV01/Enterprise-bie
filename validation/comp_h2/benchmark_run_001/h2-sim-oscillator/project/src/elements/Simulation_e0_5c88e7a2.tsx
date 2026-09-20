import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
const contract = {"accepted": false, "assumptions": "Undamped linear oscillator x'' + omega^2 x = 0; no external forcing.", "axes": ["t (s)", "x (m)"], "duration_ms": 2000, "execution_class": "analytic_model", "initial_state": {"v": 0.0, "x": 1.0}, "model_ref": "bie.sim.harmonic-oscillator-1d@1", "parameters": {"omega": 3.141592653589793}, "solver": "closed-form.v1", "start_ms": 0, "title": "Synthetic oscillator model", "trajectory_samples": 65, "units": {"omega": "rad/s", "t": "s", "v": "m/s", "x": "m"}, "view": [0.0, 2.0, -1.1, 1.1]};
const initialState: Record<string, number> = {"v": 0.0, "x": 1.0};
const parameters: Record<string, number> = {"omega": 3.141592653589793};
const units: Record<string, string> = {"omega": "rad/s", "t": "s", "v": "m/s", "x": "m"};
const trajectory = [[70.0, 89.54545454545456], [83.4375, 90.00509427219941], [96.875, 91.37958687060075], [110.3125, 93.65569522556186], [123.75, 96.81149916937721], [137.1875, 100.81660658492976], [150.625, 105.63244609839339], [164.0625, 111.21263854264785], [177.5, 117.50344361401139], [190.9375, 124.44427742074294], [204.375, 131.96829593903797], [217.8125, 140.0030387575184], [231.25, 148.47112691060505], [244.6875, 157.29100808025586], [258.125, 166.37774198936955], [271.5625, 175.6438184230874], [285.0, 185.0], [298.4375, 194.3561815769126], [311.875, 203.62225801063042], [325.3125, 212.7089919197441], [338.75, 221.52887308939492], [352.1875, 229.9969612424816], [365.625, 238.031704060962], [379.0625, 245.55572257925706], [392.5, 252.4965563859886], [405.9375, 258.7873614573522], [419.375, 264.3675539016066], [432.8125, 269.1833934150702], [446.25, 273.18850083062284], [459.6875, 276.3443047744381], [473.125, 278.62041312939925], [486.5625, 279.9949057278006], [500.0, 280.45454545454544], [513.4375, 279.9949057278006], [526.875, 278.62041312939925], [540.3125, 276.3443047744381], [553.75, 273.18850083062284], [567.1875, 269.18339341507027], [580.625, 264.3675539016066], [594.0625, 258.7873614573522], [607.5, 252.49655638598864], [620.9375, 245.55572257925712], [634.375, 238.03170406096203], [647.8125, 229.99696124248163], [661.25, 221.52887308939498], [674.6875, 212.70899191974416], [688.125, 203.62225801063045], [701.5625, 194.3561815769126], [715.0, 185.00000000000003], [728.4375, 175.64381842308745], [741.875, 166.37774198936955], [755.3125, 157.2910080802559], [768.75, 148.47112691060502], [782.1875, 140.00303875751842], [795.625, 131.96829593903803], [809.0625, 124.4442774207429], [822.5, 117.50344361401139], [835.9375, 111.21263854264788], [849.375, 105.63244609839339], [862.8125, 100.81660658492976], [876.25, 96.81149916937721], [889.6875, 93.65569522556186], [903.125, 91.37958687060075], [916.5625, 90.00509427219941], [930.0, 89.54545454545456]];
export const evaluateSimulation = (t: number): Record<string, number> => {
  if (!Number.isFinite(t) || t < 0 || t > contract.duration_ms/1000) throw new Error("SIMULATION_TIME_OUT_OF_RANGE");
  const s = initialState; const p = parameters;
  const x = s.x*Math.cos(p.omega*t) + s.v/p.omega*Math.sin(p.omega*t); const v = -s.x*p.omega*Math.sin(p.omega*t) + s.v*Math.cos(p.omega*t); return {t, x, v, plot_x: t, plot_y: x};
};
export const Simulation_e0_5c88e7a2: React.FC = () => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const time = Math.min(contract.duration_ms/1000, Math.max(0, frame/fps-contract.start_ms/1000));
  const state = evaluateSimulation(time);
  const cx = 70 + (state.plot_x - 0.0) / 2.0 * 860;
  const cy = 290 - (state.plot_y - -1.1) / 2.2 * 210;
  return <svg viewBox="0 0 1000 400" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label={"Synthetic simulation compiler fixture"} data-model-ref={"bie.sim.harmonic-oscillator-1d@1"} data-execution-class="analytic_model">
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
