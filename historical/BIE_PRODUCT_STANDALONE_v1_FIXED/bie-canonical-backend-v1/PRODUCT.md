# BIE Product v1

BIE is a reusable specialized intelligence engine around the canonical M1–M300 pipeline.

## Surfaces
- Standalone web app: `/`
- HTTP API: `POST /v1/jobs`, `GET /v1/jobs/{job_id}`
- Health: `/health`
- OpenAI agent/tool descriptor: `/openai-tool.json`

## Run
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=...
python run.py
```
Open `http://localhost:8080`.

For deterministic smoke testing without an API key:
```bash
BIE_MOCK=1 python run.py
```

The product stops at video-generation code/project generation. MP4 rendering is intentionally a later phase.
