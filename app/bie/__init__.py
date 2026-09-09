"""Compatibility imports resolve to the SAME canonical module and class identities."""
from importlib import import_module
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_loader
import sys

_ROOTS = {"enterprise": "infrastructure", "book_intelligence": "document_intelligence", "game_ir": "game_engine"}


class _CanonicalAlias(Loader):
    def __init__(self, target):
        self.target = target

    def create_module(self, spec):
        return import_module(self.target)

    def exec_module(self, module):
        pass


class _LegacyFinder(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith("app.bie."):
            return None
        bits = fullname.split(".")[2:]
        bits[0] = _ROOTS.get(bits[0], bits[0])
        canonical = ".".join(["bie", *bits])
        module = import_module(canonical)
        return spec_from_loader(fullname, _CanonicalAlias(canonical), is_package=hasattr(module, "__path__"))


if not any(type(x).__module__ == __name__ and type(x).__name__ == "_LegacyFinder" for x in sys.meta_path):
    sys.meta_path.insert(0, _LegacyFinder())
