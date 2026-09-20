from dataclasses import dataclass

class AniAccessibilityError(ValueError): pass

HIGH_MOTION={"camera","path_follow","trace","morph","simulation_state"}

@dataclass(frozen=True)
class AccessibilityPolicy:
    reduced_motion_required:bool
    max_flash_hz:float=3.0
    allow_orbit_camera:bool=True

@dataclass(frozen=True)
class AccessibilityResult:
    status:str
    replacements:tuple[tuple[str,str],...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def enforce_animation_accessibility(tracks,policy):
    blockers=[];warnings=[];replacements=[]
    for t in tracks:
        tid=getattr(t,"track_id",None) or t.get("track_id")
        action=getattr(t,"semantic_action",None) or t.get("semantic_action")
        payload=getattr(t,"payload",{}) if not isinstance(t,dict) else t.get("payload",{})
        reduced=getattr(t,"reduced_motion_variant",None) if not isinstance(t,dict) else t.get("reduced_motion_variant")
        flash=float(payload.get("flash_hz",0) or 0)
        if flash>policy.max_flash_hz:
            blockers.append("flash_frequency_exceeded:"+tid)
        if policy.reduced_motion_required and action in HIGH_MOTION:
            if not reduced: blockers.append("missing_reduced_motion_variant:"+tid)
            else: replacements.append((tid,reduced))
        if action=="camera" and payload.get("camera_mode")=="orbit" and not policy.allow_orbit_camera:
            if reduced: replacements.append((tid,reduced))
            else: blockers.append("orbit_camera_disallowed:"+tid)
    status="BLOCKED" if blockers else ("REVIEW" if warnings else "PASS")
    return AccessibilityResult(status,tuple(sorted(set(replacements))),
                               tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),True,False)

def require_accessibility_pass(result):
    if result.status=="BLOCKED":
        raise AniAccessibilityError("accessibility blocked")
    return True
