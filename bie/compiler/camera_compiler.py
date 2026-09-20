from .animation_compiler_common import *

def compile_camera_track(track):
    tid,eid,action,start_ms,end_ms,params,src,rsn=normalize_track(track)
    if action!="camera":
        raise AnimationCompilerError("camera compiler requires camera action")
    start=params.get("from",{})
    end=params.get("to",{})
    def pose(raw):
        raw=dict(raw or {})
        return (
            float(raw.get("x",0)),
            float(raw.get("y",0)),
            float(raw.get("scale",1)),
            float(raw.get("rotation_deg",0)),
        )
    sx,sy,ss,sr=pose(start)
    ex,ey,es,er=pose(end)
    if ss<=0 or es<=0:
        raise AnimationCompilerError("camera scale must be positive")
    comp=component_name("Camera",tid)
    source=f"""import React from "react";
import {{Easing, interpolate, useCurrentFrame, useVideoConfig}} from "remotion";

export const {comp}: React.FC<React.PropsWithChildren> = ({{children}}) => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  const startFrame = {ms_to_frame_expr(start_ms)};
  const endFrame = {ms_to_frame_expr(end_ms)};

  return (
    <div
      style={{{{
        width: "100%",
        height: "100%",
        translate: interpolate(frame, [startFrame, endFrame], [{jsx(f"{sx}px {sy}px")}, {jsx(f"{ex}px {ey}px")}], {{
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }}),
        scale: interpolate(frame, [startFrame, endFrame], [{ss}, {es}], {{
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.16, 1, 0.3, 1),
          output: "perceptual-scale",
        }}),
        rotate: interpolate(frame, [startFrame, endFrame], [{jsx(f"{sr}deg")}, {jsx(f"{er}deg")}], {{
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }}),
      }}}}
    >
      {{children}}
    </div>
  );
}};
"""
    return compile_result(tid,action,f"src/animations/{comp}.tsx",source)
