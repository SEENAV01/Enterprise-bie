import React from "react";
import { AbsoluteFill, FrameProvider, interpolate } from "./lite";
import { C, Header, SceneCtx, SceneInfo, Stage } from "./kit";
import { SCENES } from "./scenes";

export type Timeline = { fps: number; width: number; height: number; frames: number; seconds: number; title: string;
  scenes: (SceneInfo & { component: string; start: number })[] };

const SECTION: Record<string, [string, string]> = {
  hook: ["SOCHO", C.amber], title: ["PART 1", C.sky], "prereq-cell": ["PREREQUISITE", C.violet], "prereq-division": ["PREREQUISITE", C.violet],
  tissue: ["CONCEPT", C.sky], ladder: ["CONCEPT", C.sky], growth: ["PLANT TISSUE", C.leaf], "meristem-cells": ["MERISTEMATIC TISSUE", C.leaf],
  apical: ["MERISTEMATIC TISSUE", C.leaf], lateral: ["MERISTEMATIC TISSUE", C.leaf], intercalary: ["MERISTEMATIC TISSUE", C.leaf],
  summary: ["RECAP", C.teal], traps: ["UPSC EXAM TRAPS", C.coral], next: ["AAGE KYA", C.amber],
};

export const App: React.FC<{ timeline: Timeline; frame: number }> = ({ timeline, frame }) => {
  const scene = timeline.scenes.find((s) => frame >= s.start && frame < s.start + s.duration) ?? timeline.scenes[timeline.scenes.length - 1];
  const local = frame - scene.start;
  const Comp = SCENES[scene.component];
  const first = scene.start === 0;
  const fade = Math.min(first ? 1 : interpolate(local, [0, 12], [0, 1]), interpolate(local, [scene.duration - 10, scene.duration], [1, 0]));
  const [section, color] = SECTION[scene.id] ?? ["", C.sky];
  const config = { fps: timeline.fps, width: timeline.width, height: timeline.height, durationInFrames: scene.duration };
  return (
    <FrameProvider frame={local} config={config}>
      <SceneCtx.Provider value={scene}>
        <AbsoluteFill style={{ background: C.bg0 }}>
          <div style={{ position: "absolute", inset: 0, opacity: fade }}>
            <Stage tint={color}>
              <g transform={`translate(960,540) scale(${1 + 0.035 * (local / scene.duration)}) translate(-960,-540)`}>
                {Comp ? <Comp /> : <text x={960} y={540} fill="#fff" fontSize={60} textAnchor="middle">missing {scene.component}</text>}
              </g>
              {scene.id !== "title" && <Header section={section} color={color} progress={frame / timeline.frames} />}
            </Stage>
          </div>
        </AbsoluteFill>
      </SceneCtx.Provider>
    </FrameProvider>
  );
};
