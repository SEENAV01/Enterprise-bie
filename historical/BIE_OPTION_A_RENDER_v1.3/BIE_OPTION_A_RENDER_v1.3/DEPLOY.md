# BIE Product v1.2 — Deployment

## Docker (recommended)

1. Build:

```bash
docker build -t bie-product:1.2 .
```

2. Run with the OpenAI key supplied at runtime (never bake it into the image):

```bash
docker run --rm -p 8080:8080 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e BIE_OPENAI_MODEL="gpt-5.6-luna" \
  -e BIE_AGENT_MODEL="gpt-5.6-luna" \
  bie-product:1.2
```

3. Verify:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/openai-tool.json
curl http://localhost:8080/v1/agent/schema
```

## Web app

Open `http://localhost:8080/`, choose a PDF, and submit it. The UI creates a background BIE job and polls `/v1/jobs/<job_id>`.

## Agent SDK

The Python agent is in `agent.py`. The HTTP endpoint `POST /v1/agent/run` accepts JSON:

```json
{"message":"Run BIE on /path/to/book.pdf"}
```

The SDK dependency is declared in `pyproject.toml` as `openai-agents>=0.14.0`.

## Production notes

For long-running books, put `/v1/jobs` behind a durable queue/worker rather than keeping execution in the web process. Keep API keys in the hosting platform's secret manager/environment.

## Render Free Test

This repository also contains `render.yaml` and `OPTION_A_DEPLOY.md` for a temporary Render Web Service test. The free service is intended for validation, not production workloads.
