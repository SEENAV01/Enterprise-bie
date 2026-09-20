from dataclasses import dataclass,replace
from typing import Mapping,Any
class AccessibilityIntegrationError(ValueError): pass
@dataclass(frozen=True)
class AccessibleVisualNode:
    node_id:str; role:str; font_px:float|None=None; foreground:str|None=None; background:str|None=None; color_category:str|None=None; secondary_encoding:str|None=None; alt_mode:str|None=None; alt_required:bool=False; payload:Mapping[str,Any]|None=None
@dataclass(frozen=True)
class AccessibilityAction:
    node_id:str; action:str; reason:str; blocking:bool
@dataclass(frozen=True)
class AccessibilityIntegrationResult:
    nodes:tuple[AccessibleVisualNode,...]; actions:tuple[AccessibilityAction,...]; blocked:bool; review_required:bool=True; accepted:bool=False
def integrate_accessibility(nodes,*,min_font_px=18,contrast_results=None,allow_auto_repair=True):
    cr=dict(contrast_results or {});out=[];actions=[]
    for n0 in nodes:
        n=n0
        if n.font_px is not None and n.font_px<min_font_px:
            if allow_auto_repair: n=replace(n,font_px=float(min_font_px));actions.append(AccessibilityAction(n.node_id,'increase_font',f'raised to {min_font_px}px',False))
            else: actions.append(AccessibilityAction(n.node_id,'block','font below readable floor',True))
        if n.node_id in cr and not cr[n.node_id]: actions.append(AccessibilityAction(n.node_id,'block','contrast check failed',True))
        if n.color_category and not n.secondary_encoding: actions.append(AccessibilityAction(n.node_id,'block','color-only information encoding',True))
        if n.alt_required and not n.alt_mode: actions.append(AccessibilityAction(n.node_id,'block','missing alt-description intent',True))
        out.append(n)
    return AccessibilityIntegrationResult(tuple(out),tuple(actions),any(a.blocking for a in actions),True,False)
def assert_accessible_for_handoff(r):
    if r.blocked: raise AccessibilityIntegrationError('accessibility blockers prevent handoff')
    return True
