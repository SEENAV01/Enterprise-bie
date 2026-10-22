// Preview harness: renders any frame of a VideoSpec in a plain browser page (window.setFrame), so BIE can take
// stills for the reviewer AI and encode quick previews with ffmpeg without installing Remotion.
import React from "react";
import { createRoot } from "react-dom/client";
import { FrameProvider } from "remotion";
import { Video, VideoSpec, totalFrames } from "../blocks/Video";

declare global { interface Window { __VIDEO__?: VideoSpec; setFrame: (n: number) => Promise<void>; ready: boolean; totalFrames: () => number } }

const root = createRoot(document.getElementById("root")!);
window.totalFrames = () => (window.__VIDEO__ ? totalFrames(window.__VIDEO__) : 0);
window.setFrame = (n: number) => new Promise((resolve) => {
  const spec = window.__VIDEO__!;
  root.render(
    <FrameProvider frame={n} config={{ fps: spec.fps, width: spec.width, height: spec.height, durationInFrames: totalFrames(spec) }}>
      <Video spec={spec} />
    </FrameProvider>,
  );
  requestAnimationFrame(() => requestAnimationFrame(() => {
    const images = Array.from(document.images).filter((img) => !img.complete);
    Promise.all(images.map((img) => new Promise((r) => { img.onload = img.onerror = r; }))).then(() => resolve());
  }));
});
window.ready = true;
