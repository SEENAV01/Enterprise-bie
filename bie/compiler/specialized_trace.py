"""H5-004. Bounded signed-data polyline tracing; axes and units are not animated away."""
from .animation_compiler_common import component_name, compile_result, jsx
from .specialized_motion import specialized_contract, graph_contract, fail
from .specialized_camera import progress_source


def compile_specialized_trace(track, element, *, typesetter=None):
    c = specialized_contract(track)
    from .specialized_motion import validate_element_source
    from .animation_compiler_common import normalize_track
    fields = normalize_track(track)
    if element is None: fail('SPECIALIZED_TARGET_REQUIRED', 'source element required')
    validate_element_source(c, element, fields[6], fields[7])
    if c.action != 'trace': fail('SPECIALIZED_ACTION_MISMATCH', 'trace action required')
    if element is None: fail('TRACE_TARGET_TYPE_MISMATCH', 'graph required')
    graph = graph_contract(element)
    selected = next((s for s in graph['series'] if s['series_id'] == c.parameters['series_id']), None)
    if selected is None: fail('TRACE_SERIES_MISSING', 'selected series not found')
    name = component_name('GraphTrace', c.track_id)
    x, y = graph['domains']['x'], graph['domains']['y']
    # Axis origin stays in the plot when zero is outside the domain; endpoint labels expose that fact.
    xzero = 48+(max(x[0], min(x[1], 0))-x[0])/(x[1]-x[0])*320
    yzero = 184-(max(y[0], min(y[1], 0))-y[0])/(y[1]-y[0])*150
    label = element.get('accessibility', {}).get('alt') or 'Source-bound graph trace'
    source = f'''import React from "react";
import {{useCurrentFrame, useVideoConfig}} from "remotion";
const graph = {jsx(graph)};
const selectedId = {jsx(c.parameters['series_id'])};
const selected = graph.series.find(s=>s.series_id===selectedId)!;
const pathFor = (points: number[][]) => points.map(([x,y],i)=>(i===0?"M":"L")+" "+x+" "+y).join(" ");
export const evaluateTrace = (frame: number, fps: number) => {{
  {progress_source(c)}
  if (progress===0 || progress===1) {{
    const i=progress===0?0:selected.points.length-1;
    return {{progress,head:[...selected.pixels[i]],data:[...selected.points[i]],dashOffset:1-progress}};
  }}
  const distance = progress*selected.total_length; let covered=0;
  for (let i=0;i<selected.lengths.length;i++) {{
    const length=selected.lengths[i];
    if (distance<=covered+length || i===selected.lengths.length-1) {{
      const r=Math.min(1,Math.max(0,(distance-covered)/length));
      const head=selected.pixels[i].map((v,k)=>v+(selected.pixels[i+1][k]-v)*r);
      const data=selected.points[i].map((v,k)=>v+(selected.points[i+1][k]-v)*r);
      return {{progress,head,data,dashOffset:1-progress}};
    }} covered+=length;
  }} throw new Error("TRACE_SERIES_INVALID");
}};
export const {name}: React.FC<React.PropsWithChildren> = () => {{
  const frame=useCurrentFrame(); const {{fps}}=useVideoConfig(); const state=evaluateTrace(frame,fps);
  return <svg data-bie-element-id={{{jsx(c.element_id)}}} data-bie-track-id={{{jsx(c.track_id)}}}
    data-bie-action="trace" data-bie-progress-model="screen-arc-length" role="img" aria-label={{{jsx(label)}}}
    viewBox={{{jsx(' '.join(str(v) for v in graph['viewbox']))}}} style={{{{width:"100%",height:"100%",display:"block"}}}}>
    <line x1={{48}} y1={{{yzero}}} x2={{368}} y2={{{yzero}}} stroke="currentColor" />
    <line x1={{{xzero}}} y1={{34}} x2={{{xzero}}} y2={{184}} stroke="currentColor" />
    <text x={{208}} y={{16}} textAnchor="middle" fontSize={{13}}>{{graph.y_label+" ["+graph.y_unit+"]"}}</text>
    <text x={{208}} y={{220}} textAnchor="middle" fontSize={{13}}>{{graph.x_label+" ["+graph.x_unit+"]"}}</text>
    <text x={{48}} y={{200}} fontSize={{11}}>{{String(graph.domains.x[0])}}</text>
    <text x={{368}} y={{200}} textAnchor="end" fontSize={{11}}>{{String(graph.domains.x[1])}}</text>
    <text x={{43}} y={{184}} textAnchor="end" fontSize={{11}}>{{String(graph.domains.y[0])}}</text>
    <text x={{43}} y={{39}} textAnchor="end" fontSize={{11}}>{{String(graph.domains.y[1])}}</text>
    {{graph.series.map(s=><path key={{s.series_id}} data-bie-series-id={{s.series_id}} d={{pathFor(s.pixels)}}
      pathLength={{1}} fill="none" stroke="currentColor" strokeWidth={{s.series_id===selectedId?2.5:1}}
      strokeLinecap="butt" strokeDasharray={{s.series_id===selectedId?"1":undefined}}
      strokeDashoffset={{s.series_id===selectedId?state.dashOffset:undefined}} />)}}
    {{{str(c.parameters['head_marker']).lower()} && state.progress>0 ? <circle data-bie-trace-head={{{jsx(c.track_id)}}}
      cx={{state.head[0]}} cy={{state.head[1]}} r={{3}} fill="currentColor" /> : null}}
    {{graph.series.map((s,i)=><text key={{s.series_id}} x={{48}} y={{240+i*16}} fontSize={{12}}>
      {{s.label+(s.series_id===selectedId?" (traced)":"")}}
    </text>)}}
  </svg>;
}};
'''
    return compile_result(c.track_id, c.action, f'src/animations/{name}.tsx', source)
