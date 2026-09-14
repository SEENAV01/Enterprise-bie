from dataclasses import dataclass
@dataclass(frozen=True)
class Payoff: gap_id:str; resolving_scene:str; resolution:str; evidence_ids:tuple[str,...]
def bind_payoffs(gaps,resolutions):
    out=[]
    for gid,gev in gaps:
        if gid not in resolutions: raise ValueError("unresolved gap")
        scene,res,ev=resolutions[gid]; merged=tuple(sorted(set(gev)|set(ev)))
        if not scene.strip() or not res.strip() or not merged: raise ValueError("payoff")
        out.append(Payoff(gid,scene,res,merged))
    return tuple(sorted(out,key=lambda x:x.gap_id))
