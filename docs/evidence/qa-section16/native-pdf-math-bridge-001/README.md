# Selected native-PDF math source bridge — bounded Section 16 evidence

Status: **CANDIDATE ONLY; QA16-GAP-025 AND QA16-GAP-028 REMAIN OPEN**.

`bie/qa/math_v2/native_pdf_bridge.py` composes the canonical source-linked PDF
text runtime. An operator supplies one exact block ID; the bridge retains the
source hash, page, region and geometry, then accepts only a strict explicit
binary arithmetic expression or one `=` equation. Both the native math parser
and existing Section 16 QA math adapter must agree with the original block
text. Unsupported notation, incomplete expressions, absent blocks and malformed
PDFs fail closed. Safe output carries only hashes/counts/geometry, not formula
or textbook text. It never asserts formula truth or automatic extraction.

Fifteen structural positive/seeded-negative tests pass locally in the existing
repository Python environment. The tests use generated native-text PDFs, not
the real Money PDF. No existing DI or math contract implementation is modified
by this bridge. Hosted combined CI and exact-candidate integration evidence are
still required.

This does **not** resolve general calculus, matrices, OCR, LaTeX, source
semantics, rendered math, scientifically correct derivations, independent
reference judgment or learner outcomes. It is one bounded connection toward
the wider original obligations, not a Section 16 sign-off disposition.
