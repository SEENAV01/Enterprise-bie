"""Generate frame-evaluated analytic simulation geometry, not an initial-state dump."""
from .element_compiler_common import *
from .simulation_models import simulation_contract, evaluate_simulation, simulation_js_evaluator
from .hardening_contracts import literal_js_string, text_value


def compile_simulation_element(element):
    eid, props, acc, src, rsn = require_type(element, "simulation")
    c = simulation_contract(props)
    comp = component_name("Simulation", eid)
    trajectory = [evaluate_simulation(c, c.duration_ms/1000*i/(c.trajectory_samples-1)) for i in range(c.trajectory_samples)]
    xmin, xmax, ymin, ymax = c.view
    def project(state):
        return [70+(state["plot_x"]-xmin)/(xmax-xmin)*860, 290-(state["plot_y"]-ymin)/(ymax-ymin)*210]
    points = [project(s) for s in trajectory]
    source = f'''import React from "react";
import {{useCurrentFrame, useVideoConfig}} from "remotion";
const contract = {jsx(c.to_dict())};
const initialState: Record<string, number> = {jsx(dict(c.initial_state))};
const parameters: Record<string, number> = {jsx(dict(c.parameters))};
const units: Record<string, string> = {jsx(dict(c.units))};
const trajectory = {jsx(points)};
export const evaluateSimulation = (t: number): Record<string, number> => {{
  if (!Number.isFinite(t) || t < 0 || t > contract.duration_ms/1000) throw new Error("SIMULATION_TIME_OUT_OF_RANGE");
  const s = initialState; const p = parameters;
  {simulation_js_evaluator(c)}
}};
export const {comp}: React.FC = () => {{
  const frame = useCurrentFrame(); const {{fps}} = useVideoConfig();
  const time = Math.min(contract.duration_ms/1000, Math.max(0, frame/fps-contract.start_ms/1000));
  const state = evaluateSimulation(time);
  const cx = 70 + (state.plot_x - {xmin}) / {xmax-xmin} * 860;
  const cy = 290 - (state.plot_y - {ymin}) / {ymax-ymin} * 210;
  return <svg viewBox="0 0 1000 400" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label={{{literal_js_string(text_value(acc.get('alt') or c.title, 'simulation alt', maximum=2000))}}} data-model-ref={{{jsx(c.model_ref)}}} data-execution-class="analytic_model">
    <title>{{contract.title + ": " + contract.assumptions}}</title>
    <text x={{70}} y={{28}} fontSize={{20}}>{{contract.title}}</text>
    <path d="M 70 80 L 70 290 L 930 290" fill="none" stroke="currentColor" />
    <polyline points={{trajectory.map(p => p.join(",")).join(" ")}} fill="none" stroke="currentColor" strokeWidth={{2}} strokeDasharray="4 4" />
    <circle data-bie-sim-marker="state" cx={{cx}} cy={{cy}} r={{7}} fill="currentColor" />
    <text x={{70}} y={{55}} fontSize={{16}}>{{contract.axes[1] + " [" + contract.view[2] + ", " + contract.view[3] + "]"}}</text>
    <text x={{70}} y={{315}} fontSize={{16}}>{{contract.axes[0] + " [" + contract.view[0] + ", " + contract.view[1] + "]"}}</text>
    <text x={{70}} y={{343}} fontSize={{14}}>{{Object.entries(state).filter(([k]) => k !== "plot_x" && k !== "plot_y").map(([k,v]) => k + "=" + v.toPrecision(6) + " " + units[k]).join("; ")}}</text>
    <text x={{70}} y={{375}} fontSize={{13}}>Analytic model; not an observed measurement. Dashed curve: full model trajectory.</text>
  </svg>;
}};
'''
    return compile_result(eid, "simulation", comp, source)
