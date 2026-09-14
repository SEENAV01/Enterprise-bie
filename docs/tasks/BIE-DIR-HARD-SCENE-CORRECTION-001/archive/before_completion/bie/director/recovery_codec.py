"""BIE-DIR-HARD-REPAIR-001: decode known frozen DIR records, never Python code.

Callers select a compiled-in type. JSON cannot select classes or import modules.
Decoding is structural; the original production validators still own semantics.
"""
from dataclasses import is_dataclass
from types import UnionType
from typing import get_args, get_origin, get_type_hints, Union
from .director_artifacts import fields


def _tuple(value):
    if type(value) is list:
        return tuple(_tuple(v) for v in value)
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise ValueError('untyped record must contain only immutable JSON scalars/arrays')


def decode(kind, value):
    """Strict known-type JSON decoding; no coercion of bool to int or string IDs."""
    origin, args = get_origin(kind), get_args(kind)
    if origin in (Union, UnionType):
        for choice in args:
            try:
                return decode(choice, value)
            except (ValueError, TypeError):
                pass
        raise ValueError('record does not match union type')
    if origin is tuple or kind is tuple:
        if type(value) is not list:
            raise ValueError('tuple record requires JSON array')
        if not args:
            return _tuple(value)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(decode(args[0], v) for v in value)
        if len(value) != len(args):
            raise ValueError('tuple arity mismatch')
        return tuple(decode(t, v) for t, v in zip(args, value))
    if is_dataclass(kind) and kind.__dataclass_params__.frozen:
        fields(value, kind.__dataclass_fields__, kind.__name__)
        hints = get_type_hints(kind)
        return kind(**{name: decode(hints[name], value[name]) for name in hints})
    if kind is type(None) and value is None:
        return None
    if kind in (str, bool, int) and type(value) is kind:
        return value
    if kind is float and type(value) in (int, float):
        from math import isfinite
        if isfinite(value):
            return value
    raise ValueError('unsupported or mismatched record type')


def grounded_record(value):
    from .grounded_directing import GroundedDirectorResult, DirectingPlan, PlannedScene
    from .contextual_teaching import ContextPlannedScene, ContextNarratedScene
    from .windowed_directing import WindowedDirectorResult, WindowExecution
    from .director_artifacts import array
    from .director_benchmark import DirectorExecution
    from .grounded_directing import NarratedScene
    from .director_model import DirectingAttempt
    from .semantic_execution import SemanticEvaluation
    from .qa_contract import QAReport
    kind = WindowedDirectorResult if 'window_execution' in value else GroundedDirectorResult
    fields(value, kind.__dataclass_fields__, 'grounded result')
    raw_plan = fields(value['plan'], DirectingPlan.__dataclass_fields__, 'directing plan')
    # Two explicit, compiled-in variants. Extra JSON fields are still rejected
    # by decode, and verify_base reruns the authoritative input/teaching checks.
    scenes = tuple(decode(ContextPlannedScene if 'teaching_obligation_ids' in row else PlannedScene, row)
                   for row in array(raw_plan['scenes'], 'planned scenes'))
    plan = DirectingPlan(decode(str, raw_plan['input_fingerprint']), decode(str, raw_plan['lesson_id']),
                         scenes, decode(tuple[str, ...], raw_plan['review_reasons']))
    narrated = tuple(decode(ContextNarratedScene if 'teaching_realizations' in row else NarratedScene, row)
                     for row in array(value['narrated_scenes'], 'narrated scenes'))
    types = {'window_execution': WindowExecution, 'execution': DirectorExecution, 'generation_attempts': tuple[DirectingAttempt, ...],
             'semantic_evaluation': SemanticEvaluation, 'qa_reports': tuple[QAReport, ...],
             'generated_assessment_bindings': tuple[tuple[str, str, str], ...],
             'limitations': tuple[str, ...]}
    return kind(plan=plan, narrated_scenes=narrated,
        **{k: decode(types.get(k, str), v) for k, v in value.items() if k not in ('plan', 'narrated_scenes')})


def annotation_production_record(value):
    from .narration_annotations import AnnotationProduction,NarrationAnnotations,AnnotationPolicy
    from .windowed_annotations import WindowedAnnotationProduction
    from .annotation_window_context import WindowedAnnotationPolicy,ScopedAnnotationCall
    from .semantic_execution import EvaluatorIdentity
    from .director_model import DirectingAttempt
    marked='window_version' in value.get('annotations',{}).get('policy',{})
    if marked and not {'window_calls','discourse_call'}<=value.keys():raise ValueError('windowed annotation record requires retained scope evidence')
    if not marked and ({'window_calls','discourse_call'}&value.keys()):raise ValueError('legacy annotation policy cannot select window record type')
    kind=WindowedAnnotationProduction if marked else AnnotationProduction
    fields(value,kind.__dataclass_fields__,'annotation production')
    raw=fields(value['annotations'],NarrationAnnotations.__dataclass_fields__,'annotations')
    policy=decode(WindowedAnnotationPolicy if 'window_version' in raw['policy'] else AnnotationPolicy,raw['policy'])
    hints=get_type_hints(NarrationAnnotations)
    annotations=NarrationAnnotations(policy=policy,**{k:decode(hints[k],v) for k,v in raw.items() if k!='policy'})
    types={'attempts':tuple[DirectingAttempt,...],'identity':EvaluatorIdentity,
        'window_calls':tuple[ScopedAnnotationCall,...],'discourse_call':ScopedAnnotationCall}
    return kind(annotations=annotations,**{k:decode(types.get(k,str),v) for k,v in value.items() if k!='annotations'})


def annotation_review_record(value):
    from .annotation_review import AnnotationReview,AnnotationReviewPolicy,AnnotationJudgment
    from .windowed_annotation_review import WindowedAnnotationReview,ReviewWindow
    from .annotation_window_context import WindowedAnnotationReviewPolicy
    from .semantic_execution import EvaluatorIdentity
    from .director_model import DirectingAttempt
    marked='window_version' in value.get('policy',{})
    if marked and 'review_windows' not in value:raise ValueError('scoped review requires retained window evidence')
    if not marked and 'review_windows' in value:raise ValueError('legacy review policy cannot select window record type')
    kind=WindowedAnnotationReview if marked else AnnotationReview
    fields(value,kind.__dataclass_fields__,'annotation review')
    policy=decode(WindowedAnnotationReviewPolicy if 'window_version' in value['policy'] else AnnotationReviewPolicy,value['policy'])
    types={'identity':EvaluatorIdentity,'judgments':tuple[AnnotationJudgment,...],'attempts':tuple[DirectingAttempt,...],
        'failures':tuple[str,...],'response_json':str|None,'review_windows':tuple[ReviewWindow,...]}
    return kind(policy=policy,**{k:decode(types.get(k,str),v) for k,v in value.items() if k!='policy'})
