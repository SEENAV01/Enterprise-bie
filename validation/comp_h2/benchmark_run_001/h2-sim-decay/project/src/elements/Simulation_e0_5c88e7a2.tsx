import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
const contract = {"accepted": false, "assumptions": "Continuous nonnegative state satisfying n' = -rate*n; not individual stochastic events.", "axes": ["t (s)", "n (dimensionless)"], "duration_ms": 2000, "execution_class": "analytic_model", "initial_state": {"n": 10.0}, "model_ref": "bie.sim.exponential-decay@1", "parameters": {"rate": 0.5}, "solver": "closed-form.v1", "start_ms": 0, "title": "Synthetic decay model", "trajectory_samples": 65, "units": {"n": "1", "rate": "1/s", "t": "s"}, "view": [0.0, 2.0, 0.0, 11.0]};
const initialState: Record<string, number> = {"n": 10.0};
const parameters: Record<string, number> = {"rate": 0.5};
const units: Record<string, string> = {"n": "1", "rate": "1/s", "t": "s"};
const trajectory = [[70.0, 99.0909090909091], [83.4375, 102.0506802080584], [96.875, 104.96456432724338], [110.3125, 107.83327286042766], [123.75, 110.65750619015463], [137.1875, 113.43795384054272], [150.625, 116.17529464562983], [164.0625, 118.87019691510764], [177.5, 121.52331859748634], [190.9375, 124.13530744072995], [204.375, 126.70680115040113], [217.8125, 129.23842754535426], [231.25, 131.73080471101446], [244.6875, 134.18454115028058], [258.125, 136.6002359320884], [271.5625, 138.9784788376708], [285.0, 141.31985050454998], [298.4375, 143.624922568298], [311.875, 145.8942578020986], [325.3125, 148.12841025414613], [338.75, 150.32792538291383], [352.1875, 152.4933401903251], [365.625, 154.62518335286032], [379.0625, 156.72397535063055], [392.5, 158.79022859445075], [405.9375, 160.82444755094266], [419.375, 162.82712886569777], [432.8125, 164.7987614845315], [446.25, 166.739826772857], [459.6875, 168.65079863320824], [473.125, 170.53214362094167], [486.5625, 172.38432105814326], [500.0, 174.20778314577], [513.4375, 176.00297507405293], [526.875, 177.7703351311884], [540.3125, 179.5102948103439], [553.75, 181.2232789150056], [567.1875, 182.90970566269195], [580.625, 184.56998678705975], [594.0625, 186.20452763842718], [607.5, 187.81372728273823], [620.9375, 189.39797859899284], [634.375, 190.95766837516658], [647.8125, 192.49317740264343], [661.25, 194.004880569184], [674.6875, 195.493146950453], [688.125, 196.95833990012727], [701.5625, 198.400817138607], [715.0, 199.82093084035174], [728.4375, 201.21902771986197], [741.875, 202.59544911632818], [755.3125, 203.95053107696717], [768.75, 205.28460443906658], [782.1875, 206.59799491075725], [795.625, 207.89102315053358], [809.0625, 209.16400484554072], [822.5, 210.4172507886484], [835.9375, 211.65106695432937], [849.375, 212.86575457336198], [862.8125, 214.06161020637413], [876.25, 215.23892581624744], [889.6875, 216.39798883939864], [903.125, 217.53908225595563], [916.5625, 218.66248465884635], [930.0, 219.76847032181556]];
export const evaluateSimulation = (t: number): Record<string, number> => {
  if (!Number.isFinite(t) || t < 0 || t > contract.duration_ms/1000) throw new Error("SIMULATION_TIME_OUT_OF_RANGE");
  const s = initialState; const p = parameters;
  const n = s.n*Math.exp(-p.rate*t); return {t, n, plot_x: t, plot_y: n};
};
export const Simulation_e0_5c88e7a2: React.FC = () => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const time = Math.min(contract.duration_ms/1000, Math.max(0, frame/fps-contract.start_ms/1000));
  const state = evaluateSimulation(time);
  const cx = 70 + (state.plot_x - 0.0) / 2.0 * 860;
  const cy = 290 - (state.plot_y - 0.0) / 11.0 * 210;
  return <svg viewBox="0 0 1000 400" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label={"Synthetic simulation compiler fixture"} data-model-ref={"bie.sim.exponential-decay@1"} data-execution-class="analytic_model">
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
