"""Native loopback HTTP + actual Edge DOM/AX regressions, not screenshots/fixtures alone."""
from pathlib import Path
import gc,json,os,secrets,socket,subprocess,sys,tempfile,time,unittest
from urllib.request import urlopen,Request
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/productization/document_intelligence'))
from apps.operator.service import Service
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from structural_pdf_fixtures import hierarchy_pdf_with_outline

def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

class UiTemp(tempfile.TemporaryDirectory):
    def cleanup(self):
        target=Path(self.name).resolve()
        if target.parent!=Path(tempfile.gettempdir()).resolve() or not target.name.startswith('bie-app18-ui-'):
            raise RuntimeError('UNSAFE_UI_TEMP_CLEANUP_TARGET')
        # Bounded retry of our own fresh directory only. Never ignore cleanup
        # failure or delete profiles belonging to an existing user browser.
        for attempt in range(21):
            try:return super().cleanup()
            except PermissionError:
                if attempt==20:raise
                gc.collect();time.sleep(.25)

class NativeUi(unittest.TestCase):
    def journey(self,mode,batch002=False,batch003=False,batch003b=False,batch003c=False,batch003d=False,batch004=False):
        browser=Path(os.environ.get('BIE_SECTION18_BROWSER','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'))
        self.assertTrue(browser.is_file(),'Native browser required; NOT a skipped UI check')
        token=secrets.token_hex(32);env=dict(os.environ,BIE_OPERATOR_TOKEN=token,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
        with UiTemp(prefix='bie-app18-ui-') as tmp:
            root=Path(tmp);c=Credentials();p=Principal('local-operator','local',PERMISSIONS,time.time()+3600);c.grant(token,p)
            service=Service(root/'data',c);pdf=hierarchy_pdf_with_outline()
            source=service.import_pdf(p,pdf);run=service.create(p,source['source_id'],{},'native-ui')['run_id']
            if batch002:
                from apps.operator.artifacts import ProductArtifacts
                from batch002_fixtures import documents
                with service.catalog.tx() as db:_,body=service.catalog.intent(db,p,run)
                window=ProductArtifacts(service)
                for kind,document in documents(body).items():
                    window.publish(p,run,kind,document,evidence_origin='SYNTHETIC_TEST')
                window.publish_code(p,run,'<script>window.injected=true</script>\n','html',evidence_origin='SYNTHETIC_TEST')
            if batch003:
                from apps.operator.previews import Previews
                from preview_fixtures import game,render
                window=Previews(service);data,receipt,policy,decoded=render()
                window.publish_render(p,run,data,receipt,policy,source_hash=source['sha256'],decoder=lambda *args:decoded)
                window.publish_game(p,run,*game(),source_hash=source['sha256'],evidence_origin='SYNTHETIC_TEST')
            if batch003b:
                from quality_fixtures import publish_quality
                publish_quality(service,p,run,root)
            if batch003c:
                from assurance_fixtures import publish_gates
                publish_gates(service,p,run,root)
            if batch003d:
                from admin_fixtures import prepare
                admin_runs=prepare(service,p,source)
            if batch004:
                from governance_fixtures import prepare
                prepare(service,p,run)
            nodes=[{'id':'a','label':'<img src=x onerror=alert(1)>'},{'id':'b','label':'Dependent'}]
            for kind,relation in [('concept','related_to'),('prerequisite','prerequisite')]:
                service.publish_graph(p,run,kind,dict(source_hash=source['sha256'],nodes=nodes,
                    edges=[{'source':'a','target':'b','type':relation}]),evidence_origin='SYNTHETIC_TEST')
            fixture=root/'synthetic.pdf';fixture.write_bytes(pdf)
            if batch004:(root/'invalid-benchmark.json').write_text('{"manifest":{},"manifest":{},"policy":{}}')
            http_port,debug_port=port(),port()
            process=subprocess.Popen([sys.executable,'-B',str(ROOT/'scripts/run_bie_operator.py'),
                '--data-root',str(root/'data'),'--port',str(http_port)],cwd=ROOT,env=env,
                stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            try:
                for _ in range(100):
                    try:
                        with urlopen(f'http://127.0.0.1:{http_port}/healthz',timeout=1) as r:
                            self.assertEqual(r.status,200);break
                    except OSError:time.sleep(.1)
                else:self.fail('Native HTTP server did not start')
                command=['node',str(ROOT/'tests/section18/browser_journey.mjs'),str(browser),
                    str(root/'edge-profile'),str(debug_port),f'http://127.0.0.1:{http_port}/',run,mode,str(fixture),
                    'batch004' if batch004 else 'batch003d' if batch003d else 'batch003c' if batch003c else 'batch003b' if batch003b else 'batch003' if batch003 else 'batch002' if batch002 else 'batch001']
                if os.name=='nt':
                    from windows_browser_lifecycle import WindowsBrowserJob
                    job=WindowsBrowserJob();node=None
                    try:
                        node=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
                        job.attach(node)
                        stdout,stderr=node.communicate('GO\n',timeout=90)
                        result=subprocess.CompletedProcess(command,node.returncode,stdout,stderr)
                    finally:
                        job.close()
                        if node is not None:
                            if node.poll() is None:node.kill();node.wait(timeout=5)
                            for stream in (node.stdin,node.stdout,node.stderr):
                                if stream is not None:stream.close()
                else:
                    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
                self.assertEqual(result.returncode,0,result.stderr)
                receipt=json.loads(result.stdout);self.assertTrue(receipt['passed']);self.assertTrue(receipt['ax_tree'])
                self.assertEqual(service.status(p,run)['status'],'READY')
                if batch003d:
                    self.assertEqual(service.status(p,admin_runs['failed'])['status'],'FAILED')
                    self.assertEqual(service.status(p,admin_runs['success'])['status'],'SUCCEEDED')
                    self.assertEqual(len(service.list_runs(p)['items']),5 if mode=='desktop' else 4)
            finally:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
                process.stderr.close();gc.collect();time.sleep(.2);gc.collect()
    def test_desktop_actual_upload_controls_and_graphs(self):self.journey('desktop')
    def test_phone_native_layout_and_accessibility(self):self.journey('phone')
    def test_tablet_native_layout_and_accessibility(self):self.journey('tablet')

if __name__=='__main__':unittest.main(verbosity=2)
