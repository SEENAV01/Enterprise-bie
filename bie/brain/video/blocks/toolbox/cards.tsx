// case_card (Task 046a, batch 3): a card for a case or judgment that fills in field by field: the parties, the court
// and date, the bench (one chip per judge), the citations, and where the record comes from. Every field comes from the
// record BIE read (for the Supreme Court: the open judgments dataset), nothing is typed into the card.
import React from "react";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, ramp, useRel } from "./common";

const titleCase = (s: string) => (s || "").toLowerCase().replace(/\b([a-z])/g, (m) => m.toUpperCase()).replace(/\bOf\b/g, "of")
  .replace(/\bAnd\b/g, "and").replace(/\bVersus\b/g, "v.");

const CaseCard: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const c = data.card;
  const step = (data.step_seconds ?? 0.45) * fps;
  const show = (i: number) => ramp(rel, (data.first_at ?? 0.3) * fps + i * step, 10);
  const judges = (c.coram as string[]) || [];
  const chipsAt = (data.first_at ?? 0.3) * fps + 4 * step;
  const rows: [string, string][] = [["Court", c.court], ["Decided", c.decided], ["Bench", c.bench]];
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <div style={{ position: "absolute", left: (width - 1320) / 2, top: 120, width: 1320, height: height - 170, background: "#0f2a38",
        border: `3px solid ${C.accent}`, borderRadius: 26, boxShadow: "0 20px 60px rgba(0,0,0,0.45)", padding: "34px 48px", boxSizing: "border-box",
        transform: `translateY(${(1 - show(0)) * 40}px)`, opacity: show(0), color: C.ink }}>
        <div style={{ fontSize: 22, letterSpacing: 4, color: C.accent, fontWeight: 800 }}>{(data.kind || "JUDGMENT").toUpperCase()}</div>
        <div style={{ fontSize: 46, fontWeight: 800, lineHeight: 1.12, marginTop: 8 }}>{titleCase(c.petitioner)}</div>
        <div style={{ fontSize: 28, color: C.muted, margin: "4px 0" }}>versus</div>
        <div style={{ fontSize: 40, fontWeight: 800, lineHeight: 1.12 }}>{titleCase(c.respondent)}</div>
        <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", rowGap: 10, marginTop: 26, fontSize: 30 }}>
          {rows.map(([k, v], i) => <React.Fragment key={k}>
            <div style={{ color: C.muted, opacity: show(i + 1) }}>{k}</div><div style={{ fontWeight: 700, opacity: show(i + 1) }}>{v}</div></React.Fragment>)}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 14 }}>
          {judges.map((j, i) => <div key={j} style={{ fontSize: 21, padding: "5px 12px", borderRadius: 999, background: "#123a4a",
            border: `2px solid ${i === 0 ? C.warm : "rgba(255,255,255,0.15)"}`, opacity: ramp(rel, chipsAt + i * 2.5, 8) }}>
            {titleCase(j)}</div>)}
        </div>
        <div style={{ marginTop: 20, fontSize: 28, opacity: show(5 + Math.ceil(judges.length * 2.5 / step)) }}>
          <span style={{ color: C.muted }}>Citations </span>
          {(c.citations as string[]).map((t) => <span key={t} style={{ fontWeight: 800, color: C.warm, marginRight: 26 }}>{t}</span>)}
        </div>
        {data.held ? <div style={{ marginTop: 18, fontSize: 30, fontWeight: 700, borderLeft: `6px solid ${C.warm}`, paddingLeft: 16,
          opacity: show(6 + Math.ceil(judges.length * 2.5 / step)) }}>{data.held}</div> : null}
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {data.credit ? <div style={{ position: "absolute", left: 40, bottom: 10, color: C.muted, fontSize: 18 }}>{data.credit}</div> : null}
    </div>
  );
};

registerBlock("case_card", CaseCard);
