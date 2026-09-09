# BIE Product Layer

BIE is a specialized intelligence engine around the canonical M1-M300 pipeline. It is not a foundation model. A model provider supplies general reasoning; BIE supplies the document-to-video workflow, contracts, provenance and validation.

## Run the standalone product

```bash
pip install -r requirements.txt
python -m bie_product.server
```

Open `http://127.0.0.1:8080`.

## API

- `GET /health` — engine/provider readiness
- `GET /v1/agent/tools` — OpenAI-compatible function-tool manifest
- `POST /v1/jobs` — upload a document as `application/octet-stream` with `X-Filename`
- `GET /v1/jobs/{job_id}` — job status and result

Set `BIE_API_KEY` to protect API routes. Keep `OPENAI_API_KEY` server-side; never put it in browser code.

## Provider boundary

`BIEProduct` consumes a provider implementing `generate_json(...)` and `healthcheck()`. OpenAI is included. New model providers should implement `bie_product.providers.base.BIEModelProvider` and be registered in `factory.py` rather than changing the canonical pipeline.

## Scope

The product targets PDF/book → understanding → course/lesson → script → scenes → validated video-generation code. MP4 rendering/publishing remains outside this phase.
