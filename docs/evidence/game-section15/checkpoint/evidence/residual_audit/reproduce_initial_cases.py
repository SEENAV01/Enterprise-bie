from pathlib import Path
from dataclasses import replace
import json,subprocess,sys
ROOT=Path(__file__).parent.resolve();sys.path.insert(0,str(ROOT/'h7'))
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.expressions import Compare,CompareOp,Variable,Literal
from bie.game_engine.interaction import EffectSpec,EffectKind
out=ROOT/'audit_runtime';out.mkdir(exist_ok=True)
node=Path('C:/Users/Dell/AppData/Local/Programs/nodejs-v22.16.0/node.exe')
tsc=ROOT/'h6/tooling/react/node_modules/typescript/bin/tsc'
results=[]
for case in ('incomplete_challenge','state_overflow'):
    ctx=compiler_context();game=ctx.document.experiences[0];level=game.levels[0]
    if case=='incomplete_challenge':
        challenge=replace(level.challenges[0],success_condition=Compare(CompareOp.EQ,Variable('x'),Literal(3)))
        level=replace(level,challenges=(challenge,))
    else:
        rule=replace(level.interaction.rules[0],effects=(EffectSpec('x',EffectKind.ADD,100.0),))
        level=replace(level,interaction=replace(level.interaction,rules=(rule,)))
    ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(level,)),))).validate()
    folder=out/case;folder.mkdir(exist_ok=True)
    bundle=compile_game(ctx)
    for a in bundle.artifacts:
        if a.path.endswith('.ts'):(folder/Path(a.path).name).write_text(a.content,encoding='utf-8')
    cmd=[str(node),'--preserve-symlinks','--preserve-symlinks-main',str(tsc),'--target','ES2020','--module','commonjs','--strict','--skipLibCheck','--lib','ES2020,DOM','--noEmitOnError','--outDir',str(folder/'js')]+[str(p) for p in folder.glob('*.ts')]
    p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
    js="global.window={};global.document={querySelector:()=>null,getElementById:()=>null};const c=require('./js/runtime-controller.js').createRuntimeController('level:1');try{console.log(JSON.stringify(c.dispatch('drag:mover')));}catch(e){console.log(JSON.stringify({error:String(e),state:c.getState(),score:c.getScore()}));}"
    (folder/'probe.cjs').write_text(js)
    p=subprocess.run([str(node),'--preserve-symlinks','--preserve-symlinks-main',str(folder/'probe.cjs')],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    results.append({'case':case,'actual':json.loads(p.stdout)})
(out/'INITIAL_RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
