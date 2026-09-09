from remotion_spec import build_remotion_spec
from composition import composition_metadata
from determinism import render_policy

def compile_for_remotion(visual, audio=None):
    spec=build_remotion_spec(visual)
    result={
      "schema_version":"5.0",
      "renderer_spec":spec,
      "composition":composition_metadata(spec),
      "render_policy":render_policy(),
      "audio":audio
    }
    return result
