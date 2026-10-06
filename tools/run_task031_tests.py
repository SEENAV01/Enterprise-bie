"""Safe unique-count runner; canonical Math/QA/legacy suites remain selected."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("task030_runner",ROOT/"tools/run_task030_tests.py")
task030=importlib.util.module_from_spec(spec);spec.loader.exec_module(task030)
runner=task030.runner
runner.AFFECTED=list(runner.NEW)+list(runner.AFFECTED)
runner.NEW=["tests/productization/math/test_math_producer.py","tests/productization/math/test_math_recovery.py",
            "tests/productization/math/test_math_graph_preservation.py"]
for pattern in ("BIE_MATH_*/tests/**/test*.py","BIE_BI_EQ_*/tests/**/test*.py",
                "BIE_KI_EQ_LINK_*/tests/**/test*.py","BIE_BI_OCR_003/tests/**/test*.py",
                "BIE_INFRA_INTEGRATION_001/tests/**/test*.py"):
    for p in sorted((ROOT/"tests/imported").glob(pattern)):runner.AFFECTED.append(p.relative_to(ROOT).as_posix())
for folder in ("tests/qa_math16",):
    for p in sorted((ROOT/folder).glob("test*.py")):runner.AFFECTED.append(p.relative_to(ROOT).as_posix())
runner.AFFECTED.extend(["tests/assembly/test_native_pdf_math_bridge.py","tests/assembly/test_native_math_parser_repair.py",
    "tests/assembly/test_section16_native_math_amendment.py","tests/qa_hardening_h3/test_h3_readiness.py"])
for folder in ("tests/productization/math","tests/qa_math16","tests/qa_hardening_h3"):
    sys.path.insert(0,str(ROOT/folder))
assert len(runner.AFFECTED)==len(set(runner.AFFECTED))
if __name__=="__main__":raise SystemExit(runner.main())
