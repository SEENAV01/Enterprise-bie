"""Cross-section canonical SQLite race; real last-close, not forged stat/errors."""
from pathlib import Path
import inspect,os,subprocess,sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from bie.evaluation.benchmarks.native_campaign.runtime import Campaign,private_directory
from bie.evaluation.benchmarks.native_campaign.contracts import require
from bie.evaluation.benchmarks.models import BenchmarkError
import stat

# Exact historical guard is a qualified negative control, never production.
def historical_guard(self):
    private_directory(self.root)
    for name in ('campaign.sqlite','campaign.sqlite-wal','campaign.sqlite-shm','campaign.sqlite-journal'):
        p=self.root/name
        require(not p.is_symlink(),'CAMPAIGN_DATABASE_SYMLINK')
        if p.exists():
            s=p.stat()
            require(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'CAMPAIGN_DATABASE_FILE')

CHILD='''import sqlite3,sys
db=sqlite3.connect(sys.argv[1],isolation_level=None)
db.execute('PRAGMA journal_mode=WAL')
db.execute('CREATE TABLE probe(value TEXT)')
db.execute("INSERT INTO probe VALUES('synthetic')")
print('READY',flush=True)
if sys.stdin.readline()!='CLOSE\\n':raise SystemExit(3)
db.close();print('CLOSED',flush=True)
'''

class CampaignSidecarRace(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bie-s18-campaign-race-');self.root=Path(self.tmp.name)
        self.c=Campaign.__new__(Campaign);self.c.root=self.root
    def tearDown(self):self.tmp.cleanup()
    def cut_real_sidecar(self,method):
        child=subprocess.Popen([sys.executable,'-B','-c',CHILD,str(self.root/'campaign.sqlite')],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        cuts=[]
        try:
            self.assertEqual(child.stdout.readline().strip(),'READY')
            wal=self.root/'campaign.sqlite-wal';self.assertTrue(wal.is_file())
            lines,start=inspect.getsourcelines(method)
            target=start+next(i for i,line in enumerate(lines) if 's=p.stat()' in line or 's = p.lstat()' in line)
            def trace(frame,event,arg):
                if event=='line' and frame.f_code is method.__code__ and frame.f_lineno==target:
                    path=frame.f_locals['p']
                    if path.name=='campaign.sqlite-wal' and not cuts:
                        stdout,stderr=child.communicate('CLOSE\n',timeout=5)
                        self.assertEqual(child.returncode,0,stderr);self.assertEqual(stdout.strip(),'CLOSED')
                        self.assertFalse(wal.exists());cuts.append('REAL_SQLITE_LAST_CLOSE')
                return trace
            prior=sys.gettrace();sys.settrace(trace)
            try:method(self.c)
            finally:sys.settrace(prior)
            self.assertEqual(cuts,['REAL_SQLITE_LAST_CLOSE'])
        finally:
            if child.poll() is None:child.kill()
            child.wait(timeout=5)
            for stream in (child.stdin,child.stdout,child.stderr):stream.close()
    def test_historical_guard_reproduces_real_missing_sidecar_race(self):
        with self.assertRaises(FileNotFoundError):self.cut_real_sidecar(historical_guard)
    def test_current_no_follow_guard_survives_same_real_race(self):
        self.cut_real_sidecar(Campaign._database_paths)
        self.assertTrue((self.root/'campaign.sqlite').is_file())
    def test_regular_database_and_sidecars_still_pass(self):
        for name in ('campaign.sqlite','campaign.sqlite-wal','campaign.sqlite-shm','campaign.sqlite-journal'):
            (self.root/name).write_bytes(b'synthetic-storage-test')
        self.c._database_paths()
    def test_hardlinked_main_database_is_still_rejected(self):
        main=self.root/'campaign.sqlite';main.write_bytes(b'db');os.link(main,self.root/'hardlink')
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_DATABASE_FILE'):self.c._database_paths()
    def test_hardlinked_sidecar_is_still_rejected(self):
        wal=self.root/'campaign.sqlite-wal';wal.write_bytes(b'wal');os.link(wal,self.root/'hardlink')
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_DATABASE_FILE'):self.c._database_paths()
    def test_nonregular_sidecar_is_still_rejected(self):
        (self.root/'campaign.sqlite-wal').mkdir()
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_DATABASE_FILE'):self.c._database_paths()

class CampaignSidecarPosix(CampaignSidecarRace):
    # No inherited-count duplication in the explicit POSIX scope.
    test_historical_guard_reproduces_real_missing_sidecar_race=None
    test_current_no_follow_guard_survives_same_real_race=None
    test_regular_database_and_sidecars_still_pass=None
    test_hardlinked_main_database_is_still_rejected=None
    test_hardlinked_sidecar_is_still_rejected=None
    test_nonregular_sidecar_is_still_rejected=None
    def test_symlink_sidecar_is_still_rejected(self):
        target=self.root/'foreign';target.write_bytes(b'foreign')
        (self.root/'campaign.sqlite-wal').symlink_to(target)
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_DATABASE_SYMLINK'):self.c._database_paths()
    def test_fifo_sidecar_is_still_rejected(self):
        os.mkfifo(self.root/'campaign.sqlite-wal')
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_DATABASE_FILE'):self.c._database_paths()

if __name__=='__main__':unittest.main(verbosity=2)
