"""Credential-free, private root-owned native candidate gate; not integration."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--project',type=Path,required=True);args=parser.parse_args()
    assert sys.platform=='linux' and os.getuid()==0 and not args.output.exists()
    assert args.project.is_dir() and not args.project.is_symlink()
    args.output.mkdir(parents=True,mode=0o755)
    result=dict(schema='bie.section18.chromium-production-validation/1',lanes=[],source=[],
        candidate_not_integrated=True,synthetic_test=True,real_book_acceptance=False,product_accepted=False,task028='PAUSED')
    try:
        with tempfile.TemporaryDirectory(prefix='bie-s18-owned-native-') as tmp:
            private=Path(tmp);source=private/'source';source.mkdir()
            names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0');total=0
            for raw in names:
                if not raw:continue
                name=raw.decode();rel=Path(name)
                if (rel.parts[0] not in ('bie','apps','tests','tools','docs','task_registry') or
                    rel.suffix.lower() not in ('.py','.json','.js','.cjs','.ts','.tsx','.html','.css','.md','.txt')):continue
                path=ROOT/rel
                assert path.is_file() and not path.is_symlink() and path.stat().st_size<=16*1024**2
                total+=path.stat().st_size;assert total<=256*1024**2 and len(result['source'])<15000
                target=source/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
                digest=sha(path);assert sha(target)==digest
                result['source'].append(dict(path=name,sha256=digest))
            project=private/'project';shutil.copytree(args.project,project,symlinks=True)
            env={'PATH':'/opt/nvm/versions/node/v22.16.0/bin:/opt/pyvenv/bin:/usr/local/bin:/usr/bin:/bin',
                 'LANG':'C.UTF-8','HOME':str(private),'PYTHONDONTWRITEBYTECODE':'1',
                 'BIE_SECTION18_RENDER_PROJECT':str(project),
                 'BIE_SECTION18_RENDER_BROWSER':'/usr/local/lib/bie-section18-chromium/chrome',
                 'BIE_SECTION18_WASM_EVIDENCE':str(args.output/'wasm-command-receipts')}
            lanes=[('resource-controls',['tools/run_section18_chromium_controls.py','--native']),
                   ('wasm-bounds',['tools/run_section18_posix_validation.py','--scope','wasm-bounds']),
                   ('bundle-cache',['tools/run_section18_posix_validation.py','--scope','bundle-cache']),
                   ('render',['tools/run_section18_posix_validation.py','--scope','render'])]
            for name,command in lanes:
                out=args.output/name;argv=[sys.executable,'-I','-B',str(source/command[0]),*command[1:],'--output',str(out)]
                started=time.monotonic()
                completed=subprocess.run(argv,cwd=source,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600)
                assert len(completed.stdout)+len(completed.stderr)<=2*1024**2
                (args.output/(name+'.stdout.log')).write_bytes(completed.stdout)
                (args.output/(name+'.stderr.log')).write_bytes(completed.stderr)
                result['lanes'].append(dict(name=name,argv=argv,exit_code=completed.returncode,
                    duration_s=round(time.monotonic()-started,3),passed=completed.returncode==0))
                (args.output/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
                if name=='resource-controls' and completed.returncode!=0:break
            for name in ('actual-paint/CHROMIUM_RESOURCE.json','actual-paint/PROCESS.json','actual-paint-witness.json',
                         'CHROMIUM_RESOURCE.json','isolation.json','RENDER_RECEIPT.json','recipe.json'):
                path=project/'render-evidence/operator18-native-preview'/name
                if path.is_file():
                    target=args.output/'producer'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
            result['source_bytes_unchanged']=all(sha(source/r['path'])==r['sha256'] for r in result['source'])
            result['original_checkout_permissions_changed']=False;assert result['source_bytes_unchanged']
    except BaseException as error:
        result.update(failure_type=type(error).__name__,failure=str(error)[:16384]);raise
    finally:
        result['passed']=len(result['lanes'])==4 and all(l['passed'] for l in result['lanes']) and not result.get('failure_type')
        (args.output/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(passed=result['passed'],lanes=[{k:v for k,v in l.items() if k!='argv'} for l in result['lanes']])))
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
