"""Project declared inline map data into actual SVG coordinates."""
from .element_compiler_common import *
from .map_geometry import map_geometry
from .hardening_contracts import literal_js_string, text_value


def compile_map_element(element):
    eid, props, acc, src, rsn = require_type(element, "map")
    g = map_geometry(props)
    comp = component_name("Map", eid)
    # Every declared layer is rendered; original and projected coordinates are retained.
    source = f'''import React from "react";
const geometry = {jsx(g.to_dict())};
const routes = geometry.layers.filter(layer => layer.kind === "route");
export const {comp}: React.FC = () => {{
  return <svg viewBox="0 0 1000 600" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label={{{literal_js_string(text_value(acc.get('alt') or g.title, 'map alt', maximum=2000))}}} data-crs={{{jsx(g.source_crs)}}} data-projection={{{jsx(g.projection)}}}>
    <title>{{geometry.title}}</title>
    <text x={{50}} y={{28}} fontSize={{20}}>{{geometry.title}}</text>
    <text x={{50}} y={{50}} fontSize={{13}}>{{geometry.projection + "; axes=" + geometry.axis_order + "; extent=" + geometry.extent.join(", ")}}</text>
    {{routes.map(layer => <polyline key={{layer.layer_id}} data-layer-id={{layer.layer_id}} points={{layer.pixels.map(p => p.join(",")).join(" ")}} fill="none" stroke="currentColor" strokeWidth={{3}} />)}}
    {{geometry.layers.filter(layer => layer.kind === "point").map(layer => <g key={{layer.layer_id}} data-layer-id={{layer.layer_id}}><circle cx={{layer.pixels[0][0]}} cy={{layer.pixels[0][1]}} r={{6}} fill="currentColor" /><title>{{layer.label}}</title></g>)}}
    {{geometry.layers.filter(layer => layer.kind === "polygon").map(layer => <polygon key={{layer.layer_id}} data-layer-id={{layer.layer_id}} points={{layer.pixels.map(p => p.join(",")).join(" ")}} fill="currentColor" fillOpacity={{0.12}} stroke="currentColor" strokeWidth={{2}} />)}}
    {{geometry.layers.map((layer,i) => <text key={{layer.layer_id + "-label"}} x={{50+(i%3)*310}} y={{515+Math.floor(i/3)*22}} fontSize={{13}}>{{layer.kind + ": " + layer.label}}</text>)}}
    <text x={{50}} y={{566}} fontSize={{12}}>{{geometry.attribution}}</text>
    <text x={{50}} y={{586}} fontSize={{12}}>Inline geometry only; no basemap. Projected segments are not geodesic paths or distance/area measurements.</text>
  </svg>;
}};
'''
    return compile_result(eid, "map", comp, source)
