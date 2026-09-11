"""RE-TEMP-057 — Detect dangerous path/content collisions before canonical overlay."""
from dataclasses import dataclass

@dataclass(frozen=True)
class FileRecord:
    path: str
    sha256: str
    task_id: str

@dataclass(frozen=True)
class Collision:
    path: str
    existing_task_id: str
    incoming_task_id: str
    kind: str

def detect_collisions(existing, incoming):
    by_path={x.path:x for x in existing}
    out=[]
    for inc in incoming:
        prev=by_path.get(inc.path)
        if prev is None:
            continue
        kind="IDENTICAL" if prev.sha256==inc.sha256 else "CONTENT_CONFLICT"
        out.append(Collision(inc.path,prev.task_id,inc.task_id,kind))
    return tuple(sorted(out,key=lambda c:(c.path,c.incoming_task_id)))

def blocking_collisions(existing,incoming):
    return tuple(c for c in detect_collisions(existing,incoming) if c.kind=="CONTENT_CONFLICT")
