from .animation_compiler_common import *

def compile_equation_morph(track):
    tid,eid,action,start_ms,end_ms,params,src,rsn=normalize_track(track)
    if action!="morph":
        raise AnimationCompilerError("equation morph requires morph action")
    states=params.get("states")
    if not isinstance(states,(list,tuple)) or len(states)<2:
        raise AnimationCompilerError("equation morph requires >=2 states")
    states=[str(x) for x in states]
    if any(not x for x in states):
        raise AnimationCompilerError("equation morph states must be nonblank")
    comp=component_name("EquationMorph",tid)
    source=f"""import React from "react";
import {{interpolate, useCurrentFrame, useVideoConfig}} from "remotion";

const states = {jsx(states)} as const;

export const {comp}: React.FC = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  const startFrame = {ms_to_frame_expr(start_ms)};
  const endFrame = {ms_to_frame_expr(end_ms)};
  const progress = interpolate(frame, [startFrame, endFrame], [0, states.length - 1], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  const lower = Math.floor(progress);
  const upper = Math.min(states.length - 1, lower + 1);
  const local = progress - lower;

  return (
    <div role="math" data-bie-equation-target={{{jsx(eid)}}} style={{{{position: "relative"}}}}>
      <div style={{{{opacity: 1 - local}}}}>{{states[lower]}}</div>
      {{upper !== lower ? (
        <div style={{{{position: "absolute", inset: 0, opacity: local}}}}>{{states[upper]}}</div>
      ) : null}}
    </div>
  );
}};
"""
    return compile_result(
        tid,action,f"src/animations/{comp}.tsx",source,
        warnings=("semantic_equation_morph_uses_crossfade_states_unless_symbol_mapping_is_available",)
    )
