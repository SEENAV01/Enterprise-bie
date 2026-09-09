# 500-Page Test Protocol

1. Place the test PDF at a local path.
2. Run:

`python run.py --book /path/to/book.pdf`

3. The run must progressively produce:
   - source manifest
   - chapter/section map
   - concept graph
   - prerequisite graph
   - course map
   - lesson specs
   - scene specs
   - visual specs
   - video-code generation inputs
   - generated Remotion code
   - static validation report

4. Evaluate:
   - page/chapter coverage
   - concept coverage
   - prerequisite correctness
   - lesson completeness
   - scene completeness
   - source provenance
   - unresolved items
   - code validity

5. Rendering is explicitly out of scope for this benchmark.
