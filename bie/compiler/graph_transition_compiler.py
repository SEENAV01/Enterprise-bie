from .animation_compiler_common import *

def compile_graph_transition(track):
    tid,eid,action,start_ms,end_ms,params,src,rsn=normalize_track(track)
    if action not in {"transform","crossfade_states","morph"}:
        raise AnimationCompilerError("graph transition action unsupported")
    start=params.get("from_points")
    end=params.get("to_points")
    if not isinstance(start,(list,tuple)) or not isinstance(end,(list,tuple)) or not start or not end:
        raise AnimationCompilerError("graph transition points required")
    start=[(float(p[0]),float(p[1])) for p in start]
    end=[(float(p[0]),float(p[1])) for p in end]
    comp=component_name("GraphTransition",tid)

    if len(start)==len(end):
        mode="interpolate"
        source=f"""import React from "react";
import {{interpolate, useCurrentFrame, useVideoConfig}} from "remotion";

const fromPoints = {jsx(start)} as const;
const toPoints = {jsx(end)} as const;

export const {comp}: React.FC = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  const startFrame = {ms_to_frame_expr(start_ms)};
  const endFrame = {ms_to_frame_expr(end_ms)};
  const progress = interpolate(frame, [startFrame, endFrame], [0, 1], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  const points = fromPoints.map(([x,y],i) => [
    x + (toPoints[i][0] - x) * progress,
    y + (toPoints[i][1] - y) * progress,
  ] as const);
  const d = points.map(([x,y],i) => `${{i === 0 ? "M" : "L"}} ${{40 + x * 300}} ${{200 - y * 150}}`).join(" ");

  return <svg viewBox="0 0 400 240"><path d={{d}} fill="none" stroke="currentColor" strokeWidth={{2}} /></svg>;
}};
"""
        warnings=()
    else:
        mode="crossfade"
        source=f"""import React from "react";
import {{interpolate, useCurrentFrame, useVideoConfig}} from "remotion";

const fromPoints = {jsx(start)} as const;
const toPoints = {jsx(end)} as const;

const pathFor = (points: readonly (readonly [number, number])[]) =>
  points.map(([x,y],i) => `${{i === 0 ? "M" : "L"}} ${{40 + x * 300}} ${{200 - y * 150}}`).join(" ");

export const {comp}: React.FC = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  const startFrame = {ms_to_frame_expr(start_ms)};
  const endFrame = {ms_to_frame_expr(end_ms)};
  const progress = interpolate(frame, [startFrame, endFrame], [0, 1], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});

  return (
    <svg viewBox="0 0 400 240">
      <path d={{pathFor(fromPoints)}} fill="none" stroke="currentColor" strokeWidth={{2}} opacity={{1-progress}} />
      <path d={{pathFor(toPoints)}} fill="none" stroke="currentColor" strokeWidth={{2}} opacity={{progress}} />
    </svg>
  );
}};
"""
        warnings=("graph_point_topology_mismatch_uses_crossfade_fallback",)
    return compile_result(tid,action,f"src/animations/{comp}.tsx",source,warnings=warnings)
