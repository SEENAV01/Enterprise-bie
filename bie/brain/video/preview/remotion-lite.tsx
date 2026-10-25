// A small subset of Remotion's API (useCurrentFrame, useVideoConfig, interpolate, spring, Easing,
// AbsoluteFill, Sequence) with the same names and semantics, so these components can move into a
// real Remotion project by changing one import. Used here because the cloud workspace cannot
// install packages; every frame is still rendered by Chromium and encoded with ffmpeg.
import React, { createContext, useContext } from "react";

type Config = { fps: number; width: number; height: number; durationInFrames: number };
const FrameCtx = createContext(0);
const ConfigCtx = createContext<Config>({ fps: 30, width: 1920, height: 1080, durationInFrames: 1 });

export const FrameProvider: React.FC<{ frame: number; config: Config; children: React.ReactNode }> = ({ frame, config, children }) => (
  <ConfigCtx.Provider value={config}>
    <FrameCtx.Provider value={frame}>{children}</FrameCtx.Provider>
  </ConfigCtx.Provider>
);

export const useCurrentFrame = () => useContext(FrameCtx);
export const useVideoConfig = () => useContext(ConfigCtx);

type Extrapolate = "clamp" | "extend";
export function interpolate(
  input: number,
  inputRange: number[],
  outputRange: number[],
  options: { extrapolateLeft?: Extrapolate; extrapolateRight?: Extrapolate; easing?: (t: number) => number } = {},
): number {
  const { extrapolateLeft = "clamp", extrapolateRight = "clamp", easing = (t: number) => t } = options;
  let i = 1;
  while (i < inputRange.length - 1 && input > inputRange[i]) i++;
  const [a, b] = [inputRange[i - 1], inputRange[i]];
  const [c, d] = [outputRange[i - 1], outputRange[i]];
  let t = b === a ? 1 : (input - a) / (b - a);
  if (t < 0 && extrapolateLeft === "clamp") t = 0;
  if (t > 1 && extrapolateRight === "clamp") t = 1;
  return c + (d - c) * easing(t);
}

// Easing with Remotion's API (Task 046a): in, out and inOut take an easing function and return one, exactly as in
// Remotion (Easing.inOut(Easing.cubic)). The first version of this shim had inOut, in and out as ready functions,
// which real Remotion does not; the bridge proof (the same clip rendered by Remotion itself) found it.
type Ease = (t: number) => number;
function bezier(x1: number, y1: number, x2: number, y2: number): Ease {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const x = (t: number) => ((ax * t + bx) * t + cx) * t;
  const y = (t: number) => ((ay * t + by) * t + cy) * t;
  const dx = (t: number) => (3 * ax * t + 2 * bx) * t + cx;
  return (v: number) => {
    let t = v;
    for (let i = 0; i < 8; i++) { const d = dx(t); if (Math.abs(d) < 1e-6) break; t -= (x(t) - v) / d; }
    return y(Math.max(0, Math.min(1, t)));
  };
}
export const Easing = {
  linear: (t: number) => t,
  ease: bezier(0.42, 0, 1, 1),
  quad: (t: number) => t * t,
  cubic: (t: number) => t * t * t,
  poly: (n: number): Ease => (t) => Math.pow(t, n),
  sin: (t: number) => 1 - Math.cos((t * Math.PI) / 2),
  circle: (t: number) => 1 - Math.sqrt(1 - t * t),
  exp: (t: number) => Math.pow(2, 10 * (t - 1)),
  back: (s = 1.70158): Ease => (t) => t * t * ((s + 1) * t - s),
  bezier,
  in: (easing: Ease): Ease => easing,
  out: (easing: Ease): Ease => (t) => 1 - easing(1 - t),
  inOut: (easing: Ease): Ease => (t) => (t < 0.5 ? easing(t * 2) / 2 : 1 - easing((1 - t) * 2) / 2),
};

// Damped spring like Remotion's spring(): returns 0 -> 1 (may overshoot slightly).
export function spring({ frame, fps, config = {}, delay = 0 }: { frame: number; fps: number; delay?: number;
  config?: { damping?: number; stiffness?: number; mass?: number } }): number {
  const { damping = 12, stiffness = 120, mass = 1 } = config;
  const t = (frame - delay) / fps;
  if (t <= 0) return 0;
  const omega = Math.sqrt(stiffness / mass);
  const zeta = damping / (2 * Math.sqrt(stiffness * mass));
  if (zeta < 1) {
    const wd = omega * Math.sqrt(1 - zeta * zeta);
    return 1 - Math.exp(-zeta * omega * t) * (Math.cos(wd * t) + ((zeta * omega) / wd) * Math.sin(wd * t));
  }
  return 1 - Math.exp(-omega * t) * (1 + omega * t);
}

export const AbsoluteFill: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ style, ...rest }) => (
  <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, width: "100%", height: "100%", display: "flex",
    flexDirection: "column", ...style }} {...rest} />
);

export const Sequence: React.FC<{ from: number; durationInFrames?: number; children: React.ReactNode }> = ({ from, durationInFrames = Infinity, children }) => {
  const frame = useCurrentFrame();
  const config = useVideoConfig();
  if (frame < from || frame >= from + durationInFrames) return null;
  return <FrameProvider frame={frame - from} config={config}>{children}</FrameProvider>;
};

// Media helpers with Remotion's names, for the preview only.
export const Img: React.FC<React.ImgHTMLAttributes<HTMLImageElement>> = (props) => <img {...props} />;
export const staticFile = (name: string) => name;
export const Audio: React.FC<{ src: string }> = () => null;

// delayRender / continueRender with Remotion's names and meaning (Task 046a): a block that loads a model or draws on
// its own WebGL canvas holds the frame until it is really drawn; the preview harness waits until no handle is open
// before it takes the screenshot, exactly as Remotion's renderer does.
const pending = new Map<number, string>();
let nextHandle = 1;
export function delayRender(label = "") {
  const handle = nextHandle++;
  pending.set(handle, label);
  return handle;
}
export function continueRender(handle: number) {
  pending.delete(handle);
}
export function cancelRender(error: unknown): never {
  throw error instanceof Error ? error : new Error(String(error));
}
export const pendingRenders = () => Array.from(pending.values());
