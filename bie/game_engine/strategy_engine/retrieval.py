from __future__ import annotations
from .contracts import StrategyKind, CognitiveOperation, KnowledgeForm, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();objectives={o.objective_id:o for o in bundle.objectives};items=bundle.retrieval_items
    covered=tuple(sorted({i.objective_id for i in items}))
    target=[o for o in bundle.objectives if CognitiveOperation.RECALL in o.cognitive_operations or KnowledgeForm.FACT in o.knowledge_forms]
    target_ids={o.objective_id for o in target};target_covered=target_ids & set(covered)
    unique_prompts=len({i.prompt_ref for i in items});unique_answers=len({i.answer_ref for i in items});spacing=len({i.spacing_key for i in items})
    blockers=[]
    if not target:blockers.append('no_recall_or_fact_objective')
    if not items:blockers.append('no_retrieval_items')
    if target and target_covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    if items and (unique_prompts!=len(items) or unique_answers!=len(items)):blockers.append('duplicate_prompt_or_answer_reference')
    required=('semantic_visuals','accessibility_keyboard','audio_feedback');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(target_covered),len(target_ids)),4,'Coverage of recall/fact objectives'),ScoreComponent('item_diversity',fraction(min(unique_prompts,unique_answers),max(1,len(items))),2,'Distinct grounded prompts and answers'),ScoreComponent('spacing_support',fraction(spacing,max(1,len(items))),2,'Items expose deterministic spacing keys'),ScoreComponent('misconception_targeting',fraction(sum(bool(objectives[i].misconception_ids) for i in target_covered),max(1,len(target_covered))),1,'Retrieval can target known misconceptions'))
    strengths=tuple(x for x,c in [('grounded_recall_practice',bool(items)),('spacing_ready',spacing==len(items) and bool(items)),('misconception_aware',any(o.misconception_ids for o in target))] if c)
    prov=[i.provenance for i in items]+[o.provenance for o in target]
    return build_assessment(strategy=StrategyKind.RETRIEVAL,eligible=not blockers,components=comps,coverage=tuple(target_covered),blockers=tuple(blockers),strengths=strengths,runtime_required=required,design_requirements=('active_recall_before_answer_reveal','spaced_or_interleaved_prompt_selection','semantic_feedback_not_flashcard_slides','no_mcq_only_core_gameplay'),evidence_refs=evidence_ids(prov),confidence=confidence_from_evidence(len(items),fraction(len(target_covered),len(target_ids))))
