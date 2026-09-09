# BIE v1.6 — LLM Book Understanding Engine

M10 architecture.

It defines the source-grounded JSON contract, evidence tracking, long-book chunk/batch strategy, contradiction/ambiguity review, and an API-key-safe model adapter boundary.

It deliberately does not hard-code an API call or expose a secret. The next integration step can connect the structured contract to the chosen model API using `OPENAI_API_KEY` from the environment.

Run preparation:
`python engine/run_engine.py examples/document.json examples/prepared.json`

Run tests:
`python -m pytest`
