"""BIE's toolbox (auzaar-ghar, Task 046a): every library, tool and asset source BIE uses to show what a scene asks for.

- ``registry.json`` lists each tool with its version, licence, source, capabilities, role, render path and status;
  ``capabilities.json`` is the fixed vocabulary of what BIE may need to show.
- ``registry.load()`` reads and checks both; ``resolver.resolve()`` picks the tools for a capability, subject, level
  and render path, with fallbacks, and logs a missing capability when nothing fits.
- ``adapters/`` wrap the Python libraries (compute: they emit plain JSON for BIE's web blocks) and the offline
  renderers (Blender, Manim); ``sources.py`` fetches models, structures and pictures on demand into the asset library
  with their licence and credit; ``demos.py`` builds the proof clips; ``page.py`` writes the readable toolbox page.
- ``licence_policy.json`` is BIE's only licence policy (Task 046a-L: lessons take only CC0, public domain and CC BY);
  ``licence.py`` reads it for every licence decision and holds the lesson licence gate (``lesson_licence_check``).

Principle: a Python library computes, a BIE block shows.
"""
