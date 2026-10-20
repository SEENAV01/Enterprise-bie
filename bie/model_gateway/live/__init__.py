"""Task 038: live AI providers behind the existing ``bie.model_gateway`` interface.

The thin adapters in ``bie/model_gateway`` (``ClaudeAdapter``, ``GPTAdapter``, ``GeminiAdapter``)
take an injected client. This package supplies the real clients (standard-library HTTPS only, no
vendor SDK), a deterministic fake client for offline tests, and ``LiveGateway``, which adds
bounded retries, a response cache, schema validation with one repair pass, and a per-call token
and cost ledger.

Keys are read only from environment variables (in CI: GitHub Actions secrets). They are never
logged, cached, written to evidence or echoed in errors; provider error text is redacted.
"""
