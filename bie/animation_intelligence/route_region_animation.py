from .map_contracts import *

def animate_route_region(ctx, *, animation_id, route_points=(), route_source_ref=None,
                         regions=(), region_source_ref=None, route_mode="trace",
                         route_claim="illustrative", ordered=True, reveal_regions=True):
    animation_id=tok(animation_id,"animation_id")
    if route_mode not in {"trace","marker_follow","progressive_segment"}:
        raise MapAnimationError("unsupported route_mode")
    if route_claim not in {"illustrative","documented_route","measured_trajectory","shortest_path"}:
        raise MapAnimationError("unsupported route_claim")
    warnings=[]; blockers=[]; ops=[]
    pts=tuple(tuple(finite(v,"route point") for v in p) for p in route_points)
    if pts:
        if route_source_ref is None or route_source_ref not in ctx.evidence_refs:
            raise MapGroundingError("route requires grounded source_ref")
        if len(pts)<2:
            raise MapTopologyError("route needs at least two points")
        if not ordered:
            blockers.append("route_order_not_declared")
        if route_claim in {"measured_trajectory","shortest_path"} and not ctx.payload.get("route_evidence_level") in {"measured","verified_network"}:
            blockers.append("route_claim_exceeds_evidence")
        ops.append({"op":"animate_route","animation_id":animation_id,"points":pts,
                    "route_mode":route_mode,"route_claim":route_claim})
    clean_regions=[]
    for r in regions:
        rid=tok(r.get("region_id"),"region_id")
        boundary=tuple(tuple(finite(v,"region point") for v in p) for p in r.get("boundary",()))
        if len(boundary)<3:
            raise MapTopologyError("region boundary needs at least three points")
        clean_regions.append({"region_id":rid,"boundary":boundary,"label":r.get("label")})
    if clean_regions:
        if region_source_ref is None or region_source_ref not in ctx.evidence_refs:
            raise MapGroundingError("regions require grounded source_ref")
        if len({r["region_id"] for r in clean_regions})!=len(clean_regions):
            raise MapTopologyError("duplicate region ids")
        if reveal_regions:
            ops.append({"op":"reveal_regions","animation_id":animation_id,"regions":clean_regions})
    if not ops:
        return make_plan(ctx,suffix=":route-region",kind="route_region_animation",status="UNSUPPORTED",
                         blockers=("no_route_or_regions_supplied",))
    if ctx.uncertainty>=.4:
        warnings.append("map_source_uncertainty_requires_review")
    status="BLOCKED" if blockers else ("REVIEW" if warnings else "PASS")
    return make_plan(ctx,suffix=":route-region",kind="route_region_animation",
                     status=status,operations=ops,warnings=warnings,blockers=blockers)
