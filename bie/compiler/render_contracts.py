"""BUILD render contracts; extends the restored BuildError/composition contracts."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any
import json
import math
import re
from .artifact_hashing import require_sha256, safe_relative
from .build_common import BuildError
from .remotion_composition_discovery import CompositionDescriptor
from .render_logs import safe_token

@dataclass(frozen=True)
class RenderRequest:
    workspace: str
    entrypoint: str
    composition: CompositionDescriptor
    output_path: str
    scene_fingerprint: str
    run_id: str
    timeout_s: float = 600
    frame_timeout_ms: int = 30000
    concurrency: int = 1
    crf: int = 18
    props_file: str | None = None
    browser_executable: str | None = None
    require_audio: bool = False
    node_bin: str = "node"
    ffprobe_bin: str = "ffprobe"
    max_output_bytes: int = 2 * 1024 * 1024

    def __post_init__(self) -> None:
        safe_relative(self.entrypoint)
        safe_relative(self.output_path)
        if not self.entrypoint.endswith((".ts", ".tsx", ".js", ".jsx")):
            raise BuildError("entrypoint must be a local JavaScript/TypeScript file")
        if not self.output_path.endswith(".mp4"):
            raise BuildError("this governed render profile produces H.264 MP4 only")
        if self.output_path.split("/")[0] in {"src", "public", "node_modules", "render-evidence"}:
            raise BuildError("output must not overwrite source, dependencies or evidence")
        require_sha256(self.scene_fingerprint, "scene_fingerprint")
        safe_token(self.run_id, "run_id")
        descriptor = self.composition
        if not isinstance(descriptor, CompositionDescriptor):
            raise BuildError("existing CompositionDescriptor required")
        if not isinstance(descriptor.composition_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", descriptor.composition_id):
            raise BuildError("Remotion composition ID must contain letters, digits or hyphens")
        for name in ("width", "height", "duration_in_frames"):
            value = getattr(descriptor, name)
            if type(value) is not int or value < 1:
                raise BuildError(f"known positive integer {name} required")
        if descriptor.width % 2 or descriptor.height % 2:
            raise BuildError("H.264 yuv420p requires even dimensions")
        fps = descriptor.fps
        if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
            raise BuildError("known positive finite fps required")
        for name in ("frame_timeout_ms", "concurrency", "max_output_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise BuildError(f"{name} must be positive integer")
        if type(self.crf) is not int or not 0 <= self.crf <= 51:
            raise BuildError("crf outside H.264 range")
        if isinstance(self.timeout_s, bool) or not isinstance(self.timeout_s, (int, float)) or not math.isfinite(self.timeout_s) or self.timeout_s <= 0:
            raise BuildError("timeout_s must be positive and finite")
        if type(self.require_audio) is not bool:
            raise BuildError("require_audio must be boolean")
        if self.props_file is not None:
            safe_relative(self.props_file)
            if not self.props_file.endswith(".json"):
                raise BuildError("props file must be JSON")
        for name in ("node_bin", "ffprobe_bin"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value) or value.startswith("-"):
                raise BuildError(f"invalid {name}")
        if self.browser_executable is not None and not Path(self.browser_executable).is_absolute():
            raise BuildError("browser_executable must be an absolute operator-controlled path")

@dataclass(frozen=True)
class RenderPlan:
    mode: str
    first_frame: int
    last_frame: int
    expected_frames: int

def make_render_plan(request: RenderRequest, mode: str, *, first_frame: int = 0,
                     frame_count: int | None = None) -> RenderPlan:
    total = request.composition.duration_in_frames
    if mode == "full":
        if first_frame != 0 or frame_count is not None:
            raise BuildError("full render cannot select a partial frame range")
        return RenderPlan("full", 0, total - 1, total)
    if mode != "smoke":
        raise BuildError("unknown render mode")
    if type(first_frame) is not int or first_frame < 0:
        raise BuildError("first_frame must be a nonnegative integer")
    if type(frame_count) is not int or frame_count < 1:
        raise BuildError("smoke frame_count must be a positive integer")
    if first_frame + frame_count > total:
        raise BuildError("smoke frame range exceeds composition")
    return RenderPlan("smoke", first_frame, first_frame + frame_count - 1, frame_count)

@dataclass(frozen=True)
class MediaProbe:
    width: int
    height: int
    fps: float
    decoded_frames: int
    duration_s: float
    codec_name: str
    pixel_format: str
    audio_streams: int

@dataclass(frozen=True)
class RenderReceipt:
    schema_version: str
    run_id: str
    mode: str
    composition_id: str
    passed: bool
    failure_code: str | None
    errors: tuple[str, ...]
    output_path: str | None
    expected_frames: int
    media: MediaProbe | None
    input_sha256: str | None
    recipe_sha256: str | None
    evidence_directory: str
    execution_kind: str
    process_started: bool
    artifact_sha256: str | None = None
    artifact_size_bytes: int | None = None
    accepted: bool = False

def parse_media_probe(text: str, request: RenderRequest, plan: RenderPlan) -> MediaProbe:
    try:
        raw = json.loads(text)
        if not isinstance(raw, dict):
            raise BuildError("ffprobe response must be an object")
        streams = raw["streams"]
        if not isinstance(streams, list) or not all(isinstance(item, dict) for item in streams):
            raise BuildError("ffprobe streams must be objects")
        video = [s for s in streams if s.get("codec_type") == "video"]
        audio = [s for s in streams if s.get("codec_type") == "audio"]
        if len(video) != 1:
            raise BuildError("exactly one video stream required")
        stream = video[0]
        frames = int(stream["nb_read_frames"])
        width, height = int(stream["width"]), int(stream["height"])
        fps = float(Fraction(stream["avg_frame_rate"]))
        duration = float(stream.get("duration", raw.get("format", {}).get("duration")))
        if not math.isfinite(duration) or duration <= 0 or not math.isfinite(fps) or fps <= 0:
            raise BuildError("nonfinite/invalid media timing")
        if (width, height) != (request.composition.width, request.composition.height):
            raise BuildError("rendered dimensions do not match composition")
        if frames != plan.expected_frames:
            raise BuildError(f"decoded frame count mismatch: {frames} != {plan.expected_frames}")
        if not math.isclose(fps, float(request.composition.fps), rel_tol=1e-6, abs_tol=1e-6):
            raise BuildError("rendered fps mismatch")
        if abs(duration - frames / float(request.composition.fps)) > max(0.002, 0.51 / fps):
            raise BuildError("rendered duration mismatch")
        if stream.get("codec_name") != "h264" or stream.get("pix_fmt") != "yuv420p":
            raise BuildError("rendered codec/pixel-format mismatch")
        if request.require_audio and not audio:
            raise BuildError("required audio track missing")
        return MediaProbe(width, height, fps, frames, duration, stream["codec_name"], stream["pix_fmt"], len(audio))
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        if isinstance(exc, BuildError):
            raise
        raise BuildError("invalid ffprobe media evidence") from exc
