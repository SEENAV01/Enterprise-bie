"""BIE-DIR-SYNC-004: revision-bound quantitative graph narration cues."""
from dataclasses import dataclass
import math
from .timing_contract import ordered, nonblank, number, fingerprint
from .sync_contract import (IntentBinding, SyncCue, SyncIndex, SyncIssue, unique_inputs,
    immutable_ids, parameters, finish_plan, require_target, _immutable, SyncPlan, same_plan)
from .narration_visual_sync import validate_visual_sync


@dataclass(frozen=True)
class GraphAxis:
    axis_id: str
    label: str
    unit: str
    minimum: float
    maximum: float
    scale: str = "LINEAR"


@dataclass(frozen=True)
class GraphPoint:
    point_id: str
    x: float
    y: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class GraphSeries:
    series_id: str
    label: str
    points: tuple[GraphPoint, ...]


@dataclass(frozen=True)
class GraphDefinition:
    graph_id: str
    scene_id: str
    element_id: str
    revision: str
    x_axis: GraphAxis
    y_axis: GraphAxis
    series: tuple[GraphSeries, ...]
    evidence_ids: tuple[str, ...]

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class GraphIntent:
    binding: IntentBinding
    visual_intent_id: str
    graph_id: str
    graph_fingerprint: str
    action: str
    series_id: str | None = None
    point_ids: tuple[str, ...] = ()


def _fraction(value, axis):
    if axis.scale=="LOG":
        low,high,x=math.log(axis.minimum),math.log(axis.maximum),math.log(value)
    else:
        low,high,x=axis.minimum,axis.maximum,value
    result=(x-low)/(high-low)
    number(result,"normalized graph coordinate",0.0,1.0)
    return result


def _validate_graph(graph):
    if not isinstance(graph,GraphDefinition): raise ValueError("expected GraphDefinition")
    _immutable(graph)
    for field in ("graph_id","scene_id","element_id","revision"):
        nonblank(getattr(graph,field),field)
    immutable_ids(graph.evidence_ids,"graph evidence")
    for axis in (graph.x_axis,graph.y_axis):
        if not isinstance(axis,GraphAxis): raise ValueError("expected GraphAxis")
        for field in ("axis_id","label","unit"): nonblank(getattr(axis,field),field)
        number(axis.minimum,"axis minimum",low=-float("inf"))
        number(axis.maximum,"axis maximum",low=-float("inf"))
        if axis.maximum<=axis.minimum or axis.scale not in ("LINEAR","LOG"):
            raise ValueError("invalid axis domain or scale")
        if axis.scale=="LOG" and axis.minimum<=0: raise ValueError("log axis must be positive")
        if axis.scale=="LINEAR": number(axis.maximum-axis.minimum,"axis span",positive=True)
        elif math.log(axis.maximum)<=math.log(axis.minimum): raise ValueError("log domain lacks representable resolution")
    if graph.x_axis.axis_id==graph.y_axis.axis_id: raise ValueError("axis ids must differ")
    if not graph.series: raise ValueError("graph has no series")
    seen=set()
    for series in graph.series:
        if not isinstance(series,GraphSeries): raise ValueError("expected GraphSeries")
        nonblank(series.series_id,"series id"); nonblank(series.label,"series label")
        if series.series_id in seen or not series.points: raise ValueError("duplicate or empty series")
        seen.add(series.series_id); point_ids=set()
        for point in series.points:
            if not isinstance(point,GraphPoint): raise ValueError("expected GraphPoint")
            nonblank(point.point_id,"point id")
            if point.point_id in point_ids: raise ValueError("duplicate point id in series")
            point_ids.add(point.point_id)
            immutable_ids(point.evidence_ids,"point evidence")
            if not set(point.evidence_ids)<=set(graph.evidence_ids): raise ValueError("point evidence outside graph")
            number(point.x,"point x",graph.x_axis.minimum,graph.x_axis.maximum)
            number(point.y,"point y",graph.y_axis.minimum,graph.y_axis.maximum)


