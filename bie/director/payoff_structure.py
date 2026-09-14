from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class Payoff: gap_id:str; resolving_scene:str; resolution:str; evidence_ids:tuple[str,...]
def bind_payoffs(gaps,resolutions):
    out=[]; seen=set()
    if not isinstance(resolutions,dict): raise ValueError("resolution mapping required")
    for gap in items(gaps,"curiosity gaps",required=False):
        gap=items(gap,"gap record")
        if len(gap)!=2: raise ValueError("gap id and evidence required")
        gid,gev=gap; nonblank(gid,"gap id"); gev=ids(gev,"gap evidence",canonical=True)
        if gid in seen: raise ValueError("duplicate gap")
        seen.add(gid)
        if gid not in resolutions: raise ValueError("unresolved gap")
        resolution=items(resolutions[gid],"resolution record")
        if len(resolution)!=3: raise ValueError("scene, resolution and evidence required")
        scene,res,ev=resolution; nonblank(scene,"resolution scene"); nonblank(res,"resolution")
        ev=ids(ev,"resolution evidence",canonical=True); merged=tuple(sorted(set(gev)|set(ev)))
        if not scene.strip() or not res.strip() or not merged: raise ValueError("payoff")
        out.append(Payoff(gid,scene,res,merged))
    return tuple(sorted(out,key=lambda x:x.gap_id))
