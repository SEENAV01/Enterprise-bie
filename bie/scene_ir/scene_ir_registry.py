from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .unified_scene_ir_contract import UnifiedElement, UnifiedTrack, UnifiedSceneIRDocument

class SceneIRRegistryError(ValueError): pass

ELEMENT_TYPES = (
 "text","equation","shape","vector","diagram","graph","chart","map","timeline",
 "image","video","simulation","model2d","model3d","annotation","callout","highlight","particle_system"
)
ACTIONS = (
 "enter","exit","emphasize","reveal","transform","morph","trace","path_follow",
 "camera","simulation_state","static_focus","static_trace","crossfade_states",
 "state_snapshots","progressive_static_trace","path_endpoints_with_progress_marker"
)

@dataclass(frozen=True)
class ElementTypeSpec:
    element_type:str
    required_props:tuple[str,...]=()
    asset_backed:bool=False

class SceneIRRegistry:
    def __init__(self):
        self._types={}
        self._actions=set()

    def register_element_type(self,spec):
        if spec.element_type in self._types:
            raise SceneIRRegistryError("duplicate element type")
        self._types[spec.element_type]=spec

    def register_action(self,action):
        if action in self._actions:
            raise SceneIRRegistryError("duplicate action")
        self._actions.add(action)

    def normalize_document(self,doc):
        for e in doc.elements:
            spec=self._types.get(e.element_type)
            if spec is None:
                raise SceneIRRegistryError("unknown element type:"+e.element_type)
            for p in spec.required_props:
                if p not in e.props:
                    raise SceneIRRegistryError(f"{e.element_type} missing required prop {p}")
            if spec.asset_backed and "asset_ref" not in e.props:
                raise SceneIRRegistryError(f"{e.element_type} missing asset_ref")
        for t in doc.tracks:
            if t.action not in self._actions:
                raise SceneIRRegistryError("unknown action:"+t.action)
        return doc

    def snapshot(self):
        return {
          "element_types":tuple(sorted(self._types)),
          "actions":tuple(sorted(self._actions)),
        }

def default_registry():
    r=SceneIRRegistry()
    required={
      "text":("text",),"equation":("expression",),"image":("asset_ref",),
      "video":("asset_ref",),"model3d":("asset_ref",)
    }
    for et in ELEMENT_TYPES:
        r.register_element_type(ElementTypeSpec(et,required.get(et,()),et in {"image","video","model3d"}))
    for a in ACTIONS:
        r.register_action(a)
    return r
