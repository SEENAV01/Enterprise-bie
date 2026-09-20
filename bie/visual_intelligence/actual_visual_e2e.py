from __future__ import annotations
from dataclasses import dataclass
from .canonical_dir_codec import decode_canonical_dir_packet,ExactDirSourceUnavailableError
from .rep_original_codec import decode_rep_decision,OriginalRepSourceUnavailableError
from .canonical_family_wiring import execute_original_family_path
@dataclass(frozen=True)
class ActualE2E:
 status:str;completed_stages:tuple[str,...];blockers:tuple[str,...];family_status:str|None;review_required:bool=True;accepted:bool=False
def run_actual_visual_e2e(*,dir_raw,dir_receipt,rep_raw,rep_archives_verified,grammar_inputs,allow_contract_fixture=False):
 b=[];s=[]
 try:
  dp=decode_canonical_dir_packet(dir_raw,dir_receipt,not allow_contract_fixture);s.append('DIR_ADOPT' if dir_receipt.runtime_source_verified else 'DIR_ADOPT_FIXTURE')
  if allow_contract_fixture and not dir_receipt.runtime_source_verified:b.append('canonical_dir_source_not_verified')
 except ExactDirSourceUnavailableError:
  if not allow_contract_fixture:return ActualE2E('BLOCKED',tuple(s),('canonical_dir_source_not_verified',),None)
  dp=decode_canonical_dir_packet(dir_raw,dir_receipt,False);s.append('DIR_ADOPT_FIXTURE');b.append('canonical_dir_source_not_verified')
 try:
  rp=decode_rep_decision(rep_raw,rep_archives_verified,not allow_contract_fixture);s.append('REP' if rep_archives_verified else 'REP_FIXTURE')
  if allow_contract_fixture and not rep_archives_verified:b.append('original_rep_source_not_verified')
 except OriginalRepSourceUnavailableError:
  if not allow_contract_fixture:return ActualE2E('BLOCKED',tuple(s),('original_rep_source_not_verified',),None)
  rp=decode_rep_decision(rep_raw,False,False);s.append('REP_FIXTURE');b.append('original_rep_source_not_verified')
 fr=execute_original_family_path(domain=rp.domain,representation=rp.representation,tags=rp.tags,grammar_inputs=grammar_inputs,evidence_refs=rp.evidence_refs,reasoning_refs=rp.reasoning_refs);s.extend(('GRAM','LAYOUT','ASSET','TEXT','ACCESS','QA'))
 if fr.status!='PASS':b.append('original_family_execution_blocked')
 return ActualE2E('PASS' if not b else 'REVIEW',tuple(s),tuple(sorted(set(b))),fr.status)
