"""H4-002: real, opt-in presentation adapters with no textual content reduction.

Legacy generated output remains byte-identical unless compiler_layout is supplied.
No overflow clipping, font shrinking, ellipsis, CSS animations or raw HTML occur.
"""
from __future__ import annotations
from .element_compiler_common import compile_result, component_name, jsx, require_type
from .hardening_contracts import literal_child, literal_js_string, text_value, known_properties
from .layout_repair_contracts import presentation
from .map_geometry import map_geometry


def compile_reflow_text(element):
    eid, props, acc, _, _ = require_type(element, "text")
    known_properties(props, {"text", "role", "compiler_layout"})
    layout = presentation("text", props["compiler_layout"])
    text = text_value(props.get("text"), "text")
    comp = component_name("Text", eid)
    role = text_value(props.get("role", "body"), "text role", maximum=100)
    style = {"boxSizing": "border-box", "width": "100%", "minWidth": 0,
             "whiteSpace": "pre-wrap", "overflowWrap": "anywhere",
             "fontSize": layout["font_px"], "lineHeight": layout["line_height"],
             "padding": layout["padding_px"]}
    source = f'''import React from "react";
import {{Interactive}} from "remotion";
export const {comp}: React.FC = () => {{
  return <Interactive.Div name={{{jsx(eid)}}} role="text" dir="auto"
    aria-label={{{literal_js_string(acc.get('alt') or text)}}} data-role={{{jsx(role)}}}
    data-bie-text-id={{{jsx(eid + ':text')}}} style={{{jsx(style)}}}>
    {literal_child(text)}
  </Interactive.Div>;
}};
'''
    return compile_result(eid, "text", comp, source)


def compile_reflow_map(element):
    eid, props, acc, _, _ = require_type(element, "map")
    props = dict(props)
    layout = presentation("map", props.pop("compiler_layout"))
    geometry = map_geometry(props)
    comp = component_name("Map", eid)
    style = {"width": "100%", "minWidth": 0, "boxSizing": "border-box", "margin": 0,
             "padding": layout["padding_px"], "fontSize": layout["font_px"],
             "lineHeight": layout["line_height"], "overflowWrap": "anywhere"}
    legend = {"display": "grid", "gridTemplateColumns": f'repeat({layout["legend_columns"]}, minmax(0, 1fr))',
              "columnGap": 12, "rowGap": 4, "padding": 0, "margin": 0, "listStyle": "none"}
    source = f'''import React from "react";
const geometry = {jsx(geometry.to_dict())};
const legendPrefix = {jsx(eid + ":legend:")};
export const {comp}: React.FC = () => {{
  return <figure data-bie-reflow="map" style={{{jsx(style)}}}>
    <figcaption dir="auto" data-bie-text-id={{{jsx(eid + ':title')}}}>{{geometry.title}}</figcaption>
    <div dir="auto" data-bie-text-id={{{jsx(eid + ':context')}}}>{{geometry.projection + "; axes=" + geometry.axis_order + "; extent=" + geometry.extent.join(", ")}}</div>
    <svg viewBox="0 0 1000 500" width="100%" height={{{layout['plot_height_px']}}}
      style={{{{display: "block"}}}} preserveAspectRatio="xMidYMid meet" role="img"
      aria-label={{{literal_js_string(text_value(acc.get('alt') or geometry.title, 'map alt', maximum=2000))}}}
      data-crs={{{jsx(geometry.source_crs)}}} data-projection={{{jsx(geometry.projection)}}}>
      <title>{{geometry.title}}</title>
      {{geometry.layers.filter(layer => layer.kind === "route").map(layer => <polyline key={{layer.layer_id}} data-layer-id={{layer.layer_id}} points={{layer.pixels.map(p => p.join(",")).join(" ")}} fill="none" stroke="currentColor" strokeWidth={{3}} />)}}
      {{geometry.layers.filter(layer => layer.kind === "point").map(layer => <g key={{layer.layer_id}} data-layer-id={{layer.layer_id}}><circle cx={{layer.pixels[0][0]}} cy={{layer.pixels[0][1]}} r={{6}} fill="currentColor" /><title>{{layer.label}}</title></g>)}}
      {{geometry.layers.filter(layer => layer.kind === "polygon").map(layer => <polygon key={{layer.layer_id}} data-layer-id={{layer.layer_id}} points={{layer.pixels.map(p => p.join(",")).join(" ")}} fill="currentColor" fillOpacity={{0.12}} stroke="currentColor" strokeWidth={{2}} />)}}
    </svg>
    <ul style={{{jsx(legend)}}}>
      {{geometry.layers.map(layer => <li key={{layer.layer_id}} dir="auto" data-bie-text-id={{legendPrefix + layer.layer_id}}>{{layer.kind + ": " + layer.label}}</li>)}}
    </ul>
    <div dir="auto" data-bie-text-id={{{jsx(eid + ':attribution')}}}>{{geometry.attribution}}</div>
    <div dir="auto" data-bie-text-id={{{jsx(eid + ':limits')}}}>Inline geometry only; no basemap. Projected segments are not geodesic paths or distance/area measurements.</div>
  </figure>;
}};
'''
    return compile_result(eid, "map", comp, source)
