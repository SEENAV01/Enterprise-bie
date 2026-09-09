from pathlib import Path
import json

ROOT_TSX = """import React from "react";
import { Composition } from "remotion";
import { BIELesson } from "./BIELesson";

export const Root: React.FC = () => (
  <Composition
    id="BIELesson"
    component={BIELesson}
    durationInFrames={DURATION_FRAMES}
    fps={30}
    width={1920}
    height={1080}
  />
);
"""

LESSON_TSX = """import React from "react";
import { AbsoluteFill, Sequence } from "remotion";

type Scene = {
  scene_id: string;
  duration_seconds: number;
  audio: { type: string; text: string };
  visuals: { type: string; text?: string }[];
};

const scenes: Scene[] = SCENES_JSON;

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
"""

def render_frames(scene_dsl):
    return sum(max(1, round(s.get("duration_seconds", 1) * 30))
               for s in scene_dsl.get("scenes", []))

def generate_remotion_project(scene_dsl, output_dir):
    out = Path(output_dir)
    remotion = out / "generated" / "remotion"
    src = remotion / "src"
    src.mkdir(parents=True, exist_ok=True)
    frames = render_frames(scene_dsl)

    (src / "Root.tsx").write_text(
        ROOT_TSX.replace("DURATION_FRAMES", str(frames)), encoding="utf-8"
    )
    (src / "BIELesson.tsx").write_text(
        LESSON_TSX.replace(
            "SCENES_JSON",
            json.dumps(scene_dsl.get("scenes", []), ensure_ascii=False)
        ), encoding="utf-8"
    )
    (src / "index.tsx").write_text(
        'import { registerRoot } from "remotion";\n'
        'import { Root } from "./Root";\n'
        'registerRoot(Root);\n', encoding="utf-8"
    )
    (remotion / "package.json").write_text(json.dumps({
        "name":"bie-remotion-output",
        "private":True,
        "scripts":{
            "start":"remotion studio",
            "render":"remotion render src/index.tsx BIELesson out/bie-lesson.mp4"
        },
        "dependencies":{
            "@remotion/cli":"latest",
            "remotion":"latest",
            "react":"latest",
            "react-dom":"latest"
        }
    }, indent=2), encoding="utf-8")

    return {
        "project_dir": str(remotion),
        "composition_id":"BIELesson",
        "duration_in_frames":frames,
        "fps":30,
        "width":1920,
        "height":1080,
        "entry":"remotion/src/index.tsx"
    }

def validate_generated_project(meta):
    errors=[]
    for key in ["project_dir","composition_id","duration_in_frames","entry"]:
        if not meta.get(key):
            errors.append(f"missing generated metadata: {key}")
    if meta.get("duration_in_frames",0) <= 0:
        errors.append("non-positive duration")
    return {"passed":not errors,"errors":errors}
