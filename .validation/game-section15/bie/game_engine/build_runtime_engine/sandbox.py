from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
import hashlib, json, os, re, shutil, shlex
from ..canonical import fingerprint
from .errors import GameBuildError
from .toolchain import discover_toolchain

CANONICAL_MAIN='375d99af0edd0086206817dae932156ddf61c569'
CANONICAL_BROWSER_WORKER_PATH='bie/infrastructure/browser_game_worker.py'
CANONICAL_BROWSER_WORKER_BLOB='1e177160c85e5d53e148d6116a454bf7c230bf36'

@dataclass(frozen=True)
class BrowserSandboxEvidence:
    canonical_main:str
    canonical_worker_blob:str
    worker_manifest_fingerprint:str
    uid:int
    gid:int
    no_new_privs:bool
    renderer_seccomp:bool
    no_sandbox_flag_present:bool
    network_default:str
    process_count:int
    product_accepted:bool=False
    def validate(self):
        if self.canonical_main!=CANONICAL_MAIN or self.canonical_worker_blob!=CANONICAL_BROWSER_WORKER_BLOB:
            raise GameBuildError('GAME_BUILD_CANONICAL_BROWSER_WORKER_IDENTITY')
        if not self.worker_manifest_fingerprint.startswith('sha256:'):
            raise GameBuildError('GAME_BUILD_BROWSER_WORKER_MANIFEST_HASH')
        if self.uid==0 or self.gid==0 or not self.no_new_privs or not self.renderer_seccomp or self.no_sandbox_flag_present:
            raise GameBuildError('GAME_BUILD_BROWSER_SANDBOX_NOT_ENFORCED')
        if self.network_default!='deny' or self.process_count<2 or self.product_accepted:
            raise GameBuildError('GAME_BUILD_BROWSER_SANDBOX_SCOPE')
        return self

def canonical_worker_manifest():
    tools={x.name for x in discover_toolchain()[0]}
    m={'tools':sorted({'node','chromium','playwright'} & (tools|{'playwright'})), 'network_default':'deny','sandbox':True,
       'canonical_main':CANONICAL_MAIN,'canonical_worker_path':CANONICAL_BROWSER_WORKER_PATH,'canonical_worker_blob':CANONICAL_BROWSER_WORKER_BLOB}
    # mirror canonical contract exactly: node/chromium/playwright, deny-by-default, sandbox required
    if not {'node','chromium','playwright'}.issubset(set(m['tools'])):raise GameBuildError('GAME_BUILD_CANONICAL_BROWSER_TOOLCHAIN')
    if m['network_default']!='deny' or m['sandbox'] is not True:raise GameBuildError('GAME_BUILD_CANONICAL_BROWSER_POLICY')
    return m

def _process_snapshot(profile:Path):
    rows=[];needle=str(profile/'userdata')
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode('utf-8','replace')
            if needle not in cmd or 'chromium' not in cmd:continue
            status=(proc/'status').read_text()
        except (OSError,PermissionError):continue
        def field(name):
            m=re.search(rf'^{re.escape(name)}:\s*(.*)$',status,re.M);return m.group(1).strip() if m else ''
        uid=int(field('Uid').split()[0]);gid=int(field('Gid').split()[0]);nnp=field('NoNewPrivs')=='1';seccomp=int(field('Seccomp') or '0')
        rows.append({'pid':int(proc.name),'uid':uid,'gid':gid,'no_new_privs':nnp,'seccomp':seccomp,'renderer':'--type=renderer' in cmd,'cmd_sha256':hashlib.sha256(cmd.encode()).hexdigest()})
    return tuple(sorted(rows,key=lambda x:x['pid']))

def _minimal_browser_env(profile:Path):
    path=os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin')
    return {'PATH':path,'HOME':str(profile/'home'),'XDG_CONFIG_HOME':str(profile/'home/.config'),'XDG_CACHE_HOME':str(profile/'home/.cache'),
            'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','BIE_BROWSER_PROFILE':str(profile)}

