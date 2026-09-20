#!/usr/bin/env python3
"""Generate an isolated technical Remotion project using the original BIE emitters.

This is not a textbook lesson, a game, or product-acceptance evidence. First-party
emitter output is not manually patched. Existing destination files are refused.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bie.compiler.react_project_emitter import emit_react_project
from bie.compiler.root_emitter import emit_root
from bie.compiler.composition_emitter import emit_composition
from bie.compiler.scene_component_emitter import emit_scene_component
from bie.compiler.reusable_primitives_emitter import emit_reusable_primitives
from bie.compiler.react_emitter_common import emitted_file
from bie.compiler.deterministic_codegen import plan_deterministic_codegen
from bie.compiler.npm_workspace_generation import generate_npm_workspace
from bie.compiler.artifact_hashing import canonical_json

FIXTURE = {"kind": "TECHNICAL_COMPILER_FIXTURE_NOT_A_LESSON", "composition_id": "BieBuildFixture",
           "width": 640, "height": 360, "fps": 24, "duration_in_frames": 48,
           "description": "Frame-driven primitive reveal and position change"}
LAYER = '''import React from "react";
import {useCurrentFrame, interpolate} from "remotion";
import {BieReveal} from "./primitives";

export const TechnicalFixture: React.FC = () => {
  const frame = useCurrentFrame();
  const x = interpolate(frame, [0, 47], [50, 490], {extrapolateRight: "clamp"});
  return <BieReveal durationInFrames={12}>
    <div style={{fontFamily: "sans-serif", padding: 24, color: "black"}}>
      <h2>BIE compiler execution fixture</h2>
      <p>Technical test only — not an accepted learning video.</p>
      <div style={{position: "absolute", left: x, top: 195, width: 64, height: 64,
                   border: "4px solid black", transform: `rotate(${frame * 3}deg)`}} />
      <p style={{position: "absolute", bottom: 20}}>Frame {frame} / 47</p>
    </div>
  </BieReveal>;
};
'''

def generate(destination: Path) -> dict:
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("destination is not empty; refusing to overwrite")
    files = list(emit_react_project(project_name="bie-build-render-fixture",
                                   remotion_version="4.0.506", react_version="19.0.0",
                                   typescript_version="5.9.3"))
    files += [emit_root(),
              emit_composition(composition_id=FIXTURE["composition_id"], width=640, height=360,
                               fps=24, duration_in_frames=48),
              emit_scene_component(layers=({"layer_id": "technical", "component_name": "TechnicalFixture",
                                           "import_path": "./TechnicalFixture", "from_frame": 0,
                                           "duration_in_frames": 48, "props": {}},)),
              emit_reusable_primitives(), emitted_file("src/TechnicalFixture.tsx", LAYER)]
    fingerprint = sha256(canonical_json(FIXTURE)).hexdigest()
    package = json.loads(next(f.content for f in files if f.path == "package.json"))
    receipt = generate_npm_workspace(root=destination, package_name=package["name"],
                                     files=[(f.path, f.content) for f in files if f.path != "package.json"],
                                     scripts=package["scripts"], dependencies=package["dependencies"],
                                     dev_dependencies=package["devDependencies"])
    codegen = plan_deterministic_codegen(scene_fingerprint=fingerprint, compiler_version="1.0.0",
                                         deterministic_seed=0, component_snapshot=(("TechnicalFixture", "./TechnicalFixture"),),
                                         files=[(f.path, f.content) for f in files])
    (destination / "FIXTURE_SOURCE.json").write_text(json.dumps({**FIXTURE, "scene_fingerprint": fingerprint,
                                                                "codegen": asdict(codegen)}, indent=2))
    for mode in ("smoke", "full"):
        request = {"workspace": ".", "entrypoint": "src/index.ts",
                   "composition": {k: FIXTURE[k] for k in ("composition_id", "width", "height", "fps", "duration_in_frames")},
                   "output_path": f"out/{mode}.mp4", "scene_fingerprint": fingerprint,
                   "run_id": f"real-{mode}-001", "timeout_s": 180, "concurrency": 1,
                   "browser_executable": "/usr/bin/chromium"}
        (destination / f"{mode}-request.json").write_text(json.dumps(request, indent=2))
    return {"fixture": FIXTURE, "workspace": asdict(receipt), "scene_fingerprint": fingerprint,
            "accepted": False, "empirical_render": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.destination), indent=2))
