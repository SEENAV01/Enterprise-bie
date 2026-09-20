from .physics_contracts import *
def animate(ctx,field_id,lines,source_ref,direction_declared=True,magnitude_encoding=None,generated_from_model=False):
    if source_ref not in ctx.evidence_refs:raise GroundingError("source_ref not grounded")
    if not direction_declared:return plan(ctx,":field","field_line_animation","BLOCKED",blockers=("direction_not_declared",))
    if generated_from_model and not ctx.model_fingerprint:return plan(ctx,":field","field_line_animation","BLOCKED",blockers=("model_fingerprint_required",))
    clean=[]
    for i,line in enumerate(lines):
        pts=tuple(tuple(finite(v,"point") for v in p) for p in line)
        if len(pts)<2:raise PhysError("short field line")
        clean.append({"id":f"{field_id}:{i}","points":pts})
    if not clean:raise PhysError("field lines required")
    warnings=() if magnitude_encoding else ("line_density_not_magnitude_without_encoding",)
    return plan(ctx,":field","field_line_animation","REVIEW" if warnings else "PASS",
                ops=({"op":"reveal_field_lines","lines":clean,"magnitude_encoding":magnitude_encoding},),warnings=warnings)
