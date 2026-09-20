from .physics_contracts import *
def animate(ctx,system_id,particles,source_ref,seed,trajectory_mode="supplied",observed_execution=False):
    if source_ref not in ctx.evidence_refs:raise GroundingError("source_ref not grounded")
    if isinstance(seed,bool) or not isinstance(seed,int):raise PhysError("seed")
    if trajectory_mode not in {"supplied","illustrative","model_output"}:raise PhysError("trajectory_mode")
    if trajectory_mode=="model_output" and not ctx.model_fingerprint:return plan(ctx,":particles","particle_animation","BLOCKED",blockers=("model_fingerprint_required",))
    clean=[]
    for p in particles:
        pts=tuple(tuple(finite(v,"point") for v in q) for q in p.get("trajectory",()))
        if not pts:raise PhysError("trajectory required")
        clean.append({"particle_id":p["particle_id"],"trajectory":pts})
    if len({p["particle_id"] for p in clean})!=len(clean):raise PhysError("duplicate particle")
    warnings=[]
    if trajectory_mode=="illustrative":warnings.append("illustrative_not_physical_evidence")
    if trajectory_mode=="model_output" and not observed_execution:warnings.append("model_output_not_observed_execution")
    if not observed_execution:warnings.append("execution_not_observed")
    return plan(ctx,":particles","particle_animation","REVIEW" if warnings else "PASS",
                ops=({"op":"particle_system","id":system_id,"particles":clean,"seed":seed,"trajectory_mode":trajectory_mode,"observed_execution":observed_execution},),warnings=warnings)
