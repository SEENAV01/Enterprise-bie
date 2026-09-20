from .text_contracts import *
from dataclasses import dataclass
@dataclass(frozen=True)
class DensityReport:
    total_chars:int
    text_items:int
    occupied_area:float
    chars_per_area:float
    item_density:float
    level:str
    blockers:tuple[str,...]
    review_required:bool=True
def evaluate_text_density(decisions, *, canvas_area=1.0, max_chars_per_area=900.0, max_items=12):
    area=finite(canvas_area,field_name="canvas_area")
    if area<=0: raise DensityError("canvas_area must be > 0")
    if max_chars_per_area<=0 or max_items<1: raise DensityError("invalid density thresholds")
    visible=[d for d in decisions if d.action not in {"omit_optional_text","escalate_text_overflow"} and d.display_text]
    total=sum(len(d.display_text) for d in visible)
    occupied=sum(d.box.width*d.box.height for d in visible if d.box is not None)
    cpa=total/area; item_density=len(visible)/area
    blockers=[]
    if cpa>max_chars_per_area: blockers.append("character_density_exceeded")
    if len(visible)>max_items: blockers.append("item_count_exceeded")
    if occupied>.70*area: blockers.append("text_area_exceeded")
    if blockers: level="high"
    elif cpa>.65*max_chars_per_area or len(visible)>.65*max_items: level="medium"
    else: level="low"
    return DensityReport(total,len(visible),occupied,cpa,item_density,level,tuple(blockers),True)
def density_action(report):
    if report.blockers: return "reduce_or_reflow"
    if report.level=="medium": return "monitor"
    return "keep"
