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

export const Easing = {
  linear: (t: number) => t,
  inOut: (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  out: (t: number) => 1 - Math.pow(1 - t, 3),
  in: (t: number) => t * t * t,
  back: (t: number) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
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
