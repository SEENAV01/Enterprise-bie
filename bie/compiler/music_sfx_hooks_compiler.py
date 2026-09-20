from .audio_compiler_common import *

def compile_music_sfx_hooks(hooks):
    normalized=[]
    seen=set()
    for item in hooks:
        item=dict(item)
        hook_id=nonblank(item.get("hook_id"),"hook_id")
        if hook_id in seen:
            raise AudioCompilerError("duplicate hook_id")
        seen.add(hook_id)
        kind=item.get("kind")
        if kind not in {"music","sfx"}:
            raise AudioCompilerError("kind must be music or sfx")
        normalized.append({
            "hook_id":hook_id,
            "kind":kind,
            "asset":resolved_asset(item.get("resolved_asset_path")),
            "start_ms":nonnegative_int(item.get("start_ms",0),"start_ms"),
            "duration_ms":positive_int(item.get("duration_ms"),"duration_ms"),
            "volume":gain(item.get("volume",0.25 if kind=="music" else 1.0)),
            "loop":bool(item.get("loop",False)),
            "duck":bool(item.get("duck_under_voiceover",False)),
        })
    normalized.sort(key=lambda x:(x["start_ms"],x["hook_id"]))

    lines=[
      'import React from "react";',
      'import {staticFile, useVideoConfig} from "remotion";',
      'import {Audio} from "@remotion/media";',
      '',
      'export const BieMusicSfxHooks: React.FC = () => {',
      '  const {fps} = useVideoConfig();',
      '  return <>',
    ]
    warnings=[]
    assets=[]
    for item in normalized:
        effective=item["volume"]*0.45 if item["duck"] else item["volume"]
        if item["duck"]:
            warnings.append("static_ducking_not_sidechain_compression:"+item["hook_id"])
        assets.append(item["asset"])
        lines += [
          '    <Audio',
          f'      key={{{js(item["hook_id"])}}}',
          f'      src={{staticFile({js(item["asset"])})}}',
          f'      from={{Math.round(({item["start_ms"]} / 1000) * fps)}}',
          f'      durationInFrames={{Math.max(1, Math.round(({item["duration_ms"]} / 1000) * fps))}}',
          f'      volume={{{effective}}}',
          f'      loop={{{str(item["loop"]).lower()}}}',
          '    />',
        ]
    lines += ['  </>;','};','']
    return artifact(
        "music-sfx-hooks",
        "src/audio/music-sfx-hooks.tsx",
        "\n".join(lines),
        deps=("@remotion/media",),
        assets=tuple(assets),
        warnings=tuple(warnings),
    )
