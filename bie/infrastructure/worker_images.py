
from dataclasses import dataclass
class WorkerImageError(ValueError):pass
@dataclass(frozen=True)
class WorkerImage:
 profile:str;image:str;capabilities:frozenset
REQUIRED={"cpu_general":{"python"},"render_gpu":{"remotion","ffmpeg","gpu"},"browser_game":{"browser","node"},"vision_qa":{"vision"}}
def validate(w):
 if w.profile not in REQUIRED:raise WorkerImageError("unknown profile")
 if ":latest" in w.image or not w.image:raise WorkerImageError("immutable image")
 if not REQUIRED[w.profile].issubset(w.capabilities):raise WorkerImageError("missing capability")
 return True
