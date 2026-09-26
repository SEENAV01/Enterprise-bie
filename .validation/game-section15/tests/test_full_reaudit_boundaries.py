from dataclasses import replace
import unittest
from tests import test_runtime_audit_regressions as harness
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.contracts import ScoringPolicy,hashlib_sha
from bie.game_engine.compiler_engine.expression_codegen import compile_expr
from bie.game_engine.expressions import Boolean,BoolOp,Literal,Compare,CompareOp,Binary,BinaryOp,Variable

class FullReauditBoundaries(unittest.TestCase):
    run_runtime=harness.RuntimeAuditRegressions.run_runtime

    def test_nonfinite_scoring_rejected(self):
        for value in (float('nan'),float('inf'),-float('inf')):
            with self.subTest(value=value),self.assertRaises(Exception):ScoringPolicy('policy:test',value).validate()

    def test_unsafe_integer_literal_rejected_before_precision_loss(self):
        with self.assertRaises(Exception):compile_expr(Literal(2**53+1))

    def test_adaptation_error_rolls_back_state_score_and_events(self):
        from bie.game_engine.adaptation import AdaptationRule,AdaptAction
        ctx=compiler_context();game=ctx.document.experiences[0];level=game.levels[0]
        bad=AdaptationRule('adapt:bad',Compare(CompareOp.GT,Binary(BinaryOp.DIV,Literal(1),Variable('attempts')),Literal(0)),AdaptAction.REPEAT,1)
        level=replace(level,adaptation=replace(level.adaptation,rules=(bad,)))
        ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(level,)),)))
        r=self.run_runtime(custom_context=ctx)
        self.assertIn('GAME_EXPR_DIV_ZERO',r['error']);self.assertEqual(r['state']['x'],1)
        self.assertEqual(r['score'],0);self.assertEqual(r['telemetry'],[])

    def test_receipt_cannot_attest_different_artifact_bytes(self):
        bundle=compile_game(compiler_context());old=bundle.artifacts[0]
        changed=replace(old,content=old.content+'\n',sha256=hashlib_sha(old.content+'\n'))
        with self.assertRaises(Exception):replace(bundle,artifacts=(changed,)+bundle.artifacts[1:]).validate()

    def test_telemetry_readout_does_not_expose_mutable_internal_events(self):
        r=self.run_runtime(js_probe="c.dispatch('drag:mover');c.getTelemetry()[0].outcome_code='forged';console.log(JSON.stringify(c.getTelemetry()[0]));")
        self.assertEqual(r['outcome_code'],'succeeded')

    def test_disposed_controller_cannot_play_audio(self):
        r=self.run_runtime(js_probe="c.dispose();let error='';try{c.playNarration()}catch(e){error=String(e)}console.log(JSON.stringify({error}));")
        self.assertIn('GAME_RUNTIME_DISPOSED',r['error'])

    def test_disposing_one_controller_preserves_another_controllers_audio(self):
        ctx=compiler_context();game=ctx.document.experiences[0];level=game.levels[0]
        cue=replace(level.audio.cues[0],trigger_event='level_start',asset_ref='asset:sfx:success')
        level=replace(level,audio=replace(level.audio,cues=(cue,)))
        ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(level,)),)))
        r=self.run_runtime(custom_context=ctx,js_probe="const played=[];global.__BIE_GAME_ASSETS__={'asset:sfx:success':'local.wav'};global.Audio=class{constructor(){this.paused=false;this.dataset={};played.push(this)}addEventListener(){}play(){return Promise.resolve()}pause(){this.paused=true}};const other=require('./js/runtime-controller.js').createRuntimeController('level:1');c.playNarration();other.playNarration();c.dispose();console.log(JSON.stringify(played.map(a=>a.paused)));")
        self.assertEqual(r,[True,False])

    def test_dispatch_result_cannot_mutate_stored_telemetry(self):
        r=self.run_runtime(js_probe="const r=c.dispatch('drag:mover');r.telemetry.outcome_code='forged';console.log(JSON.stringify(c.getTelemetry()[0]));")
        self.assertEqual(r['outcome_code'],'succeeded')

    def test_non_boolean_boolean_operand_rejected(self):
        with self.assertRaises(Exception):compile_expr(Boolean(BoolOp.AND,(Literal(1),Literal(True))))

    def test_mixed_ordering_rejected_before_javascript_coercion(self):
        with self.assertRaises(Exception):compile_expr(Compare(CompareOp.LT,Literal('2'),Literal(3)))

    def test_same_level_id_in_different_games_resolves_explicit_game(self):
        ctx=compiler_context();first=ctx.document.experiences[0]
        second=replace(first,game_id='game:second',scoring_policy_ref='policy:second')
        ctx=replace(ctx,document=replace(ctx.document,experiences=(first,second)),scoring_policies={**ctx.scoring_policies,'policy:second':ScoringPolicy('policy:second',25)})
        # Helper's initial controller is deliberately unambiguous on an extra level.
        first=replace(first,levels=first.levels+(replace(first.levels[0],level_id='level:unique'),))
        ctx=replace(ctx,document=replace(ctx.document,experiences=(first,second)))
        r=self.run_runtime(custom_context=ctx,level_id='level:unique',js_probe="const other=require('./js/runtime-controller.js').createRuntimeController('level:1','game:second');const r=other.dispatch('drag:mover');console.log(JSON.stringify({score:other.getScore(),event:r.telemetry}));")
        self.assertEqual(r['score'],25);self.assertEqual(r['event']['game_id'],'game:second')

    def test_ambiguous_level_requires_game_instead_of_first_match(self):
        ctx=compiler_context();first=ctx.document.experiences[0];second=replace(first,game_id='game:second')
        first=replace(first,levels=first.levels+(replace(first.levels[0],level_id='level:unique'),))
        ctx=replace(ctx,document=replace(ctx.document,experiences=(first,second)))
        r=self.run_runtime(custom_context=ctx,level_id='level:unique',js_probe="let error='';try{require('./js/runtime-controller.js').createRuntimeController('level:1')}catch(e){error=String(e)}console.log(JSON.stringify({error}));")
        self.assertIn('GAME_LEVEL_AMBIGUOUS',r['error'])
