// kinetic_text (Task 046a, batch 3): a sentence in an Indian script animated word by word: each word builds akshara by
// akshara (as BIE's language adapter split it with the Indic NLP Library), then its Roman form (indic_transliteration)
// and its meaning appear under it; the word being read glows. The script font (Noto Sans Devanagari, OFL) is loaded
// from the asset library, so every machine draws the same letters.
import React from "react";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, assetUrl, ramp, useAsset, useRel } from "./common";

type Word = { text: string; aksharas: string[]; roman: string; gloss?: string; punct?: string };

const KineticText: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const family = data.font_family || "BIE Script";
  const font = useAsset(`font:${data.font_src}`, async () => {
    const face = new FontFace(family, `url(${assetUrl(data.font_src)})`);
    await face.load();
    (document as any).fonts.add(face);
    return true;
  });
  if (!font) return null;
  const words = data.words as Word[];
  const first = (data.first_at ?? 0.3) * fps, per = ((data.seconds ?? 3.2) * fps) / words.length;
  const script = `"${family}", ${FONT}`;
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <div style={{ position: "absolute", left: 60, right: 60, top: 230, display: "flex", flexWrap: "wrap", justifyContent: "center", columnGap: 46, rowGap: 30 }}>
        {words.map((w, i) => {
          const start = first + i * per;
          const now = rel >= start && rel < start + per;
          const n = w.aksharas.length;
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 120, opacity: ramp(rel, start, 4) }}>
              <div style={{ fontFamily: script, fontSize: 104, lineHeight: 1.25, fontWeight: 600, color: now ? C.warm : C.ink,
                textShadow: now ? `0 0 24px ${C.warm}` : "none", whiteSpace: "nowrap" }}>
                {w.aksharas.map((a, k) => {
                  const o = ramp(rel, start + (k * per * 0.55) / n, 5);
                  return <span key={k} style={{ display: "inline-block", opacity: o, transform: `translateY(${(1 - o) * 26}px)` }}>{a}</span>;
                })}
                {w.punct ? <span style={{ opacity: ramp(rel, start + per * 0.55, 5) }}>{" " + w.punct}</span> : null}
              </div>
              <div style={{ fontSize: 40, fontStyle: "italic", color: C.accent, opacity: ramp(rel, start + per * 0.5, 6) }}>{w.roman}</div>
              {w.gloss ? <div style={{ fontSize: 26, color: C.muted, opacity: ramp(rel, start + per * 0.7, 6) }}>{w.gloss}</div> : null}
            </div>
          );
        })}
      </div>
      {data.translation ? <div style={{ position: "absolute", left: 0, right: 0, bottom: 110, textAlign: "center", fontSize: 38, color: C.ink,
        opacity: ramp(rel, first + words.length * per, 10) }}>{data.translation}</div> : null}
      <Title text={data.title} sub={data.subtitle} />
      {data.credit ? <div style={{ position: "absolute", left: 40, bottom: 10, color: C.muted, fontSize: 18 }}>{data.credit}</div> : null}
    </div>
  );
};

registerBlock("kinetic_text", KineticText);
