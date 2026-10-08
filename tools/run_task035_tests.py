"""Unique Task035 technical tests plus every inherited Task034 preservation test."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("task034_runner", ROOT / "tools/run_task034_tests.py")
task034 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task034)
runner = task034.runner
runner.AFFECTED = list(runner.NEW) + list(runner.AFFECTED)
runner.NEW = [
    "tests/productization/animation/test_animation_producer.py",
    "tests/productization/animation/test_animation_recovery.py",
]

# Exercise every native ANI contract without calling its historical default-reveal
# helper from the production adapter. Existing Director sync coverage is inherited.
for folder in ("tests/animation_intelligence", "tests/qa_animation16"):
    for path in sorted((ROOT / folder).glob("test*.py")):
        runner.AFFECTED.append(path.relative_to(ROOT).as_posix())
runner.AFFECTED.extend([
    "tests/scene_ir/test_bie_dsl_hard_ani_adopt_001.py",
    "tests/post_dir/test_canonical_adoption.py",
])
for folder in ("tests/productization/animation", "tests/animation_intelligence",
               "tests/qa_animation16", "tests/scene_ir"):
    sys.path.insert(0, str(ROOT / folder))

runner.AFFECTED = list(dict.fromkeys(runner.AFFECTED))
assert not set(runner.NEW).intersection(runner.AFFECTED)
assert len(runner.NEW) == len(set(runner.NEW))
assert len(runner.AFFECTED) == len(set(runner.AFFECTED))

if __name__ == "__main__":
    raise SystemExit(runner.main())
