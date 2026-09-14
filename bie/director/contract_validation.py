"""Shared boundary checks for original DIR contracts; HARD-CONTRACTS-001.

Original archive bytes remain immutable. Valid identifiers are retained exactly;
blank/non-string identifiers and ambiguous collection shapes are rejected.
"""
from collections import deque
import math


def nonblank(value, name):
    if not isinstance(value,str) or not value.strip():
        raise ValueError(f'{name} must be a nonblank string')
    return value


def items(values, name, required=True):
    if isinstance(values,(str,bytes,dict)):
        raise ValueError(f'{name} must be a collection of records/identifiers')
    try: out=tuple(values)
    except TypeError as exc: raise ValueError(f'{name} must be iterable') from exc
    if required and not out: raise ValueError(f'{name} must not be empty')
    return out


def ids(values, name, required=True, canonical=False):
    out=items(values,name,required)
    for value in out: nonblank(value,name)
    if canonical: return tuple(sorted(set(out)))
    if isinstance(values,(set,frozenset)) or len(out)!=len(set(out)):
        raise ValueError(f'{name} must have unique ordered identifiers')
    return out


def finite(value,name,low=0,high=None,positive=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError(f'{name} must be finite numeric data')
    try: is_finite=math.isfinite(value)
    except OverflowError: is_finite=False
    if not is_finite: raise ValueError(f'{name} must be finite numeric data')
    if value<low or (positive and value<=0) or (high is not None and value>high):
        raise ValueError(f'{name} outside permitted range')
    return value


def acyclic(parents):
    """Kahn traversal avoids recursion failure for book-scale lesson graphs."""
    indegrees={key:len(deps) for key,deps in parents.items()}
    children={key:[] for key in parents}
    for key,deps in parents.items():
        for parent in deps:
            if parent not in parents: raise ValueError('unknown parent scene')
            children[parent].append(key)
    ready=deque(key for key,count in indegrees.items() if not count); visited=0
    while ready:
        key=ready.popleft(); visited+=1
        for child in children[key]:
            indegrees[child]-=1
            if indegrees[child]==0: ready.append(child)
    if visited!=len(parents): raise ValueError('cyclic scene parent graph')
