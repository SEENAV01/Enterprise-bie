#!/usr/bin/env python3
"""Explicit DEVELOPMENT fixture/golden creation, never run by regression checks.

Changes in expectations are the reviewed contract changes below. This command
asserts source findings match those expectations; it never learns 'PASS' from
whatever the current compiler happens to do. No product/expert approval implied.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT)]
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.generated_code_regression import record_generated_baseline,probe_typescript_sources
from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
from tests.compiler.h2_test_support import scene,sim_props,geo_props,track

CHANGES={
 'reject-untypeset-equation':(True,[], 'Actual pinned Mathtext SVG replaces raw LaTeX text.'),
 'reject-metadata-animation':(True,[], 'Reveal track applies sampled clipPath and reaches its final included frame.'),
 'reject-state-only-simulation':(False,['SIMULATION_MODEL_UNSUPPORTED'], 'Unregistered conceptual model explicitly rejected; no substitute state dump.'),
 'reject-geographic-crs':(False,['MAP_PROJECTION_REQUIRED'], 'Missing declared geographic projection explicitly rejected.'),
}

def inherited(name):
    d=json.loads((ROOT/'fixtures/comp_h1'/name).read_text())
    d['corpus_id']='bie-comp-h2-'+name.removesuffix('.json')
    d['compiler_version']='1.2.0-comp-h2';d['accepted']=False
    for c in d['cases']:
        if c['case_id'] in CHANGES:
            ok,codes,_=CHANGES[c['case_id']];c['expected_source_passed']=ok;c['expected_error_codes']=codes
    return d


def new_case(cid,domain,kind,props,*,duration=3000,tracks=None,errors=()):
    p=scene(kind,props);p.pop('fingerprint',None);p['scene_id']=cid;p['duration_ms']=duration
    p['title']='Synthetic H2 technical compiler fixture';p['source_refs']=['fixture:'+cid];p['reasoning_refs']=['fixture-reasoning:'+cid]
    p['metadata']={'fixture_id':cid,'not_textbook':True,'source_kind':'SYNTHETIC_TECHNICAL_FIXTURE_NOT_TEXTBOOK'}
    e=p['elements'][0];e['source_refs']=['fixture:'+cid+':e0'];e['reasoning_refs']=['fixture-reasoning:'+cid+':e0'];e['normalized_box']={'x':.025,'y':.025,'width':.95,'height':.95}
    if tracks is not None:p['tracks']=tracks
    p=decode_scene_ir(p).to_dict()
    return {'case_id':cid,'domain':domain,'document':p,'expected_source_passed':not errors,'expected_error_codes':list(errors),'max_codegen_ms':5000,'max_source_bytes':700000,'source_kind':'SYNTHETIC_TECHNICAL_FIXTURE_NOT_TEXTBOOK'}


def main():
    dest=ROOT/'fixtures/comp_h2';dest.mkdir(exist_ok=True);(dest/'baselines').mkdir(exist_ok=True)
    base=inherited('corpus.json');extended=inherited('extended_corpus.json');extra=[]
    def add(*args,**kw):extra.append(new_case(*args,**kw))
    add('h2-latex-radical','mathematics','equation',{'format':'latex','expression':r'\frac{x^2}{\sqrt{y}}'})
    add('h2-native-mathml','mathematics','equation',{'format':'mathml','expression':'<math><mfrac><msup><mi>x</mi><mn>2</mn></msup><msqrt><mi>y</mi></msqrt></mfrac></math>'})
    for kind,domain in [('acceleration','physics'),('oscillator','engineering'),('decay','chemistry')]:add('h2-sim-'+kind,domain,'simulation',sim_props(kind))
    for action,params in [('enter',{}),('exit',{}),('emphasize',{}),('transform',{'from':{'translate_x':0,'rotate':0},'to':{'translate_x':100,'rotate':30}}),('path_follow',{'coordinate_space':'pixels','points':[[0,0],[20,0],[20,80]]})]:
        add('h2-motion-'+action,'engineering','text',{'text':'Synthetic '+action+' behavior'},tracks=[track(action,params)])
    for projection in ('web_mercator','equirectangular'):add('h2-map-'+projection,'geography','map',geo_props(projection))
    p=geo_props();p['layers'] += [{'kind':'point','points':[[0,40]],'label':'Synthetic point'},{'kind':'polygon','points':[[-5,30],[5,30],[0,50],[-5,30]],'label':'Synthetic area'}];add('h2-map-mixed','geography','map',p)
    add('h2-unsupported-latex','mathematics','equation',{'format':'latex','expression':r'\notKnown{x}'},errors=['EQUATION_LATEX_UNSUPPORTED'])
    add('h2-unsafe-mathml','mathematics','equation',{'format':'mathml','expression':'<math><script>x</script></math>'},errors=['EQUATION_MATHML_UNSAFE'])
    p=sim_props();p['units']['x']='cm';add('h2-sim-units','physics','simulation',p,errors=['SIMULATION_UNITS_MISMATCH'])
    p=sim_props();p['receipt_ref']='forged:observed';add('h2-sim-observation','physics','simulation',p,errors=['SIMULATION_OBSERVATION_NOT_VERIFIED'])
    p=sim_props();p['view']['y_max']=1;add('h2-sim-clips','physics','simulation',p,errors=['SIMULATION_VIEW_CLIPS_MODEL'])
    p=sim_props('oscillator');p['parameters']['omega']=40;add('h2-sim-alias','physics','simulation',p,errors=['SIMULATION_FRAME_ALIASING'])
    add('h2-sim-end-truncated','physics','simulation',sim_props(),duration=2000,errors=['SIMULATION_FINAL_STATE_NOT_VISIBLE'])
    add('h2-motion-unimplemented','engineering','text',{'text':'Unsupported specialized morph must not become metadata.'},tracks=[track('morph')],errors=['ANIMATION_ACTION_UNSUPPORTED'])
    add('h2-motion-conflict','engineering','text',{'text':'Conflicting persistent opacity owners.'},tracks=[track(),track(track_id='second',start_ms=500,end_ms=1500)],errors=['ANIMATION_PROPERTY_OWNERSHIP_CONFLICT'])
    add('h2-motion-one-sample','engineering','text',{'text':'One sampled frame is not a transition.'},tracks=[track(end_ms=40)],errors=['ANIMATION_FRAME_RANGE_COLLAPSES'])
    p=geo_props();p['projection']['extent']=[-10,20,10,90];add('h2-map-polar','geography','map',p,errors=['MAP_MERCATOR_LATITUDE_LIMIT'])
    p=geo_props();p['projection']['extent']=[-180,-60,180,60];p['layers'][0]['points']=[[179,0],[-179,0]];add('h2-map-dateline','geography','map',p,errors=['MAP_ANTIMERIDIAN_UNSUPPORTED'])
    p=geo_props();p['layers'].append({'kind':'raster','points':[[0,40]]});add('h2-map-external-layer','geography','map',p,errors=['MAP_LAYER_UNSUPPORTED'])
    extended['cases'] += extra
    for label,data in [('corpus.json',base),('extended_corpus.json',extended)]:
        (dest/label).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    rows=[]
    for c in extended['cases']:
        b=compile_scene_for_qa(c['document']);probe=probe_typescript_sources(b.codegen.files)
        codes=sorted({f.code for f in (*b.findings,*probe.findings) if f.severity=='ERROR'})
        assert b.source_contract_passed == c['expected_source_passed'],(c['case_id'],codes)
        assert codes == sorted(c['expected_error_codes']),(c['case_id'],codes,c['expected_error_codes'])
        baseline=record_generated_baseline(baseline_id='comp-h2-'+c['case_id'],fixture_id=c['case_id'],approval_ref='development-contract-review:COMP_H2_BASELINE_REVIEW_NOT_PRODUCT_APPROVAL',files=b.codegen.files,context=b.context)
        (dest/'baselines'/(c['case_id']+'.json')).write_text(json.dumps(asdict(baseline),indent=2)+'\n')
        rows.append({'case_id':c['case_id'],'expected_source_passed':c['expected_source_passed'],'expected_error_codes':codes,'baseline_sha256':baseline.baseline_sha256,'source_manifest_sha256':b.codegen.manifest_sha256})
    (ROOT/'governance/COMP_H2_BASELINE_REVIEW.json').write_text(json.dumps({'kind':'DEVELOPMENT_EXPECTATION_REVIEW_NOT_PRODUCT_OR_EXPERT_APPROVAL','preserved_parent_corpus':'fixtures/comp_h1','source_documents_changed':False,'changes':CHANGES,'new_synthetic_case_ids':[c['case_id'] for c in extra],'reviewed_baselines':rows,'accepted':False},indent=2)+'\n')
    print('Reviewed cases',len(rows),'positive',sum(c['expected_source_passed'] for c in extended['cases']))
if __name__=='__main__':main()
