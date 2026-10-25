// experiment_flow (Task 046a, batch 3): a psychology experiment as it runs: the routines of one trial in a loop
// (fixation → stimulus → feedback), the screen the participant sees at each moment, and the trial list PsychoPy's
// TrialHandler made (word × ink colour, congruent or not), the current trial marked.
import React from "react";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

type Routine = { name: string; seconds: number | null; shows: string; ends?: string };
type Trial = { n: number; word: string; ink: string; ink_hex: string; congruent: boolean };

const ExperimentFlow: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const routines = data.routines as Routine[], trials = data.trials as Trial[];
  const first = (data.first_at ?? 0.6) * fps, per = ((data.seconds ?? 3.4) * fps) / trials.length;
  const t = Math.max(0, rel - first);
  const ti = Math.min(trials.length - 1, Math.floor(t / per));
  const within = (t - ti * per) / per;                         // 0..1 inside the trial
  const shares = [0.25, 0.55, 0.2];                            // fixation, stimulus, feedback: shares of a trial on screen
  const ri = rel < first ? -1 : within < shares[0] ? 0 : within < shares[0] + shares[1] ? 1 : 2;
  const trial = trials[ti];
  const screen = { x: 80, y: 330, w: 980, h: 560 };
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT, color: C.ink }}>
      <div style={{ position: "absolute", left: 80, top: 140, display: "flex", alignItems: "center", gap: 18, opacity: ramp(rel, 0, 12) }}>
        {routines.map((r, i) => <React.Fragment key={r.name}>
          <div style={{ padding: "10px 22px", borderRadius: 14, fontSize: 28, fontWeight: 700, background: i === ri ? "rgba(255,179,92,0.22)" : C.panel,
            border: `3px solid ${i === ri ? C.warm : "rgba(255,255,255,0.15)"}` }}>
            {r.name}<span style={{ color: C.muted, fontSize: 20, marginLeft: 10 }}>{r.seconds ? `${r.seconds} s` : r.ends ? "until key" : ""}</span></div>
          {i < routines.length - 1 ? <div style={{ fontSize: 34, color: C.muted }}>→</div> : null}
        </React.Fragment>)}
        <div style={{ fontSize: 26, color: C.accent, marginLeft: 16 }}>{`↺ loop × ${trials.length} trials`}</div>
      </div>
      <div style={{ position: "absolute", left: screen.x, top: screen.y, width: screen.w, height: screen.h, background: "#111", borderRadius: 18,
        border: "14px solid #2a3b45", boxSizing: "border-box", display: "flex", alignItems: "center", justifyContent: "center" }}>
        {ri === 0 ? <div style={{ fontSize: 120, color: "#ddd" }}>+</div> : null}
        {ri === 1 ? <div style={{ fontSize: 150, fontWeight: 800, color: trial.ink_hex, letterSpacing: 4 }}>{trial.word}</div> : null}
        {ri === 2 ? <div style={{ fontSize: 44, color: C.muted }}>{`response: the ink was ${trial.ink}`}</div> : null}
        <div style={{ position: "absolute", left: 20, bottom: 12, fontSize: 22, color: "#777" }}>{`trial ${ti + 1} of ${trials.length}`}</div>
      </div>
      <div style={{ position: "absolute", right: 70, top: 250, width: 640, display: "grid", gridTemplateColumns: "60px 1fr 1fr 150px", rowGap: 6,
        fontSize: 25, opacity: ramp(rel, 0.2 * fps, 12) }}>
        {["#", "word", "ink", ""].map((h) => <div key={h} style={{ color: C.muted, fontWeight: 700 }}>{h}</div>)}
        {trials.map((tr, i) => {
          const active = i === ti && rel >= first;
          const bg = active ? "rgba(255,179,92,0.18)" : "transparent";
          return <React.Fragment key={i}>
            <div style={{ background: bg, padding: "3px 6px" }}>{i + 1}</div>
            <div style={{ background: bg, padding: "3px 6px", fontWeight: 700 }}>{tr.word}</div>
            <div style={{ background: bg, padding: "3px 6px", color: tr.ink_hex, fontWeight: 700 }}>{tr.ink}</div>
            <div style={{ background: bg, padding: "3px 6px", color: tr.congruent ? C.accent : C.warm }}>{tr.congruent ? "congruent" : "conflict"}</div>
          </React.Fragment>;
        })}
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 70, bottom: 40 }} /> : null}
    </div>
  );
};

registerBlock("experiment_flow", ExperimentFlow);
