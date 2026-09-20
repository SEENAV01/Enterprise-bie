"""H1-002 native SVG chart emission; unsupported inputs fail before generation."""
from .element_compiler_common import *
from .chart_geometry import chart_geometry

def compile_chart_element(element):
    eid, props, acc, src, rsn = require_type(element, "chart")
    geometry = chart_geometry(props)
    comp = component_name("Chart", eid)
    source = f'''import React from "react";

type ChartGeometry = {{
  kind: string; categories: string[]; values: number[]; units: string; x_label: string; y_label: string;
  width: number; height: number; left: number; right: number; top: number; bottom: number;
  domain: number[] | null; baseline: number | null;
  bars: Array<{{index: number; label: string; value: number; x: number; y: number; width: number; height: number}}>;
  points: Array<{{index: number; label: string; value: number; x: number; y: number}}>;
  slices: Array<{{index: number; label: string; value: number; fraction: number; path: string}}>;
  line_points: string; area_points: string; x_values?: number[]; x_domain?: number[];
}};
const chart: ChartGeometry = {jsx(geometry)};
export const {comp}: React.FC = () => (
  <figure style={{{{margin: 0, width: "100%", height: "100%", display: "grid", gridTemplateRows: "minmax(0, 1fr) auto"}}}}>
    <svg viewBox="0 0 640 400" width="100%" height="100%" role="img"
      aria-label={{{jsx(acc.get("alt") or "chart")}}} data-chart-kind={{{jsx(geometry["kind"])}}}>
      <title>{{chart.categories.map((label, index) => label + ": " + chart.values[index]).join("; ")}}</title>
      {{chart.kind !== "pie" ? <g data-bie-axis="signed-domain">
        <line x1={{chart.left}} x2={{chart.right}} y1={{chart.baseline ?? 0}} y2={{chart.baseline ?? 0}} stroke="currentColor" />
        <line x1={{chart.left}} x2={{chart.left}} y1={{chart.top}} y2={{chart.bottom}} stroke="currentColor" />
        <text x={{2}} y={{chart.top + 12}} fontSize={{12}}>{{chart.domain?.[1]}}</text>
        <text x={{2}} y={{chart.bottom}} fontSize={{12}}>{{chart.domain?.[0]}}</text>
        <text x={{32}} y={{chart.baseline ?? 0}} fontSize={{12}}>0</text>
      </g> : null}}
      {{chart.bars.map((bar) => <rect key={{bar.index}} data-value={{bar.value}}
        x={{bar.x}} y={{bar.y}} width={{bar.width}} height={{bar.height}} fill="currentColor"><title>{{bar.label + ": " + bar.value}}</title></rect>)}}
      {{chart.kind === "area" ? <polygon points={{chart.area_points}} fill="currentColor" fillOpacity={{0.18}} /> : null}}
      {{chart.kind === "line" || chart.kind === "area" ? <polyline points={{chart.line_points}} fill="none" stroke="currentColor" strokeWidth={{2}} /> : null}}
      {{chart.kind !== "bar" ? chart.points.map((point) => <circle key={{point.index}} cx={{point.x}} cy={{point.y}} r={{4}} fill="currentColor"><title>{{point.label + ": " + point.value}}</title></circle>) : null}}
      {{chart.slices.map((slice) => <path key={{slice.index}} d={{slice.path}} fill="currentColor" fillOpacity={{0.25 + 0.65 * (slice.index + 1) / chart.categories.length}} stroke="currentColor"><title>{{slice.label + ": " + slice.value}}</title></path>)}}
      {{chart.kind !== "pie" ? chart.points.map((point) => <text key={{point.index}} x={{point.x}} y={{340}} textAnchor="middle" fontSize={{12}}>{{point.label}}</text>) : null}}
      {{chart.kind === "scatter" ? <text x={{320}} y={{357}} textAnchor="middle" fontSize={{11}}>{{"Numeric x-domain: " + chart.x_domain?.join(" to ")}}</text> : null}}
      <text x={{320}} y={{375}} textAnchor="middle" fontSize={{14}}>{{chart.x_label + (chart.units ? " | units: " + chart.units : "")}}</text>
    </svg>
    <figcaption style={{{{fontSize: 12, overflowWrap: "anywhere"}}}}>{{chart.y_label}}{{chart.categories.map((label, i) => " | " + label + ": " + chart.values[i]).join("")}}</figcaption>
  </figure>
);
'''
    warnings = ("CHART_DENSE_LABEL_LAYOUT_REQUIRES_REVIEW",) if len(geometry["categories"]) > 12 or any(len(x) > 30 for x in geometry["categories"]) else ()
    return compile_result(eid, "chart", comp, source, warnings=warnings)
