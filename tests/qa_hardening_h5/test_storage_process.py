from h5_helpers import *
import os,stat,time
from bie.qa.media_runtime_v2.storage import *
from bie.qa.media_runtime_v2.process import capture,pipe
class Storage(Case):
    def seed(self,data=b'hello'):
        return ref(self.root,'media/a.bin',data,'a',True)
    def test_snapshot_exact_bytes_and_cleanup(self):
        r=self.seed(b'ab'*7000)
        with snapshot(self.root,r,chunk_bytes=4096) as (p,m):self.assertEqual(p.read_bytes(),b'ab'*7000);self.assertTrue(verify_chunk_manifest(m));dest=p
        self.assertFalse(dest.exists())
    def test_large_input_exceeds_old_store_without_truncation(self):
        r=self.seed(b'x'*(17*1024**2))
        with snapshot(self.root,r) as (p,m):self.assertEqual(m['bytes'],17*1024**2);self.assertEqual(len(m['chunks']),17);self.assertEqual(hash_file(p)[0],r.sha256)
    def test_hash_tamper(self):
        r=self.seed();(self.root/r.path).write_bytes(b'jello')
        with self.assertRaisesRegex(ContractError,'H5_INPUT_HASH'):
            with snapshot(self.root,r):pass
    def test_size_tamper(self):
        r=self.seed();(self.root/r.path).write_bytes(b'hi')
        with self.assertRaisesRegex(ContractError,'H5_INPUT_SIZE'):
            with snapshot(self.root,r):pass
    def test_budget(self):
        r=self.seed()
        with self.assertRaisesRegex(ContractError,'H5_INPUT_BUDGET'):
            with snapshot(self.root,r,maximum=4):pass
    def test_leaf_symlink(self):
        r=self.seed();(self.root/'copy').write_bytes(b'hello');(self.root/r.path).unlink();(self.root/r.path).symlink_to(self.root/'copy')
        with self.assertRaises(ContractError):
            with snapshot(self.root,r):pass
    def test_ancestor_symlink(self):
        r=self.seed();(self.root/'media').rename(self.root/'elsewhere');(self.root/'media').symlink_to(self.root/'elsewhere',target_is_directory=True)
        with self.assertRaises(ContractError):
            with snapshot(self.root,r):pass
    def test_hardlink(self):
        r=self.seed();os.link(self.root/r.path,self.root/'alias')
        with self.assertRaisesRegex(ContractError,'H5_REGULAR_SINGLE_LINK_REQUIRED'):
            with snapshot(self.root,r):pass
    def test_fifo(self):
        (self.root/'pipe').parent.mkdir(exist_ok=True);os.mkfifo(self.root/'pipe')
        with self.assertRaisesRegex(ContractError,'H5_REGULAR_SINGLE_LINK_REQUIRED'):open_confined(self.root,'pipe')
    def test_unknown_role(self):
        with self.assertRaises(ContractError):StreamArtifact('x','a','1'*64,1,'trusted-secret')
    def test_snapshot_is_independent_from_later_path_change(self):
        r=self.seed()
        with snapshot(self.root,r) as (p,m):(self.root/r.path).write_bytes(b'world');self.assertEqual(p.read_bytes(),b'hello')
    def test_tool_identity(self):
        t=tool('ffprobe');self.assertTrue(t.verify())
        with self.assertRaises(ContractError):replace(t,sha256='0'*64).verify()
    def test_rehashed_gap_manifest(self):
        r=self.seed(b'1'*9000)
        with snapshot(self.root,r,chunk_bytes=4096) as (_,m):pass
        m['chunks'][1]['offset']+=1;m['inventory_digest']=digest({k:v for k,v in m.items() if k!='inventory_digest'})
        with self.assertRaisesRegex(ContractError,'H5_CHUNK_COVERAGE'):verify_chunk_manifest(m)
    def test_rehashed_short_interior_chunk(self):
        r=self.seed(b'1'*9000)
        with snapshot(self.root,r,chunk_bytes=4096) as (_,m):pass
        m['chunks'][0]['bytes']-=1;m['inventory_digest']=digest({k:v for k,v in m.items() if k!='inventory_digest'})
        with self.assertRaisesRegex(ContractError,'H5_SHORT_INTERIOR_CHUNK'):verify_chunk_manifest(m)
    def test_manifest_digest(self):
        r=self.seed()
        with snapshot(self.root,r) as (_,m):pass
        m['bytes']+=1
        with self.assertRaisesRegex(ContractError,'H5_CHUNK_MANIFEST_DIGEST'):verify_chunk_manifest(m)
