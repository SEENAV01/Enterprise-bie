"""Safe unique Task034 receipts; retain every selected Task033 preservation test."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("task033_runner", ROOT / "tools/run_task033_tests.py")
task033 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task033)
runner = task033.runner
runner.AFFECTED = list(runner.NEW) + list(runner.AFFECTED)
runner.NEW = [
    "tests/productization/visual/test_visual_producer.py",
    "tests/productization/visual/test_visual_recovery.py",
]

# Preserve all native Visual algorithms, historical DIR/REP pin checks, grammar,
# layout, asset, text/accessibility and QA suites alongside current production.
for folder in ("tests/visual_intelligence", "tests/qa_visual16"):
    for path in sorted((ROOT / folder).glob("test*.py")):
        runner.AFFECTED.append(path.relative_to(ROOT).as_posix())

# Native Animation contracts are checked for handoff compatibility only. These
# inherited tests do not mean that the Task034 global ANIMATION stage executes.
runner.AFFECTED.extend([
    "tests/animation_intelligence/test_h1_001.py",
    "tests/animation_intelligence/test_h1_002.py",
    "tests/animation_intelligence/test_h2_replay.py",
])
for folder in (
    "tests/productization/visual", "tests/visual_intelligence", "tests/qa_visual16",
    "tests/animation_intelligence",
):
    sys.path.insert(0, str(ROOT / folder))

runner.AFFECTED = list(dict.fromkeys(runner.AFFECTED))
assert not set(runner.NEW).intersection(runner.AFFECTED)
assert len(runner.NEW) == len(set(runner.NEW))
assert len(runner.AFFECTED) == len(set(runner.AFFECTED))

if __name__ == "__main__":
    raise SystemExit(runner.main())
