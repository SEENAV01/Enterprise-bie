"""Live DSL registry-to-compiler dispatch inventory, derived from inherited R02.

Presence in a dispatch table is NOT complete behavior/property coverage. This
inventory makes omitted source vocabulary explicit and cannot authorize render,
section exit, instructional equivalence or product acceptance.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import inspect
from .qa_common import CompilerQAError, digest


def inspect_consumer_coverage() -> dict:
    from bie.scene_ir import scene_ir_registry as registry
    from . import qa_scene_compile, animation_behavior, specialized_motion, registered_actions
    root = Path(__file__).resolve().parents[3]
    kinds, actions = tuple(registry.ELEMENT_TYPES), tuple(registry.ACTIONS)
    if len(set(kinds)) != len(kinds) or len(set(actions)) != len(actions):
        raise CompilerQAError('COVERAGE_DUPLICATE_REGISTRY_ENTRY')
    if any(not isinstance(x, str) or not x for x in (*kinds, *actions)):
        raise CompilerQAError('COVERAGE_REGISTRY_INVALID')
    source_files = {}
    def identity(path):
        p = Path(path).resolve()
        try: name = p.relative_to(root).as_posix()
        except ValueError as e: raise CompilerQAError('COVERAGE_SOURCE_OUTSIDE_WORKSPACE') from e
        source_files[name] = sha256(p.read_bytes()).hexdigest()
        return name
    for mod in (registry, qa_scene_compile, animation_behavior, specialized_motion, registered_actions): identity(mod.__file__)
    rows = []
    for kind in kinds:
        fn = qa_scene_compile.EMITTERS.get(kind)
        if fn is not None and not callable(fn): raise CompilerQAError('COVERAGE_INVALID_DISPATCH')
        rows.append({'kind': 'element', 'name': kind,
                     'dispatch': None if fn is None else fn.__module__ + ':' + fn.__name__,
                     'source': None if fn is None else identity(inspect.getsourcefile(fn)),
                     'status': 'MISSING_CONSUMER' if fn is None else 'DISPATCH_PRESENT_BEHAVIOR_NOT_EXHAUSTIVELY_CERTIFIED'})
    generic, special = set(animation_behavior.SUPPORTED_ACTIONS), set(specialized_motion.ACTIONS)
    registered = set(registered_actions.ACTIONS)
    for action in actions:
        dispatcher = animation_behavior.motion_contract if action in generic else specialized_motion.specialized_contract if action in special else registered_actions.registered_contract if action in registered else None
        rows.append({'kind': 'action', 'name': action,
                     'dispatch': None if dispatcher is None else dispatcher.__module__ + ':' + dispatcher.__name__,
                     'source': None if dispatcher is None else identity(inspect.getsourcefile(dispatcher)),
                     'status': 'MISSING_CONSUMER' if dispatcher is None else 'DISPATCH_PRESENT_BEHAVIOR_NOT_EXHAUSTIVELY_CERTIFIED'})
    missing = [{'kind': r['kind'], 'name': r['name']} for r in rows if r['status'] == 'MISSING_CONSUMER']
    extra = {'elements': sorted(set(qa_scene_compile.EMITTERS) - set(kinds)), 'actions': sorted((generic | special | registered) - set(actions))}
    result = {'schema_version': 'bie.compiler-consumer-coverage.v1', 'rows': rows, 'missing': missing,
              'unregistered_dispatch': extra, 'registry_elements': len(kinds), 'registry_actions': len(actions),
              'source_files': dict(sorted(source_files.items())),
              'dispatch_complete': not missing and not any(extra.values()),
              'behavior_coverage_complete': False, 'section_exit_permitted': False, 'accepted': False,
              'limits': 'Name-level live source inventory only. Missing consumers remain implementation gaps; present entries require property/combination tests and actual execution. Interactive game and speech production belong to their own sections, not silently implemented here.'}
    result['inventory_sha256'] = digest(result)
    return result


def require_dispatch_coverage(report: dict) -> None:
    """Recompute live source identity; no caller-supplied PASS can close coverage."""
    current = inspect_consumer_coverage()
    if report != current: raise CompilerQAError('COVERAGE_STALE_OR_FORGED_INVENTORY')
    if not current['dispatch_complete']: raise CompilerQAError('COVERAGE_REQUIRED_CONSUMERS_MISSING')
    # Even success would establish dispatch presence only, not section acceptance.
