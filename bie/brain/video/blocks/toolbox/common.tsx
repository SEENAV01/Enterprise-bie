// Shared helpers for the toolbox blocks (Task 046a): frame maths, a panel, and the two hooks that keep every frame
// deterministic: useAsset (load a model or file once, holding the frame until it is drawn) and useFrameHold (a block
// that draws on its own canvas holds the frame until that draw is done).
import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { continueRender, delayRender, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT } from "../index";

export { C, FONT };

/** A file the video ships with (a model, a PDB file): through staticFile, so the same block works in real Remotion. */
export const assetUrl = (src: string) => (src.startsWith("http") || src.startsWith("data:") ? src : staticFile(src));

export function useRel(at: number) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return { frame, rel: Math.max(0, frame - at), fps };
}

export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
export const ramp = (rel: number, start: number, length: number, ease = Easing.inOut(Easing.cubic)) =>
  interpolate(rel, [start, start + Math.max(1, length)], [0, 1], { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" });

type Entry = { done: boolean; value?: any; error?: any; handle: number; listeners: Set<() => void> };
const assets = new Map<string, Entry>();

/** Load something once per key (a glTF model, a PDB file ...). Returns null until loaded; the frame is held meanwhile,
 *  and released only after the component has rendered with the value, so the next hold (a canvas draw) is already set. */
export function useAsset<T>(key: string, load: () => Promise<T>): T | null {
  const [, force] = useState(0);
  let entry = assets.get(key);
  if (!entry) {
    const e: Entry = { done: false, handle: delayRender(`load ${key}`), listeners: new Set() };
    assets.set(key, e);
    load().then((v) => { e.value = v; }, (err) => { e.error = err; }).finally(() => { e.done = true; e.listeners.forEach((f) => f()); });
    entry = e;
  }
  const current = entry;
  useEffect(() => {
    const f = () => force((n) => n + 1);
    current.listeners.add(f);
    if (current.done) f();
    return () => { current.listeners.delete(f); };
  }, [current]);
  useLayoutEffect(() => {
    if (current.done && current.handle) { continueRender(current.handle); current.handle = 0; }
  });
  if (current.error) throw current.error instanceof Error ? current.error : new Error(String(current.error));
  return current.done ? (current.value as T) : null;
}

/** For a block that draws on its own canvas: holds the frame from render until ``release()`` (call it after drawing). */
export function useFrameHold(frame: number) {
  const hold = useRef<{ frame: number; id: number } | null>(null);
  if (!hold.current || hold.current.frame !== frame) {
    if (hold.current) continueRender(hold.current.id);
    hold.current = { frame, id: delayRender(`draw frame ${frame}`) };
  }
  useEffect(() => () => { if (hold.current) continueRender(hold.current.id); }, []);
  return () => { if (hold.current) continueRender(hold.current.id); };
}

export const Title: React.FC<{ text?: string; sub?: string }> = ({ text, sub }) =>
  text ? (
    <div style={{ position: "absolute", left: 24, top: 14, fontFamily: FONT, color: C.ink, zIndex: 2 }}>
      <div style={{ fontSize: 36, fontWeight: 800 }}>{text}</div>
      {sub ? <div style={{ fontSize: 24, color: C.muted, marginTop: 4 }}>{sub}</div> : null}
    </div>
  ) : null;

export const Badge: React.FC<{ text: string; tone?: "accent" | "warm"; style?: React.CSSProperties }> = ({ text, tone = "accent", style }) => (
  <div style={{ fontFamily: FONT, fontSize: 22, fontWeight: 700, color: tone === "warm" ? C.warm : C.accent, border: `2px solid ${tone === "warm" ? C.warm : C.accent}`,
    borderRadius: 999, padding: "4px 14px", background: "rgba(6,18,28,0.75)", display: "inline-block", ...style }}>{text}</div>
);

/** Ticks of a linear scale [lo, hi] as nice round numbers. */
export function ticks(lo: number, hi: number, count = 6): number[] {
  const span = hi - lo || 1;
  const raw = span / count;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * pow).find((s) => span / s <= count) || raw;
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(Math.round(v / step) * step);
  return out;
}
