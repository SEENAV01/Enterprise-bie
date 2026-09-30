import unittest,tempfile,shutil,subprocess,json
from pathlib import Path
from dataclasses import replace
from h5_support import *
from bie.evaluation.benchmarks.browser.served.admission import build_candidate
class H5010(unittest.TestCase):
 def test_manifest_has_module_mode(self):self.assertEqual(candidate()['load_mode'],'HTTP_MODULE_APP')
 def test_manifest_has_actual_files(self):self.assertEqual(len(candidate()['files']),7)
 def test_manifest_deterministic(self):self.assertEqual(candidate(),candidate())
 def test_relative_root_rejected(self):assert_error(self,lambda:build_candidate('relative'),'HTTP_IMPORT_ROOT_INVALID')
 def test_symlink_root_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'link';p.symlink_to(GAME,target_is_directory=True);assert_error(self,lambda:build_candidate(p),'HTTP_IMPORT_ROOT_INVALID')
 def test_symlink_asset_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'a.mjs';p.symlink_to(GAME/'main.mjs');assert_error(self,lambda:build_candidate(Path(t)),'HTTP_IMPORT_SYMLINK')
 def test_unsupported_file_not_silently_omitted(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'private.key';p.write_text('private');assert_error(self,lambda:build_candidate(Path(t)))
 def test_file_limit_enforced(self):assert_error(self,lambda:build_candidate(GAME,limits=replace(BrowserLimits(),max_file_bytes=1)),'HTTP_IMPORT_FILE_LIMIT')
 def test_missing_entrypoint_rejected(self):assert_error(self,lambda:build_candidate(GAME,entrypoint='missing.html'),'BROWSER_ENTRYPOINT_MISSING')
 def test_actual_node_module_execution_not_browser(self):
  cmd=['node','--input-type=module','-e',"import {equivalent} from './math.mjs';import {correct} from './feedback.mjs';console.log(JSON.stringify({yes:equivalent(1,2,2,4),no:equivalent(1,2,1,3),correct}));"]
  p=subprocess.run(cmd,cwd=GAME,capture_output=True,text=True,timeout=10);self.assertEqual(p.returncode,0,p.stderr)
  self.assertEqual(json.loads(p.stdout),{'yes':True,'no':False,'correct':'Correct. 1/2 = 2/4.'})

 def test_manifest_hashes_match_source(self):
  for row in candidate()["files"]:self.assertEqual(row["sha256"],hashlib.sha256((GAME/row["path"]).read_bytes()).hexdigest())
