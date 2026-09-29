from h7_helpers import *
import subprocess,signal,time
class Files(Temp):
 def test_exact_read(self):
  (self.root/'a').write_bytes(b'hello');self.assertEqual(regular_bytes(self.root,'a'),b'hello')
 def test_hash_bytes(self):self.assertEqual(identity(b'abc'),hashlib.sha256(b'abc').hexdigest())
 def test_nonbyte_hash_rejected(self):self.error('H7_BYTES_REQUIRED',identity,'abc')
 def test_symlink_file(self):
  (self.root/'a').write_text('x');(self.root/'b').symlink_to('a');self.error('H7_FILE_ACCESS',regular_bytes,self.root,'b')
 def test_parent_symlink(self):
  (self.root/'d').mkdir();(self.root/'l').symlink_to('d',target_is_directory=True);self.error('H7_LINKED_DIRECTORY',inventory,self.root)
 def test_hardlink(self):
  (self.root/'a').write_text('x');os.link(self.root/'a',self.root/'b');self.error('H7_UNSAFE_FILE',regular_bytes,self.root,'a')
 def test_fifo(self):
  os.mkfifo(self.root/'fifo');self.error('H7_UNSAFE_FILE',regular_bytes,self.root,'fifo')
 def test_file_limit(self):
  (self.root/'a').write_bytes(b'abc');self.error('H7_FILE_LIMIT',regular_bytes,self.root,'a',2)
 def test_path_escape(self):
  with self.assertRaises(ContractError):regular_bytes(self.root,'../a')
 def test_copy_exact(self):
  (self.root/'in').mkdir();(self.root/'in/a').write_text('x');r=inventory(self.root/'in');copy_verified(self.root/'in',self.root/'out',r);self.assertEqual(inventory(self.root/'out'),r)
 def test_copy_changed(self):
  (self.root/'in').mkdir();(self.root/'in/a').write_text('x');r=inventory(self.root/'in');(self.root/'in/a').write_text('y');self.error('H7_COPY_CHANGED',copy_verified,self.root/'in',self.root/'out',r)
 def test_copy_no_overwrite(self):
  (self.root/'out').mkdir()
  with self.assertRaises(FileExistsError):copy_verified(self.root,self.root/'out',[])
 def test_duplicate_ids(self):self.error('H7_TEST_DUPLICATE',exact_ids,('a','a'),'H7_TEST')
 def test_nonfinite_json(self):
  with self.assertRaises(ContractError):strict_object(b'{"v":NaN}')
 def test_duplicate_json(self):
  with self.assertRaises(ContractError):strict_object(b'{"v":1,"v":2}')
 def test_total_limit(self):
  (self.root/'a').write_text('too long');self.error('H7_INVENTORY_LIMIT',inventory,self.root,max_total=1)

