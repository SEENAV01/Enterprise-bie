"""H6-003: bounded PCM assets, verified bytes, transactional publication support.

No network fetch or audio decoder subprocess is invoked here. A supplied rights
reference and transcript hash are retained assertions, not independent approval.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import io
import os
import stat
import struct
import wave
from .frame_runtime_contract import fail


def _read_under(root, relative, maximum):
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir() or any(p.is_symlink() for p in root.parents):
        fail('NARRATION_ASSET_ROOT', 'root must be a real directory without symlink ancestors')
    parts = relative.split('/')
    if len(parts) != 2 or parts[0] != 'narration' or any(p in {'', '.', '..'} for p in parts):
        fail('NARRATION_ASSET_PATH', 'unexpected asset path')
    fd = None
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        child = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
        os.close(fd); fd = child
        f = os.open(parts[1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=fd)
        try:
            info = os.fstat(f)
            if not stat.S_ISREG(info.st_mode) or not 44 <= info.st_size <= maximum:
                fail('NARRATION_ASSET_SIZE', 'asset must be a bounded regular file')
            chunks, count = [], 0
            while True:
                part = os.read(f, min(65536, maximum + 1 - count))
                if not part:
                    break
                count += len(part); chunks.append(part)
                if count > maximum:
                    fail('NARRATION_ASSET_SIZE', 'asset grew beyond its declared bound')
            after = os.fstat(f)
            if (after.st_size, after.st_mtime_ns, after.st_ino) != (info.st_size, info.st_mtime_ns, info.st_ino):
                fail('NARRATION_ASSET_CHANGED', 'file changed while reading')
            return b''.join(chunks)
        finally:
            os.close(f)
    except OSError as exc:
        fail('NARRATION_ASSET_UNAVAILABLE', str(exc))
    finally:
        if fd is not None:
            os.close(fd)


def inspect_pcm(data):
    if len(data) < 44 or data[:4] != b'RIFF' or data[8:12] != b'WAVE' or struct.unpack('<I', data[4:8])[0] + 8 != len(data):
        fail('NARRATION_PCM_HEADER', 'complete, size-consistent RIFF/WAVE is required')
    try:
        with wave.open(io.BytesIO(data), 'rb') as w:
            meta = {'sample_rate': w.getframerate(), 'channels': w.getnchannels(),
                    'sample_width': w.getsampwidth(), 'frame_count': w.getnframes()}
            if w.getcomptype() != 'NONE' or meta['sample_width'] != 2 or meta['channels'] not in (1, 2) or not 8000 <= meta['sample_rate'] <= 96000:
                fail('NARRATION_PCM_FORMAT', 'unsupported PCM format')
            samples = w.readframes(meta['frame_count'] + 1)
            if len(samples) != meta['frame_count'] * meta['channels'] * meta['sample_width']:
                fail('NARRATION_PCM_TRUNCATED', 'header sample count does not match decoded bytes')
    except (wave.Error, EOFError, struct.error) as exc:
        fail('NARRATION_PCM_DECODE', str(exc))
    return meta, samples


def verified_asset_bytes(plan, asset_root):
    assets = plan['audio_assets'] if plan else []
    if not assets:
        return {}, {'schema_version': 'bie.narration-assets.v1', 'assets': [], 'status': 'NOT_REQUIRED', 'accepted': False}
    if asset_root is None:
        fail('NARRATION_ASSET_ROOT_REQUIRED', 'source publication requires actual verified PCM bytes')
    data_by_path, records = {}, []
    for asset in assets:
        data = _read_under(asset_root, asset['public_path'], asset['byte_length'])
        if len(data) != asset['byte_length'] or sha256(data).hexdigest() != asset['sha256']:
            fail('NARRATION_ASSET_HASH_MISMATCH', asset['asset_id'])
        meta, _ = inspect_pcm(data)
        if any(meta[k] != asset[k] for k in meta):
            fail('NARRATION_ASSET_METADATA_MISMATCH', asset['asset_id'])
        data_by_path[asset['public_path']] = data
        records.append({'asset_id': asset['asset_id'], 'sha256': asset['sha256'], 'byte_length': len(data),
                        **meta, 'rights_ref': asset['rights_ref'], 'source_refs': asset['source_refs'],
                        'reasoning_refs': asset['reasoning_refs']})
    return data_by_path, {'schema_version': 'bie.narration-assets.v1', 'assets': records,
                         'status': 'PCM_BYTES_VERIFIED_NOT_SPEECH_ALIGNMENT', 'accepted': False}


def stage_verified_assets(data_by_path, staging):
    """Only for a newly allocated private publication staging directory."""
    staging = Path(staging)
    for rel, data in sorted(data_by_path.items()):
        p = staging / 'public' / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(data)
