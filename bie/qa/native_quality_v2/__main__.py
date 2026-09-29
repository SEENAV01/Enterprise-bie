"""Read-only byte/provenance CLI. No OCR, provider call, signing or release action.

Policies and source references are independently supplied by the operator. API
users can explicitly provision an OCRRunner or out-of-band assessor registry.
Existing output paths are never overwritten.
"""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from .common import strict_json,ContractError,ArtifactRef,Binding,canonical_bytes,fields
from .documents import DocumentPolicy,inspect_pdf,verify_document

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('inspect-document','audit-document'))
    for name in ('root','source-ref','binding','policy','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',type=Path)
    a=p.parse_args(argv)
    try:
        if a.output.exists() or a.output.is_symlink():raise ContractError('OUTPUT_EXISTS')
        ref=ArtifactRef(**strict_json(a.source_ref.read_bytes()));binding=Binding(**strict_json(a.binding.read_bytes()));policy=DocumentPolicy(**strict_json(a.policy.read_bytes()))
        if a.command=='audit-document':
            if a.snapshot is None:raise ContractError('SNAPSHOT_REQUIRED')
            snapshot=strict_json(a.snapshot.read_bytes())
        else:snapshot=inspect_pdf(ref,a.root,binding,policy)
        report=verify_document(snapshot,ref,a.root,binding,policy)
        result=dict(snapshot=snapshot,report=report.to_dict())
        with a.output.open('xb') as out:out.write(canonical_bytes(result)+b'\n')
        print(json.dumps(dict(status=report.status,product_accepted=False)))
        return 2 if report.status=='BLOCKED' else 3 if report.status=='REVIEW_REQUIRED' else 0
    except (ContractError,ValueError,TypeError,OSError,KeyError) as e:
        print(json.dumps({'status':'BLOCKED','error_type':type(e).__name__,'code':getattr(e,'code','INPUT_OR_IO_ERROR'),'product_accepted':False}),file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
