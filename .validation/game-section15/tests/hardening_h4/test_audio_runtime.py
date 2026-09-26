import unittest,hashlib
from dataclasses import replace
from tests.hardening_h4.support import *
from bie.game_engine.runtime_quality_engine.audio_bridge import adapt_canonical_audio_handoff
from bie.game_engine.errors import GameContractError

class AudioRuntimeTests(unittest.TestCase):
 def test_real_browser_audio_user_activation_and_caption(self):
  from bie.game_engine.build_runtime_engine.sandbox import sandboxed_chromium
  from bie.game_engine.build_runtime_engine.contracts import BuildPolicy
  td,ws=build()
  try:
   runtime=ws.root/'dist/runtime';html=(runtime/'index.html').read_text().replace('<script type="module" src="./entry.js"></script>','');bundle=(runtime/'smoke-bundle.js').read_text()
   with sandboxed_chromium(BuildPolicy()) as (ctx,_,__):
    page=ctx.pages[0] if ctx.pages else ctx.new_page();page.set_content(html);page.evaluate(bundle)
    page.evaluate("""() => { globalThis.__audioPlayed=false; globalThis.Audio=class { constructor(url){this.url=url;this.preload='';this.volume=1;this.duration=.1;this.dataset={};this.listeners={};} addEventListener(k,f){this.listeners[k]=f;} play(){globalThis.__audioPlayed=true;return Promise.resolve();} }; }""")
    page.locator('[data-audio-control="play"]').click();self.assertTrue(page.evaluate('globalThis.__audioPlayed===true'));self.assertEqual(page.locator('#bie-game-captions').inner_text(),'یہ سبق حرکت کو سمجھاتا ہے۔');self.assertEqual(page.locator('#bie-game-captions').get_attribute('data-cue-id'),'cue:narration:1')
  finally:td.cleanup()

 def handoff(self):
  b=wav_bytes();sha=hashlib.sha256(b).hexdigest();return {'schema_version':'bie.audio.compiler-handoff/1','real_remotion_render_verified':False,'product_accepted':False,'compiler_h6':{'audio_assets':[{'asset_id':'audio:narration','public_path':'narration/a.wav','sha256':sha,'rights_ref':'rights:audio','source_refs':['source:book'],'reasoning_refs':['reason:audio']}],'audio_segments':[{'cue_id':'cue:1','asset_id':'audio:narration'}]},'narration_cues':[{'cue_id':'cue:1','text_ref':'text:narration:1','start_ms':0,'end_ms':100}]}, {'narration/a.wav':b}
 def test_canonical_audio_handoff(self):
  h,f=self.handoff();b=adapt_canonical_audio_handoff(h,f,level_id='level:1');self.assertEqual(b.cues[0].trigger_event,'level_start');self.assertEqual(b.rights[0][1],'rights:audio');self.assertEqual(b.timings[0][1:3],(0,100))
 def test_audio_hash_tamper_fails(self):
  h,f=self.handoff();f['narration/a.wav']=b'x';self.assertRaises(GameContractError,adapt_canonical_audio_handoff,h,f,level_id='level:1')
 def test_missing_rights_fails(self):
  h,f=self.handoff();h['compiler_h6']['audio_assets'][0]['rights_ref']='';self.assertRaises(GameContractError,adapt_canonical_audio_handoff,h,f,level_id='level:1')
 def test_runtime_controller_contains_playback(self):
  from bie.game_engine.compiler_engine.runtime_controller import compile_runtime_controller
  s=compile_runtime_controller(context()).content;self.assertIn('new Audio(url)',s);self.assertIn('playNarration',s);self.assertIn('bie-game-captions',s)
 def test_runtime_enforces_sync_and_ducking(self):
  from bie.game_engine.compiler_engine.runtime_controller import compile_runtime_controller
  s=compile_runtime_controller(context()).content;self.assertIn('GAME_AUDIO_SYNC_DRIFT',s);self.assertIn('duck_narration',s);self.assertIn('volume=.35',s)
 def test_asset_manifest_carries_rights(self):
  from bie.game_engine.compiler_engine.asset_manifest import compile_asset_manifest
  s=compile_asset_manifest(context()).content;self.assertIn('CC-BY-4.0',s);self.assertIn('rights:audio',s)
