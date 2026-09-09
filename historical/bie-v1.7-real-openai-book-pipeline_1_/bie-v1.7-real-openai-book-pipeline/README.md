# BIE v1.7 — Real OpenAI Book Pipeline
M11 connects the BIE contract to the OpenAI Responses API with strict JSON Schema output.

Set `OPENAI_API_KEY` in the environment. Optionally set `BIE_MODEL`.

Prepare:
`python src/prepare_pdf_text.py examples/pages.json examples/excerpts.json`

Run:
`python src/openai_book_engine.py examples/excerpts.json output.json`

Validate:
`python src/validate_output.py output.json`

The API key is never stored in this repository.
