// Chart blocks on three chart libraries (Task 046a, batch 3), each growing from data BIE fetched or computed:
// - chartjs_build: bars or lines by Chart.js on its canvas, the bars rising one after another (chart_bar_line_pie);
// - vega_build: a Vega-Lite chart compiled and rendered by Vega to SVG every frame, the points moving year by year
//   between the World Bank's yearly values (and a trail for the countries named in data.trail);
// - plotly_build: a Plotly figure (here a contour of a production function) with a path drawn over it point by point.
// Chart.js and Plotly draw asynchronously or on their own canvas, so each frame is held until it is drawn.
import React, { useLayoutEffect, useRef } from "react";
import { Chart, registerables } from "chart.js";
import * as vega from "vega";
import { compile } from "vega-lite";
import Plotly from "plotly.js-dist-min";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useAsset, useFrameHold, useRel } from "./common";

Chart.register(...registerables);
const box = (width: number, height: number) => ({ left: 40, top: 130, w: width - 80, h: height - 170 });

const ChartJsBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { frame, rel, fps } = useRel(at);
  const canvas = useRef<HTMLCanvasElement>(null);
  const chart = useRef<Chart | null>(null);
  const release = useFrameHold(frame);
  const b = { ...box(width, height), w: width - 80 - 340 };       // the right column holds the year's value and the note
  const values: number[] = data.values;
  const grow = values.length * ramp(rel, (data.first_at ?? 0.3) * fps, (data.seconds ?? 3.0) * fps, (t: number) => t);
  const whole = Math.floor(grow), part = grow - whole;
  useLayoutEffect(() => {
    if (!canvas.current) return;
    if (!chart.current) {
      Chart.defaults.font.family = FONT;
      Chart.defaults.color = C.muted;
      chart.current = new Chart(canvas.current, {
        type: data.type || "bar",
        data: { labels: data.labels, datasets: [{ label: data.series_label || "", data: [] as any[], backgroundColor: [] as string[], borderWidth: 0 }] },
        options: {
          animation: false, responsive: false, devicePixelRatio: 1, maintainAspectRatio: false,
          plugins: { legend: { display: false }, title: { display: false } },
          scales: {
            x: { ticks: { color: C.muted, font: { size: 20 }, maxRotation: 0, autoSkip: true, autoSkipPadding: 18 }, grid: { color: "rgba(255,255,255,0.06)" } },
            y: { min: data.y_min, max: data.y_max, ticks: { color: C.muted, font: { size: 22 } }, grid: { color: "rgba(255,255,255,0.12)" },
                 title: { display: !!data.y_label, text: data.y_label, color: C.ink, font: { size: 24 } } },
          },
        },
      });
    }
    const ds = chart.current.data.datasets[0];
    ds.data = values.map((v, i) => (i < whole ? v : i === whole ? v * part : null));
    ds.backgroundColor = values.map((v, i) => (i === data.highlight ? C.warm : v < 0 ? C.danger : C.accent));
    chart.current.update("none");
    release();
  });
  const shown = Math.min(values.length - 1, Math.max(0, whole - (part > 0 ? 0 : 1)));
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <canvas ref={canvas} width={b.w} height={b.h} style={{ position: "absolute", left: b.left, top: b.top, width: b.w, height: b.h }} />
      <div style={{ position: "absolute", right: 50, top: 170, width: 280, textAlign: "right", color: C.ink, background: C.panel, padding: "10px 20px",
        borderRadius: 14, boxSizing: "border-box" }}>
        <div style={{ fontSize: 28, color: C.muted }}>{data.labels[shown]}</div>
        <div style={{ fontSize: 60, fontWeight: 800, color: values[shown] < 0 ? C.danger : C.accent }}>{`${values[shown] > 0 ? "+" : ""}${values[shown].toFixed(1)}${data.unit || ""}`}</div>
      </div>
      {data.note && whole > data.highlight ? <div style={{ position: "absolute", right: 50, top: 340, width: 280, boxSizing: "border-box", fontSize: 26,
        fontWeight: 700, color: C.warm, border: `2px solid ${C.warm}`, borderRadius: 14, padding: "10px 16px", background: C.panel }}>{data.note}</div> : null}
      <Title text={data.title} sub={data.subtitle} />
      {data.credit ? <div style={{ position: "absolute", left: 40, bottom: 8, color: C.muted, fontSize: 18 }}>{data.credit}</div> : null}
    </div>
  );
};

// ---------------------------------------------------------------- Vega-Lite

type Pt = { iso3: string; country: string; x: number; y: number; size: number };

function between(a: Pt[], b: Pt[], f: number): Pt[] {
  const next = new Map(b.map((p) => [p.iso3, p]));
  return a.filter((p) => next.has(p.iso3)).map((p) => {
    const q = next.get(p.iso3)!;
    return { ...p, x: p.x + (q.x - p.x) * f, y: p.y + (q.y - p.y) * f, size: p.size + (q.size - p.size) * f };
  });
}

const VegaBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const frames = data.frames as { year: number; points: Pt[] }[];
  const t = (frames.length - 1) * ramp(rel, (data.first_at ?? 0.3) * fps, (data.seconds ?? 3.4) * fps, (s: number) => s);
  const i = Math.min(frames.length - 2, Math.floor(t)), f = Math.min(1, t - i);
  const now = between(frames[i].points, frames[i + 1].points, f);
  const trail = frames.slice(0, i + 1).flatMap((fr) => fr.points.filter((p) => (data.trail || []).includes(p.iso3)))
    .concat(now.filter((p) => (data.trail || []).includes(p.iso3)));
  const b = box(width, height);
  // one x and one y for all three layers (Vega-Lite would otherwise join the layers' own domains and add zero)
  const x = { field: "x", type: "quantitative", title: data.x_title, scale: { type: "log", domain: data.x_domain, nice: false } };
  const y = { field: "y", type: "quantitative", title: data.y_title, scale: { domain: data.y_domain, zero: false, nice: false } };
  const colour = { field: "country", type: "nominal", legend: null, scale: { scheme: "tableau10" } };
  const spec: any = {
    $schema: "https://vega.github.io/schema/vega-lite/v6.json", width: b.w - 40, height: b.h - 90, background: null,
    config: { font: FONT, axis: { labelColor: C.muted, titleColor: C.ink, gridColor: "rgba(255,255,255,0.1)", domainColor: C.muted,
      labelFontSize: 22, titleFontSize: 24 }, view: { stroke: null } },
    encoding: { x, y },
    layer: [
      { data: { values: trail }, mark: { type: "line", strokeWidth: 4, opacity: 0.6 }, encoding: { detail: { field: "iso3" }, color: colour } },
      { data: { values: now }, mark: { type: "circle", opacity: 0.85, stroke: C.bg0, strokeWidth: 1.5 },
        encoding: { size: { field: "size", type: "quantitative", scale: { range: [80, 5200], domain: data.size_domain }, legend: null }, color: colour } },
      { data: { values: now }, mark: { type: "text", dy: -34, fontSize: 24, fontWeight: 700, color: C.ink }, encoding: { text: { field: "country" } } },
    ],
  };
  const key = `vega:${data.key || "chart"}:${t.toFixed(3)}`;
  const svg = useAsset(key, async () => {
    const view = new vega.View(vega.parse(compile(spec).spec), { renderer: "none" });
    await view.runAsync();
    const out = await view.toSVG();
    view.finalize();
    return out;
  });
  const year = Math.round(frames[i].year + (frames[i + 1].year - frames[i].year) * f);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <div style={{ position: "absolute", left: b.left + 260, top: b.top + 120, fontSize: 220, fontWeight: 800, color: "rgba(255,255,255,0.07)" }}>{year}</div>
      {svg ? <div style={{ position: "absolute", left: b.left, top: b.top }} dangerouslySetInnerHTML={{ __html: svg }} /> : null}
      <Title text={data.title} sub={data.subtitle} />
      {data.credit ? <div style={{ position: "absolute", left: 40, bottom: 8, color: C.muted, fontSize: 18 }}>{data.credit}</div> : null}
    </div>
  );
};

// ---------------------------------------------------------------- Plotly

const PlotlyBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { frame, rel, fps } = useRel(at);
  const div = useRef<HTMLDivElement>(null);
  const release = useFrameHold(frame);
  const b = box(width, height);
  const path = data.path as number[][];
  const k = path.length * ramp(rel, (data.path_at ?? 1.0) * fps, (data.path_seconds ?? 2.4) * fps, (s: number) => s);
  const reveal = ramp(rel, 0, 0.8 * fps);
  useLayoutEffect(() => {
    if (!div.current) return;
    const shownPath = path.slice(0, Math.max(1, Math.floor(k)));
    const traces: any[] = [
      { type: "contour", x: data.x, y: data.y, z: data.z, colorscale: "Viridis", opacity: 0.35 + 0.6 * reveal, showscale: false,
        contours: { coloring: "heatmap", showlabels: true, labelfont: { size: 18, color: "white" }, start: data.levels[0],
                    end: data.levels[data.levels.length - 1], size: data.levels[1] - data.levels[0] }, line: { color: "rgba(255,255,255,0.75)", width: 2 } },
      { type: "scatter", mode: "lines+markers", x: shownPath.map((p) => p[0]), y: shownPath.map((p) => p[1]),
        line: { color: C.warm, width: 5 }, marker: { size: 10, color: C.warm }, name: data.path_label },
    ];
    const layout: any = {
      width: b.w - 420, height: b.h, margin: { l: 90, r: 20, t: 10, b: 70 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: FONT, color: C.ink, size: 24 }, showlegend: false,
      xaxis: { title: { text: data.x_title }, gridcolor: "rgba(255,255,255,0.1)", range: [data.x[0], data.x[data.x.length - 1]] },
      yaxis: { title: { text: data.y_title }, gridcolor: "rgba(255,255,255,0.1)", range: [data.y[0], data.y[data.y.length - 1]] },
    };
    Plotly.react(div.current, traces, layout, { staticPlot: true, displayModeBar: false }).then(() => release(), () => release());
  });
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <div ref={div} style={{ position: "absolute", left: b.left, top: b.top, width: b.w - 420, height: b.h }} />
      <div style={{ position: "absolute", right: 50, top: 170, width: 360, color: C.ink, fontSize: 26, display: "flex", flexDirection: "column", gap: 14 }}>
        {(data.panel as string[] || []).map((l, i) => <div key={i} style={{ background: C.panel, borderRadius: 12, padding: "10px 16px",
          opacity: ramp(rel, (0.5 + i * 0.5) * fps, 10) }}>{l}</div>)}
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, bottom: 40 }} /> : null}
    </div>
  );
};

registerBlock("chartjs_build", ChartJsBuild);
registerBlock("vega_build", VegaBuild);
registerBlock("plotly_build", PlotlyBuild);
