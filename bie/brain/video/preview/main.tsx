// Preview harness: renders any frame of a VideoSpec in a plain browser page (window.setFrame), so BIE can take
// stills for the reviewer AI and encode quick previews with ffmpeg without installing Remotion.
// Task 046a: setFrame also waits until every block that draws on its own canvas (three.js, 3Dmol.js, Mol*) has
// released its delayRender handle for this frame, as Remotion's renderer does.
import React from "react";
import { createRoot } from "react-dom/client";
import { FrameProvider, pendingRenders } from "remotion";
import { Video, VideoSpec, totalFrames } from "../blocks/Video";

declare global { interface Window { __VIDEO__?: VideoSpec; setFrame: (n: number) => Promise<void>; ready: boolean; totalFrames: () => number;
  pendingRenders: () => string[] } }

const root = createRoot(document.getElementById("root")!);
const raf = () => new Promise<void>((r) => requestAnimationFrame(() => r()));
window.totalFrames = () => (window.__VIDEO__ ? totalFrames(window.__VIDEO__) : 0);
window.pendingRenders = pendingRenders;
window.setFrame = async (n: number) => {
  const spec = window.__VIDEO__!;
  root.render(
    <FrameProvider frame={n} config={{ fps: spec.fps, width: spec.width, height: spec.height, durationInFrames: totalFrames(spec) }}>
      <Video spec={spec} />
    </FrameProvider>,
  );
  await raf();
  await raf();
  const started = Date.now();
  while (pendingRenders().length) {
    if (Date.now() - started > 60000) throw new Error("BIE_RENDER_TIMEOUT:" + pendingRenders().join(","));
    await new Promise((r) => setTimeout(r, 10));
  }
  await raf();
  const images = Array.from(document.images).filter((img) => !img.complete);
  await Promise.all(images.map((img) => new Promise((r) => { img.onload = img.onerror = r; })));
};
window.ready = true;
