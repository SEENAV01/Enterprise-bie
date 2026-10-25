// Chemistry blocks (Task 046a):
// - reaction: reactants drawn by RDKit (SVG) appear, the arrow draws, the products appear, and RDKit's atom balance
//   check is shown; optional amounts over time from Cantera (kinetics) draw under it;
// - molecule_3d / protein_3d: 3Dmol.js (molecules as ball and stick, proteins as cartoon) or Mol* for proteins,
//   turned frame by frame on their own WebGL canvas.
import React, { useLayoutEffect, useRef } from "react";
import { line, scaleLinear } from "d3";
import * as $3Dmol from "3dmol";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, assetUrl, ramp, useAsset, useFrameHold, useRel } from "./common";

const Reaction: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const cardW = Math.min(380, (width - 300) / (data.reactants.length + data.products.length));
  const card = (m: any, o: number, key: string) => (
    <div key={key} style={{ width: cardW, opacity: o, transform: `translateY(${(1 - o) * 30}px)`, textAlign: "center" }}>
      <div style={{ height: cardW * 0.72 }} dangerouslySetInnerHTML={{ __html: m.svg.replace(/<\?xml[^>]*>/, "").replace(/width='\d+px' height='\d+px'/, "width='100%' height='100%'") }} />
      <div style={{ color: C.ink, fontSize: 30, fontWeight: 700 }}>{m.name}</div>
      <div style={{ color: C.muted, fontSize: 24 }}>{m.formula}</div>
    </div>);
  const arrow = ramp(rel, 1.2 * fps, 0.8 * fps);
  const kin = data.kinetics;
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <Title text={data.title} sub={data.subtitle} />
      <div style={{ position: "absolute", left: 30, right: 30, top: 120, display: "flex", alignItems: "center", justifyContent: "center", gap: 18 }}>
        {data.reactants.map((m: any, i: number) => [i ? <div key={"p" + i} style={{ color: C.ink, fontSize: 56, opacity: ramp(rel, i * 0.4 * fps, 15) }}>+</div> : null,
          card(m, ramp(rel, i * 0.4 * fps, 15), "r" + i)])}
        <svg width={170} height={60}><line x1={10} y1={30} x2={10 + 140 * arrow} y2={30} stroke={C.warm} strokeWidth={7} />
          {arrow > 0.95 ? <path d="M146,14 L166,30 L146,46 z" fill={C.warm} /> : null}</svg>
        {data.products.map((m: any, i: number) => [i ? <div key={"q" + i} style={{ color: C.ink, fontSize: 56, opacity: ramp(rel, 2.1 * fps + i * 0.4 * fps, 15) }}>+</div> : null,
          card(m, ramp(rel, 2.1 * fps + i * 0.4 * fps, 15), "s" + i)])}
      </div>
      {data.balanced ? <Badge text={data.balance_label || "✓ atoms balanced (RDKit)"} style={{ position: "absolute", left: 60, top: 120 + cardW * 0.72 + 110, opacity: ramp(rel, 3 * fps, 12) }} /> : null}
      {kin ? <Kinetics kin={kin} rel={rel - 2.5 * fps} fps={fps} width={width} top={height * 0.62} height={height * 0.36} /> : null}
    </div>
  );
};

const Kinetics: React.FC<{ kin: any; rel: number; fps: number; width: number; top: number; height: number }> = ({ kin, rel, fps, width, top, height }) => {
  const t: number[] = kin.t_ms;
  const n = Math.max(2, Math.round(t.length * Math.max(0, Math.min(1, rel / (2 * fps)))));
  const sx = scaleLinear().domain([t[0], t[t.length - 1]]).range([120, width - 60]);
  const sy = scaleLinear().domain([0, 0.7]).range([height - 40, 20]);
  const colours = [C.accent, C.warm, "#7CFFB2", "#c79bff", "#ff6b6b"];
  return (
    <svg width={width} height={height} style={{ position: "absolute", left: 0, top }}>
      <line x1={120} x2={width - 60} y1={height - 40} y2={height - 40} stroke={C.line} />
      {Object.entries(kin.species as Record<string, number[]>).map(([name, ys], i) => (
        <g key={name}>
          <path d={line<number>().x((_, k) => sx(t[k])).y((v) => sy(v))(ys.slice(0, n)) || ""} fill="none" stroke={colours[i % 5]} strokeWidth={4} />
          <text x={sx(t[n - 1]) + 10} y={sy(ys[n - 1]) + 8} fill={colours[i % 5]} fontSize={22} fontWeight={700}>{name}</text>
        </g>))}
      <text x={120} y={height - 8} fill={C.muted} fontSize={20}>{kin.caption || "mole fraction over time (Cantera)"}</text>
    </svg>
  );
};

/** A 3Dmol.js viewer turned by the frame clock. */
const Mol3D: React.FC<BlockProps & { mode: "molecule" | "protein" }> = ({ data, at, width, height, mode }) => {
  const { rel, frame, fps } = useRel(at);
  const text = useAsset<string>(`mol:${data.src || data.name}`, async () => (data.src ? (await fetch(assetUrl(data.src))).text() : data.text));
  const holder = useRef<HTMLDivElement>(null);
  const viewer = useRef<any>(null);
  const base = useRef<number[] | null>(null);
  const release = useFrameHold(frame);
  useLayoutEffect(() => {
    if (!text || !holder.current) return;
    if (!viewer.current) {
      const v = $3Dmol.createViewer(holder.current, { backgroundColor: "black", backgroundAlpha: 0, antialias: true } as any);
      v.addModel(text, data.format || (mode === "protein" ? "pdb" : "sdf"));
      if (mode === "protein") {
        v.setStyle({}, { cartoon: { color: "spectrum", thickness: 0.6 } });
        if (data.show_ligands !== false) v.setStyle({ hetflag: true }, { stick: { radius: 0.25 } });
      } else {
        v.setStyle({}, { stick: { radius: 0.18 }, sphere: { scale: 0.28 } });
      }
      v.zoomTo();
      v.zoom(data.zoom ?? 1.1);
      viewer.current = v;
      base.current = v.getView();
    }
    const v = viewer.current;
    v.setView(base.current);
    v.rotate((data.turn_degrees ?? 200) * ramp(rel, 0, (data.seconds ?? 5) * fps, (t: number) => t), "y", 0);
    v.render();
    release();
  });
  return (
    <>
      <div ref={holder} style={{ position: "absolute", inset: 0, width, height }} />
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 30, bottom: 24 }} /> : null}
    </>
  );
};

registerBlock("reaction", Reaction);
registerBlock("molecule_3d", (p) => <Mol3D {...p} mode="molecule" />);
registerBlock("protein_3d", (p) => <Mol3D {...p} mode="protein" />);
