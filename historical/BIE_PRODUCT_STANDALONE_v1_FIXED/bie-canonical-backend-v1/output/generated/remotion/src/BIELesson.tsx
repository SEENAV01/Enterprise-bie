import React from "react";
import { AbsoluteFill, Sequence } from "remotion";

type Scene = {
  scene_id: string;
  duration_seconds: number;
  audio: { type: string; text: string };
  visuals: { type: string; text?: string }[];
};

const scenes: Scene[] = [{"scene_id": "visual:0001", "script_id": "script:demo:h1", "duration_seconds": 2.9, "audio": {"type": "narration", "text": "Electric charge is a property of matter.", "source_blocks": ["demo:p1"]}, "visuals": [{"type": "title", "text": "Chapter 1: Electric Charge", "source": "script_section"}, {"type": "source_text", "text": "Electric charge is a property of matter.", "source_blocks": ["demo:p1"]}], "transitions": {"in": "cut", "out": "cut"}, "grounding": {"source_blocks": ["demo:p1"]}}];

export const BIELesson: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill>
      {scenes.map((scene) => {
        const start = from;
        const duration = Math.max(1, Math.round(scene.duration_seconds * 30));
        from += duration;
        return (
          <Sequence key={scene.scene_id} from={start} durationInFrames={duration}>
            <AbsoluteFill style={{
              padding: 80, fontFamily: "Arial, sans-serif",
              justifyContent: "center", alignItems: "center"
            }}>
              <div style={{textAlign:"center", maxWidth:1500}}>
                <h1>{scene.visuals[0]?.text || ""}</h1>
                <p style={{fontSize:42, lineHeight:1.35}}>
                  {scene.audio.text}
                </p>
              </div>
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
