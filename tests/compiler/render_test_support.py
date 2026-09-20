"""Explicit test doubles. This module never claims that Remotion rendered media."""
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
from bie.compiler.build_common import ProcessReceipt
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.render_process import RenderProcessResult, run_bounded_process

def fixture_workspace(root: Path) -> RenderRequest:
    (root / "src").mkdir(parents=True)
    (root / "src/index.ts").write_text("// TEST ONLY: not a real Remotion project\n")
    (root / "tsconfig.json").write_text('{}\n')
    deps = {"remotion": "4.0.506", "@remotion/cli": "4.0.506", "react": "19.0.0", "react-dom": "19.0.0"}
    package = {"name": "bie-test-double", "version": "0.0.0", "private": True, "bie_test_fixture": True, "dependencies": deps}
    (root / "package.json").write_text(json.dumps(package))
    packages = {"": {"dependencies": deps}}
    for name, version in deps.items():
        directory = root / "node_modules" / name
        directory.mkdir(parents=True)
        (directory / "package.json").write_text(json.dumps({"name": name, "version": version, "test_only": True}))
        packages[f"node_modules/{name}"] = {"version": version}
    (root / "node_modules/@remotion/cli/remotion-cli.js").write_text('// TEST DOUBLE: never run as a real renderer\n')
    (root / "package-lock.json").write_text(json.dumps({"name": package["name"], "lockfileVersion": 3, "packages": packages}))
    return RenderRequest(str(root), "src/index.ts", CompositionDescriptor("BieFixture", 320, 180, 12.0, 12),
                         "out/full.mp4", "a" * 64, "test-run")

@lru_cache(maxsize=16)
def media_bytes(frames=12, width=320, height=180, fps=12, audio=False) -> bytes:
    """REAL FFmpeg makes an explicit technical test-pattern MP4, not BIE content."""
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / 'fixture.mp4'
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                   f"testsrc2=size={width}x{height}:rate={fps}"]
        if audio:
            command += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000"]
        command += ["-t", str(frames / fps), "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-preset", "ultrafast", "-threads", "1"]
        if audio:
            command += ["-c:a", "aac", "-shortest"]
        command += ["-y", str(output)]
        subprocess.run(command, check=True, capture_output=True, timeout=20)
        return output.read_bytes()

def fake_result(command, cwd, *, outcome="SUCCEEDED", code=0, stdout="fixture render\n", stderr=""):
    return RenderProcessResult(ProcessReceipt(tuple(command), str(cwd), code, stdout, stderr, 0,
                                              outcome == "SUCCEEDED", False), outcome, True,
                               len(stdout.encode()), len(stderr.encode()))

class FixtureRunner:
    """Injects a media file for the render call, but uses REAL ffprobe afterward."""
    def __init__(self, *, frames=None, media=None, outcome="SUCCEEDED", code=0, mutate=None, no_file=False):
        self.frames = frames
        self.media = media
        self.outcome = outcome
        self.code = code
        self.mutate = mutate
        self.no_file = no_file
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(tuple(command))
        if len(command) > 2 and command[2] == "render":
            output = Path(command[5])
            count = self.frames
            for arg in command:
                if arg.startswith("--frames=") and count is None:
                    start, end = map(int, arg.split("=", 1)[1].split("-"))
                    count = end - start + 1
            if not self.no_file:
                output.write_bytes(self.media if self.media is not None else media_bytes(frames=count or 12))
            if self.mutate:
                self.mutate(Path(kwargs["cwd"]))
            return fake_result(command, kwargs["cwd"], outcome=self.outcome, code=self.code)
        return run_bounded_process(command, **kwargs)
