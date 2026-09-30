"""H3-007: canonical source/recipe/artifact custody and scoped worker attestations.

A matching unsigned manifest is NOT execution authentication. A signature proves
an authorized configured key made an assertion, not that its host is trustworthy.
Real source extraction, isolation and educational acceptance remain separate gates.
"""
from __future__ import annotations
from pathlib import Path
from ..models import BenchmarkError,digest,digest_string,exact_fields,ident
from ..av.native import map_render_receipt,verify_contract_bytes,COMMIT as CANONICAL_COMMIT
from ..av.service import verify_receipt
from ..release.auth import verify
from .custody import open_root,capture,read_confined_json
from .contracts import relative_path,snapshot

MAX_FILES=10000
MAX_TOTAL_BYTES=8*1024**3
RECIPE_FIELDS={'schema_version','scene_fingerprint','input_sha256','composition','plan','codec',
 'pixel_format','crf','concurrency','frame_timeout_ms','require_audio','props_file','tool_versions',
 'cli_sha256','node_sha256','ffprobe_sha256','browser_launcher_sha256','recipe_sha256'}

def verify_manifest(root,relative,*,expected_binding_sha256,expected_manifest_sha256=None):
    value,rawsha,size=read_confined_json(root,relative)
    exact_fields(value,{'schema_version','binding_sha256','artifacts','manifest_sha256','accepted'})
    if value['schema_version']!='bie.artifacts.v1' or value['accepted'] is not False:
        raise BenchmarkError('NATIVE_MANIFEST_SCHEMA')
    if digest_string(value['binding_sha256'])!=digest_string(expected_binding_sha256):
        raise BenchmarkError('NATIVE_MANIFEST_BINDING')
    body={k:v for k,v in value.items() if k!='manifest_sha256'}
    if digest(body)!=digest_string(value['manifest_sha256']):raise BenchmarkError('NATIVE_MANIFEST_HASH')
    if expected_manifest_sha256 is not None and value['manifest_sha256']!=digest_string(expected_manifest_sha256):
        raise BenchmarkError('NATIVE_MANIFEST_PIN_MISMATCH')
    rows=value['artifacts']
    if type(rows) is not list or not 1<=len(rows)<=MAX_FILES:raise BenchmarkError('NATIVE_MANIFEST_SIZE')
    names=[];total=0
    for row in rows:
        exact_fields(row,{'path','size_bytes','sha256'});names.append(relative_path(row['path']))
        if type(row['size_bytes']) is not int or row['size_bytes']<0:raise BenchmarkError('NATIVE_MANIFEST_SIZE')
        total+=row['size_bytes'];digest_string(row['sha256'])
    if total>MAX_TOTAL_BYTES:raise BenchmarkError('NATIVE_MANIFEST_BUDGET')
    if names!=sorted(set(names)) or relative in names:raise BenchmarkError('NATIVE_MANIFEST_PATHS')
    with open_root(root) as fd:
        checked=[capture(fd,row,maximum=MAX_TOTAL_BYTES,allow_empty=True) for row in rows]
    return value,{'path':relative,'sha256':rawsha,'size_bytes':size,'files_checked':len(checked),
                  'verified_inventory_sha256':digest(checked)}

