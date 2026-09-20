"""H6-004: source-bound caption/voice scheduling.

Remotion Sequence owns scene scheduling; Audio trimBefore owns source trimming.
Both intervals derive from the SAME integer-frame plan. This implementation uses
Sequence explicitly; it does not trigger playback from effect callbacks.
"""
from __future__ import annotations
from .react_emitter_common import emitted_file
from .element_compiler_common import jsx


def emit_narration(plan):
    if not plan['narration']:
        return None
    source = '''import React from "react";
import {Sequence, staticFile, useVideoConfig} from "remotion";
import {Audio} from "@remotion/media";
import {cues, EXPECTED_FPS} from "../runtime/frame-runtime";
export const BieNarration: React.FC = () => {
  if (useVideoConfig().fps !== EXPECTED_FPS) throw new Error("FRAME_RUNTIME_FPS_MISMATCH");
  return <>{cues.map(c => <Sequence key={c.cue_id} name={c.cue_id} from={c.start_frame}
      durationInFrames={c.end_frame-c.start_frame} layout="none">
    <Audio src={staticFile(c.public_path)} trimBefore={c.trim_before_frames}
      trimAfter={c.trim_before_frames+c.end_frame-c.start_frame} volume={c.volume}
      onError={(): "fail" => "fail"} />
  </Sequence>)}</>;
};
'''
    return emitted_file('src/audio/BieNarration.tsx', source)


def cue_schedule(plan):
    """Inspectable plan, not an audio-render pass receipt."""
    entries = []
    by_id = {a['asset_id']: a for a in plan['audio_assets']}
    for c in plan['narration']:
        a = by_id[c['asset_id']]; fps = plan['fps']
        entries.append({**c, 'start_drift_ms': c['start_frame'] * 1000 / fps - c['start_ms'],
                        'end_drift_ms': c['end_frame'] * 1000 / fps - c['end_ms'],
                        'source_sample_start_floor': c['trim_before_frames'] * a['sample_rate'] // fps,
                        'source_sample_end_ceil': ((c['trim_before_frames'] + c['end_frame'] - c['start_frame']) * a['sample_rate'] + fps-1)//fps,
                        'playback_rate': 1, 'speech_alignment': 'NOT_VERIFIED'})
    return {'schema_version': 'bie.narration-cue-schedule.v1', 'plan_sha256': plan['plan_sha256'],
            'fps': plan['fps'], 'entries': entries, 'real_remotion_render': 'NOT_RUN', 'accepted': False}
