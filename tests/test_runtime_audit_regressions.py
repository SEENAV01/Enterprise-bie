"""Execute emitted TypeScript under Node to test runtime semantics, not strings."""
from dataclasses import replace
from pathlib import Path
import json,os,shutil,subprocess,tempfile,unittest
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.expressions import Compare,CompareOp,Variable,Literal
from bie.game_engine.interaction import EffectSpec,EffectKind

class RuntimeAuditRegressions(unittest.TestCase):
    def run_runtime(self,*,target=2,failure=False,effects=None,multiple=False,repeat=False,custom_context=None,level_id='level:1',js_probe=None):
        ctx=compiler_context();game=ctx.document.experiences[0];level=game.levels[0]
        ch=replace(level.challenges[0],success_condition=Compare(CompareOp.EQ,Variable('x'),Literal(target)))
        if failure:ch=replace(ch,failure_conditions=(Compare(CompareOp.EQ,Variable('x'),Literal(2)),))
        challenges=(ch,replace(ch,challenge_id='challenge:second')) if multiple else (ch,)
        rule=level.interaction.rules[0]
        if effects is not None:rule=replace(rule,effects=effects)
        if repeat:rule=replace(rule,condition=Compare(CompareOp.LE,Variable('x'),Literal(2)))
        level=replace(level,challenges=challenges,interaction=replace(level.interaction,rules=(rule,)))
        ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(level,)),))).validate()
        if custom_context is not None:ctx=custom_context.validate()
        node=os.environ.get('BIE_NODE') or shutil.which('node');self.assertIsNotNone(node)
        with tempfile.TemporaryDirectory(prefix='bie-runtime-audit-') as td:
            root=Path(td)
            for a in compile_game(ctx).artifacts:
                if a.path.endswith('.ts'):(root/Path(a.path).name).write_text(a.content,encoding='utf-8')
            tsc_js=os.environ.get('BIE_TSC_JS')
            cmd=[node,'--preserve-symlinks','--preserve-symlinks-main',tsc_js] if tsc_js else [shutil.which('tsc')]
            self.assertIsNotNone(cmd[0])
            cmd+=['--target','ES2020','--module','commonjs','--strict','--skipLibCheck','--lib','ES2020,DOM','--noEmitOnError','--outDir',str(root/'js')]+[str(p) for p in root.glob('*.ts')]
            built=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
            self.assertEqual(built.returncode,0,built.stdout+built.stderr)
            js="global.window={};global.document={querySelector:()=>null,getElementById:()=>null};const c=require('./js/runtime-controller.js').createRuntimeController("+json.dumps(level_id)+");try{const first=c.dispatch('drag:mover');"
            js+=("c.dispatch('drag:mover');" if repeat else '')
            js+="console.log(JSON.stringify({first,state:c.getState(),score:c.getScore()}));}catch(e){console.log(JSON.stringify({error:String(e),state:c.getState(),score:c.getScore(),telemetry:c.getTelemetry()}));}"
            if js_probe is not None:
                js="global.window={};global.document={querySelector:()=>null,getElementById:()=>null};const c=require('./js/runtime-controller.js').createRuntimeController("+json.dumps(level_id)+");"+js_probe
            (root/'probe.cjs').write_text(js)
            run=subprocess.run([node,'--preserve-symlinks','--preserve-symlinks-main',str(root/'probe.cjs')],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            return json.loads(run.stdout)

    def test_pending_challenge_cannot_receive_success_points(self):
        r=self.run_runtime(target=3);self.assertEqual(r['score'],0)
        self.assertEqual(r['first']['telemetry']['outcome_code'],'in_progress')
        self.assertNotIn('Correct',r['first']['feedback'])
    def test_met_condition_receives_points(self):
        r=self.run_runtime();self.assertEqual(r['score'],10)
        self.assertEqual(r['first']['telemetry']['outcome_code'],'succeeded')
    def test_failure_takes_precedence_over_success(self):
        r=self.run_runtime(failure=True);self.assertEqual(r['score'],0)
        self.assertEqual(r['first']['telemetry']['outcome_code'],'failed')
    def test_repeating_success_cannot_farm_points(self):
        self.assertEqual(self.run_runtime(repeat=True)['score'],10)
    def test_out_of_range_effect_rolls_back_without_score_or_telemetry(self):
        r=self.run_runtime(effects=(EffectSpec('x',EffectKind.ADD,100.0),))
        self.assertIn('GAME_RUNTIME_STATE_RANGE',r['error']);self.assertEqual(r['state']['x'],1)
        self.assertEqual(r['score'],0);self.assertEqual(r['telemetry'],[])
    def test_partial_effect_transaction_rolls_back(self):
        r=self.run_runtime(effects=(EffectSpec('x',EffectKind.SET,2.0),EffectSpec('attempts',EffectKind.SET,1.5)))
        self.assertIn('GAME_RUNTIME_STATE_TYPE',r['error']);self.assertEqual(r['state'],{'x':1,'attempts':0})
    def test_ambiguous_challenge_route_cannot_silently_pick_first(self):
        r=self.run_runtime(multiple=True);self.assertIn('GAME_RUNTIME_CHALLENGE_ROUTE_AMBIGUOUS',r['error'])
        self.assertEqual(r['score'],0);self.assertEqual(r['state']['x'],1)

    def test_numeric_string_effect_is_not_silently_coerced(self):
        r=self.run_runtime(effects=(EffectSpec('x',EffectKind.ADD,'1'),))
        self.assertIn('GAME_RUNTIME_EFFECT_NUMERIC',r.get('error',''))
        self.assertEqual(r['state']['x'],1);self.assertEqual(r['score'],0)

    def test_repeated_rule_ids_in_distinct_levels_keep_their_own_predicates(self):
        ctx=compiler_context();game=ctx.document.experiences[0];first=game.levels[0]
        rule=replace(first.interaction.rules[0],condition=Compare(CompareOp.GT,Variable('x'),Literal(8)))
        second=replace(first,level_id='level:2',interaction=replace(first.interaction,rules=(rule,)))
        ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(first,second)),)))
        r=self.run_runtime(custom_context=ctx,level_id='level:2')
        self.assertFalse(r['first']['applied']);self.assertEqual(r['state']['x'],1);self.assertEqual(r['score'],0)

    def test_punctuation_distinct_ids_do_not_collide_in_generated_functions(self):
        ctx=compiler_context();game=ctx.document.experiences[0];first=game.levels[0]
        second=replace(first,level_id='level_1')
        ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(first,second)),)))
        r=self.run_runtime(custom_context=ctx,level_id='level_1')
        self.assertTrue(r['first']['applied']);self.assertEqual(r['score'],10)

    def test_reviewed_legacy_candidate_reaches_actual_compiled_consumer(self):
        from tests.hardening_h6.legacy_support import fixture
        from bie.game_engine.legacy_migration import migrate_legacy
        from bie.game_engine.legacy_codec import dump_legacy,load_legacy
        wire,enrichment=fixture();migration=migrate_legacy(wire,enrichment)
        ctx=compiler_context()
        ctx=replace(ctx,document=migration.document(),text_catalog={**ctx.text_catalog,**enrichment.text_catalog})
        result=self.run_runtime(custom_context=ctx)
        self.assertEqual(result['state']['x'],2)
        self.assertEqual(result['score'],10)
        self.assertEqual(result['first']['feedback'],'Success')
        self.assertEqual(migration.legacy_wire,wire)
        self.assertEqual(dump_legacy(load_legacy(wire)),wire)
        self.assertFalse(json.loads(migration.receipt_wire)['independent_semantic_equivalence_proven'])
