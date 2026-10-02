"""Finding H1-006 origin control: exact one-path adoption maintenance, no waiver."""
from pathlib import Path
import importlib.util,json,shutil,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('s18_campaign_origin_gate',ROOT/'scripts/verify_section17_adoption.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

class CampaignMaintenance(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bie-s18-campaign-origin-');self.root=Path(self.temp.name)
        self.original_root=gate.ROOT;gate.ROOT=self.root
        shutil.copytree(ROOT/gate.MAINTENANCE_DIR,self.root/gate.MAINTENANCE_DIR)
        self.document=self.root/gate.MAINTENANCE_DIR/'AMENDMENT.json'
        self.before=self.document.with_name('runtime.py.before')
    def tearDown(self):gate.ROOT=self.original_root;self.temp.cleanup()
    def test_only_the_pinned_campaign_replacement_is_authorized(self):
        self.assertEqual(gate.verified_maintenance(),{gate.CAMPAIGN_PATH:gate.CAMPAIGN_REPLACEMENT})
    def test_missing_maintenance_never_authorizes_new_source(self):
        self.document.unlink();self.assertEqual(gate.verified_maintenance(),{})
    def test_self_edited_replacement_hash_cannot_authorize_arbitrary_source(self):
        body=json.loads(self.document.read_text());body['replacement_sha256']='0'*64
        self.document.write_text(json.dumps(body))
        with self.assertRaisesRegex(ValueError,'MAINTENANCE_DOCUMENT_TAMPERED'):gate.verified_maintenance()
    def test_second_unreviewed_path_cannot_be_added(self):
        body=json.loads(self.document.read_text());body['additional_path']='bie/infrastructure/persistence.py'
        self.document.write_text(json.dumps(body))
        with self.assertRaisesRegex(ValueError,'MAINTENANCE_DOCUMENT_TAMPERED'):gate.verified_maintenance()
    def test_before_image_tampering_is_detected_independently(self):
        self.before.write_bytes(self.before.read_bytes()+b'# tampered\n')
        with self.assertRaisesRegex(ValueError,'MAINTENANCE_PREIMAGE_TAMPERED'):gate.verified_maintenance()
    def test_exact_lf_git_preimage_remains_valid_without_semantic_reconstruction(self):
        self.before.write_bytes(self.before.read_bytes().replace(b'\r\n',b'\n'))
        self.assertEqual(gate.verified_maintenance(),{gate.CAMPAIGN_PATH:gate.CAMPAIGN_REPLACEMENT})