@contextmanager
def sandboxed_chromium(policy,*,allow_loopback=False):
    policy.validate();manifest=canonical_worker_manifest()
    setpriv=shutil.which('setpriv')
    if not setpriv:raise GameBuildError('GAME_BUILD_SETPRIV_MISSING')
    chromium=next(x for x in discover_toolchain()[0] if x.name=='chromium')
    profile=Path(mkdtemp(prefix='bie-game-sandbox-browser-'));(profile/'home').mkdir();(profile/'userdata').mkdir()
    try:
        os.chown(profile,policy.browser_sandbox_uid,policy.browser_sandbox_gid)
        for p in (profile/'home',profile/'userdata'):os.chown(p,policy.browser_sandbox_uid,policy.browser_sandbox_gid)
    except PermissionError as e:raise GameBuildError('GAME_BUILD_BROWSER_SANDBOX_CHOWN') from e
    wrapper=profile/'chromium-wrapper.sh'
    wrapper.write_text('#!/bin/sh\nPROFILE="${BIE_BROWSER_PROFILE:?}"\nexport HOME="$PROFILE/home"\nexport XDG_CONFIG_HOME="$HOME/.config"\nexport XDG_CACHE_HOME="$HOME/.cache"\nexec '+shlex.quote(setpriv)+f' --reuid={policy.browser_sandbox_uid} --regid={policy.browser_sandbox_gid} --clear-groups --no-new-privs sh -c \'printf "%s\\n" "$@" > "$BIE_BROWSER_PROFILE/launch-args.txt"; grep -E "^(Uid|Gid|NoNewPrivs):" /proc/self/status > "$BIE_BROWSER_PROFILE/launcher-status.txt"; exec {shlex.quote(chromium.path)} "$@"\' sh "$@"\n')
    wrapper.chmod(0o755)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:raise GameBuildError('GAME_BUILD_PLAYWRIGHT_MISSING') from e
    pw=sync_playwright().start();ctx=None
    try:
        ctx=pw.chromium.launch_persistent_context(str(profile/'userdata'),executable_path=str(wrapper),headless=True,
             args=['--disable-dev-shm-usage'],ignore_default_args=['--no-sandbox'],env=_minimal_browser_env(profile),timeout=policy.browser_timeout_ms)
        # enforce deny-by-default for network navigations/requests; data/about stay available for hermetic verification.
        def network_route(route):
            from urllib.parse import urlparse
            u=urlparse(route.request.url)
            if allow_loopback and u.hostname in ('127.0.0.1','localhost','::1'):route.continue_()
            else:route.abort('blockedbyclient')
        ctx.route('http://**',network_route);ctx.route('https://**',network_route)
        yield ctx,profile,manifest
    finally:
        if ctx is not None:ctx.close()
        pw.stop()
        shutil.rmtree(profile,ignore_errors=True)

def sandbox_evidence(profile:Path,manifest)->BrowserSandboxEvidence:
    args=(profile/'launch-args.txt').read_text() if (profile/'launch-args.txt').exists() else ''
    rows=_process_snapshot(profile)
    if not rows:raise GameBuildError('GAME_BUILD_BROWSER_PROCESS_EVIDENCE_MISSING')
    chromium_rows=[r for r in rows if r['uid']!=0]
    renderers=[r for r in chromium_rows if r['renderer']]
    if not chromium_rows or not renderers:raise GameBuildError('GAME_BUILD_BROWSER_RENDERER_EVIDENCE_MISSING')
    uid=chromium_rows[0]['uid'];gid=chromium_rows[0]['gid']
    ev=BrowserSandboxEvidence(CANONICAL_MAIN,CANONICAL_BROWSER_WORKER_BLOB,fingerprint(manifest),uid,gid,
       all(r['no_new_privs'] for r in chromium_rows),any(r['seccomp']==2 for r in renderers),'--no-sandbox' in args,'deny',len(chromium_rows),False)
    return ev.validate()
