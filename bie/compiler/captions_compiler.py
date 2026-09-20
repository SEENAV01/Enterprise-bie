from .audio_compiler_common import *

def normalize_caption(item):
    item=dict(item)
    text=nonblank(item.get("text"),"caption.text")
    start=nonnegative_int(item.get("startMs"),"caption.startMs")
    end=nonnegative_int(item.get("endMs"),"caption.endMs")
    if end<=start:
        raise AudioCompilerError("caption endMs must exceed startMs")
    timestamp=item.get("timestampMs")
    if timestamp is not None:
        timestamp=nonnegative_int(timestamp,"caption.timestampMs")
    confidence=item.get("confidence")
    if confidence is not None:
        confidence=gain(confidence,"caption.confidence")
    return {
        "text":text,
        "startMs":start,
        "endMs":end,
        "timestampMs":timestamp,
        "confidence":confidence,
    }

def compile_captions(captions):
    normalized=[normalize_caption(x) for x in captions]
    if not normalized:
        raise AudioCompilerError("captions required")
    normalized.sort(key=lambda x:(x["startMs"],x["endMs"],x["text"]))
    source=f"""import React from "react";
import type {{Caption}} from "@remotion/captions";
import {{useCurrentFrame, useVideoConfig}} from "remotion";

export const captions: Caption[] = {js(normalized)};

export const BieCaptions: React.FC = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  const active = captions.find((caption) => nowMs >= caption.startMs && nowMs < caption.endMs);

  if (!active) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      style={{{{
        position: "absolute",
        left: "8%",
        right: "8%",
        bottom: "6%",
        textAlign: "center",
        fontSize: 42,
      }}}}
    >
      {{active.text}}
    </div>
  );
}};
"""
    return artifact(
        "captions",
        "src/audio/captions.tsx",
        source,
        deps=("@remotion/captions",),
    ),tuple(normalized)
