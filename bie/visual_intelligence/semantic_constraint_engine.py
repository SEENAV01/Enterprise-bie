from __future__ import annotations
from dataclasses import dataclass
from .visual_plan_contract import fp

class SemanticPolicyError(ValueError): pass
@dataclass(frozen=True)
class Violation:
    policy:str; location:str; message:str; severity:str="HARD"
@dataclass(frozen=True)
class Report:
    passed:bool; violations:tuple[Violation,...]; executed:tuple[str,...]; fingerprint:str; review_required:bool=True; accepted:bool=False

POLICIES=(
"vectors require an explicit reference frame",
"arrow direction encodes signed direction; magnitude is never inferred from arrow length unless scale is explicit",
"component guides must preserve the declared basis",
"field samples must retain coordinates and declared field type",
"field lines/contours are derived only when explicitly requested and supported by supplied samples/model evidence",
"no direction or source sign may be invented",
"flow edges preserve declared direction","cycles must be explicitly marked as feedback/loop","branch labels remain explicit",
"compartment containment is explicit","transport arrows encode declared transport only","diagrammatic size is not physical scale unless scale metadata is supplied",
"bond order is explicit","formal charge is preserved when supplied","2D depiction does not imply stereochemistry unless stereochemistry is explicitly encoded",
"coordinate reference system is explicit","features from incompatible coordinate frames are rejected","route order and region membership preserve source semantics",
"uncertain dates remain uncertain","simultaneity and intervals are preserved","visual order must follow declared chronology rather than lexical label order",
"causal arrows require evidence bindings","association is not silently promoted to causation","feedback cycles must be explicitly declared",
"axis scales and units are explicit","sampled data are not presented as an exact analytic curve","discontinuities and domain restrictions remain visible",
"declared incidences and measurements are preserved","diagram appearance is not proof of equality/parallelism/perpendicularity","measurements require units when dimensioned",
"encoding channels are explicit","uncertainty/error values remain visible when supplied","truncated baselines and aggregation choices are disclosed",
)

