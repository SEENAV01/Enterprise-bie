import unittest
from dataclasses import replace
from bie.game_engine.compiler_engine.scoring_compiler import compile_scoring as FUNC
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.contracts import *
from bie.game_engine.compiler_engine.errors import GameCompilerError

class Comp007Tests(unittest.TestCase):
    def test_valid_compile(self):
        a=FUNC(compiler_context());self.assertEqual(a.kind,ArtifactKind.SCORING_PROGRAM);self.assertIn('scoring.ts',a.path);a.validate()
    def test_deterministic(self):self.assertEqual(FUNC(compiler_context()),FUNC(compiler_context()))
    def test_content_hash_bound(self):
        a=FUNC(compiler_context());import hashlib;self.assertEqual(a.sha256,hashlib.sha256(a.content.encode()).hexdigest())
    def test_product_acceptance_false(self):self.assertFalse(FUNC(compiler_context()).product_accepted)
    def test_missing_provenance_fails(self):
        c=compiler_context();from bie.game_engine.provenance import ProvenanceBundle;c=replace(c,document=replace(c.document,provenance=ProvenanceBundle(())))
        with self.assertRaises(Exception):FUNC(c)

    def test_speed_pressure_forbidden(self):
        c=compiler_context();bad=ScoringPolicy('policy:score:v1',10,0,1,0,True,True);c=replace(c,scoring_policies={'policy:score:v1':bad})
        with self.assertRaises(GameCompilerError):FUNC(c)

if __name__=='__main__':unittest.main()
