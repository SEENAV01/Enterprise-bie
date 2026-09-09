"""Required local gate: preservation audit plus all canonical regression tests."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=ROOT / "validation"); args = parser.parse_args()
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    for script, args in [("verify_assembly.py", []), ("audit_canonical.py", ["--output", str(output / "canonical_integrity.json")]), ("test_enterprise.py", ["--output", str(output / "integrated_tests.json")])]:
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT)
        if result.returncode: return result.returncode
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
