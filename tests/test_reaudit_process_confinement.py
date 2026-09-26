import sys,time,tempfile,unittest
from pathlib import Path
from bie.game_engine.build_runtime_engine.process import run_bounded
from bie.game_engine.build_runtime_engine.errors import GameBuildError

class ProcessConfinementReaudit(unittest.TestCase):
    def test_streaming_output_hits_bound_before_timeout(self):
        script="import os\nwhile True: os.write(1,b'x'*4096)"
        with self.assertRaisesRegex(GameBuildError,'OUTPUT_LIMIT'):
            run_bounded([sys.executable,'-c',script],max_output=8192,timeout=3)

    def test_timeout_terminates_descendants(self):
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/'child.pid'
            script="import subprocess,sys,time;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);Path(sys.argv[1]).write_text(str(p.pid));time.sleep(30)"
            with self.assertRaisesRegex(GameBuildError,'TIMEOUT'):
                run_bounded([sys.executable,'-c',script,str(marker)],timeout=1)
            self.assertTrue(marker.exists(),'Child must actually start before the timeout')
            status=Path('/proc')/marker.read_text()/'status'
            for _ in range(20):
                if not status.exists():return
                if any(line.startswith('State:') and ('Z' in line or 'X' in line) for line in status.read_text().splitlines()):return
                time.sleep(.05)
            self.fail('Timed-out invocation left a live child process')
