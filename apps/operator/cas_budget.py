"""Bound physical local CAS writes; delegate bytes/hash/atomic publication to native CAS.

One root-wide kernel lock covers admission plus native publication across processes.
All physical CAS bytes, including interrupted temporary files, consume capacity.
No automatic deletion, eviction, tenant-budget bypass or distributed guarantee.
"""
from contextlib import contextmanager
from dataclasses import asdict,dataclass
from pathlib import Path
import errno,hashlib,json,os,stat,time
from bie.infrastructure.artifact_store import FileSystemCAS
from .contracts import canonical,private_path,require,OperatorError,ident,strict_json


@dataclass(frozen=True)
class CASLimits:
    max_bytes:int=1024**3
    max_files:int=32768
    max_inventory_entries:int=65536
    max_blob_bytes:int=256*1024**2

    def __post_init__(self):
        for key,ceiling in {'max_bytes':1024**3,'max_files':32768,
                            'max_inventory_entries':65536,'max_blob_bytes':256*1024**2}.items():
            value=getattr(self,key)
            require(type(value) is int and 1<=value<=ceiling,'cas_budget_invalid',400)


class CASBudget:
    def __init__(self,root,limits=None):
        self.root=private_path(root)
        self.policy_path=private_path(root,'cas-budget.json')
        self.lock_path=private_path(root,'cas-budget.lock')
        require(limits is None or type(limits) is CASLimits,'cas_budget_invalid',400)
        with self.lock():
            if self.policy_path.exists():
                raw=self._read_policy('cas_policy_invalid')
                try:
                    value=strict_json(raw,4096)
                    require(type(value) is dict and set(value)==set(asdict(CASLimits())),'cas_policy_invalid')
                    saved=CASLimits(**value)
                except (OperatorError,TypeError,ValueError):
                    raise OperatorError('cas_policy_invalid') from None
                require(limits is None or limits==saved,'cas_policy_conflict')
                require(raw==canonical(asdict(saved)),'cas_policy_invalid')
                self.limits=saved
            else:
                self.limits=CASLimits() if limits is None else limits
                raw=canonical(asdict(self.limits))
                fd=os.open(self.policy_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),0o600)
                with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
            self.policy_bytes=raw
            self.policy_sha256=hashlib.sha256(raw).hexdigest()

    @contextmanager
    def lock(self):
        private_path(self.root,self.lock_path.name)
        flags=os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0)
        fd=os.open(self.lock_path,flags,0o600);held=False
        try:
            info=os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'storage_link_rejected')
            if info.st_size==0:os.write(fd,b'0');os.fsync(fd)
            deadline=time.monotonic()+5
            while not held:
                try:
                    if os.name=='nt':
                        import msvcrt
                        os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
                    else:
                        import fcntl
                        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    held=True
                except OSError as error:
                    if error.errno not in (errno.EACCES,errno.EAGAIN,errno.EDEADLK):raise
                    require(time.monotonic()<deadline,'cas_storage_busy',503);time.sleep(.01)
            yield
        finally:
            if held:
                if os.name=='nt':
                    import msvcrt
                    os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
                else:
                    import fcntl
                    fcntl.flock(fd,fcntl.LOCK_UN)
            os.close(fd)

    def _read_policy(self,code):
        """Bounded no-follow descriptor read; the descriptor owns link checks.

        Path checks alone cannot reject a hardlink or an intervening replacement.
        Recheck the opened inode after reading without exposing parser/OS details.
        """
        fd=None
        try:
            private_path(self.root,self.policy_path.name)
            fd=os.open(self.policy_path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and
                    0<before.st_size<=4096,code)
            raw=os.read(fd,4097)
            after=os.fstat(fd)
            current=os.stat(self.policy_path,follow_symlinks=False)
            require(len(raw)==before.st_size and len(raw)<=4096 and
                    stat.S_ISREG(current.st_mode) and current.st_nlink==after.st_nlink==1 and
                    (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
                    (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)==
                    (current.st_dev,current.st_ino,current.st_size,current.st_mtime_ns),code)
            return raw
        except (OSError,OperatorError):
            raise OperatorError(code) from None
        finally:
            if fd is not None:os.close(fd)

    def verify_policy(self):
        require(self._read_policy('cas_policy_tampered')==self.policy_bytes,'cas_policy_tampered')

    def inventory(self):
        self.verify_policy();total=count=entries=0
        def visit(directory,collect=False,depth=0):
            nonlocal total,count,entries
            require(depth<=16,'cas_inventory_depth_reached',503)
            if not directory.exists():return
            private_path(self.root,directory.relative_to(self.root))
            require(directory.is_dir(),'cas_inventory_invalid')
            with os.scandir(directory) as children:
                for item in children:
                    entries+=1
                    require(entries<=self.limits.max_inventory_entries,'cas_inventory_capacity_reached',503)
                    require(not item.is_symlink(),'storage_link_rejected')
                    # DirEntry.stat on Windows deliberately sets st_nlink=0.
                    # Query the real no-follow stat; do not weaken link checks.
                    info=os.stat(item.path,follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        visit(Path(item.path),collect,depth+1)
                    else:
                        require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'storage_link_rejected')
                        if collect:total+=info.st_size;count+=1
        visit(self.root/'sources-cas',True)
        runs=self.root/'runs'
        if runs.exists():
            private_path(self.root,'runs')
            with os.scandir(runs) as children:
                for item in children:
                    entries+=1
                    require(entries<=self.limits.max_inventory_entries,'cas_inventory_capacity_reached',503)
                    ident(item.name);require(not item.is_symlink() and item.is_dir(follow_symlinks=False),'storage_link_rejected')
                    visit(Path(item.path)/'cas',True)
        require(total<=self.limits.max_bytes and count<=self.limits.max_files,'cas_capacity_reached',429)
        return dict(bytes=total,files=count,inventory_entries=entries)


class BudgetedCAS(FileSystemCAS):
    def __init__(self,root,budget):
        require(type(budget) is CASBudget,'cas_budget_invalid',400)
        self.budget=budget
        root=private_path(budget.root,Path(root).absolute().relative_to(budget.root))
        super().__init__(root)

    def put_bytes(self,data):
        require(type(data) is bytes,'cas_payload_invalid',400)
        require(len(data)<=self.budget.limits.max_blob_bytes,'cas_blob_too_large',413)
        with self.budget.lock():
            usage=self.budget.inventory()
            destination=self._path(hashlib.sha256(data).hexdigest())
            private_path(self.budget.root,destination.relative_to(self.budget.root))
            exists=destination.exists()
            extra=0 if exists else len(data)
            require(usage['bytes']+extra<=self.budget.limits.max_bytes and
                    usage['files']+int(not exists)<=self.budget.limits.max_files,
                    'cas_capacity_reached',429)
            result=super().put_bytes(data)
            self.budget.inventory()
            # Native CAS remains authoritative for digest/size/corruption checks.
            require(super().get_bytes(result)==data,'cas_publication_mismatch')
            return result
