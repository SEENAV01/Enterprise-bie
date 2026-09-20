#!/usr/bin/env python3
"""Synthetic H5 dynamic-consumer evidence. Real Chromium, explicit API doubles.

No production render authorization, no textbook correctness or equation proof.
Measures every frame separately from an exhaustive DOM-semantic evaluation pass.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import argparse, json, math, subprocess, sys, tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT)]
from bie.compiler.qa_common import digest
from bie.compiler.qa_scene_compile import CompilerQATarget
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.layout_browser import ChromiumLayoutProbe, SUPPORT
from bie.compiler.layout_measurements import inspect_owner_fit
from bie.compiler.specialized_motion import specialized_contract, camera_state, equation_state, graph_contract, trace_state
from bie.compiler.host_toolchain import file_identity

DOM = r'''() => {
 const data=[];
 for(const e of document.querySelectorAll('[data-bie-action="camera"],[data-bie-action="morph"],[data-bie-action="trace"]')) {
  const action=e.dataset.bieAction, id=e.dataset.bieTrackId, row={action,track_id:id};
  if(action==='camera') { const c=getComputedStyle(e);row.scale=Number(c.scale);row.translate=c.translate==='none'?[0,0]:c.translate.split(' ').map(parseFloat);if(row.translate.length===1)row.translate.push(0); }
  if(action==='morph') {row.states=Array.from(e.querySelectorAll('[data-bie-state-index]')).map(n=>({index:Number(n.dataset.bieStateIndex),expression:n.dataset.bieStateExpression,opacity:Number(getComputedStyle(n).opacity),glyph_paths:n.querySelectorAll('svg path').length}));row.side_conditions=e.querySelector('[aria-label="side conditions"]')?.textContent;}
  if(action==='trace') {const p=e.querySelector('[data-bie-series-id][stroke-dasharray]');const head=e.querySelector('[data-bie-trace-head]');row.dash_offset=Number(p.getAttribute('stroke-dashoffset'));row.dash_style=getComputedStyle(p).strokeDashoffset;row.total_length=p.getTotalLength();const q=p.getPointAtLength((1-row.dash_offset)*row.total_length);row.path_head=[q.x,q.y];row.head=head?[Number(head.getAttribute('cx')),Number(head.getAttribute('cy'))]:null;row.path=p.getAttribute('d');row.series=Array.from(e.querySelectorAll('[data-bie-series-id]')).map(n=>n.dataset.bieSeriesId);row.labels=Array.from(e.querySelectorAll('text')).map(n=>n.textContent);}
  data.push(row);
 } return data;
}'''

def close(a,b,tol=1e-5):
    return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol

def semantic_pass(probe,result,target,output):
    raw=result.effective_document; n=result.layout['frames_expected']
    req={'files':{f.path:f.content for f in result.codegen.files},'frames':list(range(n)),
         'fps':target.fps,'width':target.width,'height':target.height}
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'request.json';p.write_text(json.dumps(req))
        proc=subprocess.run(['node',str(SUPPORT/'layout_bridge.cjs'),str(p)],capture_output=True,text=True,timeout=60)
    if proc.returncode: raise RuntimeError('Bridge failed: '+proc.stderr[:2000])
    payload=json.loads(proc.stdout)
    if payload.get('execution_kind')!='REAL_TS_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES': raise RuntimeError('Scope mismatch')
    if [r['frame'] for r in payload['trees']]!=list(range(n)):raise RuntimeError('Incomplete frame coverage')
    page=probe.browser.new_page(viewport={'width':target.width,'height':target.height},device_scale_factor=1)
    network=[];errors=[]
    page.route('**/*',lambda route:(network.append(route.request.url),route.abort())[-1])
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:white;color:black;font:16px sans-serif}#root{width:100vw;height:100vh}</style></head><body><div id="root"></div></body></html>')
    host=(SUPPORT/'layout_dom_host.js').read_text();records=[];failures=[]
    elements={e['element_id']:e for e in raw['elements']}
    expected={t['track_id']:(specialized_contract(t),elements[t['element_id']]) for t in raw['tracks'] if t['action'] in {'camera','morph','trace'}}
    try:
        for item in payload['trees']:
            frame=item['frame'];page.evaluate(host,item['tree']);page.wait_for_function("document.fonts.status === 'loaded'")
            rows=page.evaluate(DOM)
            if sorted(r['track_id'] for r in rows)!=sorted(expected):failures.append({'frame':frame,'error':'CONSUMER_MISSING_OR_DUPLICATE'})
            for obs in rows:
                if obs['track_id'] not in expected:continue
                c,element=expected[obs['track_id']];checks={}
                if c.action=='camera':
                    ref=camera_state(c,frame,target.fps)
                    checks={'scale':close(obs['scale'],ref['scale'],1e-5),
                            'translation':all(close(a,b,.001) for a,b in zip(obs['translate'],[ref['translate_x'],ref['translate_y']])) and len(obs['translate'])==2}
                elif c.action=='morph':
                    ref=equation_state(c,frame,target.fps)
                    wanted={ref['lower']:ref['lower_opacity']}
                    if ref['upper_opacity']>0 and ref['upper']!=ref['lower']:wanted[ref['upper']]=ref['upper_opacity']
                    checks={'states':sorted(wanted)==sorted(s['index'] for s in obs['states']),
                            'opacity':all(close(s['opacity'],wanted.get(s['index'],-1),1e-5) for s in obs['states']),
                            'actual_glyphs':all(s['glyph_paths']>0 for s in obs['states']),
                            'source_expression':all(s['expression']==c.parameters['states'][s['index']]['expression'] for s in obs['states']),
                            'side_conditions':obs['side_conditions']==', '.join(element['props'].get('side_conditions',[]))}
                else:
                    graph=graph_contract(element);ref=trace_state(c,graph,frame,target.fps)
                    checks={'dash_offset':close(obs['dash_offset'],ref['dash_offset']),
                            'head_visibility':bool(obs['head'])==(ref['progress']>0 and c.parameters['head_marker']),
                            'retained_series':obs['series']==[s['series_id'] for s in graph['series']],
                            'browser_path_length':close(obs['total_length'],next(s for s in graph['series'] if s['series_id']==c.parameters['series_id'])['total_length'],.01),
                            'browser_path_head':all(close(a,b,.01) for a,b in zip(obs['path_head'],ref['head'])),
                            'axis_units':graph['x_label']+' ['+graph['x_unit']+']' in obs['labels'] and graph['y_label']+' ['+graph['y_unit']+']' in obs['labels']}
                    if obs['head']:checks['head_coordinates']=all(close(a,b,1e-6) for a,b in zip(obs['head'],ref['head']))
                record={'frame':frame,'observed':obs,'reference':ref,'checks':checks,'passed':all(checks.values())};records.append(record)
                if not record['passed']:failures.append({'frame':frame,'track_id':obs['track_id'],'checks':checks})
    finally:page.close()
    for t,(c,_) in expected.items():
        if c.action=='trace' and len({r['observed']['path'] for r in records if r['observed']['track_id']==t})!=1:failures.append({'track_id':t,'error':'SOURCE_PATH_CHANGED_DURING_TRACE'})
    out={'scope':'ACTUAL_CHROMIUM_DOM_AND_SVG_GEOMETRY_WITH_EXPLICIT_API_DOUBLES',
         'frames':n,'consumer_frame_records':len(records),'records':records,'failures':failures,
         'browser_errors':errors,'blocked_network_requests':network,
         'passed':not failures and not errors and not network,'real_remotion':False,'accepted':False}
    output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');return out

def run(output,chromium,corpus):
    if output.exists():raise ValueError('New evidence directory required')
    output.mkdir(parents=True);cases=[c for c in json.loads(corpus.read_text())['cases'] if c['expected_source_pass']]
    target=CompilerQATarget(width=1280,height=720,fps=24,compiler_version='1.3.0-comp-h3')
    rows=[]
    with ChromiumLayoutProbe(chromium) as probe:
        version=probe.browser.version
        for c in cases:
            result=compile_h3_scene(c['document'],target=target)
            if not result.receipt.source_gate_passed:raise RuntimeError(c['case_id']+':source failed '+str(result.receipt.findings))
            path=output/c['case_id'];path.mkdir()
            measured=probe.measure(result,target,path/'layout',screenshots=True)
            fit=inspect_owner_fit(measured,result.effective_document,target,result.codegen.manifest_sha256)
            (path/'FIT.json').write_text(json.dumps(fit,indent=2)+'\n')
            semantics=semantic_pass(probe,result,target,path/'SEMANTICS.json')
            row={'case_id':c['case_id'],'source_gate_passed':True,'manifest_sha256':result.codegen.manifest_sha256,
                 'scene_identity':digest(result.effective_document),'layout_frames':measured['frame_count'],
                 'element_frame_records':len(measured['records']),'fit_passed':fit['passed'],'fit_findings':fit['findings'],
                 'expected_fit':c['expected_fit'],'expected_fit_codes':c['expected_fit_codes'],
                 'fit_expectation_matched':fit['passed']==c['expected_fit'] and set(c['expected_fit_codes']) == {f['code'] for f in fit['findings'] if f['severity']=='ERROR'},
                 'semantic_frames':semantics['frames'],'consumer_frame_records':semantics['consumer_frame_records'],
                 'semantics_passed':semantics['passed'],'semantic_failures':semantics['failures'],
                 'screenshots':[{'path':str(Path(c['case_id'])/'layout'/s['path']),**{k:v for k,v in s.items() if k!='path'}} for s in measured['screenshots']]}
            rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in {'screenshots','fit_findings','semantic_failures'}}),flush=True)
    summary={'schema_version':'bie.comp-h5-browser-evidence.v1','scope':'SYNTHETIC_REAL_CHROMIUM_EXPLICIT_REACT_REMOTION_DOUBLES',
             'case_count':len(rows),'cases':rows,'browser_version':version,'browser_executable_sha256':file_identity(chromium),
             'runner_sha256':file_identity(__file__),'corpus_sha256':file_identity(corpus),
             'layout_frames':sum(r['layout_frames'] for r in rows),'element_frame_records':sum(r['element_frame_records'] for r in rows),
             'semantic_pass_frames':sum(r['semantic_frames'] for r in rows),'consumer_frame_records':sum(r['consumer_frame_records'] for r in rows),
             'screenshots':sum(len(r['screenshots']) for r in rows),'all_fit_passed':all(r['fit_passed'] for r in rows),
             'fit_expectations_matched':all(r['fit_expectation_matched'] for r in rows),
             'all_semantics_passed':all(r['semantics_passed'] for r in rows),'os_sandbox_enabled':False,
             'real_react':False,'real_remotion':False,'mathematical_equivalence_verified':False,'real_book':False,'accepted':False}
    (output/'BROWSER_EVIDENCE.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0 if summary['fit_expectations_matched'] and summary['all_semantics_passed'] else 2

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--chromium',default='/usr/bin/chromium');p.add_argument('--corpus',type=Path,default=ROOT/'fixtures/comp_h5/browser_corpus.json');a=p.parse_args()
    raise SystemExit(run(a.output,a.chromium,a.corpus))
