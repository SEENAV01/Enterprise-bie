// circuit_build (Task 046a, batch 2): a circuit drawn by schemdraw, element by element, then what it does: ngspice's
// simulated trace next to lcapy's exact formula. A block refuses to show numbers the two tools disagree on.
import React from "react";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";
import { Chart, tex } from "./charts";

const CircuitBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  if (data.trace && data.trace.agree === false) throw new Error("BIE_UNCHECKED_RESULT: ngspice and lcapy disagree");
  const pieces: string[] = data.pieces;
  const every = (data.piece_seconds ?? 0.35) * fps;
  const [vx, vy, vw, vh] = String(data.view_box).split(/\s+/).map(Number);
  const boxW = width * 0.46, boxH = height - 200;
  const traceStart = pieces.length * (data.piece_seconds ?? 0.35) + 0.2;
  const tr = data.trace;
  const labels: string[] = data.labels || [];
  const current = Math.min(pieces.length - 1, Math.floor(rel / every));
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={boxW} height={boxH} viewBox={`${vx - 10} ${vy - 10} ${vw + 20} ${vh + 20}`} style={{ position: "absolute", left: 30, top: 150 }}>
        {pieces.map((p, i) => <g key={i} opacity={ramp(rel, i * every, 8)}
          style={{ filter: i === current && rel < pieces.length * every ? "drop-shadow(0 0 4px #38d3c3)" : undefined }}
          dangerouslySetInnerHTML={{ __html: p }} />)}
      </svg>
      {labels[current] && rel < pieces.length * every ?
        <Badge text={labels[current]} style={{ position: "absolute", left: 40, bottom: 40 }} /> : null}
      {tr ? <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <g opacity={ramp(rel, traceStart * fps - 6, 10)}>
          <Chart series={[{ x: tr.t, y: tr.v_exact, colour: C.warm, width: 10, start: traceStart, seconds: 0.01, label: "lcapy" },
                          { x: tr.t, y: tr.v_spice, colour: C.accent, width: 4, start: traceStart, seconds: data.trace_seconds ?? 2.0, label: "ngspice" }]}
            rel={rel} fps={fps} left={width * 0.5} top={190} width={width * 0.48} height={height - 230}
            xLabel={data.x_label || "t (s)"} yLabel={data.y_label || "V across C (volts)"} />
        </g>
      </svg> : null}
      <Title text={data.title} sub={data.subtitle} />
      {tr?.formula_latex ? <div style={{ position: "absolute", right: 50, top: 110, fontSize: 36, color: C.ink, background: C.panel,
        padding: "4px 16px", borderRadius: 12, opacity: ramp(rel, traceStart * fps, 12) }} dangerouslySetInnerHTML={{ __html: tex(data.latex || tr.formula_latex) }} /> : null}
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, bottom: 30, opacity: ramp(rel, (traceStart + 2) * fps, 12) }} /> : null}
    </div>
  );
};

registerBlock("circuit_build", CircuitBuild);
