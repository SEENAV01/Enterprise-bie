#!/usr/bin/env python3
"""Explicit H9 capability-context migration; refuses ANY legacy source-byte change.
Never invoked implicitly by a failed test or compiler. Old fixtures stay immutable.
"""
from pathlib import Path
from dataclasses import asdict
from hashlib import sha256
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT)]
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.generated_code_regression import baseline_from_dict,record_generated_baseline
from bie.compiler.deterministic_output_qa import snapshot_generated

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('OUTPUT_EXISTS_NO_BASELINE_OVERWRITE')
 parent=ROOT/'fixtures/comp_h2';corpus=(parent/'corpus.json').read_bytes();rows=[];prepared={}
 for c in json.loads(corpus)['cases']:
  cid=c['case_id'];old_raw=(parent/'baselines'/(cid+'.json')).read_bytes();old=baseline_from_dict(json.loads(old_raw))
  b=compile_scene_for_qa(c['document']);current=snapshot_generated(b.codegen.files,b.context)
  if old.snapshot.files!=current.files or old.snapshot.files_sha256!=current.files_sha256:raise ValueError('SOURCE_BYTE_CHANGE_REQUIRES_SEPARATE_REVIEW: '+cid)
  fresh=record_generated_baseline(baseline_id='comp-h9-context-'+cid,fixture_id=cid,approval_ref='development-review:H9_CAPABILITY_CONTEXT_ONLY_EXACT_H2_SOURCE_BYTES_NOT_PRODUCT_APPROVAL',files=b.codegen.files,context=b.context)
  prepared[cid]=json.dumps(asdict(fresh),indent=2).encode()
  rows.append({'case_id':cid,'old_baseline_sha256':sha256(old_raw).hexdigest(),'new_baseline_sha256':sha256(prepared[cid]).hexdigest(),'source_files_byte_identical':True,'source_files_sha256':current.files_sha256,'old_context_sha256':old.snapshot.context_sha256,'new_context_sha256':current.context_sha256})
 a.output.mkdir(parents=True);(a.output/'baselines').mkdir()
 (a.output/'corpus.json').write_bytes(corpus)
 for cid,data in prepared.items():(a.output/'baselines'/(cid+'.json')).write_bytes(data)
 (a.output/'CONTEXT_MIGRATION.json').write_text(json.dumps({'schema_version':'bie.h9.explicit-context-migration.v1','reason':'Live capabilities expand from 15 elements/render-only action declarations to 18 elements with bounded registered actions. Adapter identity must change; unchanged code bytes must not be mislabeled as code defects.','source':'fixtures/comp_h2','source_corpus_sha256':sha256(corpus).hexdigest(),'historical_source_golden_files_modified':False,'auto_blessing':False,'cases':rows,'accepted':False},indent=2))
 print('Verified exact legacy generated files for',len(rows),'cases; only contexts re-versioned.')
if __name__=='__main__':main()