class Runtime(Temp):
 def setup_program(self,code,timeout=10,max_log=1024*1024):
  inp=self.root/'in';inp.mkdir();(inp/'data.txt').write_text('input');p=make_program(self.root/'tool.py',code,timeout=timeout,max_log=max_log);return inp,p
 def run_it(self,code,**kw):
  inp,p=self.setup_program(code,**kw);return run_trusted(p,inp,self.root/'out')
 def test_success_actual(self):
  r=self.run_it("import os;from pathlib import Path;Path(os.environ['BIE_OUTPUT_ROOT'],'v').write_text('hello')")
  self.assertIsNone(r['error']);self.assertEqual(len(r['outputs']),1);self.assertFalse(r['kernel_isolated'])
 def test_nonzero(self):self.assertEqual(self.run_it('raise SystemExit(2)')['error'],'NONZERO_EXIT')
 def test_timeout(self):self.assertEqual(self.run_it('import time;time.sleep(3)',timeout=1)['error'],'TIMEOUT')
 def test_log_limit(self):self.assertEqual(self.run_it("print('x'*10000)",max_log=256)['error'],'OUTPUT_LIMIT')
 def test_input_mutation(self):self.assertEqual(self.run_it("import os;from pathlib import Path;Path(os.environ['BIE_INPUT_ROOT'],'data.txt').write_text('changed')")['error'],'INPUT_CHANGED')
 def test_program_hash(self):
  inp,p=self.setup_program('pass');(self.root/'tool.py').write_text('print(1)');self.error('H7_PROGRAM_CHANGED',run_trusted,p,inp,self.root/'out')
 def test_cancellation_before(self):
  from threading import Event
  inp,p=self.setup_program('pass');e=Event();e.set();self.error('H7_CANCELLED_BEFORE_START',run_trusted,p,inp,self.root/'out',cancel=e)
 def test_environment_no_secret(self):
  os.environ['H7_FAKE_SECRET']='CANARY'
  try:r=self.run_it("import os;assert 'H7_FAKE_SECRET' not in os.environ;assert os.environ['PYTHONHASHSEED']=='0'")
  finally:os.environ.pop('H7_FAKE_SECRET',None)
  self.assertIsNone(r['error'])
 def test_log_hash(self):
  r=self.run_it("print('exact')");self.assertEqual(r['stdout_sha256'],identity(b'exact\n'))
 def test_execution_ids_independent(self):
  inp,p=self.setup_program('pass');a=run_trusted(p,inp,self.root/'a');b=run_trusted(p,inp,self.root/'b');self.assertNotEqual(a['execution_id'],b['execution_id'])
 def test_output_never_in_input(self):
  inp,p=self.setup_program('pass');self.error('H7_OUTPUT_INPUT_OVERLAP',run_trusted,p,inp,inp/'out')
 def test_program_requires_script(self):
  with self.assertRaises(ContractError):Program('p',('/usr/bin/python','-c','pass'),'a'*64,'/tmp/f','b'*64)
 def test_native_missing_checkout(self):
  p=NativeWorkerProfile((dict(path='missing',sha256='a'*64,bytes=1),),'a'*64,'b'*64)
  self.error('H7_NATIVE_CHECKOUT_CHANGED',native_worker,self.root,p,('/usr/bin/true',),self.root,output=self.root/'out')
 def test_native_no_false_proof(self):
  p=NativeWorkerProfile((dict(path='p',sha256='a'*64,bytes=1),),'a'*64,'b'*64)
  self.error('H7_NATIVE_PROOF_SCHEMA',validate_kernel_proof,{'kernel_enforced':True},p)
 def test_native_controls_strict_bool(self):
  p=NativeWorkerProfile((dict(path='p',sha256='a'*64,bytes=1),),'a'*64,'b'*64)
  self.error('H7_NATIVE_CONTROL_MISSING',validate_kernel_proof,{'schema_version':'bie.linux-worker-proof.v1','kernel_enforced':1},p)

class ToolIdentity(Temp):
    def test_incremental_digest(self):
        p=self.root/'tool';p.write_bytes(b'abcd'*10000);r=tool_identity(p)
        self.assertEqual(r['sha256'],identity(p.read_bytes()));self.assertEqual(r['bytes'],40000)
    def test_limit(self):
        p=self.root/'tool';p.write_bytes(b'abcd');self.error('H7_TOOL_LIMIT',tool_identity,p,3)
    def test_actual_node_program(self):
        import shutil
        exe=Path(shutil.which('node')).resolve();script=self.root/'worker.js'
        script.write_text("const fs=require('fs');fs.writeFileSync(process.env.BIE_OUTPUT_ROOT+'/result.txt','node actual execution');")
        p=Program('node-diagnostic',(str(exe),str(script)),tool_identity(exe)['sha256'],str(script),identity(script.read_bytes()))
        inp=self.root/'in';inp.mkdir();(inp/'source').write_text('input');r=run_trusted(p,inp,self.root/'out')
        self.assertIsNone(r['error']);self.assertEqual((self.root/'out/result.txt').read_text(),'node actual execution');self.assertFalse(r['kernel_isolated'])
