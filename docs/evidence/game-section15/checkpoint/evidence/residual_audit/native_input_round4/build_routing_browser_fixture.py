from pathlib import Path
from dataclasses import replace
import hashlib,json,runpy,sys
root=Path(__file__).parent.resolve();source=root/'residual'
module=runpy.run_path(str(source/'scripts/build_h6_browser_probe.py'),run_name='routing_fixture_builder')
namespace=module['main'].__globals__;original=namespace['probe_context']
from bie.game_engine.expressions import Compare,CompareOp,Variable,Literal
from bie.game_engine.interaction import EffectSpec,EffectKind
def context():
    ctx,audio=original();game=ctx.document.experiences[0];level=game.levels[0]
    rule=replace(level.interaction.rules[0],condition=Compare(CompareOp.LT,Variable('x'),Literal(9)),effects=(EffectSpec('x',EffectKind.ADD,1),))
    first=level.challenges[0];second=replace(first,challenge_id='challenge:second',title='Second challenge',learning=replace(first.learning,objective_id='obj:second'))
    level=replace(level,challenges=(first,second),interaction=replace(level.interaction,rules=(rule,)))
    return replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(level,)),))).validate(),audio
namespace['probe_context']=context
# Compiler modules above were imported from the current candidate; reuse only
# the exact locked TypeScript tool and unchanged test harness from the H6 tree.
namespace['ROOT']=root/'h6'
dest=root/'routing_browser_fixture'
sys.argv=['build_routing_browser_fixture.py','--node','C:/Users/Dell/AppData/Local/Programs/nodejs-v22.16.0/node.exe','--output',str(dest)]
module['main']()
receipt=json.loads((dest/'BUILD_RECEIPT.json').read_text())
receipt['candidate_source_sha256']={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((source/'bie/game_engine').rglob('*.py'))}
receipt['fixture_scope']='Two authored actions share one entity; repeatable +1 rule exposes duplicate event dispatch; two explicitly selectable challenges.'
(dest/'BUILD_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
