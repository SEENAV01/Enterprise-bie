from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any, Sequence

class RealBookFixtureError(ValueError): pass

DOMAINS=("physics","mathematics","biology","chemistry","geography_history","data_charts")

@dataclass(frozen=True)
class SourceSpan:
    source_id:str
    span_id:str
    excerpt:str
    provenance_uri:str|None=None

@dataclass(frozen=True)
class RealBookFixture:
    fixture_id:str
    domain:str
    source_span:SourceSpan
    required_concepts:tuple[str,...]
    expected_representation:str
    expected_grammar:str
    required_visual_relations:tuple[str,...]
    fixture_origin:str
    acceptance_eligible:bool=False

def validate_fixture(fixture):
    if not fixture.fixture_id or fixture.domain not in DOMAINS:
        raise RealBookFixtureError("invalid fixture identity/domain")
    if not fixture.source_span.source_id or not fixture.source_span.span_id or not fixture.source_span.excerpt.strip():
        raise RealBookFixtureError("source span/provenance text required")
    if not fixture.required_concepts or not fixture.expected_representation or not fixture.expected_grammar:
        raise RealBookFixtureError("expected visual specification incomplete")
    if fixture.acceptance_eligible and fixture.fixture_origin!="verified_textbook_excerpt":
        raise RealBookFixtureError("acceptance-eligible fixture must come from verified textbook excerpt")
    return True

def validate_fixture_pack(fixtures,require_domains=True):
    fixtures=tuple(fixtures)
    if not fixtures: raise RealBookFixtureError("fixture pack empty")
    if len({f.fixture_id for f in fixtures})!=len(fixtures): raise RealBookFixtureError("duplicate fixture ids")
    if len({(f.source_span.source_id,f.source_span.span_id) for f in fixtures})!=len(fixtures): raise RealBookFixtureError("duplicate source span")
    for f in fixtures: validate_fixture(f)
    if require_domains:
        missing=set(DOMAINS)-{f.domain for f in fixtures}
        if missing: raise RealBookFixtureError(f"missing domains: {sorted(missing)}")
    return True

def acceptance_coverage(fixtures):
    eligible=[f for f in fixtures if f.acceptance_eligible]
    return {"total":len(tuple(fixtures)),"acceptance_eligible":len(eligible),
            "domains":tuple(sorted({f.domain for f in eligible}))}

def reference_nonacceptance_fixtures():
    # These are deliberately synthetic reference fixtures for harness regression.
    # They are NOT represented as real-book acceptance evidence.
    samples=[
      ("phy","physics","A force is represented with magnitude and direction.","force","vector","physics-vector",("direction","magnitude")),
      ("math","mathematics","A function changes from increasing to decreasing around a turning point.","function","graph","mathematics-graph",("trend","turning_point")),
      ("bio","biology","Material passes through a cell membrane from one compartment to another.","membrane transport","process","biology-cellular",("contains","transport")),
      ("chem","chemistry","A molecule contains bonded atoms with stated formal charges.","molecule","molecular","chemistry-molecular",("bond","formal_charge")),
      ("geo","geography_history","A route connects ordered places on a map.","route","map","geography-map",("route_order",)),
      ("data","data_charts","Measurements with uncertainty are compared across categories.","measurements","chart","data-chart",("uncertainty","comparison")),
    ]
    out=[]
    for i,(fid,dom,txt,concept,rep,gram,rels) in enumerate(samples,1):
        out.append(RealBookFixture(fid,dom,SourceSpan(f"synthetic-ref-{i}",f"span-{i}",txt,None),
                                   (concept,),rep,gram,tuple(rels),"synthetic_reference",False))
    return tuple(out)
