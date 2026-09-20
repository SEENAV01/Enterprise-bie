#!/usr/bin/env python3
"""Real Chromium component paint evidence through an explicit TEST JSX bridge.

This never calls/claims Remotion or real React. TypeScript-emitted component
functions execute in a labelled test runtime, then their host-element trees
are painted by Chromium. No book, expert, learner or product acceptance.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import argparse, json, sys
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT)]
from bie.compiler.equation_compiler import compile_equation_element
from bie.compiler.simulation_compiler import compile_simulation_element
from bie.compiler.map_compiler import compile_map_element
from bie.compiler.animation_track_compiler import compile_animation_track
from tests.compiler.h2_test_support import element, sim_props, geo_props, track, runtime

HOST_BRIDGE=r'''tree => {
  const svgNS='http://www.w3.org/2000/svg', mathNS='http://www.w3.org/1998/Math/MathML';
  const attrs={className:'class',strokeWidth:'stroke-width',strokeDasharray:'stroke-dasharray',fillOpacity:'fill-opacity',fontSize:'font-size',fillRule:'fill-rule',clipPath:'clip-path',strokeLinejoin:'stroke-linejoin',strokeLinecap:'stroke-linecap'};
  function node(n,ns=null) {
    if(n===null||n===undefined||n===false)return document.createTextNode('');
    if(typeof n==='string'||typeof n==='number')return document.createTextNode(String(n));
    ns=n.tag==='svg'?svgNS:n.tag==='math'?mathNS:ns;
    const e=ns?document.createElementNS(ns,n.tag):document.createElement(n.tag);
    for(const [k,v] of Object.entries(n.props||{})){
      if(k==='key'||k==='children'||v===null||v===undefined)continue;
      if(k==='style') { for(const [sk,sv] of Object.entries(v)) e.style[sk]=String(sv); }
      else e.setAttribute(attrs[k]||k, String(v));
    }
    for(const c of n.children||[])e.append(node(c,ns));
    return e;
  }
  document.getElementById('root').replaceChildren(node(tree));
}'''

MEASURE=r'''() => {
 const root=document.getElementById('root');
 const rect=e=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height};};
 const marker=document.querySelector('[data-bie-sim-marker]');
 const frac=document.querySelector('mfrac');
 const first=root.firstElementChild;
 const result={root:rect(root), first:first?rect(first):null, marker:marker?rect(marker):null,
   style:first?{opacity:getComputedStyle(first).opacity,clipPath:getComputedStyle(first).clipPath,translate:getComputedStyle(first).translate,rotate:getComputedStyle(first).rotate}:null,
   fraction:frac?Array.from(frac.children).map(rect):[],
   motionProbe:document.querySelector('[data-motion-probe]')?rect(document.querySelector('[data-motion-probe]')):null,
   labels:Array.from(document.querySelectorAll('svg text')).map(e=>({text:e.textContent,box:rect(e)})),
   svgBox:document.querySelector('svg')?rect(document.querySelector('svg')):null,
   glyphs:Array.from(document.querySelectorAll('svg use')).map(rect),
   routes:Array.from(document.querySelectorAll('polyline[data-layer-id]')).map(e=>e.getAttribute('points'))};
 return result;
}'''

def technical_cases():
    def case(cid,result,frames=(0,),width=1000,height=400,props=None):return dict(case_id=cid,result=result,frames=frames,width=width,height=height,props=props)
    cases=[case('latex-fraction-radical',compile_equation_element(element('equation',{'format':'latex','expression':r'\frac{x^2+1}{\sqrt{y}}'})),width=640,height=220),
           case('native-mathml-fraction',compile_equation_element(element('equation',{'format':'mathml','expression':'<math display="block"><mfrac><msup><mi>x</mi><mn>2</mn></msup><msqrt><mi>y</mi></msqrt></mfrac></math>'})),width=640,height=220)]
    for kind in ('acceleration','oscillator','decay'):
        cases.append(case('simulation-'+kind,compile_simulation_element(element('simulation',sim_props(kind))),frames=(0,24,48)))
    child={'tag':'div','props':{'data-motion-probe':'true','style':{'width':'120px','height':'120px','margin':'60px','backgroundColor':'#17365e','color':'white','display':'grid','placeItems':'center'}},'children':['Frame-driven sample']}
    for action,params in [('enter',{}),('reveal',{}),('transform',{'from':{'translate_x':0,'rotate':0},'to':{'translate_x':150,'rotate':25}}),('path_follow',{'coordinate_space':'pixels','points':[[0,0],[100,0],[100,100]]})]:
        probe=deepcopy(child)
        if action=='reveal':probe['props']['style']['width']='360px'
        if action=='transform':probe['props']['style']['margin']='120px'
        cases.append(case('motion-'+action,compile_animation_track(track(action,params)),frames=(0,12,23),width=600,height=400,props={'children':probe}))
    for kind in ('web_mercator','equirectangular'):
        props=geo_props(kind);props['layers'] += [{'kind':'point','points':[[0,40]],'label':'Point'},{'kind':'polygon','points':[[-5,30],[5,30],[0,50],[-5,30]],'label':'Area'}]
        cases.append(case('map-'+kind,compile_map_element(element('map',props)),height=600))
    return cases


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--chromium',default='/usr/bin/chromium');args=p.parse_args()
    if args.output.exists():p.error('Output must be new; previous evidence is never overwritten.')
    args.output.mkdir(parents=True);(args.output/'screenshots').mkdir()
    from playwright.sync_api import sync_playwright
    from PIL import Image,ImageChops
    records=[];failures=[];browser_errors=[];versions={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        versions['chromium']=browser.version
        for case in technical_cases():
            result=case['result'];evidence=runtime(result,frames=case['frames'],props=case['props']);versions['typescript']=evidence['typescript_version']
            page=browser.new_page(viewport={'width':case['width'],'height':case['height']},device_scale_factor=1)
            page.on('pageerror',lambda e:browser_errors.append(str(e)))
            # Explicit technical harness style, not a generated scene/design claim.
            page.set_content('<!doctype html><html><head><style>html,body{margin:0;background:white;color:#152536;font:16px Arial,sans-serif;}#root{width:100vw;height:100vh;}math{font-size:48px;}</style></head><body><div id="root"></div></body></html>')
            frames=[]
            for item in evidence['trees']:
                page.evaluate(HOST_BRIDGE,item['tree']);page.evaluate('document.fonts.ready')
                measurements=page.evaluate(MEASURE)
                rel=Path('screenshots')/(case['case_id']+'-f'+str(item['frame'])+'.png');dst=args.output/rel
                page.screenshot(path=str(dst),animations='disabled')
                with Image.open(dst) as im:
                    rgb=im.convert('RGB');diff=ImageChops.difference(rgb,Image.new('RGB',rgb.size,'white'));nonwhite=diff.getbbox()
                frames.append({'frame':item['frame'],'screenshot':rel.as_posix(),'sha256':sha256(dst.read_bytes()).hexdigest(),'nonwhite_bbox':nonwhite,'measurements':measurements})
            cid=case['case_id'];checks=[]
            def check(name,ok):
                checks.append({'check':name,'passed':bool(ok)})
                if not ok:failures.append(cid+':'+name)
            check('component_painted_in_real_chromium',len(frames)==len(case['frames']))
            if cid.startswith('simulation-'):
                markers=[f['measurements']['marker'] for f in frames];check('visible_markers_exist',all(m and m['width']>0 for m in markers));check('state_marker_moves',len({(round(m['x'],4),round(m['y'],4)) for m in markers if m})>1);check('frame_pixels_change',len({f['sha256'] for f in frames})==len(frames))
            if cid.startswith('motion-'):
                check('final_frame_paints_content',frames[-1]['nonwhite_bbox'] is not None)
                check('frame_pixels_change',len({f['sha256'] for f in frames})==len(frames))
                bounds=[f['measurements']['motionProbe'] for f in frames]
                check('bounded_fixture_content_within_frame',all(b and b['x']>=0 and b['y']>=0 and b['x']+b['width']<=case['width']+1 and b['y']+b['height']<=case['height']+1 for b in bounds))
                if cid=='motion-enter':check('opacity_reaches_endpoints',frames[0]['measurements']['style']['opacity']=='0' and frames[-1]['measurements']['style']['opacity']=='1')
                if cid=='motion-reveal':check('clip_reaches_full_visibility',frames[-1]['measurements']['style']['clipPath']=='inset(0% 0% 0% 0%)' or frames[-1]['measurements']['style']['clipPath']=='inset(0%)')
            if cid=='latex-fraction-radical':
                glyphs=frames[0]['measurements']['glyphs'];check('actual_svg_glyph_geometry_visible',len(glyphs)>=5 and frames[0]['nonwhite_bbox'] is not None)
                check('glyphs_inside_frame',all(g['x']>=-1 and g['y']>=-1 and g['x']+g['width']<=case['width']+1 and g['y']+g['height']<=case['height']+1 for g in glyphs))
            if cid=='native-mathml-fraction':
                fraction=frames[0]['measurements']['fraction'];check('native_fraction_layout',len(fraction)==2 and fraction[0]['y']+fraction[0]['height']<=fraction[1]['y'])
            if cid.startswith('map-'):
                check('projected_route_painted',len(frames[0]['measurements']['routes'])==1 and frames[0]['nonwhite_bbox'] is not None)
                labels=frames[0]['measurements']['labels'];check('representative_labels_within_frame',all(l['box']['x']>=0 and l['box']['x']+l['box']['width']<=case['width']+1 and l['box']['y']+l['box']['height']<=case['height']+1 for l in labels))
            records.append({'case_id':cid,'source_sha256':result.source_sha256,'bridge_kind':evidence['execution_kind'],'frames':frames,'checks':checks,'accepted':False})
            page.close()
        browser.close()
    maps=[r for r in records if r['case_id'].startswith('map-')]
    projection_effect=maps[0]['frames'][0]['measurements']['routes']!=maps[1]['frames'][0]['measurements']['routes']
    if not projection_effect:failures.append('projection_does_not_change_geometry')
    if browser_errors:failures.extend(browser_errors)
    report={'scope':'REAL_CHROMIUM_COMPONENT_PAINT_WITH_EXPLICIT_TEST_REACT_REMOTION_BRIDGE','versions':versions,'cases':records,'case_count':len(records),'screenshot_count':sum(len(r['frames']) for r in records),'projection_changes_geometry':projection_effect,'browser_errors':browser_errors,'failures':failures,'passed':not failures,'real_react':'NOT_USED_TEST_BRIDGE','actual_remotion_render':'NOT_RUN','full_dependency_typecheck':'NOT_RUN','real_book_e2e':'NOT_RUN','accepted':False}
    (args.output/'BROWSER_COMPONENT_EVIDENCE.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
