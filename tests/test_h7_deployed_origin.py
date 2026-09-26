"""AUD-009: combined real origin and Chromium isolation must both work."""
import dataclasses
import json
import os
import unittest
from pathlib import Path
from bie.game_engine.build_runtime_engine.deployment import deployment_smoke
from tests.hardening_h3.support import built

class DeployedOriginAcceptance(unittest.TestCase):
    def test_native_origin_runs_inside_verified_sandbox(self):
        td,ctx,assets,ws=built()
        try:
            result=deployment_smoke(ws.root/'dist')
            out=os.environ.get('BIE_GAME_EVIDENCE')
            if out:
                (Path(out)/'DEPLOYED_ORIGIN.json').write_text(json.dumps(dataclasses.asdict(result),indent=2)+'\n')
            self.assertTrue(result.browser_origin_navigation_verified,result.origin_block_reason)
            self.assertIsNone(result.origin_block_reason)
            self.assertTrue(result.sandbox_evidence.no_new_privs)
            self.assertTrue(result.sandbox_evidence.renderer_seccomp)
            self.assertFalse(result.sandbox_evidence.no_sandbox_flag_present)
            self.assertNotEqual(result.sandbox_evidence.uid,0)
        finally:
            td.cleanup()
