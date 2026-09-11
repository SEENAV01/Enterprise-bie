from pathlib import Path
import re

def classify_test_file(path: str):
    text=Path(path).read_text()
    has_unittest=bool(re.search(r"class\s+\w+\s*\(\s*unittest\.TestCase\s*\)",text))
    has_pytest_functions=bool(re.search(r"^def\s+test_",text,re.M))
    if has_unittest:
        return "UNITTEST_COMPATIBLE"
    if has_pytest_functions:
        return "PYTEST_FUNCTION_ONLY"
    return "NO_DISCOVERABLE_TESTS"

def enterprise_runner_compatible(path: str):
    return classify_test_file(path)=="UNITTEST_COMPATIBLE"
