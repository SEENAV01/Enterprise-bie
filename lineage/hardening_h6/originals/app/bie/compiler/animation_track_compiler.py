"""Frame-driven, visually applied generic tracks under explicit H2 contracts."""
from .animation_compiler_common import *
from .animation_behavior import motion_contract, SUPPORTED_ACTIONS


def compile_animation_track(track, *, element=None, typesetter=None):
    from .specialized_motion import is_specialized
    if is_specialized(track):
        from .specialized_dispatch import compile_specialized_track
        return compile_specialized_track(track, element, typesetter=typesetter)
    c = motion_contract(track)
    comp = component_name("Track", c.track_id)
    p = c.parameters
    if c.action in {"enter", "exit"}:
        body = f'return {{opacity: {p["from_opacity"]} + ({p["to_opacity"]}-{p["from_opacity"]})*progress}};'
    elif c.action == "reveal":
        idx = {"left": 1, "right": 3, "up": 2, "down": 0}[p["direction"]]
        body = f'const inset = [0,0,0,0]; inset[{idx}] = 100*(1-progress); return {{clipPath: "inset(" + inset.map(v => v + "%").join(" ") + ")"}};'
    elif c.action == "emphasize":
        body = f'return {{scale: 1 + ({p["peak_scale"]}-1)*(1-Math.abs(2*progress-1)), transformOrigin: "50% 50%"}};'
    elif c.action == "transform":
        values = {k: f'({v}+({p["to"][k]}-{v})*progress)' for k, v in p["from"].items()}
        styles = []
        for k in ("opacity", "scale", "rotate"):
            if k in values: styles.append(k + ": " + values[k] + (' + "deg"' if k == "rotate" else ""))
        if any(k in values for k in ("translate_x", "translate_y")):
            styles.append('translate: ' + values.get("translate_x", "0") + ' + "px " + ' + values.get("translate_y", "0") + ' + "px"')
        body = 'return {' + ", ".join(styles) + '};'
    else:
        body = f'''const points = {jsx(p["points"])}; const lengths = {jsx(p["lengths"])};
  const distance = progress * {p["total_length"]}; let covered = 0;
  for (let i=0; i<lengths.length; i++) {{
    if (distance <= covered+lengths[i] || i===lengths.length-1) {{
      const ratio = Math.min(1, Math.max(0, (distance-covered)/lengths[i]));
      const x = points[i][0]+(points[i+1][0]-points[i][0])*ratio;
      const y = points[i][1]+(points[i+1][1]-points[i][1])*ratio;
      return {{translate: x + "px " + y + "px"}};
    }} covered += lengths[i];
  }} throw new Error("ANIMATION_PATH_INVALID");'''
    pulse_check = 'if (endFrame-startFrame < 2) throw new Error("ANIMATION_PULSE_UNSAMPLED");' if c.action == "emphasize" else ""
    source = f'''import React from "react";
import {{interpolate, useCurrentFrame, useVideoConfig}} from "remotion";
export const evaluateTrackStyle = (frame: number, fps: number): React.CSSProperties => {{
  if (!Number.isInteger(frame) || frame < 0 || !Number.isInteger(fps) || fps < 1 || fps > 240) throw new Error("ANIMATION_FRAME_INVALID");
  const startFrame = {ms_to_frame_expr(c.start_ms)};
  const endFrame = {ms_to_frame_expr(c.end_ms)} - 1;
  if (endFrame <= startFrame) throw new Error("ANIMATION_FRAME_RANGE_COLLAPSES");
  {pulse_check}
  const rawProgress = interpolate(frame, [startFrame, endFrame], [0, 1], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  const progress = {('rawProgress*rawProgress*(3-2*rawProgress)' if c.easing == 'smoothstep' else 'rawProgress')};
  {body}
}};
export const {comp}: React.FC<React.PropsWithChildren> = ({{children}}) => {{
  const frame = useCurrentFrame(); const {{fps}} = useVideoConfig();
  const style = evaluateTrackStyle(frame, fps);
  return <div data-bie-track-id={{{jsx(c.track_id)}}} data-bie-element-id={{{jsx(c.element_id)}}} data-bie-action={{{jsx(c.action)}}}
    style={{{{width: "100%", height: "100%", ...style}}}}>{{children}}</div>;
}};
'''
    return compile_result(c.track_id, c.action, f"src/animations/{comp}.tsx", source)
