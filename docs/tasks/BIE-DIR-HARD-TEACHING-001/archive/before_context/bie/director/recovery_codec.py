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
    from .grounded_directing import GroundedDirectorResult, DirectingPlan
    from .director_benchmark import DirectorExecution
    from .grounded_directing import NarratedScene
    from .director_model import DirectingAttempt
    from .semantic_execution import SemanticEvaluation
    from .qa_contract import QAReport
    fields(value, GroundedDirectorResult.__dataclass_fields__, 'grounded result')
    types = {'plan': DirectingPlan, 'narrated_scenes': tuple[NarratedScene, ...],
             'execution': DirectorExecution, 'generation_attempts': tuple[DirectingAttempt, ...],
             'semantic_evaluation': SemanticEvaluation, 'qa_reports': tuple[QAReport, ...],
             'generated_assessment_bindings': tuple[tuple[str, str, str], ...],
             'limitations': tuple[str, ...]}
    return GroundedDirectorResult(**{k: decode(types.get(k, str), v) for k, v in value.items()})
