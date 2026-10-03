"""Explicit H1-008 lane; no inflation of original atomic test counts."""
from pathlib import Path
import argparse,hashlib,importlib.util,io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--native',action='store_true');args=parser.parse_args()
    if args.output.exists():raise SystemExit('fresh evidence directory required')
    cases=[];modules=[]
    names=[('test_chromium_resource_boundary','ChromiumResourceAdmission')]
    if args.native:names.append(('test_native_chromium_resource_boundary','NativeChromiumResources'))
    for name,klass in names:
        path=ROOT/'tests/section18'/(name+'.py');spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        modules.append(module);cases.extend(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module,klass)))
    ids=[case.id() for case in cases];assert len(ids)==len(set(ids))==(37 if args.native else 30)
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(cases))
    receipt=dict(schema='bie.section18.chromium-controls/1',tests_run=result.testsRun,unique_method_ids=ids,
        failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),
        passed=result.wasSuccessful() and not result.skipped,native_execution=args.native,
        native_controls=modules[-1].NativeChromiumResources.records if args.native else [],
        origins={str(Path(m.__file__).relative_to(ROOT)):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules},
        synthetic_test=True,product_accepted=False,task028='PAUSED')
    args.output.mkdir(parents=True)
    (args.output/'TEST_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (args.output/'TEST_RESULT.txt').write_text(stream.getvalue(),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('unique_method_ids','native_controls','origins')}))
    return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
