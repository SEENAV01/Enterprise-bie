#!/opt/pyvenv/bin/python -I
"""Immutable browser-only exec entry. No authority/resource grant inside here."""
from pathlib import Path
import hashlib,json,os,signal,sys

def main():
    import resource
    sys.path.insert(0,'/engine')
    from bie.compiler.chromium_resource_worker import validate_browser_args,require,NODE_AS,CHROME_AS,CHROME_SHA,file_sha
    require(Path(__file__).as_posix()=='/engine/bie/compiler/qa_support/chromium_resource_entry.py','ENTRY_PATH')
    config_path=Path(__file__).with_name('chromium-boundary.json')
    require(config_path.is_file() and not config_path.is_symlink() and config_path.stat().st_size<=16384,'ENTRY_CONFIG')
    config=json.loads(config_path.read_text())
    require(config==dict(schema='bie.chromium-entry-policy/1',browser=config.get('browser'),browser_sha256=CHROME_SHA,
        node_address_space_bytes=NODE_AS,chromium_address_space_bytes=CHROME_AS),'ENTRY_POLICY')
    browser=Path(config['browser']);require(browser.is_file() and not browser.is_symlink() and
        str(browser).startswith('/usr/') and file_sha(browser)==CHROME_SHA,'ENTRY_BROWSER')
    args=validate_browser_args(sys.argv[1:])
    require(resource.getrlimit(resource.RLIMIT_AS)==(NODE_AS,NODE_AS),'ENTRY_BASE_LIMIT')
    status=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines())
    require(status['NoNewPrivs'].strip()=='1' and status['Seccomp'].strip()=='2' and
        all(status[name].strip()=='0000000000000000' for name in ('CapEff','CapPrm','CapInh','CapBnd')),'ENTRY_GUARDS')
    require(not any(k.startswith('LD_') or k in ('NODE_OPTIONS','PYTHONHOME','PYTHONSTARTUP') for k in os.environ),'ENTRY_ENV')
    os.kill(os.getpid(),signal.SIGSTOP)
    require(resource.getrlimit(resource.RLIMIT_AS)==(CHROME_AS,CHROME_AS),'ENTRY_ADMISSION_REQUIRED')
    require(file_sha(browser)==CHROME_SHA,'ENTRY_BROWSER_CHANGED')
    os.execve(str(browser),[str(browser),*args],dict(os.environ))

if __name__=='__main__':
    try:main()
    except BaseException:
        print('CHROMIUM_RESOURCE_ENTRY_REJECTED',file=sys.stderr);raise SystemExit(125)
