from .map_contracts import *

def animate_map_transition(ctx, *, source_view:MapView, target_view:MapView,
                           transition_kind="pan_zoom", preserve_anchor=True,
                           anchor=None, allow_projection_change=False):
    if source_view.source_ref not in ctx.evidence_refs or target_view.source_ref not in ctx.evidence_refs:
        raise MapGroundingError("map views must be grounded in context evidence")
    if source_view.crs != ctx.crs or target_view.crs != ctx.crs:
        if not allow_projection_change:
            return make_plan(ctx,suffix=":map-transition",kind="map_transition",status="BLOCKED",
                             blockers=("map_view_crs_mismatch",))
    if transition_kind not in {"pan","zoom","pan_zoom","cut","crossfade"}:
        raise MapAnimationError("unsupported transition_kind")
    warnings=[]
    if source_view.crs != target_view.crs:
        if not allow_projection_change:
            return make_plan(ctx,suffix=":map-transition",kind="map_transition",status="BLOCKED",
                             blockers=("projection_change_not_allowed",))
        warnings.append("projection_change_requires_visual_disclosure")
    if preserve_anchor and anchor is None:
        warnings.append("anchor_preservation_requested_without_explicit_anchor")
    if anchor is not None:
        if len(anchor)!=2: raise MapAnimationError("anchor must be 2D")
        anchor=(finite(anchor[0],"anchor.x"),finite(anchor[1],"anchor.y"))
    scale_ratio=max(source_view.scale,target_view.scale)/min(source_view.scale,target_view.scale)
    if scale_ratio>100:
        warnings.append("large_scale_change_may_require_intermediate_map_view")
    ops=(
        {"op":"map_transition","transition_kind":transition_kind,
         "from_view":source_view.__dict__,"to_view":target_view.__dict__,
         "preserve_anchor":bool(preserve_anchor),"anchor":anchor,
         "projection_change":source_view.crs!=target_view.crs},
    )
    status="REVIEW" if warnings or ctx.uncertainty>=.4 else "PASS"
    if ctx.uncertainty>=.4: warnings.append("map_source_uncertainty_requires_review")
    return make_plan(ctx,suffix=":map-transition",kind="map_transition",status=status,operations=ops,warnings=warnings)
