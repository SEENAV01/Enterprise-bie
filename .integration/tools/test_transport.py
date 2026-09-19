"""Control-plane tests; independent of BIE runtime and its acceptance tests."""
import base64, copy, hashlib, io, json, struct, subprocess, tarfile, tempfile, unittest, zlib
from pathlib import Path
from restore_capsule import unpack_capsule, restore, sha
from import_plan import allowed_path, preflight_plan, apply, verify_tree, BASE
from ci_import import require_results
from publish_verified import verify_commit_chain

class Paths(unittest.TestCase):
    def test_canonical_source(self):self.assertEqual(allowed_path('bie/compiler/test.py'),'bie/compiler/test.py')
    def test_original_archive(self):self.assertEqual(allowed_path('backups/ingested/A (1).zip'),'backups/ingested/A (1).zip')
    def test_readme(self):self.assertEqual(allowed_path('README.md'),'README.md')
    def test_absolute(self):self.assertRaises(ValueError,allowed_path,'/etc/passwd')
    def test_traversal(self):self.assertRaises(ValueError,allowed_path,'bie/../outside')
    def test_git_control(self):self.assertRaises(ValueError,allowed_path,'bie/.git/config')
    def test_windows_separator(self):self.assertRaises(ValueError,allowed_path,'bie\\x')
    def test_noncanonical_slashes(self):self.assertRaises(ValueError,allowed_path,'bie//x')
    def test_workflow_overwrite(self):self.assertRaises(ValueError,allowed_path,'.github/workflows/unsafe.yml')
    def test_empty(self):self.assertRaises(ValueError,allowed_path,'')

class Capsule(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def archive(self,entries):
        p=self.root/'a.tar.xz'
        with tarfile.open(p,'w:xz') as t:
            for name,data,kind in entries:
                m=tarfile.TarInfo(name);m.type=kind;m.size=len(data)
                if kind in (tarfile.SYMTYPE,tarfile.LNKTYPE):m.linkname='/etc/passwd';m.size=0
                t.addfile(m,io.BytesIO(data) if m.isfile() else None)
        return p
    def test_hash_mismatch(self):
        p=self.archive([('summary.json',b'{}',tarfile.REGTYPE)])
        self.assertRaisesRegex(ValueError,'SHA256',unpack_capsule,p,self.root/'out','0'*64)
    def test_data_only_roundtrip(self):
        p=self.archive([('summary.json',b'{}',tarfile.REGTYPE)])
        unpack_capsule(p,self.root/'out',sha(p.read_bytes()));self.assertEqual((self.root/'out/summary.json').read_bytes(),b'{}')
    def test_traversal(self):
        p=self.archive([('../evil',b'x',tarfile.REGTYPE)])
        self.assertRaises(ValueError,unpack_capsule,p,self.root/'out',sha(p.read_bytes()))
    def test_symlink(self):
        p=self.archive([('summary.json',b'',tarfile.SYMTYPE)])
        self.assertRaises(ValueError,unpack_capsule,p,self.root/'out',sha(p.read_bytes()))
    def test_hardlink(self):
        p=self.archive([('summary.json',b'',tarfile.LNKTYPE)])
        self.assertRaises(ValueError,unpack_capsule,p,self.root/'out',sha(p.read_bytes()))
    def test_device(self):
        p=self.archive([('summary.json',b'',tarfile.CHRTYPE)])
        self.assertRaises(ValueError,unpack_capsule,p,self.root/'out',sha(p.read_bytes()))
    def test_duplicate_member(self):
        p=self.archive([('summary.json',b'{}',tarfile.REGTYPE)]*2)
        self.assertRaises(ValueError,unpack_capsule,p,self.root/'out',sha(p.read_bytes()))
    def test_unknown_member(self):
        p=self.archive([('execute.py',b'pass',tarfile.REGTYPE)])
        self.assertRaises(ValueError,unpack_capsule,p,self.root/'out',sha(p.read_bytes()))
    def recipe(self,kind='raw'):
        p=self.root/'data';(p/'raw').mkdir(parents=True);b=b'exact original bytes';key=sha(b);(p/'raw'/key).write_bytes(b)
        recipes={key:{'kind':kind,'size':len(b),'raw':key}}
        (p/'recipes.json').write_text(json.dumps(recipes));(p/'top_files.json').write_text(json.dumps([{'name':'original.txt','sha256':key,'bytes':len(b)}]));return p,key,b
    def test_restore_original(self):
        p,key,b=self.recipe();r=restore(p,self.root/'restored');self.assertTrue(r['all_originals_exact']);self.assertEqual((self.root/'restored/objects'/key).read_bytes(),b)
    def test_raw_corruption(self):
        p,key,b=self.recipe();(p/'raw'/key).write_bytes(b'changed');self.assertRaises(ValueError,restore,p,self.root/'restored')
    def test_missing_raw(self):
        p,key,b=self.recipe();(p/'raw'/key).unlink();self.assertRaises(ValueError,restore,p,self.root/'restored')
    def test_recipe_unknown(self):
        p,key,b=self.recipe('execute');self.assertRaises(ValueError,restore,p,self.root/'restored')
    def test_recursive_cycle(self):
        p,key,b=self.recipe();(p/'recipes.json').write_text(json.dumps({key:{'kind':'zip','size':len(b),'parts':[['o',key]]}}));self.assertRaises(ValueError,restore,p,self.root/'restored')
    def test_size_mismatch(self):
        p,key,b=self.recipe();(p/'top_files.json').write_text(json.dumps([{'name':'original.txt','sha256':key,'bytes':1}]));self.assertRaises(ValueError,restore,p,self.root/'restored')
    def test_duplicate_original_name(self):
        p,key,b=self.recipe();rows=json.loads((p/'top_files.json').read_text());(p/'top_files.json').write_text(json.dumps(rows*2));self.assertRaises(ValueError,restore,p,self.root/'restored')

class Plan(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name);self.root=self.p/'repo';self.root.mkdir();self.objects=self.p/'objects';self.objects.mkdir()
        self.data=b'new source\n';self.key=sha(self.data);(self.objects/self.key).write_bytes(self.data)
        self.row={'path':'bie/example.py','sha256':self.key,'before_sha256':None,'bytes':len(self.data),'mode':'100644','git_blob_sha1':hashlib.sha1(b'blob '+str(len(self.data)).encode()+b'\0'+self.data).hexdigest()}
        self.plan={'schema_version':'bie.canonical-adoption-plan.v1','base_commit':BASE,'phases':[{'section':s,'operations':[self.row] if s=='VIS' else []} for s in ['VIS','ANI','DSL','COMP']],'operation_count':1,'supplied_files':1}
    def test_valid_plan(self):self.assertEqual(preflight_plan(self.root,self.plan,self.objects),{'bie/example.py':self.key})
    def test_wrong_base(self):self.plan['base_commit']='0'*40;self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_wrong_order(self):self.plan['phases'].reverse();self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_collision(self):
        (self.root/'bie').mkdir();(self.root/'bie/example.py').write_text('old');self.assertRaisesRegex(ValueError,'BASE_COLLISION',preflight_plan,self.root,self.plan,self.objects)
    def test_correct_before_hash(self):
        (self.root/'bie').mkdir();(self.root/'bie/example.py').write_text('old');self.row['before_sha256']=sha(b'old');preflight_plan(self.root,self.plan,self.objects)
    def test_corrupt_object(self):
        (self.objects/self.key).write_bytes(b'changed');self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_missing_object(self):
        (self.objects/self.key).unlink();self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_duplicate_operation(self):
        self.plan['phases'][0]['operations'].append(self.row);self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_wrong_mode(self):self.row['mode']='120000';self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_wrong_count(self):self.plan['operation_count']=2;self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_parent_symlink(self):
        (self.root/'bie').symlink_to(self.objects,target_is_directory=True);self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)
    def test_nonregular_destination(self):
        (self.root/'bie/example.py').mkdir(parents=True);self.assertRaises(ValueError,preflight_plan,self.root,self.plan,self.objects)

