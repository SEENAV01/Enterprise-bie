"""Build a real browser probe; does not claim the Linux sandbox gate ran."""
from pathlib import Path
from dataclasses import replace, asdict
import argparse
import hashlib
import io
import json
import math
import struct
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bie.game_engine.audio import AudioCue, AudioCueKind, AudioExperienceContract
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.contracts import AssetDescriptor
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.security import csp_value
from bie.game_engine.build_runtime_engine.entrypoint import ENTRY_JS
from bie.game_engine.build_runtime_engine.linker import link_browser_esm
from bie.game_engine.build_runtime_engine.module_graph import verify_module_graph
from bie.game_engine.build_runtime_engine.smoke_bundle import build_smoke_bundle
from bie.game_engine.react_runtime_engine.vendor import materialize_vendor
from bie.game_engine.runtime_quality_engine.contracts import LocaleCatalog, RightsRecord, AudioSyncRecord, RuntimeExperienceProfile

def probe_context():
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(8000)
        wav.writeframes(b''.join(struct.pack('<h', int(1200 * math.sin(2 * math.pi * 440 * i / 8000))) for i in range(800)))
    audio = output.getvalue()
    ctx = compiler_context(); doc = ctx.document; game = doc.experiences[0]; level = game.levels[0]
    cue = AudioCue('cue:narration:1', AudioCueKind.NARRATION, 'level_start', 'audio:probe', 'text:narration', False)
    level = replace(level, audio=AudioExperienceContract((cue,)))
    doc = replace(doc, experiences=(replace(game, levels=(level,)),))
    asset = AssetDescriptor('audio:probe', 'audio/wav', hashlib.sha256(audio).hexdigest(), 'Test tone',
                            'rights:probe', 'CC0-1.0', 'Generated verification tone', 'source:probe')
    profile = RuntimeExperienceProfile('ur-IN', (LocaleCatalog('ur-IN',
        {'ui.ready':'تیار','ui.audio_play':'بیان چلائیں','ui.attribution':'ماخذ اور حقوق'}, 'rtl'),),
        rights=(RightsRecord('audio:probe','rights:probe','CC0-1.0','Generated verification tone','source:probe'),),
        audio_sync=(AudioSyncRecord('cue:narration:1',0,100,'level_start'),))
    texts = {**ctx.text_catalog, 'text:narration':'یہ حرکت کا تجربہ ہے۔'}
    return replace(ctx, document=doc, assets={'audio:probe':asset}, text_catalog=texts, experience_profile=profile).validate(), audio

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists():
        raise SystemExit('Probe output must be fresh')
    source = root / 'source'; runtime = root / 'runtime'
    source.mkdir(parents=True); runtime.mkdir()
    ctx, audio = probe_context(); bundle = compile_game(ctx)
    for artifact in bundle.artifacts:
        artifact.validate()
        (source / Path(artifact.path).name).write_bytes(artifact.content.encode('utf-8'))
    tsc = ROOT / 'tooling/react/node_modules/typescript/bin/tsc'
    command = [args.node, '--preserve-symlinks', '--preserve-symlinks-main', str(tsc),
               '--target','ES2020','--module','ES2020','--moduleResolution','node','--strict',
               '--skipLibCheck','--lib','ES2020,DOM','--noEmitOnError','--outDir',str(runtime)]
    command += [str(p) for p in sorted(source.glob('*.ts'))]
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    (root / 'typescript.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    for p in runtime.glob('*.js'):
        p.write_text(link_browser_esm(p.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    for p in source.glob('*.json'):
        (runtime / p.name).write_bytes(p.read_bytes())
    html = (source / 'index.html').read_text(encoding='utf-8').replace('./bootstrap.js','./entry.js')
    html = html.replace('; frame-ancestors &#x27;none&#x27;','')
    (runtime / 'index.html').write_text(html, encoding='utf-8', newline='\n')
    (runtime / 'probe.wav').write_bytes(audio)
    entry = ENTRY_JS.replace('__ASSET_BINDINGS__',json.dumps({'audio:probe':'./probe.wav'},sort_keys=True,separators=(',',':')))
    (runtime / 'entry.js').write_text(entry, encoding='utf-8', newline='\n')
    materialize_vendor(runtime)
    graph = verify_module_graph(runtime)
    smoke, smoke_sha = build_smoke_bundle(runtime)
    (root / 'smoke-bundle.js').write_text(smoke, encoding='utf-8', newline='\n')
    headers = {'Content-Security-Policy':csp_value(),'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'}
    (runtime / 'security-headers.json').write_text(json.dumps(headers), encoding='utf-8')
    hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.iterdir()) if p.is_file()}
    harness = {}
    for name in ('h6-probe-ui.html', 'h6-probe-ui.js'):
        data = (ROOT / 'scripts' / name).read_bytes()
        (runtime / name).write_bytes(data)
        harness[name] = hashlib.sha256(data).hexdigest()
    report = {'compile_receipt':asdict(bundle.receipt),'module_graph':graph,'artifact_sha256':hashes,
              'test_only_harness_sha256':harness,
              'smoke_sha256':smoke_sha,'typescript_exit_code':result.returncode,
              'fixture_kind':'source-contract fixture with actual locally generated WAV tone',
              'linux_sandbox_verified':False,'product_accepted':False}
    (root / 'BUILD_RECEIPT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'root':str(root),'modules':len(graph['nodes']),'typescript_exit_code':result.returncode}))

if __name__ == '__main__':
    main()
