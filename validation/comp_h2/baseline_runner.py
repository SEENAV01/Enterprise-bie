import subprocess,json,pathlib,time,os
p=pathlib.Path('/mnt/data/h2_work'); out=pathlib.Path('/mnt/data/BIE_COMP_H2_BASELINE.txt')
t=time.monotonic()
with out.open('w') as f:r=subprocess.run(['python','-m','unittest','discover','-s','tests','-v'],cwd=p,env=dict(os.environ,PYTHONPATH='app:.'),stdout=f,stderr=subprocess.STDOUT)
(p/'validation/comp_h2/baseline_run.json').write_text(json.dumps({'exit_code':r.returncode,'seconds':time.monotonic()-t}))
