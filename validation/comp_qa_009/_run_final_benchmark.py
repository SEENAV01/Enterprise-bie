from pathlib import Path
import subprocess,sys,json,datetime
r=Path(__file__).resolve().parents[2]
log=r/'validation/comp_qa_009/BENCHMARK_RUN.txt'
with log.open('w') as f:
 p=subprocess.run([sys.executable,'scripts/run_compiler_qa.py','--output','validation/comp_qa_009/benchmark_final'],cwd=r,stdout=f,stderr=subprocess.STDOUT)
(r/'validation/comp_qa_009/BENCHMARK_PROCESS_RESULT.json').write_text(json.dumps({'exit_code':p.returncode,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'0=full-compile pass; 1=source expectation failure; 2=source pass but full compile incomplete','accepted':False},indent=2)+'\n')