def payload(x): return dict(x.get("payload",{}))
def check(name,plan):
    es=list(plan.get("elements",())); rs=list(plan.get("relations",())); m=dict(plan.get("metadata",{})); out=[]
    def V(loc,msg): out.append(Violation(name,loc,msg))
    if name=="vectors require an explicit reference frame":
        if not m.get("reference_frame"): V("metadata","reference frame missing")
    elif name=="arrow direction encodes signed direction; magnitude is never inferred from arrow length unless scale is explicit":
        for e in es:
            if e.get("role")=="vector" and payload(e).get("magnitude_from_length") and not m.get("vector_scale"): V(e.get("id","?"),"unscaled vector length used as magnitude")
    elif name=="component guides must preserve the declared basis":
        for e in es:
            p=payload(e)
            if e.get("role")=="component_guide" and p.get("declared_basis")!=p.get("visual_basis"): V(e.get("id","?"),"basis changed")
    elif name=="field samples must retain coordinates and declared field type":
        for e in es:
            if e.get("role")=="field_sample" and not all(k in payload(e) for k in ("x","y","field_type")): V(e.get("id","?"),"field metadata missing")
    elif name=="field lines/contours are derived only when explicitly requested and supported by supplied samples/model evidence":
        for e in es:
            if e.get("role") in {"field_line","contour"} and not (payload(e).get("requested") and payload(e).get("model_evidence")): V(e.get("id","?"),"unsupported derived field visual")
    elif name=="no direction or source sign may be invented":
        for e in es:
            p=payload(e)
            if p.get("direction_inferred_without_source") or p.get("source_sign_inferred_without_source"): V(e.get("id","?"),"invented direction/sign")
    elif name=="flow edges preserve declared direction":
        for r in rs:
            p=payload(r)
            if r.get("kind")=="flow" and p.get("declared_direction")!=p.get("visual_direction"): V(r.get("id","?"),"flow reversed")
    elif name in {"cycles must be explicitly marked as feedback/loop","feedback cycles must be explicitly declared"}:
        for r in rs:
            if r.get("source")==r.get("target") and not (payload(r).get("loop") or payload(r).get("feedback")): V(r.get("id","?"),"cycle not declared")
    elif name=="branch labels remain explicit":
        for r in rs:
            if payload(r).get("branch") and not payload(r).get("branch_label"): V(r.get("id","?"),"branch label missing")
    elif name=="compartment containment is explicit":
        for e in es:
            if payload(e).get("compartment_id") and not any(r.get("kind")=="contains" and r.get("target")==e.get("id") for r in rs): V(e.get("id","?"),"containment relation missing")
    elif name=="transport arrows encode declared transport only":
        for r in rs:
            if r.get("kind")=="transport" and payload(r).get("declared") is not True: V(r.get("id","?"),"transport not declared")
    elif name=="diagrammatic size is not physical scale unless scale metadata is supplied":
        if any(payload(e).get("physical_scale_claim") for e in es) and not m.get("scale"): V("metadata","physical-scale claim without scale")
    elif name=="bond order is explicit":
        for r in rs:
            if r.get("kind")=="bond" and "bond_order" not in payload(r): V(r.get("id","?"),"bond order missing")
    elif name=="formal charge is preserved when supplied":
        for e in es:
            p=payload(e)
            if "source_formal_charge" in p and p.get("source_formal_charge")!=p.get("visual_formal_charge"): V(e.get("id","?"),"formal charge changed")
    elif name=="2D depiction does not imply stereochemistry unless stereochemistry is explicitly encoded":
        for e in es:
            p=payload(e)
            if p.get("depiction")=="2d" and p.get("stereochemistry_claimed") and not p.get("stereochemistry_explicit"): V(e.get("id","?"),"unsupported stereochemistry")
    elif name=="coordinate reference system is explicit":
        if not m.get("crs"): V("metadata","CRS missing")
    elif name=="features from incompatible coordinate frames are rejected":
        frames={payload(e).get("crs") for e in es if payload(e).get("crs")}
        if len(frames)>1: V("plan","incompatible CRS")
    elif name=="route order and region membership preserve source semantics":
        for e in es:
            p=payload(e)
            if p.get("source_route_order") is not None and p.get("source_route_order")!=p.get("visual_route_order"): V(e.get("id","?"),"route order changed")
            if p.get("source_region") is not None and p.get("source_region")!=p.get("visual_region"): V(e.get("id","?"),"region changed")
    elif name=="uncertain dates remain uncertain":
        for e in es:
            p=payload(e)
            if p.get("source_date_uncertain") and not p.get("visual_date_uncertain"): V(e.get("id","?"),"uncertainty removed")
    elif name=="simultaneity and intervals are preserved":
        for e in es:
            p=payload(e)
            if p.get("source_interval") is not None and p.get("source_interval")!=p.get("visual_interval"): V(e.get("id","?"),"interval changed")
    elif name=="visual order must follow declared chronology rather than lexical label order":
        seq=[payload(e).get("chronology_index") for e in es if payload(e).get("chronology_index") is not None]
        if seq and seq!=sorted(seq): V("plan","chronology order violated")
    elif name=="causal arrows require evidence bindings":
        for r in rs:
            if r.get("kind")=="causes" and not r.get("source_ids"): V(r.get("id","?"),"causal evidence missing")
    elif name=="association is not silently promoted to causation":
        for r in rs:
            if r.get("kind")=="causes" and payload(r).get("derived_from")=="association": V(r.get("id","?"),"association promoted to causation")
    elif name=="axis scales and units are explicit":
        if not m.get("x_scale") or not m.get("y_scale"): V("metadata","axis scale missing")
        if m.get("units_required") and (not m.get("x_unit") or not m.get("y_unit")): V("metadata","axis unit missing")
    elif name=="sampled data are not presented as an exact analytic curve":
        if m.get("sampled_data") and m.get("curve_claim")=="exact": V("metadata","sampled data claimed exact")
    elif name=="discontinuities and domain restrictions remain visible":
        if m.get("has_discontinuity") and not m.get("discontinuity_visible"): V("metadata","discontinuity hidden")
        if m.get("domain_restricted") and not m.get("domain_restriction_visible"): V("metadata","domain restriction hidden")
    elif name=="declared incidences and measurements are preserved":
        for e in es:
            p=payload(e)
            if p.get("source_measurement") is not None and p.get("source_measurement")!=p.get("visual_measurement"): V(e.get("id","?"),"measurement changed")
    elif name=="diagram appearance is not proof of equality/parallelism/perpendicularity":
        for e in es:
            p=payload(e)
            if p.get("appearance_inference") in {"equal","parallel","perpendicular"} and not p.get("declared_relation"): V(e.get("id","?"),"appearance treated as proof")
    elif name=="measurements require units when dimensioned":
        for e in es:
            if payload(e).get("dimensioned") and not payload(e).get("unit"): V(e.get("id","?"),"unit missing")
    elif name=="encoding channels are explicit":
        for e in es:
            if e.get("role") in {"series","data"} and not payload(e).get("encoding_channel"): V(e.get("id","?"),"encoding channel missing")
    elif name=="uncertainty/error values remain visible when supplied":
        for e in es:
            p=payload(e)
            if ("uncertainty" in p or "error" in p) and not p.get("uncertainty_visible"): V(e.get("id","?"),"uncertainty hidden")
    elif name=="truncated baselines and aggregation choices are disclosed":
        if m.get("baseline_truncated") and not m.get("baseline_disclosure"): V("metadata","truncated baseline undisclosed")
        if m.get("aggregation") and not m.get("aggregation_disclosure"): V("metadata","aggregation undisclosed")
    return tuple(out)

def evaluate(plan,policy_names):
    unknown=[p for p in policy_names if p not in POLICIES]
    if unknown: raise SemanticPolicyError(f"unknown policy: {unknown[0]}")
    v=tuple(x for p in policy_names for x in check(p,plan))
    return Report(not v,v,tuple(policy_names),fp({"violations":[x.__dict__ for x in v],"policies":policy_names}))
