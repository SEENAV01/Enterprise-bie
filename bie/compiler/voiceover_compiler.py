from .audio_compiler_common import *

def compile_voiceover_track(spec):
    spec=dict(spec)
    track_id=nonblank(spec.get("track_id"),"track_id")
    asset=resolved_asset(spec.get("resolved_asset_path"))
    start_ms=nonnegative_int(spec.get("start_ms",0),"start_ms")
    duration_ms=positive_int(spec.get("duration_ms"),"duration_ms")
    trim_before_ms=nonnegative_int(spec.get("trim_before_ms",0),"trim_before_ms")
    volume=gain(spec.get("volume",1.0))
    source_refs=tuple(spec.get("source_refs",()) or ())
    reasoning_refs=tuple(spec.get("reasoning_refs",()) or ())
    if not source_refs or not reasoning_refs:
        raise AudioCompilerError("voiceover lineage required")

    source=f"""import React from "react";
import {{staticFile, useVideoConfig}} from "remotion";
import {{Audio}} from "@remotion/media";

export const VoiceoverTrack: React.FC = () => {{
  const {{fps}} = useVideoConfig();
  const fromFrame = Math.round(({start_ms} / 1000) * fps);
  const durationInFrames = Math.max(1, Math.round(({duration_ms} / 1000) * fps));
  const trimBefore = Math.round(({trim_before_ms} / 1000) * fps);

  return (
    <Audio
      src={{staticFile({js(asset)})}}
      from={{fromFrame}}
      durationInFrames={{durationInFrames}}
      trimBefore={{trimBefore}}
      volume={{{volume}}}
    />
  );
}};
"""
    return artifact(
        track_id,
        f"src/audio/voiceover-{track_id}.tsx",
        source,
        deps=("@remotion/media",),
        assets=(asset,),
    )
