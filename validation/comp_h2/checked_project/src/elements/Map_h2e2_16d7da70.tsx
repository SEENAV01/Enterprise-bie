import React from "react";
const geometry = {"accepted": false, "attribution": "Synthetic coordinates; no external map data.", "axis_order": "lon_lat", "extent": [-10.0, 20.0, 10.0, 60.0], "interpolation": "straight-segments-in-projected-space", "layers": [{"kind": "route", "label": "Synthetic route", "layer_id": "layer-0", "pixels": [[438.9503217087785, 443.6825754146798], [500.0, 307.2499011845423], [561.0496782912215, 136.14852218112503]], "projected_points": [[-890555.9263461885, 2875744.624352243], [0.0, 4865942.279503175], [890555.9263461885, 7361866.113051188]], "source_points": [[-8.0, 25.0], [0.0, 40.0], [8.0, 55.0]], "source_ref": null}], "projected_extent": [-1113194.9079327357, 2273030.9269876895, 1113194.9079327357, 8399737.889818357], "projection": "web_mercator", "source_crs": "EPSG:4326", "title": "Projection technical fixture"};
const routes = geometry.layers.filter(layer => layer.kind === "route");
export const Map_h2e2_16d7da70: React.FC = () => {
  return <svg viewBox="0 0 1000 600" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label={"Synthetic vector compiler fixture"} data-crs={"EPSG:4326"} data-projection={"web_mercator"}>
    <title>{geometry.title}</title>
    <text x={50} y={28} fontSize={20}>{geometry.title}</text>
    <text x={50} y={50} fontSize={13}>{geometry.projection + "; axes=" + geometry.axis_order + "; extent=" + geometry.extent.join(", ")}</text>
    {routes.map(layer => <polyline key={layer.layer_id} data-layer-id={layer.layer_id} points={layer.pixels.map(p => p.join(",")).join(" ")} fill="none" stroke="currentColor" strokeWidth={3} />)}
    {geometry.layers.filter(layer => layer.kind === "point").map(layer => <g key={layer.layer_id} data-layer-id={layer.layer_id}><circle cx={layer.pixels[0][0]} cy={layer.pixels[0][1]} r={6} fill="currentColor" /><title>{layer.label}</title></g>)}
    {geometry.layers.filter(layer => layer.kind === "polygon").map(layer => <polygon key={layer.layer_id} data-layer-id={layer.layer_id} points={layer.pixels.map(p => p.join(",")).join(" ")} fill="currentColor" fillOpacity={0.12} stroke="currentColor" strokeWidth={2} />)}
    {geometry.layers.map((layer,i) => <text key={layer.layer_id + "-label"} x={50+(i%3)*310} y={515+Math.floor(i/3)*22} fontSize={13}>{layer.kind + ": " + layer.label}</text>)}
    <text x={50} y={566} fontSize={12}>{geometry.attribution}</text>
    <text x={50} y={586} fontSize={12}>Inline geometry only; no basemap. Projected segments are not geodesic paths or distance/area measurements.</text>
  </svg>;
};
