"""Adapters: each wraps one family of libraries behind small functions that return plain JSON-ready data (compute)
or files (offline render). Heavy libraries are imported inside the functions, so importing an adapter never needs them;
a missing library raises ``Unavailable`` naming the install group (pyproject extras ``toolbox-*``)."""
