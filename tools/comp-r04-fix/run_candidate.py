#!/usr/bin/env python3
"""Bind the unchanged R04 driver to an explicitly identified candidate commit/tree."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

p = argparse.ArgumentParser()
p.add_argument('--source-sha', required=True)
p.add_argument('--source-tree', required=True)
a, remaining = p.parse_known_args()
if not all(re.fullmatch('[0-9a-f]{40}', x) for x in (a.source_sha, a.source_tree)):
    raise SystemExit('EXPLICIT_IMMUTABLE_SOURCE_IDENTITY_REQUIRED')
path = Path(__file__).resolve().parents[1] / 'comp-r04/run_comp_r04_slice.py'
data = path.read_bytes()
blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
# Filled from the remotely verified original driver; no hidden runner substitution.
if blob != '72289f725d7ca778f4caefd7778f597738bf8555':
    raise SystemExit('UNREVIEWED_VALIDATION_DRIVER:' + blob)
spec = importlib.util.spec_from_file_location('r04_existing_driver', path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
module.SOURCE_SHA = a.source_sha
module.SOURCE_TREE = a.source_tree
sys.argv = [str(path), *remaining]
raise SystemExit(module.main())
