from .physics_contracts import *
def animate(ctx,graph_id,points,source_ref,x_label,x_unit,y_label,y_unit,sampled=True,exact_relation=False,domain=None):
    if source_ref not in ctx.evidence_refs:raise GroundingError("source_ref not grounded")
    pts=tuple((finite(x,"x"),finite(y,"y")) for x,y in points)
    if len(pts)<2:raise PhysError("at least two points")
    if sampled and exact_relation:return plan(ctx,":graph","physics_graph_animation","BLOCKED",blockers=("sampled_not_exact",))
    if domain is not None:
        lo,hi=finite(domain[0],"lo"),finite(domain[1],"hi")
        if hi<=lo:raise PhysError("bad domain")
        if any(x<lo or x>hi for x,_ in pts):return plan(ctx,":graph","physics_graph_animation","BLOCKED",blockers=("point_outside_domain",))
    return plan(ctx,":graph","physics_graph_animation",ops=({"op":"draw_axes","x_label":x_label,"x_unit":x_unit,"y_label":y_label,"y_unit":y_unit},{"op":"animate_series","id":graph_id,"points":pts,"sampled":sampled,"exact_relation":exact_relation,"domain":domain}))
