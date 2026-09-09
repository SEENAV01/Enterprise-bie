from __future__ import annotations
import json, os, shutil, tempfile, threading
from pathlib import Path
from uuid import uuid4
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from agent import run_agent_sync

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "data" / "jobs"
JOBS.mkdir(parents=True, exist_ok=True)

HTML = '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BIE</title><style>body{font-family:system-ui;margin:0;background:#f6f7f9;color:#171717}main{max-width:900px;margin:40px auto;padding:24px}.card{background:white;border:1px solid #ddd;border-radius:16px;padding:24px;margin:16px 0}button{padding:12px 18px;border:0;border-radius:10px;background:#111;color:white;font-weight:600}input{margin:12px 0}pre{white-space:pre-wrap;overflow:auto;background:#f3f3f3;padding:16px;border-radius:10px}</style></head><body><main><h1>BIE</h1><p>Book → Video Intelligence Engine</p><div class="card"><form id="f"><input id="pdf" type="file" accept=".pdf" required><br><button>Generate video code</button></form><p id="s"></p><pre id="o"></pre></div></main><script>const f=document.getElementById('f'),s=document.getElementById('s'),o=document.getElementById('o');f.onsubmit=async e=>{e.preventDefault();s.textContent='Uploading…';const d=new FormData();d.append('file',pdf.files[0]);const r=await fetch('/v1/jobs',{method:'POST',body:d});const j=await r.json();if(!r.ok){s.textContent=j.error||'Failed';return}poll(j.job_id)};async function poll(id){const r=await fetch('/v1/jobs/'+id);const j=await r.json();s.textContent=j.status;if(j.status==='COMPLETED'||j.status==='FAILED'){o.textContent=JSON.stringify(j,null,2);return}setTimeout(()=>poll(id),1500)}</script></body></html>'''

def provider():
    if os.getenv('BIE_MOCK','0') == '1':
        from providers.mock import MockProvider
        return MockProvider()
    from ai.openai_provider import OpenAIProvider
    return OpenAIProvider()

def run_job(job_id, pdf_path):
    p=JOBS/job_id; meta=json.loads((p/'job.json').read_text()); meta['status']='RUNNING'; (p/'job.json').write_text(json.dumps(meta,indent=2))
    try:
        from canonical_pipeline import CanonicalBIE
        ctx=CanonicalBIE(work_dir=p/'output', provider=provider()).run(str(pdf_path))
        result={'run_id':ctx.run_id,'status':'COMPLETED','artifacts':ctx.artifacts}
        meta.update(result); meta['output_dir']=str(p/'output'); (p/'result.json').write_text(json.dumps(result,indent=2,default=str));
        (p/'job.json').write_text(json.dumps(meta,indent=2,default=str))
    except Exception as e:
        meta.update({'status':'FAILED','error':str(e)}); (p/'job.json').write_text(json.dumps(meta,indent=2))

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj, content='application/json'):
        b=obj.encode() if isinstance(obj,str) else json.dumps(obj,default=str).encode(); self.send_response(code); self.send_header('Content-Type',content); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/': return self._send(200,HTML,'text/html; charset=utf-8')
        if path=='/health': return self._send(200,{'status':'ok','bie':'canonical','m1_m300':'preserved','provider':provider().healthcheck()})
        if path.startswith('/v1/jobs/'):
            jid=path.split('/')[-1]; f=JOBS/jid/'job.json'
            if not f.exists(): return self._send(404,{'error':'job_not_found'})
            return self._send(200,json.loads(f.read_text()))
        if path=='/openai-tool.json':
            return self._send(200,{'name':'bie_book_to_video','description':'Use BIE to transform a PDF/book into grounded course, lesson, script, scene and video-generation code artifacts.','input_schema':{'type':'object','properties':{'pdf_path':{'type':'string'},'goal':{'type':'string'}},'required':['pdf_path']},'endpoint':'/v1/jobs'})
        if path=='/v1/agent/schema':
            return self._send(200,{'name':'bie_book_to_video_agent','description':'OpenAI Agents SDK orchestration layer for the canonical BIE M1-M300 pipeline.','input':{'type':'object','properties':{'message':{'type':'string'}},'required':['message']}})
        return self._send(404,{'error':'not_found'})
    def do_POST(self):
        path=urlparse(self.path).path
        if path=='/v1/agent/run':
            length=int(self.headers.get('Content-Length','0'))
            try:
                payload=json.loads(self.rfile.read(length) or b'{}')
                result=run_agent_sync(payload['message'])
                return self._send(200,{'status':'COMPLETED','final_output':getattr(result,'final_output',None),'raw':str(result)})
            except Exception as e:
                return self._send(500,{'status':'FAILED','error':str(e)})
        if path != '/v1/jobs': return self._send(404,{'error':'not_found'})
        ctype=self.headers.get('Content-Type',''); length=int(self.headers.get('Content-Length','0'))
        if 'multipart/form-data' not in ctype: return self._send(415,{'error':'multipart_form_required'})
        boundary=ctype.split('boundary=',1)[-1].encode(); body=self.rfile.read(length)
        parts=body.split(b'--'+boundary)
        file_bytes=None; filename='book.pdf'
        for part in parts:
            if b'Content-Disposition' not in part or b'name="file"' not in part: continue
            head,data=part.split(b'\r\n\r\n',1); data=data.rsplit(b'\r\n',1)[0]
            if b'filename=' in head:
                filename=head.split(b'filename="',1)[1].split(b'"',1)[0].decode(errors='ignore') or filename
            file_bytes=data
        if not file_bytes: return self._send(400,{'error':'file_required'})
        jid=str(uuid4()); p=JOBS/jid; p.mkdir(); pdf=p/filename; pdf.write_bytes(file_bytes)
        meta={'job_id':jid,'status':'QUEUED','filename':filename}; (p/'job.json').write_text(json.dumps(meta,indent=2))
        threading.Thread(target=run_job,args=(jid,pdf),daemon=True).start(); return self._send(202,meta)

if __name__=='__main__':
    port=int(os.getenv('PORT','8080')); print(f'BIE running on http://0.0.0.0:{port}'); ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
