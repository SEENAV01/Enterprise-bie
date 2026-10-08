"""Frame-indexed M1 realization; target geometry/content are never transformed."""
from .animation_compiler_common import component_name, compile_result, jsx, ms_to_frame_expr
from .governed_motion import validate_element


def compile_governed_track(track, element):
    c = validate_element(track, element)
    name = component_name("Track", c.track_id)
    chart = c.parameters["binding"]["element_type"] == "chart"
    property_name = "series_opacity" if chart else "opacity"
    expression = ('{' + property_name + ': 1-Math.pow(1-u,3)>=0.5 ? 1 : 0}' if c.action == "reveal" else
        '{focus_opacity: 1-Math.abs(2*(u*u*(3-2*u))-1)}')
    chart_effect = ''
    if chart:
        # The canonical chart emitter owns the chart/axes/text. This wrapper
        # only controls its exact native bar nodes, at the committed frame.
        # useLayoutEffect runs on the React commit before browser paint; there
        # is no timer, CSS animation, interpolation of values, or axis clipping.
        chart_effect = f'''
  const root=React.useRef<HTMLDivElement>(null);
  React.useLayoutEffect(()=>{{
    const bars=Array.from(root.current?.querySelectorAll<SVGRectElement>("rect[data-value]")||[]);
    const expected:number[]={jsx(element['props']['values'])};
    if(bars.length!==expected.length||bars.some((bar,i)=>Number(bar.getAttribute("data-value"))!==expected[i])) throw new Error("M1_NATIVE_BAR_BINDING");
    for(const bar of bars)bar.style.opacity=String(state.series_opacity);
  }},[state.series_opacity]);'''
    # Two static contrasting borders are INSIDE an independently verified empty
    # gutter. Only their opacity changes. They cannot replace semantic colors,
    # rescale a cell, cover a label, or imply transport. No CSS time animation.
    focus = '''<div aria-hidden="true" data-bie-focus-indicator="m1"
      style={{position:"absolute",inset:2,border:"2px solid black",boxSizing:"border-box",pointerEvents:"none",opacity:state.focus_opacity}} />
    <div aria-hidden="true" data-bie-focus-indicator="m1-inner"
      style={{position:"absolute",inset:4,border:"2px solid white",boxSizing:"border-box",pointerEvents:"none",opacity:state.focus_opacity}} />'''
    source = f'''import React from "react";
import {{useCurrentFrame,useVideoConfig}} from "remotion";
export const evaluateTrackState = (frame:number,fps:number): {{opacity?:number;series_opacity?:number;focus_opacity?:number}} => {{
  if (!Number.isInteger(frame)||frame<0||!Number.isInteger(fps)||fps<1||fps>240) throw new Error("ANIMATION_FRAME_INVALID");
  const a={ms_to_frame_expr(c.start_ms)}; const b={ms_to_frame_expr(c.end_ms)}-1;
  if(b<=a) throw new Error("ANIMATION_FRAME_RANGE_COLLAPSES");
  {'if(b-a<2) throw new Error("ANIMATION_PULSE_UNSAMPLED");' if c.action == 'emphasize' else ''}
  const u=Math.min(1,Math.max(0,(frame-a)/(b-a)));
  return {expression};
}};
export const evaluateTrackStyle = (frame:number,fps:number):React.CSSProperties => {{
  const state=evaluateTrackState(frame,fps);
  return {'{opacity:state.opacity}' if c.action == 'reveal' and not chart else '{}'};
}};
export const {name}:React.FC<React.PropsWithChildren> = ({{children}}) => {{
  const frame=useCurrentFrame();const {{fps}}=useVideoConfig();
  const state=evaluateTrackState(frame,fps);
  {chart_effect}
  return <div {'ref={root}' if chart else ''} data-bie-track-id={{{jsx(c.track_id)}}} data-bie-element-id={{{jsx(c.element_id)}}}
    data-bie-action={{{jsx(c.action)}}} data-bie-motion-variant={{{jsx(c.parameters['variant'])}}}
    style={{{{width:"100%",height:"100%",position:"relative",...evaluateTrackStyle(frame,fps)}}}}>
    {{children}}
    {focus if c.action == 'emphasize' else ''}
  </div>;
}};
'''
    return compile_result(c.track_id, c.action, f"src/animations/{name}.tsx", source)
