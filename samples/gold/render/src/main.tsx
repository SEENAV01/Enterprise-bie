import React from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { App, Timeline } from "./App";

declare global {
  interface Window { __TIMELINE__: Timeline; setFrame: (f: number) => Promise<boolean>; ready: boolean }
}

const root = createRoot(document.getElementById("root")!);
window.setFrame = async (frame: number) => {
  flushSync(() => root.render(<App timeline={window.__TIMELINE__} frame={frame} />));
  await document.fonts.ready;
  return true;
};
window.ready = true;
