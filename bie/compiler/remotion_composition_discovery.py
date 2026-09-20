from dataclasses import dataclass
import re,json
from .build_common import BuildError
@dataclass(frozen=True)
class CompositionDescriptor:composition_id:str;width:int|None;height:int|None;fps:float|None;duration_in_frames:int|None
@dataclass(frozen=True)
class CompositionDiscoveryReceipt:source_kind:str;compositions:tuple[CompositionDescriptor,...];passed:bool;empirical_cli:bool;accepted:bool=False
def discover_compositions_static(text):
    if not isinstance(text,str):raise BuildError("source must be str")
    out=[]
    for block in re.findall(r"<Composition\b([\s\S]*?)/>",text):
        m=re.search(r'\bid=\{["\']([^"\']+)["\']\}|\bid=["\']([^"\']+)["\']',block)
        if not m:continue
        cid=m.group(1) or m.group(2)
        def num(name):
            n=re.search(rf'\b{name}=\{{([0-9]+(?:\.[0-9]+)?)\}}',block);return float(n.group(1)) if n else None
        wi,he,fp,du=num("width"),num("height"),num("fps"),num("durationInFrames")
        out.append(CompositionDescriptor(cid,int(wi) if wi is not None else None,int(he) if he is not None else None,fp,int(du) if du is not None else None))
    out=tuple(sorted(out,key=lambda x:x.composition_id))
    return CompositionDiscoveryReceipt("static-tsx",out,bool(out),False,False)
def remotion_discovery_command(entrypoint,npx_bin="npx"):
    if not isinstance(entrypoint,str) or not entrypoint or entrypoint.startswith("-"):raise BuildError("entrypoint invalid")
    return (npx_bin,"remotion","compositions",entrypoint,"--log=error")
def parse_remotion_compositions_json(text):
    data=json.loads(text);data=data.get("compositions") if isinstance(data,dict) and "compositions" in data else data
    if not isinstance(data,list):raise BuildError("composition JSON must be list")
    out=[]
    for x in data:
        cid=x.get("id") or x.get("compositionId")
        if not cid:raise BuildError("composition id missing")
        out.append(CompositionDescriptor(str(cid),x.get("width"),x.get("height"),float(x["fps"]) if x.get("fps") is not None else None,x.get("durationInFrames")))
    return tuple(sorted(out,key=lambda x:x.composition_id))
