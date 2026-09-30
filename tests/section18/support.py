from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "productization" / "document_intelligence"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))

from structural_pdf_fixtures import hierarchy_pdf_with_outline
from bie.app_product.service import OperatorService


class AppProductCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.service = OperatorService(self.root)
        self.pdf = hierarchy_pdf_with_outline()

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def create(self, key="section18-fixture-1", name="Physics.pdf"):
        return self.service.create_run(self.pdf, key, name)

    def job_id(self, key="section18-fixture-1"):
        return self.create(key).job_id
