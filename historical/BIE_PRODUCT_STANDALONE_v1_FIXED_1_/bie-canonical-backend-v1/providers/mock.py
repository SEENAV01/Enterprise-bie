from __future__ import annotations
from typing import Any, Dict

class MockProvider:
    provider_name = "mock"
    def healthcheck(self):
        return {"provider":"mock","model":"mock","api_key_configured":True,"ready":True}
    def generate_json(self, *, task, instructions, input_payload, schema_name, schema, metadata=None):
        # Deterministic smoke-test payload. Real production runs use OpenAIProvider.
        return {"task":task,"provider":"mock","model":"mock","response_id":None,
                "request_id":None,"result":{"status":"MOCK_OUTPUT","task":task}}
