from __future__ import annotations
import json
import os
import re
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .service import BIEProduct
from .jobs import JobStore
from .agent_tool import tool_manifest

MAX_UPLOAD = int(os.getenv("BIE_MAX_UPLOAD_BYTES", str(200 * 1024 * 1024)))

HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BIE Intelligence Engine</title><style>body{font-family:system-ui;margin:0;background:#f5f6f8;color:#111}main{max-width:900px;margin:40px auto;padding:24px}section{background:#fff;border:1px solid #ddd;border-radius:14px;padding:22px;margin-bottom:18px}button{padding:10px 16px;border-radius:9px;border:0;background:#111;color:#fff}pre{white-space:pre-wrap;background:#f0f1f3;padding:14px;border-radius:10px;overflow:auto}.muted{color:#666}</style></head><body><main><section><h1>BIE Intelligence Engine</h1><p class="muted">PDF → understanding → course → lesson → script → scenes → video-generation code</p><input id="file" type="file" accept=".pdf,.epub,.txt,.md"><button onclick="start()">Process document</button><p id="status"></p></section><section><h2>Result</h2><pre id="out">Waiting…</pre></section></main><script>
async function start(){const f=document.getElementById('file').files[0];if(!f)return alert('Choose a document first');const s=document.getElementById('status');s.textContent='Uploading…';const r=await fetch('/v1/jobs',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Filename':f.name},body:f});if(!r.ok){s.textContent=await r.text();return}const j=await r.json();s.textContent='Job '+j.job_id+' started';poll(j.job_id)}
async function poll(id){const r=await fetch('/v1/jobs/'+id);const j=await r.json();document.getElementById('status').textContent='Status: '+j.status;if(j.status==='queued'||j.status==='running')return setTimeout(()=>poll(id),1500);document.getElementById('out').textContent=JSON.stringify(j,null,2)}
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    server_version = "BIE/1.0"
    def _auth(self):
        expected = os.getenv("BIE_API_KEY")
        if not expected: return True
        got = self.headers.get("Authorization", "")
        return got == "Bearer " + expected
    def _send(self, code, payload, content_type="application/json"):
        data = payload if isinstance(payload, bytes) else (json.dumps(payload, ensure_ascii=False).encode() if content_type=="application/json" else str(payload).encode())
        self.send_response(code); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/": return self._send(200,HTML,"text/html; charset=utf-8")
        if not self._auth(): return self._send(401,{"error":"unauthorized"})
        if p=="/health": return self._send(200,self.server.product.health())
        if p=="/v1/agent/tools": return self._send(200,tool_manifest())
        if p.startswith("/v1/jobs/"):
            job=self.server.jobs.get(p.rsplit('/',1)[-1]); return self._send(200,job) if job else self._send(404,{"error":"job_not_found"})
        return self._send(404,{"error":"not_found"})
    def do_POST(self):
        p=urlparse(self.path).path
        if not self._auth(): return self._send(401,{"error":"unauthorized"})
        if p!="/v1/jobs": return self._send(404,{"error":"not_found"})
        length=int(self.headers.get("Content-Length","0"))
        if length<=0 or length>MAX_UPLOAD: return self._send(413,{"error":"invalid_upload_size"})
        name=self.headers.get("X-Filename","document.pdf")
        safe=re.sub(r"[^A-Za-z0-9._-]","_",Path(name).name)
        if Path(safe).suffix.lower() not in {".pdf",".epub",".txt",".md"}: return self._send(415,{"error":"unsupported_file_type"})
        root=Path(os.getenv("BIE_UPLOAD_DIR","output/uploads")); root.mkdir(parents=True,exist_ok=True)
        fd,path=tempfile.mkstemp(prefix="upload_",suffix=Path(safe).suffix,dir=root); os.close(fd)
        remaining=length
        with open(path,"wb") as f:
            while remaining:
                chunk=self.rfile.read(min(1024*1024,remaining));
                if not chunk: break
                f.write(chunk); remaining-=len(chunk)
        job=self.server.jobs.submit(str(path))
        return self._send(202,job)

def create_server(host="127.0.0.1", port=8080, work_dir="output"):
    product=BIEProduct(work_dir=work_dir)
    server=ThreadingHTTPServer((host,port),Handler)
    server.product=product; server.jobs=JobStore(product)
    return server

def main():
    host=os.getenv("BIE_HOST","127.0.0.1"); port=int(os.getenv("BIE_PORT","8080")); work=os.getenv("BIE_WORK_DIR","output")
    server=create_server(host,port,work); print(f"BIE running at http://{host}:{port}"); server.serve_forever()

if __name__=="__main__": main()
