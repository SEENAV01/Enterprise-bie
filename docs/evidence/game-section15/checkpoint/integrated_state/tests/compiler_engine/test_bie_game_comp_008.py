import unittest
from dataclasses import replace
from bie.game_engine.compiler_engine.feedback_compiler import compile_feedback as FUNC
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.contracts import *
from bie.game_engine.compiler_engine.errors import GameCompilerError

class Comp008Tests(unittest.TestCase):
    def test_valid_compile(self):
        a=FUNC(compiler_context());self.assertEqual(a.kind,ArtifactKind.FEEDBACK_PROGRAM);self.assertIn('feedback.ts',a.path);a.validate()
    def test_deterministic(self):self.assertEqual(FUNC(compiler_context()),FUNC(compiler_context()))
    def test_content_hash_bound(self):
        a=FUNC(compiler_context());import hashlib;self.assertEqual(a.sha256,hashlib.sha256(a.content.encode()).hexdigest())
    def test_product_acceptance_false(self):self.assertFalse(FUNC(compiler_context()).product_accepted)
    def test_missing_provenance_fails(self):
        c=compiler_context();from bie.game_engine.provenance import ProvenanceBundle;c=replace(c,document=replace(c.document,provenance=ProvenanceBundle(())))
        with self.assertRaises(Exception):FUNC(c)

    def test_no_premature_answer_reveal(self):
        a=FUNC(compiler_context());self.assertIn('"reveal_answer_on_failure":false',a.content)
    def test_missing_text_ref_fails_closed(self):
        c=compiler_context();c=replace(c,text_catalog={})
        with self.assertRaises(GameCompilerError):FUNC(c)

if __name__=='__main__':unittest.main()
