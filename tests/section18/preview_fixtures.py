"""Explicitly synthetic native compiler fixture + non-native diagnostic MP4."""
from pathlib import Path
from dataclasses import replace
from fractions import Fraction
import base64,hashlib,json
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.build_runtime_engine.contracts import PackageArtifact,RuntimePackageManifest
from bie.game_engine.canonical import fingerprint
from bie.compiler.render_contracts import RenderReceipt,MediaProbe
from bie.qa.video_v2.models import VideoPolicy
from bie.qa.video_v2.media import DecodedVideo
WIRE=json.loads((Path(__file__).parent/'fixtures/preview-fixtures.json').read_text())
def game():
    ctx,_=build_inputs();bundle=compile_game(ctx);m=WIRE['game_manifest']
    manifest=RuntimePackageManifest(**dict(m,artifacts=tuple(PackageArtifact(**x) for x in m['artifacts']),asset_bindings=tuple(tuple(x) for x in m['asset_bindings'])))
    files={p:base64.b64decode(raw,validate=True) for p,raw in WIRE['game_files'].items()}
    return ctx,bundle,manifest,files
def changed_game(path,data):
    """Adversarial package: reseal hashes so semantic entry checks, not just CAS,
    must reject it. Not a production build or new distinct test execution."""
    ctx,b,m,files=game();files[path]=data
    artifacts=tuple(replace(a,size_bytes=len(files[a.path]),sha256=hashlib.sha256(files[a.path]).hexdigest()) for a in m.artifacts)
    pf=fingerprint(dict(compiler_receipt_id=m.compiler_receipt_id,compiler_bundle_fingerprint=m.compiler_bundle_fingerprint,
        toolchain_fingerprint=m.toolchain_fingerprint,artifacts=[(a.path,a.sha256,a.size_bytes) for a in artifacts],entrypoint=m.entrypoint,
        asset_bindings=list(m.asset_bindings)))
    m=replace(m,artifacts=artifacts,package_fingerprint=pf,manifest_payload_sha256='')
    from dataclasses import asdict
    payload=asdict(m);payload.pop('manifest_payload_sha256')
    self_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    m=replace(m,manifest_payload_sha256=self_hash);payload['manifest_payload_sha256']=self_hash
    files['build-manifest.json']=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    return ctx,b,m,files
def render():
    data=base64.b64decode(WIRE['diagnostic_mp4_base64'],validate=True);assert hashlib.sha256(data).hexdigest()==WIRE['receipt']['mp4_sha256']
    policy=VideoPolicy('video-diagnostic','a'*64,128,96,8,1,16)
    receipt=RenderReceipt('bie.render-receipt.v1','synthetic-preview-render','full','video-diagnostic',True,None,(),
        'not-exposed.mp4',16,MediaProbe(128,96,8,16,2,'h264','yuv420p',0),'a'*64,'b'*64,
        'not-exposed-private-evidence','INJECTED_TEST_RUNNER',True,hashlib.sha256(data).hexdigest(),len(data),False)
    decoded=DecodedVideo(128,96,'h264','yuv420p',0,Fraction(8),Fraction(1,8),tuple(range(16)),(1,)*16,
                         (b'\0'*(128*96*3),)*16,'c'*64,'d'*64,'e'*64)
    return data,receipt,policy,decoded
