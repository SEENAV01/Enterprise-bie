"""H7 synthetic fixtures, not textbook/teaching or real npm dependency evidence."""
from copy import deepcopy
from pathlib import Path
import json
from tests.compiler.h6_test_support import narration_scene,state_scene,write_assets,BIG
from tests.compiler.h5_test_support import equation_scene,trace_scene,camera_scene
from bie.compiler.specialized_motion import graph_contract
from bie.compiler.layout_repair_contracts import default_policy

def reduced(p):
    p=deepcopy(p);t=p['tracks'][0];values=[0,.5,1]
    if t['action']=='trace':
        s=graph_contract(p['elements'][0])['series'][0];a=0.;values=[0.]
        for n in s['lengths']:a+=n;values.append(a/s['total_length'])
        values[-1]=1.
    if t['action']=='camera':t['parameters']['from']['zoom']=.9
    p.setdefault('metadata',{})['compiler_h7']={'reduced_variants':{t['track_id']:{'mode':'discrete-milestones',
        'rationale':'Synthetic source-preserving display milestones','teaching_review_ref':'test:review-assertion-not-acceptance',
        'source_refs':t['source_refs'][:],'reasoning_refs':t['reasoning_refs'][:],
        'milestones':[{'frame':i*(48//len(values)),'progress':v,'observation_ref':'test:observation:'+str(i)} for i,v in enumerate(values)]}}}
    return p

def dynamic_repair_case():
    p,assets=narration_scene();e=p['elements'][0];e['normalized_box']={'x':.1,'y':.1,'width':.15,'height':.12}
    p['events'][0]['payload']['value']='A later state needs more space, while the original narration and every literal character remain unchanged. '*2
    policy=default_policy(p);policy['owners']['e0']['region']={'x':.1,'y':.1,'width':.8,'height':.45}
    return p,assets,policy

def fake_node_tree(root):
    """Byte-inventory fixture only. These are NOT installed genuine packages."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    versions={'remotion':'4.0.506','@remotion/cli':'4.0.506','@remotion/bundler':'4.0.506','@remotion/renderer':'4.0.506',
              'react':'19.0.0','react-dom':'19.0.0','typescript':'5.9.3'}
    pkg={'name':'h7-test-tree','version':'0.0.0','private':True,'dependencies':versions,'bie_test_fixture':True}
    packages={'':{'name':pkg['name'],'version':'0.0.0','dependencies':versions}}
    for name,v in versions.items():
        folder=root/'node_modules'/name;folder.mkdir(parents=True)
        (folder/'package.json').write_text(json.dumps({'name':name,'version':v}))
        (folder/'index.js').write_text('// SYNTHETIC IDENTITY TEST ONLY\n')
        packages['node_modules/'+name]={'version':v,'resolved':'https://registry.npmjs.org/'+name+'/-/fixture.tgz','integrity':'sha512-'+'A'*86+'=='}
    (root/'package.json').write_text(json.dumps(pkg));(root/'package-lock.json').write_text(json.dumps({'name':pkg['name'],'version':'0.0.0','lockfileVersion':3,'packages':packages}))
    return root

def glyph_scene():
    from bie.compiler.glyph_motion import flatten_layout
    from bie.compiler.equation_typesetting import typeset_latex
    p=equation_scene();params=p['tracks'][0]['parameters'];atoms=[flatten_layout(typeset_latex(s['expression'],element_id='fixture')) for s in params['states']]
    pairs=[]
    for a,b in zip(atoms,atoms[1:]):
        used=set();mapping=[]
        for i,g in enumerate(a):
            for j,h in enumerate(b):
                if j not in used and g['shape_sha256']==h['shape_sha256']:mapping.append([i,j]);used.add(j);break
        pairs.append(mapping)
    params.update(mode='glyph-matched-affine',glyph_pairs=pairs)
    return p
