#!/usr/bin/env python3
"""Whole-scene Chromium DOM evidence over generated code with explicit API doubles.

All integer frames are measured; only selected screenshots are saved. This is
not a real React/Remotion renderer or a browser/OS security sandbox.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
from dataclasses import asdict,replace
from copy import deepcopy
import argparse,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT)]
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.content_fit_qa import inspect_content_fit,BRIDGE_SCOPE
from bie.compiler.frame_layout import iter_frame_layers
from bie.compiler.qa_common import digest
from bie.compiler.deterministic_codegen import write_codegen_plan
from tests.compiler.h3_test_support import scene,move,variant,sim_props,geo_props,TARGET

HOST_BRIDGE=r'''tree => {
 const svgNS='http://www.w3.org/2000/svg',mathNS='http://www.w3.org/1998/Math/MathML';
 const attrs={className:'class',strokeWidth:'stroke-width',strokeDasharray:'stroke-dasharray',fillOpacity:'fill-opacity',fontSize:'font-size',fillRule:'fill-rule',clipPath:'clip-path',strokeLinejoin:'stroke-linejoin',strokeLinecap:'stroke-linecap'};
 const unitless=new Set(['opacity','scale','flex','flexGrow','flexShrink','order','zIndex','fontWeight','lineHeight']);
 function node(n,ns=null){
  if(n===null||n===undefined||n===false)return document.createTextNode('');
  if(typeof n==='string'||typeof n==='number')return document.createTextNode(String(n));
  ns=n.tag==='svg'?svgNS:n.tag==='math'?mathNS:ns;
  const e=ns?document.createElementNS(ns,n.tag):document.createElement(n.tag);
  for(const [k,v] of Object.entries(n.props||{})){
   if(['key','children'].includes(k)||v===null||v===undefined)continue;
   if(k==='style'){for(const [sk,sv] of Object.entries(v))e.style[sk]=(typeof sv==='number'&&!unitless.has(sk))?sv+'px':String(sv);}
   else e.setAttribute(attrs[k]||k,String(v));
  }
  for(const c of n.children||[])e.append(node(c,ns));return e;
 }
 document.getElementById('root').replaceChildren(node(tree));
}'''

MEASURE=r'''options => {
 const rect=e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height]};
 const visible=e=>{for(let n=e;n&&n.nodeType===1;n=n.parentElement){const c=getComputedStyle(n);if(Number(c.opacity)===0||c.display==='none'||c.visibility==='hidden')return false;}return true;};
 const rows=[];
 for(const layer of document.querySelectorAll('[data-bie-layer-id]')){
  const id=layer.getAttribute('data-bie-layer-id'),tracks=Array.from(layer.querySelectorAll('[data-bie-track-id]'));
  const owner=tracks.length?tracks[tracks.length-1]:layer;
  const ink=[],texts=[];let overflow=false;
  const descendants=Array.from(layer.querySelectorAll('*'));if(owner===layer)descendants.unshift(layer);
  for(const el of descendants){
   if(el.closest('defs,title,desc')||!visible(el))continue;
   if((el===owner||!el.hasAttribute('data-bie-track-id'))&&el.namespaceURI!=='http://www.w3.org/2000/svg'&&el.clientWidth>0&&el.clientHeight>0&&(el.scrollWidth>el.clientWidth+1||el.scrollHeight>el.clientHeight+1))overflow=true;
   if(el.matches('svg use,svg path,svg polyline,svg polygon,svg circle,svg rect')){const b=rect(el);if(b[2]>0&&b[3]>0)ink.push(b);}
  }
  const walker=document.createTreeWalker(layer,NodeFilter.SHOW_TEXT);let text;
  while(text=walker.nextNode()){
   if(!text.textContent.trim())continue;const e=text.parentElement;
   if(!e||e.closest('defs,title,desc')||!visible(e))continue;
   const range=document.createRange();range.selectNodeContents(text);
   let size=parseFloat(getComputedStyle(e).fontSize);
   if(e.namespaceURI==='http://www.w3.org/2000/svg'&&e.getScreenCTM){const m=e.getScreenCTM();size*=Math.hypot(m.a,m.b);}
   else {let factor=1;for(let n=e;n&&n!==layer.parentElement;n=n.parentElement){const s=getComputedStyle(n).scale;if(s!=='none'){const vals=s.split(' ').map(Number);factor*=Math.min(...vals);}}size*=factor;}
   for(const r of range.getClientRects()){if(r.width>0&&r.height>0){const b=[r.x,r.y,r.width,r.height];texts.push({box:b,font_px:size});ink.push(b);}}
  }
  let em=null;const math=layer.querySelector('[role="math"]'),svg=math&&math.querySelector('svg'),native=math&&math.querySelector('math');
  if(svg){const m=svg.getScreenCTM();em=(options.equationFonts[id]||32)*Math.hypot(m.a,m.b);}
  else if(native)em=parseFloat(getComputedStyle(native).fontSize);
  rows.push({element_id:id,frame:options.frame,visible:visible(owner),layer_box:rect(owner),ink_boxes:ink,text_boxes:texts,scroll_overflow:overflow,equation_em_px:em});
 }
 return rows;
}'''

def cases():
    out=[]
    def add(name,p,expected=True,codes=(),target=TARGET,preference='standard'):
        out.append(dict(case_id=name,document=p,target=target,preference=preference,expected_fit=expected,expected_codes=list(codes)))
    add('safe-text',scene())
    p=scene();p['elements'][0]['normalized_box']={'x':.3,'y':.3,'width':.22,'height':.25};p['elements'][0]['props']['text']='Rotating text'
    add('safe-rotation',move(p,{'from':{'rotate':0},'to':{'rotate':90}}))
    add('standard-translation',variant(move()))
    add('reduced-opacity',variant(move()),preference='reduced')
    eq=scene('equation',{'expression':r'\frac{x^2+1}{\sqrt{y}}','format':'latex'});eq['elements'][0]['normalized_box']={'x':.1,'y':.2,'width':.8,'height':.4};add('safe-equation',eq)
    tiny=deepcopy(eq);tiny['elements'][0]['normalized_box']['height']=.018;add('tiny-equation-rejected',tiny,False,['LAYOUT_EQUATION_BELOW_MINIMUM'])
    dense=scene('text',{'text':'Deliberately overfull technical label '*45});dense['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.2,'height':.07};add('dense-text-rejected',dense,False,['LAYOUT_CONTENT_OVERFLOW','LAYOUT_TEXT_OUTSIDE_OWNER'])
    big=replace(TARGET,width=1280,height=720)
    sim=scene('simulation',sim_props(),duration_ms=3000);sim['elements'][0]['normalized_box']={'x':.05,'y':.05,'width':.9,'height':.85};add('analytic-simulation',sim,target=big)
    add('reduced-static-simulation',variant(sim),target=big,preference='reduced')
    mp=scene('map',geo_props());mp['elements'][0]['normalized_box']={'x':.05,'y':.05,'width':.9,'height':.9};mp['elements'][0]['props']['layers']=[deepcopy(mp['elements'][0]['props']['layers'][0]) for _ in range(3)];mp['elements'][0]['props']['layers'][2]['label']='W'*76
    add('long-map-legend-rejected',mp,False,['LAYOUT_TEXT_OUTSIDE_OWNER'],target=big)
    from tests.compiler.test_comp_h3_integration import combined
    from tests.compiler.h3_test_support import track
    add('combined-standard',combined(),target=big)
    add('combined-reduced',combined(),target=big,preference='reduced')
    p=scene();p['elements'][0]['normalized_box']={'x':.25,'y':.3,'width':.3,'height':.3}
    p['tracks']=[track('transform',{'from':{'scale':1},'to':{'scale':1.2}},track_id='scale',element_id='e0',source_refs=['fixture:h3'],reasoning_refs=['reasoning:h3']),track('transform',{'from':{'translate_x':0},'to':{'translate_x':30}},track_id='translate',element_id='e0',source_refs=['fixture:h3'],reasoning_refs=['reasoning:h3'])]
    add('nested-scale-translation',p)
    return out


def run(output,chromium):
    if output.exists():raise ValueError('output must be new; evidence is never overwritten')
    output.mkdir(parents=True);(output/'screenshots').mkdir();records=[];failures=[]
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        browser_version=browser.version
        for case in cases():
            r=compile_h3_scene(case['document'],target=case['target'],motion_preference=case['preference'])
            if not r.receipt.source_gate_passed:raise ValueError(case['case_id']+': unexpected source rejection '+str(r.receipt.findings))
            n=r.layout['frames_expected'];target=case['target'];cid=case['case_id']
            req={'files':{f.path:f.content for f in r.codegen.files},'frames':list(range(n)),
                 'fps':target.fps,'width':target.width,'height':target.height}
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'request.json';path.write_text(json.dumps(req))
                child=subprocess.run(['node',str(ROOT/'tests/compiler/h3_scene_test_runtime.cjs'),str(path)],capture_output=True,text=True,timeout=45)
            if child.returncode:raise ValueError('test bridge failed: '+child.stderr[:3000])
            tree_data=json.loads(child.stdout)
            if tree_data['execution_kind']!='REAL_TS_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES':raise ValueError('incorrect execution scope')
            page=browser.new_page(viewport={'width':target.width,'height':target.height},device_scale_factor=1)
            page.route('**/*',lambda route:route.abort())
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.set_content('<!doctype html><html><head><style>html,body{margin:0;background:white;color:black;font:16px sans-serif;}#root{width:100vw;height:100vh;}</style></head><body><div id="root"></div></body></html>')
            equationFonts={e['element_id']:e['props'].get('font_size',32) for e in r.effective_document['elements'] if e['element_type']=='equation'}
            observations=[];shots=[];max_delta=0.
            predicted=list(iter_frame_layers(r.effective_document,target))
            for item in tree_data['trees']:
                f=item['frame'];page.evaluate(HOST_BRIDGE,item['tree']);page.evaluate('document.fonts.ready')
                measured=page.evaluate(MEASURE,{'frame':f,'equationFonts':equationFonts});observations.extend(measured)
                for obs in measured:
                    expected=next(v for v in predicted[f] if v['element_id']==obs['element_id'])['bounds_ltrb']
                    x,y,w,h=obs['layer_box'];actual=[x,y,x+w,y+h]
                    max_delta=max(max_delta,max(abs(a-b) for a,b in zip(actual,expected)))
                if f in {0,n//2,n-1}:
                    rel='screenshots/'+cid+'-f'+str(f)+'.png';p=output/rel;page.screenshot(path=str(p),animations='disabled');shots.append({'frame':f,'path':rel,'sha256':sha256(p.read_bytes()).hexdigest()})
            report={'scope':BRIDGE_SCOPE,'scene_identity':digest(r.effective_document),'manifest_sha256':r.codegen.manifest_sha256,
                    'width':target.width,'height':target.height,'fps':target.fps,'frame_count':n,'browser_errors':errors,
                    'fonts_ready':page.evaluate('document.fonts.status')=='loaded','records':observations,
                    'harness_css':'explicit technical body: margin 0, font 16px sans-serif; not a Remotion font acceptance claim'}
            fit=inspect_content_fit(report,r.effective_document,target,r.codegen.manifest_sha256)
            codes={f['code'] for f in fit['findings']}
            matched=fit['passed']==case['expected_fit'] and set(case['expected_codes'])<=codes and not errors
            # Independent browser oracle for supported nested wrapper box transforms.
            geometry_matched=max_delta<.15
            if not matched:failures.append(cid+':unexpected content-fit outcome '+','.join(sorted(codes)))
            if not geometry_matched:failures.append(cid+':layer-box oracle mismatch '+str(max_delta))
            case_dir=output/cid;case_dir.mkdir();write_codegen_plan(r.codegen,case_dir/'generated')
            (case_dir/'observations.json').write_text(json.dumps(report,indent=2)+'\n')
            (case_dir/'fit.json').write_text(json.dumps(fit,indent=2)+'\n')
            records.append({'case_id':cid,'expected_fit':case['expected_fit'],'expected_codes':case['expected_codes'],
                            'source_receipt':asdict(r.receipt),'fit':fit,'expectation_matched':matched,
                            'frame_count':n,'observations':len(observations),'max_box_oracle_delta_px':max_delta,
                            'geometry_oracle_matched':geometry_matched,'screenshots':shots,
                            'host_identity':r.host['identity_sha256'],'typescript_version':tree_data['typescript_version'],'accepted':False})
            page.close()
        browser.close()
    receipt={'schema_version':'bie.h3-browser-evidence.v1','scope':BRIDGE_SCOPE,'chromium_version':browser_version,
             'case_count':len(records),'cases':records,'measured_frame_count':sum(r['frame_count'] for r in records),
             'saved_screenshot_count':sum(len(r['screenshots']) for r in records),'failures':failures,
             'passed':not failures,'real_react':False,'actual_remotion':False,'sandbox_disabled_for_local_fixture_browser':True,
             'evidence_harness_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
             'explicit_runtime_double_sha256':sha256((ROOT/'tests/compiler/h3_scene_test_runtime.cjs').read_bytes()).hexdigest(),
             'content_fit_negative_cases_are_expected_rejections':True,'real_book_e2e':'NOT_RUN','accepted':False}
    (output/'BROWSER_EVIDENCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--chromium',default='/usr/bin/chromium');a=p.parse_args()
    r=run(a.output,a.chromium);print(json.dumps({k:v for k,v in r.items() if k!='cases'},indent=2));return 0 if r['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
