"""Safe unique Task032/affected receipts; inherit every Task031 preservation test."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("task031_runner", ROOT / "tools/run_task031_tests.py")
task031 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task031)
runner = task031.runner
runner.AFFECTED = list(runner.NEW) + list(runner.AFFECTED)
runner.NEW = [
    "tests/productization/pedagogy/test_pedagogy_producer.py",
    "tests/productization/pedagogy/test_pedagogy_recovery.py",
]

# Native Pedagogy includes the original objectives, sequencing, examples,
# assessment/adaptation and every hardening/current integration suite.
for folder in ("tests/pedagogy", "tests/qa_pedagogy16"):
    for path in sorted((ROOT / folder).glob("test*.py")):
        runner.AFFECTED.append(path.relative_to(ROOT).as_posix())

# Exercise the actual consumer codecs and input contracts independently of the
# new producer; these inherited tests do not represent Task032 Director execution.
runner.AFFECTED.extend([
    "tests/director/test_hard_inputs_001.py",
    "tests/director/test_hard_context_001.py",
    "tests/director/test_hard_contracts_001.py",
    "tests/director/test_hard_rich_codecs_001.py",
    "tests/director/test_hard_consumers_001.py",
    "tests/director/test_hard_production_adoption_001.py",
    "tests/director/test_execution_integration.py",
    "tests/director/test_context_integration.py",
    "tests/qa_domain_repair16/test_pedagogy.py",
    "tests/assembly/test_director_integration_003.py",
])
for folder in (
    "tests/productization/pedagogy", "tests/pedagogy", "tests/director",
    "tests/qa_pedagogy16", "tests/qa_domain_repair16", "tests/assembly",
):
    sys.path.insert(0, str(ROOT / folder))

# A module is selected once even if a predecessor runner later adds coverage.
runner.AFFECTED = list(dict.fromkeys(runner.AFFECTED))
assert not set(runner.NEW).intersection(runner.AFFECTED)
assert len(runner.NEW) == len(set(runner.NEW))
assert len(runner.AFFECTED) == len(set(runner.AFFECTED))

if __name__ == "__main__":
    raise SystemExit(runner.main())
