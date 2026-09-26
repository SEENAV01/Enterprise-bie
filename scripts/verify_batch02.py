from pathlib import Path
import json,hashlib,subprocess,sys
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,"-B","-m","unittest","discover","-s","tests","-p","test_*.py"],cwd=root,check=True)
bind=json.loads((root/"evidence/DEPENDENCY_BINDING.json").read_text());assert bind["passed"] and not bind["mismatches"]
sec=json.loads((root/"evidence/SECURITY_SCAN.json").read_text());assert sec["passed"]
print("BATCH02_VERIFY_PASS")
