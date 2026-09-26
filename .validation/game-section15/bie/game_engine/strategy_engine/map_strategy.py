from __future__ import annotations
from .contracts import StrategyKind, CognitiveOperation, KnowledgeForm, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();signals=bundle.geo_entities;targets=[o for o in bundle.objectives if CognitiveOperation.LOCATE in o.cognitive_operations or KnowledgeForm.SPATIAL in o.knowledge_forms]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};locations={(round(s.latitude,6),round(s.longitude,6)) for s in signals}
    blockers=[]
    if not targets:blockers.append('no_spatial_or_location_objective')
    if len(signals)<2:blockers.append('insufficient_geospatial_entities')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    if len(locations)!=len(signals):blockers.append('duplicate_coordinates_reduce_interaction_value')
    required=('semantic_visuals','stateful_interaction','map_runtime','accessibility_keyboard','purposeful_camera');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of spatial/location objectives'),ScoreComponent('spatial_distinctness',fraction(len(locations),max(1,len(signals))),2,'Distinct grounded locations'),ScoreComponent('interaction_density',fraction(len(signals),max(2,3*len(targets))),2,'Enough entities for comparison/location tasks'),ScoreComponent('coordinate_grounding',1.0 if signals and all(s.location_ref for s in signals) else 0.0,3,'Coordinates are bound to evidence locators'))
    return build_assessment(strategy=StrategyKind.MAP,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('geospatial_reasoning','location_comparison','grounded_coordinates') if signals else (),runtime_required=required,design_requirements=('map_is_semantic_workspace_not_background_image','camera_zoom_has_learning_purpose','provide_non_pointer_navigation','distinguish_distance_direction_region_and_scale'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.5))
