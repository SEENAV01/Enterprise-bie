"""Executable, explicitly synthetic walkthrough of all five SYNC contracts."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'tests/director'))
from sync_fixtures import context,binding,visual,equation_case,graph_case,simulation_case
from bie.director.narration_animation_sync import AnimationIntent,sync_animation_intents
from bie.director.equation_narration_sync import sync_equation_narration
from bie.director.graph_narration_sync import sync_graph_narration
from bie.director.simulation_narration_sync import sync_simulation_narration


def walkthrough():
    ctx=context(); v=visual(ctx)
    a=sync_animation_intents(ctx,v,[AnimationIntent(binding(ctx,'reveal',end=2),'v','reveal'),
        AnimationIntent(binding(ctx,'emphasis',start=2,end=4),'v','emphasize',after_intent_ids=('reveal',))])
    records=[{'context':asdict(ctx),'visual':asdict(v),'animation':asdict(a),
              'status':a.status,'fingerprint':a.fingerprint()}]
    for fixture,builder,label in ((equation_case,sync_equation_narration,'equation'),
                                  (graph_case,sync_graph_narration,'graph'),
                                  (simulation_case,sync_simulation_narration,'simulation')):
        ctx,v,definitions,rows=fixture()
        p=builder(ctx,v,definitions if isinstance(definitions,tuple) else (definitions,),rows)
        records.append({'context':asdict(ctx),'visual':asdict(v),'kind':label,'plan':asdict(p),
                        'status':p.status,'fingerprint':p.fingerprint()})
    return {'scope':'Synthetic recovered-DIR and TIME to SYNC contract examples; not a real-book/render/runtime run',
            'accepted':False,'examples':records}


if __name__=='__main__': print(json.dumps(walkthrough(),indent=2,ensure_ascii=False))
