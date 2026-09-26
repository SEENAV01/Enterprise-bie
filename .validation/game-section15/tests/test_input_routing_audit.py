"""Emitted React structure and controller event binding, with a DOM event harness."""
from dataclasses import replace
import unittest
from tests import test_runtime_audit_regressions as support
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.expressions import Compare,CompareOp,Variable,Literal
from bie.game_engine.interaction import EffectSpec,EffectKind

DOM_HARNESS=r'''
const nodes=[];
const React={createElement:(tag,props,...children)=>{
 const handlers={};const node={tag,props:props||{},children,dataset:{},value:props?.defaultValue||"",
 addEventListener:(type,fn)=>{(handlers[type]??=[]).push(fn);},
 removeEventListener:(type,fn)=>{handlers[type]=(handlers[type]||[]).filter(x=>x!==fn);},
 emit:(type,event={})=>{for(const fn of [...(handlers[type]||[])])fn(event);}};
 nodes.push(node);return node;}};
const tree=require('./js/react-runtime.js').renderGameRuntime(React,'level:1');
tree.querySelector=selector=>{const m=selector.match(/^\[([^=]+)="([^"]+)"\]$/);return m?nodes.find(n=>n.props[m[1]]===m[2])||null:null;};
const entity=()=>tree.querySelector('[data-entity-id="entity:mover"]');
c.bind(tree);
'''

class InputRoutingAudit(unittest.TestCase):
    def run_probe(self,body,multiple=False):
        ctx=compiler_context();game=ctx.document.experiences[0];level=game.levels[0]
        rule=replace(level.interaction.rules[0],condition=Compare(CompareOp.LT,Variable('x'),Literal(9)),effects=(EffectSpec('x',EffectKind.ADD,1),))
        level=replace(level,interaction=replace(level.interaction,rules=(rule,)))
        if multiple:
            first=level.challenges[0]
            second=replace(first,challenge_id='challenge:second',learning=replace(first.learning,objective_id='obj:second'))
            level=replace(level,challenges=(first,second))
        ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(level,)),)))
        return support.RuntimeAuditRegressions.run_runtime(self,custom_context=ctx,js_probe=DOM_HARNESS+body)

    def test_enter_runs_one_authored_action_on_shared_target(self):
        r=self.run_probe("entity().emit('keydown',{key:'Enter',preventDefault(){}});console.log(JSON.stringify({state:c.getState(),events:c.getTelemetry()}));")
        self.assertEqual(r['state']['x'],2);self.assertEqual(len(r['events']),1)

    def test_pointer_release_and_following_click_are_one_gesture(self):
        r=self.run_probe("entity().emit('pointerup',{button:0,clientX:20,clientY:10});entity().emit('click',{detail:1});console.log(JSON.stringify({state:c.getState(),events:c.getTelemetry()}));")
        self.assertEqual(r['state']['x'],2);self.assertEqual(len(r['events']),1)

    def test_screen_reader_click_runs_one_action(self):
        r=self.run_probe("entity().emit('click',{detail:0});console.log(JSON.stringify({state:c.getState(),events:c.getTelemetry()}));")
        self.assertEqual(r['state']['x'],2);self.assertEqual(len(r['events']),1)

    def test_secondary_action_has_its_own_accessible_control(self):
        r=self.run_probe("const button=tree.querySelector('[data-action-id=\"submit\"]');if(button)button.emit('click',{detail:0});console.log(JSON.stringify({found:!!button,label:button?.props['aria-label'],state:c.getState(),events:c.getTelemetry()}));")
        self.assertTrue(r['found']);self.assertEqual(r['label'],'Submit answer')
        self.assertEqual(r['state']['x'],2);self.assertEqual(len(r['events']),1)

    def test_selected_challenge_and_objective_are_preserved(self):
        r=self.run_probe("const chooser=tree.querySelector('[data-challenge-control=\"select\"]');if(chooser){chooser.value='challenge:second';entity().emit('click',{detail:0});}console.log(JSON.stringify({found:!!chooser,events:c.getTelemetry(),state:c.getState()}));",multiple=True)
        self.assertTrue(r['found']);self.assertEqual(r['state']['x'],2)
        self.assertEqual(r['events'][0]['challenge_id'],'challenge:second')
        self.assertEqual(r['events'][0]['objective_id'],'obj:second')

    def test_dispose_removes_all_input_handlers(self):
        r=self.run_probe("c.dispose();entity().emit('keydown',{key:'Enter',preventDefault(){}});entity().emit('click',{detail:0});console.log(JSON.stringify({state:c.getState(),events:c.getTelemetry()}));")
        self.assertEqual(r['state']['x'],1);self.assertEqual(r['events'],[])
