from __future__ import annotations
from dataclasses import dataclass,is_dataclass,asdict
from hashlib import sha256
from pathlib import Path
from typing import Any,Mapping
from .grammar_registry import VisualGrammarRegistry
class OriginalRepCodecError(ValueError):pass
class OriginalRepSourceUnavailableError(OriginalRepCodecError):pass
EXPECTED_REP_ARCHIVE_SHA256={'BIE_VIS_REP_001.zip': 'e16246c98c9e27d4b0b5761ab15d05efaf96abc5498e833e1ac30d53eeb81a9f', 'BIE_VIS_REP_002.zip': '60bacbcab47ed1725a06772b75a8ce5eb3a87edb298a80949aea9c731b88d492', 'BIE_VIS_REP_003.zip': 'eabfe0872416ab7077d6f07698773e3f7d64f4aba7e3ca0e0c3817cee39e35fc', 'BIE_VIS_REP_004.zip': 'e88249affc0dc401ca7641ac30aae284a9deb6025cac494c5d25e10f7a896e5c', 'BIE_VIS_REP_005.zip': '4f8a5c0a0989bcb6c2bbcf9dd1247a6ebfe11c39edf74e91f9c49442b4d6e942', 'BIE_VIS_REP_006.zip': '4e6d8445741b274916b74df577df04541e0dc6992269a8290074c79c7ef574f0', 'BIE_VIS_REP_007.zip': '14d9670c170822556c76b0f8ca7c76c00f9acd789358bb66a9e2fa976e3eb8c2', 'BIE_VIS_REP_008.zip': '017be204a6082e01242b3d4bc60b47b310fe29e2e0b9bebe357e9fc38de32ccf'}
@dataclass(frozen=True)
class RepVerification:
 verified:tuple[str,...];missing:tuple[str,...];mismatched:tuple[str,...];all_verified:bool
@dataclass(frozen=True)
class RepDecision:
 decision_id:str;revision:int;domain:str;representation:str;confidence:float;evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];required_capabilities:tuple[str,...];tags:tuple[str,...];current:bool;source_archives_verified:bool;review_required:bool=True;accepted:bool=False
@dataclass(frozen=True)
class GrammarView:
 grammar_id:str;version:str;domains:tuple[str,...];representations:tuple[str,...];capabilities:tuple[str,...];tags:tuple[str,...]
def verify_rep_archive_bytes(name,data):
 if name not in EXPECTED_REP_ARCHIVE_SHA256:raise OriginalRepCodecError('unknown REP archive')
 return sha256(data).hexdigest()==EXPECTED_REP_ARCHIVE_SHA256[name]
def verify_rep_archive_directory(directory):
 root=Path(directory);v=[];m=[];bad=[]
 for n,h in sorted(EXPECTED_REP_ARCHIVE_SHA256.items()):
  p=root/n
  if not p.exists():m.append(n)
  elif sha256(p.read_bytes()).hexdigest()==h:v.append(n)
  else:bad.append(n)
 return RepVerification(tuple(v),tuple(m),tuple(bad),len(v)==8 and not m and not bad)
def mp(x):
 if isinstance(x,Mapping):return dict(x)
 if is_dataclass(x):return asdict(x)
 if hasattr(x,'to_dict'):return dict(x.to_dict())
 if hasattr(x,'__dict__'):return dict(x.__dict__)
 raise OriginalRepCodecError('REP output not decodable')
def decode_rep_decision(raw,source_archives_verified,require_exact_source=True):
 if require_exact_source and not source_archives_verified:raise OriginalRepSourceUnavailableError('REP source archives not byte-verified')
 d=mp(raw);req=('decision_id','domain','representation','confidence','evidence_refs','reasoning_refs')
 miss=[k for k in req if k not in d]
 if miss:raise OriginalRepCodecError('missing REP fields:'+str(miss))
 c=float(d['confidence'])
 if not 0<=c<=1:raise OriginalRepCodecError('confidence outside [0,1]')
 ev=tuple(d['evidence_refs']);rr=tuple(d['reasoning_refs'])
 if not ev or not rr:raise OriginalRepCodecError('REP lineage missing')
 return RepDecision(str(d['decision_id']),int(d.get('revision',1)),str(d['domain']),str(d['representation']),c,ev,rr,tuple(d.get('required_capabilities',())),tuple(d.get('tags',())),bool(d.get('current',True)),bool(source_archives_verified))
def adapt_original_grammar_registry(registry:VisualGrammarRegistry):
 return tuple(GrammarView(g.grammar_id,g.version,tuple(g.domains),tuple(g.representations),tuple(sorted(set(g.allowed_primitives)|set(g.required_roles))),tuple(g.tags)) for g in registry.list())
