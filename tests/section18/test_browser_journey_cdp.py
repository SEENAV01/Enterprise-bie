"""F-08 diagnostic regression: how the native browser harness reports a stuck first navigation.

Task 037B. The Section 18 browser gate sometimes failed with ``CDP_TIMEOUT:Page.navigate:7``
while the operator server was healthy. These tests drive ``browser_journey.mjs`` against a
scripted DevTools endpoint (no real browser) and pin the evidence it must give:

* a DevTools socket that closes during ``Page.navigate`` is reported at once as
  ``CDP_SOCKET_CLOSED``, not as an ambiguous 10 s timeout;
* a navigation that never answers is still ``CDP_TIMEOUT:Page.navigate:7`` and the diagnostic
  says whether the request was sent, whether the socket and target were alive, and whether
  the server was healthy.

This proves the diagnosis machinery only. It is not evidence that F-08 is gone.
"""
from pathlib import Path
import base64, hashlib, http.server, json, os, re, socket, socketserver, struct, subprocess, sys, tempfile, threading, time, unittest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / 'tests/section18/browser_journey.mjs'
GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'


class FakeDevTools(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

    def __init__(self, behaviour):
        self.behaviour, self.methods, self.list_calls = behaviour, [], 0
        super().__init__(('127.0.0.1', 0), Handler)

    @property
    def port(self):
        return self.server_address[1]


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, content_type='application/json'):
        data = body.encode()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        port = self.server.port
        if self.path == '/json/list':
            self.server.list_calls += 1
            # F-12: a real Chromium answers /json/list before its first tab exists.
            if self.server.behaviour == 'no_target' or (self.server.behaviour == 'late_target' and self.server.list_calls <= 3):
                return self.reply('[]')
            return self.reply(json.dumps([{'id': 'T1', 'type': 'page', 'url': 'about:blank',
                                           'webSocketDebuggerUrl': f'ws://127.0.0.1:{port}/devtools/page/T1'}]))
        if self.path == '/healthz':
            return self.reply('{"status":"ok"}')
        if self.path == '/devtools/page/T1' and self.headers.get('Upgrade', '').lower() == 'websocket':
            return self.websocket()
        self.send_error(404)

    def websocket(self):
        accept = base64.b64encode(hashlib.sha1(self.headers['Sec-WebSocket-Key'].encode() + GUID).digest()).decode()
        self.wfile.write(('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                          f'Sec-WebSocket-Accept: {accept}\r\n\r\n').encode())
        self.wfile.flush()
        self.close_connection = True
        while True:
            message = self.frame()
            if message is None:
                return
            row = json.loads(message)
            self.server.methods.append(row['method'])
            if row['method'] == 'Page.navigate':
                if self.server.behaviour == 'close':
                    self.wfile.write(b'\x88\x02\x03\xe8')  # close frame, code 1000
                    self.wfile.flush()
                    return
                continue  # 'silent': the navigation never answers, like F-08
            self.send(json.dumps({'id': row['id'], 'result': {}}))
            if row['method'] == 'Browser.close':
                return

    def frame(self):
        head = self.rfile.read(2)
        if len(head) < 2:
            return None
        opcode, length = head[0] & 0x0F, head[1] & 0x7F
        if length == 126:
            length = struct.unpack('>H', self.rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack('>Q', self.rfile.read(8))[0]
        mask = self.rfile.read(4)
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(self.rfile.read(length)))
        return None if opcode == 8 else payload.decode()

    def send(self, text):
        data = text.encode()
        head = bytes([0x81, len(data)]) if len(data) < 126 else bytes([0x81, 126]) + struct.pack('>H', len(data))
        self.wfile.write(head + data)
        self.wfile.flush()


class BrowserJourneyCdpDiagnostics(unittest.TestCase):
    def run_harness(self, behaviour):
        server = FakeDevTools(behaviour)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix='bie-f08-') as tmp:
                # The "browser" is the Python interpreter: it rejects the browser
                # switches and exits, so no real browser is started or killed.
                command = ['node', str(HARNESS), sys.executable, str(Path(tmp) / 'profile'), str(server.port),
                           f'http://127.0.0.1:{server.port}/', 'run', 'desktop', str(Path(tmp) / 'none.pdf'), 'batch001']
                env = {k: v for k, v in os.environ.items() if k != 'BIE_OPERATOR_TOKEN'}
                started = time.monotonic()
                result = subprocess.run(command, cwd=ROOT, env=env, input='GO\n', capture_output=True,
                                        text=True, timeout=60)
                elapsed = time.monotonic() - started
        finally:
            server.shutdown()
            server.server_close()
        failures = re.findall(r'NATIVE_UI_FAILED:(\S+)', result.stderr)
        diagnostics = [json.loads(line.split(':', 1)[1]) for line in result.stderr.splitlines()
                       if line.startswith('NATIVE_CDP_DIAGNOSTIC:')]
        return result, failures, diagnostics, elapsed, server.methods

    def test_an_empty_target_list_at_start_is_polled_again_not_a_failure(self):
        """F-12 (PR #62 run 40109667708, tablet): /json/list answered [] before the first tab existed and the old
        harness failed at once with BROWSER_START_FAILED. Now it keeps polling until a page target is listed."""
        result, failures, diagnostics, elapsed, methods = self.run_harness('late_target')
        self.assertEqual(failures, ['CDP_TIMEOUT:Page.navigate:7'])        # the start passed; the navigation is 'silent'
        self.assertEqual(methods[:2], ['Page.enable', 'Runtime.enable'])
        self.assertEqual(len(diagnostics), 1)
        self.assertNotIn('startPolls', diagnostics[0])

    def test_no_target_within_the_start_budget_fails_with_evidence(self):
        result, failures, diagnostics, elapsed, methods = self.run_harness('no_target')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(failures, ['BROWSER_START_FAILED'])
        self.assertGreaterEqual(elapsed, 29, 'the whole 30 s start budget is used before giving up')
        self.assertEqual(methods, [])
        self.assertEqual(len(diagnostics), 1)
        d = diagnostics[0]
        self.assertEqual((d['startPolls'], d['startAnswered'], d['startTargets']), (300, True, 0))
        self.assertIn('childExited', d)
        sys.path.insert(0, str(Path(__file__).parent))
        from browser_diagnostics import failure_annotation
        body = json.loads(failure_annotation('batch002', 'tablet', result.stderr).split('::', 2)[2])
        self.assertEqual(body['codes'], ['BROWSER_START_FAILED'])
        self.assertEqual((body['diagnostic']['startPolls'], body['diagnostic']['startTargets']), (300, 0))

    def test_socket_closed_during_navigate_is_reported_at_once(self):
        result, failures, diagnostics, elapsed, methods = self.run_harness('close')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(failures, ['CDP_SOCKET_CLOSED:Page.navigate:7'])
        self.assertLess(elapsed, 9, 'a closed socket must not wait for the 10 s call deadline')
        self.assertEqual(methods[-1], 'Page.navigate')
        self.assertEqual(len(diagnostics), 1)
        d = diagnostics[0]
        self.assertEqual((d['socketState'], d['socketClose'], d['requestSent'], d['healthStatus'], d['targetListed']),
                         (3, 1000, False, 200, True))

    def test_unanswered_navigate_keeps_timeout_code_with_evidence(self):
        result, failures, diagnostics, elapsed, methods = self.run_harness('silent')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(failures, ['CDP_TIMEOUT:Page.navigate:7'])
        self.assertEqual(methods[:7], ['Page.enable', 'Runtime.enable', 'Network.enable', 'Log.enable',
                                       'Target.setAutoAttach', 'Emulation.setDeviceMetricsOverride', 'Page.navigate'])
        self.assertEqual(len(diagnostics), 1)
        d = diagnostics[0]
        self.assertEqual(set(d), {'rootResponse', 'domReady', 'loadSeen', 'healthStatus', 'childExited', 'contexts',
                                  'sessions', 'requestSent', 'frameLoading', 'socketState', 'socketClose', 'targetListed'})
        self.assertTrue(all(v is None or type(v) in (bool, int) for v in d.values()), d)
        self.assertEqual((d['rootResponse'], d['requestSent'], d['frameLoading'], d['socketState'], d['socketClose'],
                          d['healthStatus'], d['targetListed'], d['childExited']),
                         (None, False, False, 1, None, 200, True, True))


class FailureAnnotation(unittest.TestCase):
    def test_annotation_keeps_only_whitelisted_codes_and_scalar_fields(self):
        sys.path.insert(0, str(Path(__file__).parent))
        from browser_diagnostics import failure_annotation
        stderr = '\n'.join([
            'NATIVE_UI_PROGRESS:BROWSER_START',
            'NATIVE_CDP_DIAGNOSTIC:' + json.dumps({'rootResponse': None, 'healthStatus': 200, 'requestSent': False,
                                                   'socketState': 1, 'leak': 'secret-token', 'contexts': [1]}),
            'NATIVE_UI_FAILED:CDP_TIMEOUT:Page.navigate:7',
            'NATIVE_UI_FAILED:BROWSER_STATE_TIMEOUT:document.getElementById("token").value=secret-token'])
        line = failure_annotation('batch001', 'tablet', stderr)
        self.assertTrue(line.startswith('::warning title=Section 18 browser failure::'))
        self.assertNotIn('secret-token', line)
        self.assertNotIn('\n', line)
        body = json.loads(line.split('::', 2)[2])
        self.assertEqual(body, {'scenario': 'batch001', 'mode': 'tablet',
                                'codes': ['CDP_TIMEOUT:Page.navigate:7', 'BROWSER_STATE_TIMEOUT'],
                                'diagnostic': {'rootResponse': None, 'healthStatus': 200, 'requestSent': False,
                                               'socketState': 1}})


if __name__ == '__main__':
    unittest.main(verbosity=2)