class Processes(Case):
    def test_actual_stdout(self):self.assertEqual(capture([sys.executable,'-I','-c','print(42)']),b'42\n')
    def test_nonzero(self):
        with self.assertRaisesRegex(ContractError,'H5_PROCESS_FAILED'):capture([sys.executable,'-I','-c','raise SystemExit(7)'])
    def test_timeout(self):
        with self.assertRaisesRegex(ContractError,'H5_PROCESS_TIMEOUT'):capture([sys.executable,'-I','-c','import time;time.sleep(9)'],timeout=1)
    def test_output_budget(self):
        with self.assertRaisesRegex(ContractError,'H5_PROCESS_OUTPUT_BUDGET'):capture([sys.executable,'-I','-c','print("x"*1000)'],output_limit=100)
    def test_stderr_budget(self):
        with self.assertRaisesRegex(ContractError,'H5_PROCESS_LOG_BUDGET'):
            with pipe([sys.executable,'-I','-c','import sys;sys.stderr.write("x"*100000)'],stderr_limit=32) as h:h['read'](1)
    def test_unconsumed_output(self):
        with self.assertRaisesRegex(ContractError,'H5_PROCESS_UNCONSUMED_OUTPUT'):
            with pipe([sys.executable,'-I','-c','print(12345)']) as h:h['read'](1)
    def test_no_shell_or_inherited_secret(self):
        os.environ['H5_SYNTHETIC_SECRET']='NOT_A_REAL_SECRET'
        try:self.assertEqual(capture([sys.executable,'-I','-c','import os;print(os.getenv("H5_SYNTHETIC_SECRET"))']),b'None\n')
        finally:del os.environ['H5_SYNTHETIC_SECRET']
    def test_explicit_nonzero_record(self):
        with pipe([sys.executable,'-I','-c','raise SystemExit(4)'],allow_nonzero=True) as h:h['read'](1)
        self.assertEqual(h['exit_code'],4)

class NativeLinkImport(Case):
    def test_explicit_import_preserves_linked_original(self):
        r=ref(self.root,'source.mp4',b'NATIVE_LINK_FIXTURE','video',True);os.link(self.root/r.path,self.root/'alias');d=self.root/'copied.mp4'
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_LINK_IMPORT_OPT_IN'):import_native_output(self.root,r,d)
        result=import_native_output(self.root,r,d,allow_linked_native_output=True)
        self.assertEqual(d.stat().st_nlink,1);self.assertEqual((self.root/'alias').read_bytes(),b'NATIVE_LINK_FIXTURE');self.assertFalse(result['original_mutated'])
        with snapshot(self.root,StreamArtifact(**result['imported'])) as (p,m):self.assertEqual(p.read_bytes(),b'NATIVE_LINK_FIXTURE')
    def test_bad_native_import_hash_cannot_publish(self):
        r=ref(self.root,'source.mp4',b'NATIVE_LINK_FIXTURE','video',True);os.link(self.root/r.path,self.root/'alias');d=self.root/'copied.mp4'
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_IMPORT_HASH'):import_native_output(self.root,replace(r,sha256='0'*64),d,allow_linked_native_output=True)
        self.assertFalse(d.exists());self.assertFalse(list(self.root.glob('.bie-h5-import-*')))
