"""Keep artifact-only imports independent of the Linux execution backend.

The public callable API is unchanged. Requesting an execution callable still
loads the same bounded process and sandbox implementation; no fallback exists.
"""
from importlib import import_module

__all__ = ['build_runtime_package', 'build_001', 'build_002', 'build_003', 'build_004', 'build_005']

def __getattr__(name):
    if name not in __all__:
        raise AttributeError(name)
    module, symbol = ('pipeline', 'build_runtime_package') if name == 'build_runtime_package' else (name, 'execute')
    value = getattr(import_module('.' + module, __name__), symbol)
    globals()[name] = value
    return value
