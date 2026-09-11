"""RE-TEMP-055 — Provide canonical unittest-compatible wrappers for legacy pytest-style TEMP-014..018 tests.

This bridge is intentionally generic: it discovers callable ``test_*`` functions
from a legacy module and exposes them through a unittest.TestCase instance so
the canonical enterprise unittest runner can execute them.
"""
import importlib
import inspect
import unittest

def load_legacy_test_functions(module_name: str):
    module = importlib.import_module(module_name)
    funcs = []
    for name, obj in sorted(vars(module).items()):
        if name.startswith("test_") and inspect.isfunction(obj):
            funcs.append((name, obj))
    return tuple(funcs)

def build_unittest_case(module_name: str):
    funcs = load_legacy_test_functions(module_name)
    attrs = {}
    for name, fn in funcs:
        def make_test(f):
            def _test(self):
                f()
            return _test
        attrs[name] = make_test(fn)
    return type("LegacyTemporalFunctionTests", (unittest.TestCase,), attrs)
