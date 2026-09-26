"""Serve a compiled probe on loopback with its production security headers."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('probe', type=Path)
args = parser.parse_args()
runtime = (args.probe / 'runtime').resolve(strict=True)
headers = json.loads((runtime / 'security-headers.json').read_text(encoding='utf-8'))

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        for key, value in headers.items():
            self.send_header(key, value)
        super().end_headers()

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(runtime)))
print('http://127.0.0.1:' + str(server.server_port) + '/index.html', flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
