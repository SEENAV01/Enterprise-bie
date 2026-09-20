"""Test-only helpers; no renderer/provider doubles masquerade as production runs."""
from copy import deepcopy
from pathlib import Path
import json
from functools import lru_cache
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.multidomain_compile_benchmark import CompileBenchmarkCase
from bie.compiler.deterministic_output_qa import DeterminismContext
from bie.compiler.qa_common import digest
from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'fixtures/comp_qa_009'

@lru_cache(maxsize=1)
def _corpus():
    return json.loads((FIXTURES/'corpus.json').read_text())

def case_raw(cid='math-plain'):
    return deepcopy(next(c for c in _corpus()['cases'] if c['case_id']==cid))

def case(cid='math-plain'):
    return CompileBenchmarkCase(**case_raw(cid))

def bundle(cid='math-plain'):
    return compile_scene_for_qa(case_raw(cid)['document'])

def document(cid='math-plain', **updates):
    raw=case_raw(cid)['document']
    raw.pop('fingerprint',None)
    raw.update(updates)
    return decode_scene_ir(raw)

def context(seed=0):
    return DeterminismContext('a'*64,'test-1.0',seed,digest({'tool':'fixture'}),digest({'adapter':'fixture'}))
