import unittest,json
from dataclasses import replace
from bie.game_engine.compiler_engine.contracts import *
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.errors import GameCompilerError
from bie.game_engine.compiler_engine.scoring_compiler import compile_scoring
from bie.game_engine.compiler_engine.feedback_compiler import compile_feedback
from bie.game_engine.compiler_engine.telemetry_compiler import compile_telemetry
from bie.game_engine.compiler_engine.asset_manifest import compile_asset_manifest
from bie.game_engine.compiler_engine.html_runtime import compile_html_runtime

class CompilerAdversarialTests(unittest.TestCase):
 def test_security_policy_remote_network_rejected(self):
  with self.assertRaises(GameCompilerError):replace(compiler_context(),security=CompilerSecurityPolicy(allow_remote_network=True)).validate()
 def test_security_policy_inline_script_rejected(self):
  with self.assertRaises(GameCompilerError):replace(compiler_context(),security=CompilerSecurityPolicy(allow_inline_script=True)).validate()
 def test_security_policy_eval_rejected(self):
  with self.assertRaises(GameCompilerError):replace(compiler_context(),security=CompilerSecurityPolicy(allow_eval=True)).validate()
 def test_security_policy_dynamic_import_rejected(self):
  with self.assertRaises(GameCompilerError):replace(compiler_context(),security=CompilerSecurityPolicy(allow_dynamic_import=True)).validate()
 def test_telemetry_raw_text_policy_rejected(self):
  with self.assertRaises(GameCompilerError):replace(compiler_context(),security=CompilerSecurityPolicy(telemetry_raw_text=True)).validate()
 def test_artifact_path_traversal_rejected(self):
  with self.assertRaises(GameCompilerError):artifact(ArtifactKind.GAME_IR,'../evil.json','application/json','{}',('source:book',))
 def test_artifact_absolute_path_rejected(self):
  with self.assertRaises(GameCompilerError):artifact(ArtifactKind.GAME_IR,'/tmp/evil.json','application/json','{}',('source:book',))
 def test_tampered_artifact_hash_rejected(self):
  a=CompiledArtifact(ArtifactKind.GAME_IR,'runtime/x.json','application/json','{}','0'*64,('source:book',),False)
  with self.assertRaises(GameCompilerError):a.validate()
 def test_missing_scoring_policy_fails_closed(self):
  with self.assertRaises(GameCompilerError):compile_scoring(replace(compiler_context(),scoring_policies={}))
 def test_speed_pressure_scoring_fails_closed(self):
  bad=ScoringPolicy('policy:score:v1',10,0,0,0,True,True)
  with self.assertRaises(GameCompilerError):compile_scoring(replace(compiler_context(),scoring_policies={'policy:score:v1':bad}))
 def test_negative_hint_cost_rejected(self):
  bad=ScoringPolicy('policy:score:v1',10,0,-1,0,True,False)
  with self.assertRaises(GameCompilerError):bad.validate()
 def test_invalid_mastery_threshold_rejected(self):
  with self.assertRaises(GameCompilerError):MasteryPolicy('policy:mastery:v1',1.2).validate()
 def test_missing_feedback_text_fails_closed(self):
  c=compiler_context();cat=dict(c.text_catalog);cat.pop('text:success')
  with self.assertRaises(GameCompilerError):compile_feedback(replace(c,text_catalog=cat))
 def test_missing_audio_asset_fails_closed(self):
  with self.assertRaises(GameCompilerError):compile_asset_manifest(replace(compiler_context(),assets={}))
 def test_duplicate_telemetry_allowlist_rejected(self):
  with self.assertRaises(GameCompilerError):replace(compiler_context(),telemetry_allowlist=('game_started','game_started')).validate()
 def test_sensitive_email_telemetry_rejected(self):
  with self.assertRaises(GameCompilerError):compile_telemetry(replace(compiler_context(),telemetry_allowlist=('email_changed',)))
 def test_sensitive_answer_text_telemetry_rejected(self):
  with self.assertRaises(GameCompilerError):compile_telemetry(replace(compiler_context(),telemetry_allowlist=('answer_text',)))
 def test_html_has_no_inline_executable_script(self):
  h=compile_html_runtime(compiler_context()).content
  self.assertNotIn('<script>',h);self.assertIn('src="./bootstrap.js"',h)
 def test_bundle_has_no_duplicate_hash_path_pairs(self):
  b=compile_game(compiler_context());pairs=[(a.path,a.sha256) for a in b.artifacts];self.assertEqual(len(pairs),len(set(pairs)))
 def test_bundle_receipt_profile_bound(self):
  b=compile_game(compiler_context());self.assertEqual(b.receipt.compiler_profile,'studio-enterprise-v1')
