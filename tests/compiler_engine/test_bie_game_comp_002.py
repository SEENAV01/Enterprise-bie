import unittest
from dataclasses import replace
from bie.game_engine.compiler_engine.react_runtime import compile_react_runtime as FUNC
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.contracts import *
from bie.game_engine.compiler_engine.errors import GameCompilerError

class Comp002Tests(unittest.TestCase):
    def test_valid_compile(self):
        a=FUNC(compiler_context());self.assertEqual(a.kind,ArtifactKind.REACT_RUNTIME);self.assertIn('react-runtime.ts',a.path);a.validate()
    def test_deterministic(self):self.assertEqual(FUNC(compiler_context()),FUNC(compiler_context()))
    def test_content_hash_bound(self):
        a=FUNC(compiler_context());import hashlib;self.assertEqual(a.sha256,hashlib.sha256(a.content.encode()).hexdigest())
    def test_product_acceptance_false(self):self.assertFalse(FUNC(compiler_context()).product_accepted)
    def test_missing_provenance_fails(self):
        c=compiler_context();from bie.game_engine.provenance import ProvenanceBundle;c=replace(c,document=replace(c.document,provenance=ProvenanceBundle(())))
        with self.assertRaises(Exception):FUNC(c)

    def test_studio_runtime_not_slide_deck(self):
        a=FUNC(compiler_context());self.assertIn('data-slide-deck',a.content);self.assertIn('data-studio-grade',a.content);self.assertIn('semantic_role',a.content)

if __name__=='__main__':unittest.main()