def sync_graph_narration(context, visuals, graphs, intents, policy_version="bie-dir-graph-sync/1.0.0"):
    validate_visual_sync(context,visuals)
    index=SyncIndex(context)
    definitions=ordered(graphs,"graph definitions")
    by_graph={}; targets=set()
    for graph in definitions:
        _validate_graph(graph)
        key=(graph.scene_id,graph.element_id)
        if graph.graph_id in by_graph or key in targets or graph.scene_id not in index.scenes:
            raise ValueError("duplicate graph revision/target or unknown scene")
        by_graph[graph.graph_id]=graph; targets.add(key)
    rows=unique_inputs(intents,GraphIntent)
    by_visual={c.binding.intent_id:c for c in visuals.cues}
    cues,issues=[],list(visuals.issues)
    for row in rows:
        if row.graph_id not in by_graph or row.visual_intent_id not in by_visual:
            raise ValueError("unknown graph or visual intent")
        graph=by_graph[row.graph_id]
        if row.graph_fingerprint!=graph.fingerprint(): raise ValueError("stale graph data, axes or unit revision")
        immutable_ids(row.point_ids,"point ids",empty=True)
        if row.action not in ("SHOW_AXES","TRACE_SERIES","HIGHLIGHT_POINT","HIGHLIGHT_RANGE"):
            raise ValueError("unknown graph narration action")
        w=index.resolve(row.binding)
        if (graph.scene_id,graph.element_id)!=(w.scene_id,row.binding.target_id): raise ValueError("graph target mismatch")
        if not set(row.binding.evidence_ids)<=set(graph.evidence_ids): raise ValueError("narration evidence outside graph source")
        selected=()
        if row.action=="SHOW_AXES":
            if row.series_id is not None or row.point_ids: raise ValueError("axis cue cannot select series/points")
        else:
            series=next((s for s in graph.series if s.series_id==row.series_id),None)
            if series is None: raise ValueError("unknown graph series")
            positions={p.point_id:i for i,p in enumerate(series.points)}
            if any(pid not in positions for pid in row.point_ids): raise ValueError("unknown graph point")
            if row.action=="HIGHLIGHT_POINT" and len(row.point_ids)!=1: raise ValueError("point highlight requires one point")
            if row.action=="HIGHLIGHT_RANGE" and len(row.point_ids)!=2: raise ValueError("range requires two ordered endpoint IDs")
            if row.action=="HIGHLIGHT_RANGE":
                lo,hi=(positions[p] for p in row.point_ids)
                if lo>=hi: raise ValueError("range endpoints reverse source series order")
                selected=series.points[lo:hi+1]
            else:
                indices=[positions[p] for p in row.point_ids] if row.point_ids else list(range(len(series.points)))
                if indices!=sorted(indices): raise ValueError("trace point order must match the declared source series")
                selected=tuple(series.points[i] for i in indices)
            if row.action=="TRACE_SERIES" and len(selected)<2: raise ValueError("trace needs at least two source points")
            if not {e for p in selected for e in p.evidence_ids}<=set(row.binding.evidence_ids):
                raise ValueError("selected graph data lacks narration evidence")
        duration=w.end_ms-w.start_ms
        if len(selected)>1 and duration<len(selected)-1:
            issues.append(SyncIssue("GRAPH_TRACE_WINDOW_TOO_SHORT",row.binding.intent_id,
                "Not enough milliseconds for distinct ordered sample times.","DIR_TIME"))
            points=()
        else:
            points=tuple((p.point_id,w.start_ms+(i*duration//(len(selected)-1) if len(selected)>1 else 0),
                p.x,p.y,_fraction(p.x,graph.x_axis),_fraction(p.y,graph.y_axis)) for i,p in enumerate(selected))
        cue=SyncCue(row.binding,row.action,w,parameters(graph_id=graph.graph_id,graph_fingerprint=graph.fingerprint(),
            series_id=row.series_id,waypoints=points,x_unit=graph.x_axis.unit,y_unit=graph.y_axis.unit,
            schedule_basis="SOURCE_INDEX_LINEAR_INTENT"))
        issues.extend(require_target(cue,by_visual[row.visual_intent_id],"graph")); cues.append(cue)
    by_row={r.binding.intent_id:r for r in rows}
    for cue in cues:
        if cue.kind!="SHOW_AXES":
            row=by_row[cue.binding.intent_id]
            axes=[a for a in cues if a.kind=="SHOW_AXES" and a.window.scene_id==cue.window.scene_id
                  and a.binding.target_id==cue.binding.target_id and a.window.end_ms<=cue.window.start_ms
                  and by_row[a.binding.intent_id].visual_intent_id==row.visual_intent_id]
            if not axes: issues.append(SyncIssue("GRAPH_AXES_NOT_INTRODUCED",row.binding.intent_id,
                "Complete an axes/units cue in this visibility window before graph analysis.","DIR_SCRIPT"))
    for graph in definitions:
        if not any(r.graph_id==graph.graph_id for r in rows):
            issues.append(SyncIssue("UNBOUND_GRAPH",graph.graph_id,"Declared graph has no narration cue.","DIR_SCRIPT"))
    return finish_plan(index,"BIE-DIR-SYNC-004",policy_version,rows,tuple(sorted(definitions,key=lambda g:g.graph_id)),
        tuple(cues),issues,visuals.fingerprint(),visuals.review_reasons+("GRAPH_DATA_MEANING_AND_RENDER_REQUIRE_QA",))


def validate_graph_sync(context, visuals, plan):
    if not isinstance(plan,SyncPlan) or plan.task_id!="BIE-DIR-SYNC-004":
        raise ValueError("expected graph sync plan")
    return same_plan(plan,sync_graph_narration(context,visuals,plan.definitions,plan.inputs,plan.policy_version))
