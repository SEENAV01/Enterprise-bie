# BIE Agent SDK interface

BIE is not replaced by the agent. The Agent SDK is the orchestration surface around the canonical M1-M300 engine.

## Architecture

`User/PDF -> BIE Agent (Agents SDK) -> run_bie_book_to_video tool -> CanonicalBIE M1-M300 -> OpenAI provider -> validated artifacts`

The canonical engine remains responsible for source ingestion, provenance, knowledge, lesson planning, script generation, scene planning and Remotion project generation.

## Local run

```bash
pip install -e .
export OPENAI_API_KEY=...
PORT=8080 uv run python main.py
```

For a deterministic smoke test without API calls:

```bash
BIE_MOCK=1 PORT=8080 python main.py
```

## Agent usage

```python
from agent import run_agent_sync
result = run_agent_sync("Run BIE on /absolute/path/to/book.pdf and create the video-generation project.")
print(result.final_output)
```

The API surface also exposes:
- `GET /health`
- `POST /v1/agent/run` with `{"message":"..."}`
- `POST /v1/bie/run` with `{"pdf_path":"..."}`
- `GET /v1/agent/schema`
