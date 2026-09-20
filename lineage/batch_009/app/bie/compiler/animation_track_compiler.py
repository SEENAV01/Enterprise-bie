from .animation_compiler_common import *

SUPPORTED_ACTIONS={
    "enter","exit","emphasize","reveal","transform","morph","trace",
    "path_follow","camera","simulation_state","static_focus","static_trace",
    "crossfade_states","state_snapshots","progressive_static_trace",
    "path_endpoints_with_progress_marker"
}

def compile_animation_track(track):
    tid,eid,action,start_ms,end_ms,params,src,rsn=normalize_track(track)
    if action not in SUPPORTED_ACTIONS:
        raise AnimationCompilerError("unsupported animation action")
    comp=component_name("Track",tid)
    source=f"""import React from "react";
import {{Easing, interpolate, useCurrentFrame, useVideoConfig}} from "remotion";

export const {comp}: React.FC<React.PropsWithChildren> = ({{children}}) => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  const startFrame = {ms_to_frame_expr(start_ms)};
  const endFrame = {ms_to_frame_expr(end_ms)};
  const progress = interpolate(frame, [startFrame, endFrame], [0, 1], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  }});

  return (
    <div
      data-bie-track-id={{{jsx(tid)}}}
      data-bie-element-id={{{jsx(eid)}}}
      data-bie-action={{{jsx(action)}}}
      data-bie-progress={{progress}}
    >
      {{children}}
    </div>
  );
}};
"""
    return compile_result(tid,action,f"src/animations/{comp}.tsx",source)
