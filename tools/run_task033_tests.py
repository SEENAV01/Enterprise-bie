"""One unique authored/affected lane; raw private failures never reach receipts."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("task032_runner", ROOT / "tools/run_task032_tests.py")
task032 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task032)
runner = task032.runner
runner.AFFECTED = list(runner.NEW) + list(runner.AFFECTED)
runner.NEW = ["tests/productization/director/test_director_producer.py",
              "tests/productization/director/test_director_recovery.py"]
for folder in ("tests/director", "tests/qa_director16"):
    for path in sorted((ROOT / folder).glob("test*.py")):
        runner.AFFECTED.append(path.relative_to(ROOT).as_posix())
runner.AFFECTED.append("tests/qa_domain_repair16/test_director.py")
for folder in ("tests/productization/director", "tests/director", "tests/qa_director16"):
    sys.path.insert(0, str(ROOT / folder))
runner.AFFECTED = list(dict.fromkeys(runner.AFFECTED))
assert not set(runner.NEW).intersection(runner.AFFECTED)

if __name__ == "__main__":
    raise SystemExit(runner.main())
