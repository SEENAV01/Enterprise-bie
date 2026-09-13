"""Preservation-gate regressions: missing provenance and byte corruption block."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts.verify_ingested_archives import audit


class IngestedArchiveIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for p in ('backups/ingested','bie/pedagogy','manifests'):
            (self.root/p).mkdir(parents=True)
        sha=lambda b:hashlib.sha256(b).hexdigest()
        source=b'VALUE=1\n'; canonical=b'VALUE=2\n'
        archive=self.root/'backups/ingested/example.zip'
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr('source.py',source);z.writestr('__init__.py',b'')
        (self.root/'bie/pedagogy/example.py').write_bytes(canonical)
        self.manifest=dict(archive_count=1,member_count=2,
            archives=[dict(archive='example.zip',backup_path='backups/ingested/example.zip',archive_sha256=sha(archive.read_bytes()),member_count=2)],
            members=[dict(archive='example.zip',member='source.py',state='MIGRATED',original_sha256=sha(source),canonical_path='bie/pedagogy/example.py',canonical_sha256=sha(canonical)),
                     dict(archive='example.zip',member='__init__.py',state='ARCHIVED_EVIDENCE',original_sha256=sha(b''),canonical_path=None,transformation='Preserved inside original ZIP')])
        self.save()

    def save(self):
        (self.root/'manifests/example_integration_001.json').write_text(json.dumps(self.manifest))

    def test_transformed_source_and_original_initializer_are_preserved(self):
        report=audit(self.root)
        self.assertTrue(report['passed'])
        self.assertEqual(report['original_members_checked'],2)

    def test_modified_canonical_source_is_rejected(self):
        (self.root/'bie/pedagogy/example.py').write_text('CORRUPTED')
        self.assertFalse(audit(self.root)['passed'])

    def test_silently_dropped_member_provenance_is_rejected(self):
        self.manifest['members'].pop()
        self.manifest['member_count']=1
        self.manifest['archives'][0]['member_count']=1
        self.save()
        self.assertFalse(audit(self.root)['passed'])