def inspect(root,receipt_path,av_receipt,*,expectation,expected_expectation_sha256,contract_path):
    """Verify actual files against the pinned canonical v1 producer format.

    All input policy values are provided by the evaluator, not the candidate.
    This function does not invoke or simulate Remotion.
    """
    e=snapshot(expectation)
    exact_fields(e,{'schema_version','commit','run_id','composition_id','scene_sha256','input_sha256',
       'recipe_sha256','artifact_manifest_sha256','required_source_paths'})
    if digest(e)!=digest_string(expected_expectation_sha256):raise BenchmarkError('NATIVE_EXPECTATION_PIN')
    if e['schema_version']!='native-lineage-policy-3' or e['commit']!=CANONICAL_COMMIT:
        raise BenchmarkError('NATIVE_CONTRACT_DRIFT')
    for k in ('scene_sha256','input_sha256','recipe_sha256','artifact_manifest_sha256'):digest_string(e[k])
    ident(e['run_id']);ident(e['composition_id'])
    required=e['required_source_paths']
    if type(required) is not list or not required or len(required)>MAX_FILES:raise BenchmarkError('NATIVE_SOURCE_ROSTER')
    required=[relative_path(x) for x in required]
    if len(required)!=len(set(required)):raise BenchmarkError('NATIVE_SOURCE_ROSTER')
    receipt,receipt_sha,receipt_size=read_confined_json(root,receipt_path)
    mapped=map_render_receipt(receipt,av_receipt,expected_commit=e['commit'],expected_run_id=e['run_id'],
      expected_input_sha256=e['input_sha256'],expected_recipe_sha256=e['recipe_sha256'],
      expected_composition_id=e['composition_id'],contract_path=contract_path)
    base=relative_path(receipt['evidence_directory'])
    if base!='render-evidence/'+e['run_id'] or receipt_path!=base+'/RENDER_RECEIPT.json':
        raise BenchmarkError('NATIVE_RECEIPT_PATH_MISMATCH')
    recipe,recipe_rawsha,recipe_size=read_confined_json(root,base+'/recipe.json')
    exact_fields(recipe,RECIPE_FIELDS)
    if recipe['schema_version']!='bie.render-recipe.v1':raise BenchmarkError('NATIVE_RECIPE_SCHEMA')
    if digest({k:v for k,v in recipe.items() if k!='recipe_sha256'})!=e['recipe_sha256'] or recipe['recipe_sha256']!=e['recipe_sha256']:
        raise BenchmarkError('NATIVE_RECIPE_HASH')
    if recipe['scene_fingerprint']!=e['scene_sha256'] or recipe['input_sha256']!=e['input_sha256']:
        raise BenchmarkError('NATIVE_RECIPE_SOURCE_MISMATCH')
    plan=recipe['plan'];composition=recipe['composition']
    if type(plan) is not dict or set(plan)!={'mode','first_frame','last_frame','expected_frames'} or type(composition) is not dict:
        raise BenchmarkError('NATIVE_RECIPE_PLAN')
    if any(type(plan[k]) is not int for k in ('first_frame','last_frame','expected_frames')):
        raise BenchmarkError('NATIVE_RECIPE_PLAN')
    for k in ('width','height','duration_in_frames'):
        if type(composition.get(k)) is not int:raise BenchmarkError('NATIVE_RECIPE_COMPOSITION')
    import math
    if type(composition.get('fps')) not in (int,float) or not math.isfinite(composition['fps']):raise BenchmarkError('NATIVE_RECIPE_COMPOSITION')
    if (composition['width'],composition['height'],composition['duration_in_frames'])!=(receipt['media']['width'],receipt['media']['height'],receipt['expected_frames']) or abs(composition['fps']-receipt['media']['fps'])>1e-6:
        raise BenchmarkError('NATIVE_RECIPE_COMPOSITION')
    for k in ('cli_sha256','node_sha256','ffprobe_sha256','browser_launcher_sha256'):digest_string(recipe[k])
    if (plan.get('mode')!='full' or plan.get('first_frame')!=0 or plan.get('expected_frames')!=receipt['expected_frames']
        or plan.get('last_frame')!=receipt['expected_frames']-1 or composition.get('composition_id')!=e['composition_id']):
        raise BenchmarkError('NATIVE_RECIPE_PLAN')
    if recipe['codec']!='h264' or recipe['pixel_format']!='yuv420p' or type(recipe['require_audio']) is not bool:
        raise BenchmarkError('NATIVE_RECIPE_MEDIA_PROFILE')
    if recipe['require_audio'] and not av_receipt['observations']['audio']:raise BenchmarkError('NATIVE_RECIPE_AUDIO_MISSING')
    source,source_check=verify_manifest(root,base+'/input-manifest.json',
         expected_binding_sha256=e['scene_sha256'],expected_manifest_sha256=e['input_sha256'])
    source_paths={x['path'] for x in source['artifacts']}
    if not set(required)<=source_paths:raise BenchmarkError('NATIVE_SOURCE_COVERAGE_MISSING')
    seal,seal_check=verify_manifest(root,base+'/ARTIFACT_MANIFEST.json',expected_binding_sha256=e['recipe_sha256'],
                                   expected_manifest_sha256=e['artifact_manifest_sha256'])
    bypath={x['path']:x for x in seal['artifacts']}
    must={receipt_path,base+'/recipe.json',base+'/input-manifest.json',receipt['output_path'],
          base+'/render-process.json',base+'/probe-process.json',base+'/toolchain.json',base+'/source-qa.json',
          base+'/full-typecheck.json',base+'/actual-paint-witness.json',base+'/installed-toolchain.json',base+'/isolation.json'}
    if not must<=set(bypath):raise BenchmarkError('NATIVE_SEAL_COVERAGE_MISSING')
    for name,h,n in ((receipt_path,receipt_sha,receipt_size),(base+'/recipe.json',recipe_rawsha,recipe_size),
                     (base+'/input-manifest.json',source_check['sha256'],source_check['size_bytes'])):
        if bypath[name]!={'path':name,'sha256':h,'size_bytes':n}:raise BenchmarkError('NATIVE_JSON_CHANGED')
    output=bypath[receipt['output_path']]
    if output['sha256']!=receipt['artifact_sha256'] or output['size_bytes']!=receipt['artifact_size_bytes']:
        raise BenchmarkError('NATIVE_OUTPUT_SEAL_MISMATCH')
    # Recheck source bytes after seal reads, avoiding a stale source custody report.
    verify_manifest(root,base+'/input-manifest.json',expected_binding_sha256=e['scene_sha256'],expected_manifest_sha256=e['input_sha256'])
    # Process/witness files are required and hash-bound; they are not by themselves trusted assertions.
    result={'schema_version':'native-lineage-result-3','status':'CUSTODY_VERIFIED_UNSIGNED',
       'expectation_sha256':digest(e),'av_receipt_sha256':av_receipt['receipt_sha256'],
       'media_sha256':output['sha256'],'receipt_sha256':receipt_sha,'source_check':source_check,'seal_check':seal_check,
       'commit':e['commit'],'run_id':e['run_id'],'scene_sha256':e['scene_sha256'],
       'input_sha256':e['input_sha256'],'recipe_sha256':e['recipe_sha256'],
       'declaration_mapping':mapped,'native_execution_verified':False,'worker_authorized':False,
       'release_authorized':False,'product_accepted':False}
    result['lineage_sha256']=digest(result);return result

