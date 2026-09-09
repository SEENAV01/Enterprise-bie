
from .orchestrator import Pipeline
from .contracts import validate_stage_output

def register_demo_handlers(p):
    def h(stage,next_key):
        def fn(x,job):
            # Deterministic integration contract; replace each handler with real implementation.
            out=dict(x)
            if stage=="M1": out={"book_id":"demo","source":x}
            elif stage=="M2": out={"pages":[{"page":1,"text":"demo"}]}
            elif stage=="M3": out={"units":[{"id":"u1","kind":"concept"}]}
            elif stage=="M4": out={"nodes":[{"id":"u1","scope":"BOOK_INTERNAL"}],"edges":[]}
            elif stage=="M5": out={"decision":"PASS","scores":{"overall":1.0}}
            elif stage=="M6": out={"sequence":[{"type":"concept","refs":["u1"]}]}
            elif stage=="M7": out={"scenes":[{"scene_id":"S1","duration_frames":300}]}
            elif stage=="M8": out={"games":[{"game_id":"G1","game_type":"mcq"}]}
            validate_stage_output(stage,out); return out
        return fn
    for s in p.STAGES:p.register(s,h(s,None))
