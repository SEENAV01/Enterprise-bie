#!/usr/bin/env python3
"""One-time authoring of NEW QA-009 technical fixtures and explicit initial goldens.

Never called by regression. These baselines are a new test corpus over unchanged
Batch-008 emitters, not historical goldens or product/subject-matter approval.
"""
from dataclasses import asdict
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement, UnifiedTrack, UnifiedSceneIRDocument
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.generated_code_regression import record_generated_baseline
from bie.compiler.qa_common import write_json


def document(case_id, specs, *, track=False):
    elements=[]
    for index, (kind, props) in enumerate(specs):
        acc={'alt':f'Synthetic {kind} compiler fixture', 'color_independent_encoding':True}
        if kind in {'simulation','particle_system'}: acc['reduced_motion_variant']='fixture:static'
        elements.append(UnifiedElement(f'e{index}',kind,props,
            (f'fixture:{case_id}:e{index}',),(f'fixture-reasoning:{case_id}:e{index}',),acc,
            {'x':0.05,'y':0.05 + index * 0.45,'width':0.9,'height':0.4}))
    tracks=(UnifiedTrack('t0','e0','reveal',0,1000,{},('fixture:track-source',),('fixture:track-reasoning',)),) if track else ()
    doc=UnifiedSceneIRDocument(case_id,'1.0.0','Synthetic technical compiler case',2000,tuple(elements),tracks,
        (f'fixture:{case_id}',),(f'fixture-reasoning:{case_id}',),
        metadata={'fixture_id':case_id,'source_kind':'SYNTHETIC_TECHNICAL_FIXTURE_NOT_TEXTBOOK','not_textbook':True})
    return doc.to_dict()


def cases():
    records=[]
    def add(cid,domain,specs,codes=(),track=False):
        records.append({'case_id':cid,'domain':domain,'document':document(cid,specs,track=track),
              'expected_source_passed':not codes,'expected_error_codes':list(codes),
              'max_codegen_ms':5000,'max_source_bytes':500000,
              'source_kind':'SYNTHETIC_TECHNICAL_FIXTURE_NOT_TEXTBOOK'})
    add('math-plain','mathematics',[('equation',{'expression':'x + 1 = 2','format':'plain'})])
    add('physics-vector','physics',[('vector',{'components':[1,2],'label':'Synthetic vector'})])
    add('chemistry-connectivity','chemistry',[('model2d',{'vertices':[[0.2,0.2],[0.8,0.2],[0.5,0.8]],'edges':[[0,1],[1,2],[2,0]]})])
    add('biology-structure','biology',[('model2d',{'vertices':[[0.2,0.3],[0.7,0.3],[0.5,0.7]],'edges':[[0,1],[1,2]]}),('text',{'text':'Synthetic structure labels — not a validated biology lesson.'})])
    add('statistics-counts','statistics',[('chart',{'chart_kind':'bar','categories':['A','B','C'],'values':[2,4,3]})])
    add('economics-series','economics',[('graph',{'series':[{'points':[[0,0.1],[0.5,0.3],[1,0.8]]}]})])
    add('accountancy-totals','accountancy',[('chart',{'chart_kind':'bar','categories':['Toy debit','Toy credit'],'values':[5,5]})])
    add('history-sequence','history',[('timeline',{'events':[{'event_id':'a','label':'Synthetic event A'},{'event_id':'b','label':'Synthetic event B'}]})])
    add('geography-route','geography',[('map',{'crs':'BIE:NORMALIZED','layers':[{'kind':'route','points':[[0.1,0.2],[0.5,0.6],[0.9,0.8]]}]})])
    add('engineering-labels','engineering',[('text',{'text':'तकनीकी परीक्षण • engineering fixture'}),('vector',{'components':[2,1]})])
    add('reject-chart-kind','statistics',[('chart',{'chart_kind':'line','categories':['A','B'],'values':[1,2]})],('CHART_KIND_DOWNGRADE',))
    add('reject-chart-sign','accountancy',[('chart',{'chart_kind':'bar','categories':['A','B'],'values':[-2,3]})],('CHART_SIGN_LOSS',))
    add('reject-vector-z','physics',[('vector',{'components':[1,2,3]})],('VECTOR_Z_COMPONENT_DROPPED',))
    add('reject-untypeset-equation','mathematics',[('equation',{'expression':r'\frac{1}{2}','format':'latex'})],('EQUATION_TYPESETTING_NOT_IMPLEMENTED',))
    add('reject-jsx-braces','engineering',[('text',{'text':'{Math.random()}'})],('TEXT_LITERAL_JSX_INJECTION','QA_UNSEEDED_RANDOM'))
    add('reject-state-only-simulation','physics',[('simulation',{'model_ref':'fixture:toy-model','initial_state':{'x':0},'execution_class':'conceptual'})],('SIMULATION_STATE_ONLY',))
    add('reject-metadata-animation','biology',[('text',{'text':'Static text does not become animation merely through a progress attribute.'})],('ANIMATION_TRACK_NO_VISUAL_EFFECT',),track=True)
    add('reject-geographic-crs','geography',[('map',{'crs':'EPSG:4326','layers':[{'kind':'route','points':[[0.1,0.2],[0.3,0.4]]}]})],('MAP_PROJECTION_UNVERIFIED',))
    add('reject-model-edge','chemistry',[('model2d',{'vertices':[[0.1,0.1],[0.2,0.2]],'edges':[[0,5]]})],('MODEL2D_EDGE_INDEX_INVALID',))
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--record-initial-baselines',action='store_true')
    p.add_argument('--approval-ref')
    args=p.parse_args()
    if args.output.exists() and any(args.output.iterdir()): raise ValueError('refusing to overwrite a corpus')
    if args.record_initial_baselines and not args.approval_ref: raise ValueError('explicit initial-baseline approval reference required')
    records=cases()
    write_json(args.output/'corpus.json',{'schema_version':'bie.comp-qa-corpus.v1','cases':records,'accepted':False})
    for c in records:
        bundle=compile_scene_for_qa(c['document'])
        if args.record_initial_baselines:
            baseline=record_generated_baseline(baseline_id='qa009-initial-'+c['case_id'],fixture_id=c['case_id'],
                approval_ref=args.approval_ref,files=bundle.codegen.files,context=bundle.context)
            write_json(args.output/'baselines'/(c['case_id']+'.json'),asdict(baseline))
    print(json.dumps({'fixtures_created':len(records),'initial_baselines_recorded':args.record_initial_baselines,'accepted':False}))
if __name__=='__main__': main()
