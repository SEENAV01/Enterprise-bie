from dataclasses import dataclass
@dataclass(frozen=True)
class ScenePacing: scene_id:str; target_seconds:float; pace_band:str; reason:str
def build_pacing_plan(scene_loads,base_seconds=35.0):
    if base_seconds<=0: raise ValueError("base")
    out=[]
    for sid,load,importance in scene_loads:
        if not sid.strip() or any(not 0<=x<=1 for x in (load,importance)): raise ValueError("scene")
        sec=base_seconds*(.65+.8*load+.45*importance)
        band="FAST" if sec<base_seconds*.9 else "SLOW" if sec>base_seconds*1.35 else "NORMAL"
        out.append(ScenePacing(sid,round(sec,2),band,"load+importance weighted duration"))
    return tuple(out)
