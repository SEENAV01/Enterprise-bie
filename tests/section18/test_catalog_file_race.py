"""H1-005 catalogue inventory: real volatile sidecar and alias negative controls."""
from pathlib import Path
from dataclasses import replace
import os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from apps.operator.catalog_budget import CatalogBudget
from apps.operator.contracts import OperatorError
CHILD='''import sqlite3,sys
db=sqlite3.connect(sys.argv[1],isolation_level=None)
db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE probe(value TEXT)')
db.execute("INSERT INTO probe VALUES('SYNTHETIC_TEST')")
print('READY',flush=True)
if sys.stdin.readline()!='CLOSE\\n':raise SystemExit(3)
db.close();print('CLOSED',flush=True)
'''
class CatalogFileSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bie-s18-catalog-files-');self.root=Path(self.tmp.name)
        self.path=self.root/'operator.sqlite3';self.budget=CatalogBudget()
    def tearDown(self):self.tmp.cleanup()
    def test_actual_sqlite_last_close_during_inventory_has_no_false_capacity_error(self):
        process=subprocess.Popen([sys.executable,'-B','-c',CHILD,str(self.path)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        cuts=[];wal=self.path.with_name(self.path.name+'-wal')
        try:
            self.assertEqual(process.stdout.readline().strip(),'READY');self.assertTrue(wal.is_file())
            def trace(frame,event,arg):
                if event=='call' and frame.f_code is Path.stat.__code__:
                    caller=frame.f_back
                    # Pause before the actual stat following the old exists /
                    # is_file check, or before repaired no-follow single stat.
                    if frame.f_locals.get('self')==wal and caller and caller.f_code is CatalogBudget.files.__code__ and not cuts:
                        stdout,stderr=process.communicate('CLOSE\n',timeout=5)
                        self.assertEqual(process.returncode,0,stderr);self.assertEqual(stdout.strip(),'CLOSED')
                        self.assertFalse(wal.exists());cuts.append('REAL_LAST_CLOSE')
                return trace
            original=sys.gettrace();sys.settrace(trace)
            try:self.budget.files(self.path)
            finally:sys.settrace(original)
            self.assertEqual(cuts,['REAL_LAST_CLOSE']);self.assertTrue(self.path.is_file())
        finally:
            if process.poll() is None:process.kill()
            process.wait(timeout=5)
            for stream in (process.stdin,process.stdout,process.stderr):stream.close()
    def test_hardlinked_main_is_rejected_before_sqlite_open(self):
        self.path.write_bytes(b'SYNTHETIC_TEST');os.link(self.path,self.root/'alias')
        with self.assertRaisesRegex(OperatorError,'storage_link_rejected'):self.budget.files(self.path)
    def test_hardlinked_sidecar_is_rejected_before_sqlite_open(self):
        wal=self.path.with_name(self.path.name+'-wal');wal.write_bytes(b'SYNTHETIC_TEST');os.link(wal,self.root/'alias')
        with self.assertRaisesRegex(OperatorError,'storage_link_rejected'):self.budget.files(self.path)
    def test_missing_startup_files_are_valid_and_not_fabricated(self):
        self.budget.files(self.path);self.assertFalse(self.path.exists())
    def test_ordinary_bounded_files_are_valid(self):
        self.path.write_bytes(b'SYNTHETIC_TEST');self.budget.files(self.path)
    def test_exact_database_capacity_and_one_byte_over_fail_closed(self):
        budget=replace(self.budget,max_database_bytes=8)
        self.path.write_bytes(b'12345678');budget.files(self.path)
        self.path.write_bytes(b'123456789')
        with self.assertRaisesRegex(OperatorError,'catalog_storage_capacity_reached'):budget.files(self.path)
        self.assertEqual(self.path.read_bytes(),b'123456789')
    def test_exact_wal_capacity_and_one_byte_over_fail_closed(self):
        budget=replace(self.budget,max_wal_bytes=4);wal=self.path.with_name(self.path.name+'-wal')
        wal.write_bytes(b'1234');budget.files(self.path)
        wal.write_bytes(b'12345')
        with self.assertRaisesRegex(OperatorError,'catalog_storage_capacity_reached'):budget.files(self.path)
        self.assertEqual(wal.read_bytes(),b'12345')
if __name__=='__main__':unittest.main(verbosity=2)

class CatalogUnlinkedDuringStat(unittest.TestCase):
    """CI run 41223280162: SQLite's last close landed between a stat's path lookup and its attribute read, so the sidecar
    was reported with st_nlink 0. The kernel window cannot be forced from Python, so the stat result is forged here; the
    real last close (missing file) is covered by CatalogFileSafety above."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bie-s18-catalog-nlink0-');self.root=Path(self.tmp.name)
        self.path=self.root/'operator.sqlite3';self.budget=CatalogBudget()
        self.path.write_bytes(b'SYNTHETIC_TEST')
    def tearDown(self):self.tmp.cleanup()
    def forged(self,name,nlink,mode=0o100600):
        real=Path.stat
        def fake(path,*a,**kw):
            if path.name==name:return os.stat_result((mode,1,1,nlink,0,0,14,0,0,0))
            return real(path,*a,**kw)
        return fake
    def test_a_sidecar_unlinked_during_the_stat_is_a_vanished_file(self):
        from unittest import mock
        with mock.patch.object(Path,'stat',self.forged('operator.sqlite3-wal',0)):self.budget.files(self.path)
    def test_a_hardlinked_sidecar_and_an_unlinked_main_database_stay_rejected(self):
        from unittest import mock
        with mock.patch.object(Path,'stat',self.forged('operator.sqlite3-wal',2)):
            with self.assertRaisesRegex(OperatorError,'storage_link_rejected'):self.budget.files(self.path)
        with mock.patch.object(Path,'stat',self.forged('operator.sqlite3',0)):
            with self.assertRaisesRegex(OperatorError,'storage_link_rejected'):self.budget.files(self.path)
        with mock.patch.object(Path,'stat',self.forged('operator.sqlite3-shm',0,mode=0o010600)):
            with self.assertRaisesRegex(OperatorError,'storage_link_rejected'):self.budget.files(self.path)
