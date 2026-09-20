from dataclasses import dataclass
from typing import Mapping
from .canonical_dir_codec import CANONICAL_DIR_COMMIT,CANONICAL_DIR_TREE
from .rep_original_codec import EXPECTED_REP_ARCHIVE_SHA256
@dataclass(frozen=True)
class GateEvidence:
 dir_commit:str;dir_tree:str;dir_source_runtime_verified:bool;rep_archive_verified:Mapping[str,bool];local_tests:int;failures:int;errors:int;skips:int
@dataclass(frozen=True)
class GateReceipt:
 status:str;blockers:tuple[str,...];local_tests:int;rep_verified:int;implementation_scope_complete:bool;accepted:bool=False
def evaluate_section_exit(e):
 b=[]
 if e.dir_commit!=CANONICAL_DIR_COMMIT or e.dir_tree!=CANONICAL_DIR_TREE:b.append('canonical_dir_commit_or_tree_mismatch')
 if not e.dir_source_runtime_verified:b.append('canonical_dir_source_not_executed')
 missing=[k for k in EXPECTED_REP_ARCHIVE_SHA256 if not e.rep_archive_verified.get(k,False)]
 if missing:b.append('original_rep_archives_not_all_byte_verified')
 if e.failures or e.errors or e.skips or e.local_tests<=0:b.append('local_regression_not_clean')
 return GateReceipt('PASS' if not b else 'BLOCKED',tuple(b),e.local_tests,8-len(missing),not b,False)
