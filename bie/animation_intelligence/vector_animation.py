from .physics_contracts import *
def animate(ctx,vector_id,components,unit,origin,source_ref,stated_magnitude=None,target_components=None):
    if source_ref not in ctx.evidence_refs:raise GroundingError("source_ref not grounded")
    comps=tuple(finite(x,"component") for x in components);orig=tuple(finite(x,"origin") for x in origin)
    if len(comps) not in {2,3} or len(orig)!=len(comps):raise PhysError("vector dimensions")
    mag=sqrt(sum(x*x for x in comps))
    if stated_magnitude is not None and abs(mag-finite(stated_magnitude,"stated_magnitude"))>1e-6*max(1,abs(mag)):
        return plan(ctx,":vec","vector_animation","BLOCKED",blockers=("magnitude_component_conflict",))
    ops=[{"op":"draw_vector","id":vector_id,"components":comps,"origin":orig,"unit":unit,"magnitude":mag}]
    if target_components is not None:
        tc=tuple(finite(x,"target") for x in target_components)
        if len(tc)!=len(comps):raise PhysError("target dimensions")
        ops.append({"op":"transform_vector","id":vector_id,"from":comps,"to":tc,"unit":unit})
    return plan(ctx,":vec","vector_animation",ops=ops)
