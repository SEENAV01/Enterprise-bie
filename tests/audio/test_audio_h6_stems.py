import base64,hashlib,io,wave,unittest
import numpy as np
from bie.audio.pipeline_stems import canonicalize_stem_specs,decode_stems,stems_fingerprint
from bie.audio.tts_contract import AudioFormat
from bie.audio.common import AudioError

def wav(rate=22050,frames=2205):
 b=io.BytesIO(); a=(np.sin(np.arange(frames)*.05)*1000).astype('<i2')
 with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(a.tobytes())
 return b.getvalue()
def spec(role='music'):
 d=wav();return {'asset_id':'a1','role':role,'wav_b64':base64.b64encode(d).decode(),'wav_sha256':hashlib.sha256(d).hexdigest(),'start_sample':0,'trim_start':0,'trim_end':2205,'source_refs':['book:p1'],'rights_ref':'rights:test','gain_db':-20.0,'channel_map':'identity','pan':0.0,'repeat':1,'fade_in_samples':0,'fade_out_samples':0}
class T(unittest.TestCase):
 def test_valid(self): self.assertEqual(len(decode_stems([spec()],AudioFormat(22050,1))),1)
 def test_stable(self): self.assertEqual(stems_fingerprint([spec()]),stems_fingerprint([spec()]))
 def test_hash_tamper(self):
  x=spec();x['wav_sha256']='0'*64
  with self.assertRaises(AudioError):canonicalize_stem_specs([x])
 def test_rights_required(self):
  x=spec();x['rights_ref']=''
  with self.assertRaises(Exception):canonicalize_stem_specs([x])
 def test_refs_required(self):
  x=spec();x['source_refs']=[]
  with self.assertRaises(AudioError):canonicalize_stem_specs([x])
 def test_duplicate(self):
  with self.assertRaises(AudioError):canonicalize_stem_specs([spec(),spec()])
 def test_role(self):
  x=spec();x['role']='voice'
  with self.assertRaises(AudioError):canonicalize_stem_specs([x])
 def test_base64(self):
  x=spec();x['wav_b64']='***'
  with self.assertRaises(AudioError):canonicalize_stem_specs([x])
