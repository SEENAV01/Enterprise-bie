"""Synthetic fixtures built through the real recovered DIR contracts."""
from dataclasses import replace
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.speech_timing import utterances_from_script, estimate_speech
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.sync_contract import build_sync_context, SyncIndex, IntentBinding
from bie.director.narration_visual_sync import VisualIntent, sync_visual_intents


def context(texts=("First explain the source concept clearly.",),wpm=120):
    segments=[ScriptSegment(f'u{i}', 's', 'EXPLAIN', 'Structured intent', ('e',), ('o',)) for i in range(len(texts))]
    script=build_script_plan('lesson',segments,'teacher-v1')
    drafts=[generate_voiceover(s.segment_id,[text],{text:('e',)}) for s,text in zip(segments,texts)]
    speech=estimate_speech(utterances_from_script(script,drafts,[s.segment_id for s in segments]),wpm=wpm)
    return build_sync_context(speech,build_pause_timing(speech),build_emphasis_timing(speech))


def binding(ctx,iid='v',uid='u0',start=0,end=None,target='element'):
    index=SyncIndex(ctx)
    end=len(index.utterances[uid].words) if end is None else end
    return IntentBinding(iid,target,index.anchor(uid,start,end),('e',),('o',),('c',),'Explain the source concept')


def visual(ctx,kind='diagram',target='element'):
    # The visible target may span several utterances; its anchor and explicit hold
    # retain the exact first narration binding and whole-scene lifetime.
    b=binding(ctx,target=target)
    first_end=SyncIndex(ctx).resolve(b).end_ms
    tail=ctx.timeline.scenes[0].duration_ms-first_end
    return sync_visual_intents(ctx,[VisualIntent(b,kind,tail_ms=tail)])


def equation_case():
    from bie.director.derivation_narration import narrate_derivation
    from bie.director.equation_narration_sync import EquationToken,EquationState,EquationIntent
    steps=narrate_derivation([('x = one','State the first expression',('e',)),
                             ('x + one = two','Add one to both sides',('e',))])
    ctx=context(tuple(s.narration for s in steps))
    states=tuple(EquationState(f'q{i}','s','element',step,(EquationToken('x',0,1),)) for i,step in enumerate(steps))
    intents=tuple(EquationIntent(binding(ctx,f'show{i}',f'u{i}'),'v',s.state_id,s.fingerprint(),'SHOW_STEP')
                  for i,s in enumerate(states))
    return ctx,visual(ctx,'equation'),states,intents


def graph_case():
    from bie.director.graph_narration_sync import GraphAxis,GraphPoint,GraphSeries,GraphDefinition,GraphIntent
    ctx=context(('Explain the axes and units.', 'Trace the three source points.', 'Highlight the middle point.'))
    graph=GraphDefinition('g','s','element','fixture/1',GraphAxis('x','Time','s',0,2),
        GraphAxis('y','Distance','m',0,4),(GraphSeries('series','Position',(
            GraphPoint('p0',0,0,('e',)),GraphPoint('p1',1,2,('e',)),GraphPoint('p2',2,4,('e',)))),),('e',))
    intents=(GraphIntent(binding(ctx,'axes','u0'),'v','g',graph.fingerprint(),'SHOW_AXES'),
        GraphIntent(binding(ctx,'trace','u1'),'v','g',graph.fingerprint(),'TRACE_SERIES','series'),
        GraphIntent(binding(ctx,'point','u2'),'v','g',graph.fingerprint(),'HIGHLIGHT_POINT','series',('p1',)))
    return ctx,visual(ctx,'graph'),graph,intents


def simulation_case():
    from bie.director.demonstration_narration import narrate_demonstration
    from bie.director.simulation_narration_sync import (SimulationParameter,ParameterValue,SimulationState,
        SimulationTransition,SimulationDefinition,SimulationIntent)
    phases=narrate_demonstration('Set the starting position.', 'Change the declared position.',
        'Observe the changed position.', 'Explain the position change.',('e',))
    ctx=context(tuple(p.narration for p in phases))
    spec=SimulationDefinition('sim','s','element','fixture/1','sha256:'+'a'*64,42,
        (SimulationParameter('position','m',0,10),),
        (SimulationState('initial',(ParameterValue('position',0),)),SimulationState('changed',(ParameterValue('position',2),))),
        (SimulationTransition('move','initial','changed',('position',),500),),'initial',('e',))
    intents=tuple(SimulationIntent(binding(ctx,f'phase{i}',f'u{i}'),'v','sim',spec.fingerprint(),step,
        'initial' if i==0 else 'changed','move' if i==1 else None) for i,step in enumerate(phases))
    return ctx,visual(ctx,'simulation'),spec,intents
