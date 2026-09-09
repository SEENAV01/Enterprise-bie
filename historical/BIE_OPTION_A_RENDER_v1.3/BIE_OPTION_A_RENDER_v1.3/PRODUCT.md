# BIE Product v1.1

BIE is a reusable specialized intelligence engine around the canonical M1-M300 pipeline.

## Product surfaces
- Standalone web app: `app/server.py`
- REST API: `main.py`
- OpenAI Agents SDK: `agent.py`
- OpenAI provider adapter: `ai/openai_provider.py`

## Agent architecture

The Agents SDK is an orchestration layer, not a replacement for BIE. The agent exposes the canonical BIE pipeline as a narrow function tool and returns the resulting grounded artifacts.

## Run

```bash
pip install -e .
export OPENAI_API_KEY=...
PORT=8080 python main.py
```

Then:
- `GET /health`
- `POST /v1/agent/run`
- `POST /v1/bie/run`

For deterministic smoke testing without an API key:

```bash
BIE_MOCK=1 PORT=8080 python main.py
```

The product stops at video-generation code/project generation. MP4 rendering remains a later phase.