def authorize(lineage,token,trust,*,now,production=True):
    r=snapshot(lineage)
    if digest({k:v for k,v in r.items() if k!='lineage_sha256'})!=r.get('lineage_sha256'):
        raise BenchmarkError('NATIVE_LINEAGE_INTEGRITY')
    if r.get('status')!='CUSTODY_VERIFIED_UNSIGNED' or any(r.get(k) is not False for k in
       ('native_execution_verified','worker_authorized','release_authorized','product_accepted')):
        raise BenchmarkError('NATIVE_LINEAGE_PROMOTION')
    p=verify(token,trust,kind='NATIVE_AV_COLLECTION',scope_sha256=r['lineage_sha256'],now=now,production=production)
    exact_fields(p['claims'],{'execution_kind','lineage_sha256'})
    if p['claims']!={'execution_kind':'LOCAL_REMOTION_CLI','lineage_sha256':r['lineage_sha256']}:
        raise BenchmarkError('NATIVE_WORKER_CLAIMS_MISMATCH')
    return {'status':'AUTHORIZED_WORKER_ASSERTION','lineage_sha256':r['lineage_sha256'],
        'attestation_sha256':digest(token),'subject_id':p['subject_id'],'key_id':p['key_id'],
        'production_key_policy':production,'native_execution_verified':False,
        'release_authorized':False,'product_accepted':False}
