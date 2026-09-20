"""H5-002 frame-indexed 2D orthographic camera, not a 3D perspective camera."""
from .animation_compiler_common import component_name, compile_result, jsx
from .specialized_motion import specialized_contract, fail


def progress_source(c):
    return f'''if (!Number.isInteger(frame) || frame < 0 || !Number.isInteger(fps) || fps < 1 || fps > 240) throw new Error("ANIMATION_FRAME_INVALID");
  const first = Math.round({c.start_ms}*fps/1000);
  const last = Math.round({c.end_ms}*fps/1000)-1;
  if (last <= first) throw new Error("ANIMATION_FRAME_RANGE_COLLAPSES");
  const u = Math.min(1, Math.max(0, (frame-first)/(last-first)));
  const progress = {('u*u*(3-2*u)' if c.easing == 'smoothstep' else 'u')};'''


def compile_specialized_camera(track, element=None, *, typesetter=None):
    c = specialized_contract(track)
    from .specialized_motion import validate_element_source
    from .animation_compiler_common import normalize_track
    fields = normalize_track(track)
    if element is None: fail('SPECIALIZED_TARGET_REQUIRED', 'source element required')
    validate_element_source(c, element, fields[6], fields[7])
    if c.action != 'camera': fail('SPECIALIZED_ACTION_MISMATCH', 'camera action required')
    p = c.parameters; name = component_name('Camera2D', c.track_id)
    source = f'''import React from "react";
import {{useCurrentFrame, useVideoConfig}} from "remotion";
const fromPose = {jsx(p['from'])};
const toPose = {jsx(p['to'])};
export const evaluateCamera = (frame: number, fps: number) => {{
  {progress_source(c)}
  const focusX = fromPose.focus_x + (toPose.focus_x-fromPose.focus_x)*progress;
  const focusY = fromPose.focus_y + (toPose.focus_y-fromPose.focus_y)*progress;
  const zoom = fromPose.zoom + (toPose.zoom-fromPose.zoom)*progress;
  return {{scale: zoom, translate_x: ({p['viewport']['width']}/2-focusX)*zoom,
    translate_y: ({p['viewport']['height']}/2-focusY)*zoom}};
}};
export const {name}: React.FC<React.PropsWithChildren> = ({{children}}) => {{
  const frame = useCurrentFrame(); const {{fps}} = useVideoConfig();
  const pose = evaluateCamera(frame, fps);
  return <div data-bie-track-id={{{jsx(c.track_id)}}} data-bie-action="camera"
    data-bie-camera-projection="orthographic-2d"
    style={{{{width:"100%", height:"100%", transformOrigin:"50% 50%", scale:pose.scale,
      translate:pose.translate_x+"px "+pose.translate_y+"px"}}}}>{{children}}</div>;
}};
'''
    return compile_result(c.track_id, c.action, f'src/animations/{name}.tsx', source)
