import React from "react";
const geometry = {"accepted": false, "attribution": "Inline normalized geometry; no external basemap.", "axis_order": "xy", "extent": [0.0, 0.0, 1.0, 1.0], "interpolation": "straight-segments-in-projected-space", "layers": [{"kind": "route", "label": "layer-0", "layer_id": "layer-0", "pixels": [[332.0, 401.0], [500.0, 233.0], [668.0, 149.0]], "projected_points": [[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]], "source_points": [[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]], "source_ref": null}], "projected_extent": [0.0, 0.0, 1.0, 1.0], "projection": "normalized-cartesian-y-up", "source_crs": "BIE:NORMALIZED", "title": "Declared inline map geometry"};
const routes = geometry.layers.filter(layer => layer.kind === "route");
export const Map_e0_5c88e7a2: React.FC = () => {
  return <svg viewBox="0 0 1000 600" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label={"Synthetic map compiler fixture"} data-crs={"BIE:NORMALIZED"} data-projection={"normalized-cartesian-y-up"}>
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
