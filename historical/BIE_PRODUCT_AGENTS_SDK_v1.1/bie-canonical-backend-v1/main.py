from __future__ import annotations

import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agent import _run_bie, run_agent_sync

ROOT = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj, content_type: str = "application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            key_present = bool(os.getenv("OPENAI_API_KEY"))
            self._send(200, {
                "status": "ok",
                "product": "BIE",
                "interfaces": ["standalone", "rest_api", "openai_agents_sdk"],
                "openai_api_key_configured": key_present,
                "agent_sdk_dependency": _agent_sdk_available(),
            })
            return
        if path == "/v1/agent/schema":
            self._send(200, {
                "name": "bie_book_to_video_agent",
                "description": "Orchestrates the canonical BIE M1-M300 book-to-video pipeline.",
                "input": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
            })
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/v1/agent/run":
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                message = payload["message"]
                result = run_agent_sync(message)
                final = getattr(result, "final_output", None)
                self._send(200, {"status": "COMPLETED", "final_output": final, "raw": str(result)})
            except Exception as exc:
                self._send(500, {"status": "FAILED", "error": str(exc)})
            return
        if path == "/v1/bie/run":
            length = int(self.headers.get("Content-Length", "0"))
            data = self.rfile.read(length)
            try:
                payload = json.loads(data or b"{}")
                result = _run_bie(payload["pdf_path"])
                self._send(200, result)
            except Exception as exc:
                self._send(400, {"status": "FAILED", "error": str(exc)})
            return
        self._send(404, {"error": "not_found"})


def _agent_sdk_available() -> bool:
    try:
        import agents  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    print(f"BIE Agent/API running on http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
