
class RenderImageError(ValueError):pass
REQUIRED_TOOLS={"node","remotion","ffmpeg","chromium"}
def validate_manifest(m):
 tools=set(m.get("tools",[]))
 if not REQUIRED_TOOLS.issubset(tools):raise RenderImageError("render toolchain incomplete")
 if not m.get("fonts_pinned"):raise RenderImageError("fonts must be pinned")
 if not m.get("gpu_optional",False):raise RenderImageError("gpu capability declaration required")
 return True
