from pathlib import Path
from dataclasses import fields
import json, unittest
from bie.qa.source_v2.models import Request, Source, Block, Output, Citation, Claim
from bie.qa.release_v2.contracts import ArtifactRef
ROOT=Path(__file__).resolve().parents[2]

class SchemaConsistencyTests(unittest.TestCase):
    def setUp(self):self.schema=json.loads((ROOT/'docs/qa_section16/batch002/request.schema.json').read_text())
    def test_root_required_fields_match_python_contract(self):
        self.assertEqual(set(self.schema['required']),{f.name for f in fields(Request)})
        self.assertFalse(self.schema['additionalProperties'])
    def test_nested_required_fields_match_python_contracts(self):
        for cls in (Source,Block,Output,Citation,Claim,ArtifactRef):
            with self.subTest(cls=cls.__name__):
                schema=self.schema['$defs'][cls.__name__]
                self.assertEqual(set(schema['required']),{f.name for f in fields(cls)})
                self.assertFalse(schema['additionalProperties'])
    def test_nonempty_critical_collections_declared(self):
        for name in ('sources','blocks','outputs','claims'):
            with self.subTest(name=name):self.assertEqual(self.schema['properties'][name]['minItems'],1)
