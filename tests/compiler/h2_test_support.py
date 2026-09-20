"""H2 fixtures; synthetic content and explicit hook/runtime doubles only."""
from copy import deepcopy
from pathlib import Path
import json, subprocess, tempfile
from tests.compiler.h1_test_support import element, scene as inherited_scene, nodes, text_nodes, ROOT
from bie.compiler.simulation_models import MODELS


def sim_props(kind='acceleration'):
    if kind == 'acceleration':
        ref='bie.sim.constant-acceleration-2d@1';state={'x':0,'y':0,'vx':2,'vy':4};params={'ax':0,'ay':-2};view={'x_min':-1,'x_max':5,'y_min':-1,'y_max':5}
    elif kind == 'oscillator':
        ref='bie.sim.harmonic-oscillator-1d@1';state={'x':1,'v':0};params={'omega':3.141592653589793};view={'x_min':0,'x_max':2,'y_min':-1.1,'y_max':1.1}
    else:
        ref='bie.sim.exponential-decay@1';state={'n':10};params={'rate':.5};view={'x_min':0,'x_max':2,'y_min':0,'y_max':11}
    return {'model_ref':ref,'execution_class':'analytic_model','initial_state':state,'parameters':params,'units':deepcopy(MODELS[ref]['units']),'start_ms':0,'duration_ms':2000,'view':view,'title':'Synthetic '+kind+' model'}


def geo_props(kind='web_mercator'):
    return {'crs':'EPSG:4326','projection':{'kind':kind,'axis_order':'lon_lat','extent':[-10,20,10,60]},'layers':[{'kind':'route','points':[[-8,25],[0,40],[8,55]],'label':'Synthetic route'}],'attribution':'Synthetic coordinates; no external map data.','title':'Projection technical fixture'}


def track(action='enter',params=None,**updates):
    t={'track_id':'h2-track','element_id':'e0','action':action,'start_ms':0,'end_ms':1000,'parameters':params or {},'source_refs':['fixture:h2'],'reasoning_refs':['reasoning:h2']}
    t.update(updates);return t


def runtime(result, frames=(0,), fps=24, calls=(), props=None):
    name=getattr(result,'component_name',Path(result.source_path).stem)
    req={'source':result.source_text,'component':name,'frames':list(frames),'fps':fps,'calls':list(calls)}
    if props is not None:req['props']=props
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'request.json';p.write_text(json.dumps(req,allow_nan=False))
        r=subprocess.run(['node',str(ROOT/'tests/compiler/h2_jsx_test_runtime.cjs'),str(p)],capture_output=True,text=True,timeout=20)
        if r.returncode:raise AssertionError(r.stderr)
        out=json.loads(r.stdout)
        assert out['execution_kind']=='REAL_TS_EXECUTION_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES'
        return out


def scene(kind, props, **kw):
    if kind == 'simulation' and 'case_id' not in kw:
        kw['case_id'] = 'reject-state-only-simulation'
    return inherited_scene(kind, props, **kw)