class Gates(unittest.TestCase):
    def setUp(self):
        self.tests={'summary':{'passed':True,'tests_run':6485,'failed_files':0,'failures':0,'errors':0,'skipped':0}}
        self.preservation={'passed':True,'errors':[],'supplied_files_verified':386,'source_member_mappings_verified':6014,'unique_zip_archives_verified':435,'nested_member_occurrences_verified':83616}
    def test_complete(self):require_results(self.tests,self.preservation)
    def test_missing_tests(self):self.tests['summary']['tests_run']=6484;self.assertRaises(ValueError,require_results,self.tests,self.preservation)
    def test_skips_block(self):self.tests['summary']['skipped']=1;self.assertRaises(ValueError,require_results,self.tests,self.preservation)
    def test_failures_block(self):self.tests['summary']['failures']=1;self.assertRaises(ValueError,require_results,self.tests,self.preservation)
    def test_missing_input(self):self.preservation['supplied_files_verified']=385;self.assertRaises(ValueError,require_results,self.tests,self.preservation)
    def test_missing_nested_members(self):self.preservation['nested_member_occurrences_verified']=0;self.assertRaises(ValueError,require_results,self.tests,self.preservation)
    def test_preservation_error(self):self.preservation['errors']=['corrupt'];self.assertRaises(ValueError,require_results,self.tests,self.preservation)

class GitData(unittest.TestCase):
    def test_four_phase_commits_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);root=p/'repo';root.mkdir();objects=p/'restored/objects';objects.mkdir(parents=True);cap=p/'cap';cap.mkdir()
            def git(*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL).decode().strip()
            git('init','-q');git('config','user.name','Transport Test');git('config','user.email','transport@example.invalid');git('config','core.autocrlf','false')
            (root/'README.md').write_text('baseline\n');git('add','README.md');git('commit','-qm','baseline');base=git('rev-parse','HEAD')
            plan={'schema_version':'bie.canonical-adoption-plan.v1','base_commit':BASE,'operation_count':4,'supplied_files':0,'phases':[]}
            for name in ('VIS','ANI','DSL','COMP'):
                data=(name+'\n').encode();key=sha(data);(objects/key).write_bytes(data)
                row={'path':'bie/'+name+'.py','sha256':key,'before_sha256':None,'bytes':len(data),'mode':'100644','git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}
                plan['phases'].append({'section':name,'operations':[row]})
            (cap/'plan.json').write_text(json.dumps(plan));result=apply(root,cap,p/'restored');self.assertEqual(len(result['phases']),4)
            self.assertEqual(len(verify_commit_chain(root,base,git('rev-parse','HEAD'),plan)),4);self.assertEqual(verify_tree(root,'HEAD',plan),4)
            (root/'bie/VIS.py').write_text('tampered');git('add','bie/VIS.py');git('commit','-qm','tampered')
            self.assertRaises(ValueError,verify_tree,root,'HEAD',plan);self.assertRaises(ValueError,verify_commit_chain,root,base,git('rev-parse','HEAD'),plan)

if __name__=='__main__':unittest.main(verbosity=2)
