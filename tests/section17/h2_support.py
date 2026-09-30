"""Authored local test fixtures; never native BIE or reviewer evidence."""
from pathlib import Path
from functools import lru_cache
import atexit, tempfile, subprocess, hashlib, copy
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.av.service import collect_and_evaluate
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'bie/compiler/render_contracts.py'
_TMP=tempfile.TemporaryDirectory(prefix='bie-h2-tests-');atexit.register(_TMP.cleanup)
TD=Path(_TMP.name)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def policy(**kw):
    p={'schema_version':'av-policy-2','width':64,'height':36,'expected_frames':8,'fps':'4',
       'require_audio':True,'require_captions':False,'caption_text_sha256':None,'narration_intervals_s':[[0,2]],
       'max_dark_fraction':0.1,'max_identical_run_s':10,'max_silent_fraction':0.05,'max_clipped_fraction':0.001,
       'min_caption_coverage':0.95,'min_narration_activity':0.9,'sync_tolerance_s':0.01}
    p.update(kw);return p
@lru_cache(None)
def media(kind='tone'):
    p=TD/(kind+('.mp4' if kind=='mp4' else '.mkv'))
    if kind=='corrupt':p.write_bytes(b'not a media file');return p
    v='color=c=black:size=64x36:rate=4:duration=2' if kind=='black' else 'testsrc2=size=64x36:rate=4:duration=2'
    cmd=['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',v]
    if kind not in ('noaudio','mp4'):
        a={'silence':'anullsrc=sample_rate=16000:channel_layout=mono:d=2',
           'clip':'aevalsrc=1:s=16000:d=2','antiphase':'aevalsrc=0.1|-0.1:s=16000:d=2'}.get(kind,'sine=frequency=440:sample_rate=16000:duration=2')
        cmd+=['-f','lavfi','-i',a]
    cmd+=['-c:v','libx264','-threads','1','-pix_fmt','yuv420p']
    if kind not in ('noaudio','mp4'):cmd+=['-c:a','pcm_s16le']
    cmd+=['-y',str(p)];subprocess.run(cmd,check=True,capture_output=True,timeout=20);return p
@lru_cache(None)
def _report(kind):
    p=policy(require_audio=kind!='mp4',narration_intervals_s=[] if kind=='mp4' else [[0,2]])
    return collect_and_evaluate(media_path=media(kind),media_sha256=sha(media(kind)),policy=p,policy_sha256=digest(p),run_id='fixture_'+kind)
def report(kind='tone'):return copy.deepcopy(_report(kind))
def native(r):
    m=r['observations'];return {'schema_version':'bie.render-receipt.v1','run_id':'native_fixture','mode':'full',
      'composition_id':'Lesson','passed':True,'failure_code':None,'errors':[],'output_path':'out/lesson.mp4',
      'expected_frames':8,'media':{'width':64,'height':36,'fps':4,'decoded_frames':8,'duration_s':2,
       'codec_name':'h264','pixel_format':'yuv420p','audio_streams':int(m['audio'] is not None)},
      'input_sha256':'a'*64,'recipe_sha256':'b'*64,'evidence_directory':'render-evidence/native_fixture',
      'execution_kind':'LOCAL_REMOTION_CLI','process_started':True,'artifact_sha256':m['artifact']['sha256'],
      'artifact_size_bytes':m['artifact']['bytes'],'accepted':False}
