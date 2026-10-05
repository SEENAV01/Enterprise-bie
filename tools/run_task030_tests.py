"""Reuse existing safe receipt runner; count distinct modules, no repeated-count claims."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("task029_receipt_runner",ROOT/"tools/run_task029_tests.py")
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
runner.AFFECTED=list(runner.NEW)+list(runner.AFFECTED)
runner.NEW=["tests/productization/reasoning/test_pr_reasoning_producer.py",
            "tests/productization/reasoning/test_pr_reasoning_recovery.py"]
for p in sorted((ROOT/"tests/imported").glob("BIE_PR_*/tests/**/test*.py")):
    runner.AFFECTED.append(p.relative_to(ROOT).as_posix())
for p in sorted((ROOT/"tests/reasoning").glob("test_*.py")):
    runner.AFFECTED.append(p.relative_to(ROOT).as_posix())
sys.path.insert(0,str(ROOT/"tests/productization/reasoning"))
assert len(runner.AFFECTED)==len(set(runner.AFFECTED))
if __name__=="__main__":raise SystemExit(runner.main())
