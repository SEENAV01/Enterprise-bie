"""HARD038: source-bound native QA/EVAL handoff, with explicit diagnostic profile.

Required stages and expected outputs are operator-owned. Does not invent stages,
replace native rendering with FFmpeg, or turn a missing provider into a PASS.
Registered programs execute in fresh copies via the H7 stage/worker infrastructure.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from .common import *
from ..operational_quality_v2.rebuild import Stage,execute_stage
from ..operational_quality_v2.common import new_id

STAGES=('BI','KI','PR','MATH','RE','PED','DIR','VIS','ANI','DSL','COMP','AUDIO','GAME','QA','EVAL')
# Minimal native source-to-QA ancestry. Valid indirect paths are accepted: this
# constrains data availability, not the internal teaching-engine implementation.
REQUIRED_ANCESTORS={
    'BI':(), 'KI':('BI',), 'PR':('KI',), 'MATH':('KI',),
    'RE':('PR','MATH'), 'PED':('PR','RE'), 'DIR':('PED',),
    'VIS':('DIR',), 'ANI':('VIS',), 'DSL':('VIS','ANI'),
    'COMP':('DSL',), 'AUDIO':('DIR',), 'GAME':('PED','DSL'),
    'QA':STAGES[:13], 'EVAL':('QA',),
}

def dependency_closure(steps):
    """Stable transitive census; an omitted dependency never shrinks QA scope."""
    closure={}
    for step in steps:
        parents=set(step.dependencies)
        for dependency in step.dependencies:
            require(dependency in closure,'H39_DEPENDENCY_NOT_REGISTERED')
            parents.update(closure[dependency])
        require(set(REQUIRED_ANCESTORS[step.name])<=parents,
                'H39_REQUIRED_DEPENDENCY_MISSING')
        closure[step.name]=tuple(n for n in STAGES if n in parents)
    return closure


@dataclass(frozen=True)
class PipelineStep:
    name:str
    stage:Stage
    dependencies:tuple[str,...]
    checks:tuple[str,...]
    golden_outputs:tuple[dict,...]=()
    def __post_init__(self):
        require(self.name in STAGES and type(self.stage) is Stage,'H8_STEP_TYPE')
        exact_strings(self.dependencies,'H8_DEPENDENCIES');exact_strings(self.checks,'H8_STEP_CHECKS',1)
        require(set(self.dependencies)<=set(STAGES) and self.name not in self.dependencies,'H8_STEP_DEPENDENCY')
        if self.golden_outputs:checked_rows(self.golden_outputs)
        require('qa-result.json' in self.stage.output_paths,'H8_STEP_RECEIPT_REQUIRED')
        require(all(r['path'] in self.stage.output_paths for r in self.golden_outputs),'H8_GOLDEN_OUTPUT_SCOPE')

@dataclass(frozen=True)
class BookPlan:
    source_rows:tuple[dict,...]
    source_path:str
    steps:tuple[PipelineStep,...]
    required_stages:tuple[str,...]=STAGES
    profile:str='NATIVE'
    def __post_init__(self):
        checked_rows(self.source_rows);safe_relative_path(self.source_path)
        require(self.source_path in {r['path'] for r in self.source_rows},'H8_SOURCE_NOT_IN_INVENTORY')
        exact_strings(self.required_stages,'H8_STAGE_CENSUS',1)
        require(self.required_stages==STAGES,'H8_MANDATORY_STAGE_WAIVER')
        require(type(self.steps) is tuple and len(self.steps)<=len(STAGES) and all(type(s) is PipelineStep for s in self.steps),'H8_STEPS')
        require(len({s.name for s in self.steps})==len(self.steps),'H8_DUPLICATE_STAGE')
        order={n:i for i,n in enumerate(STAGES)}
        require([order[s.name] for s in self.steps]==sorted(order[s.name] for s in self.steps),'H8_STAGE_ORDER')
        for s in self.steps:
            require(all(order[d]<order[s.name] for d in s.dependencies),'H8_DEPENDENCY_ORDER')
            if s.name!='BI':require(bool(s.dependencies),'H8_SOURCE_LINEAGE_MISSING')
        dependency_closure(self.steps)
        require(self.profile in ('NATIVE','DIAGNOSTIC'),'H8_PIPELINE_PROFILE')
        qa=[s for s in self.steps if s.name in ('QA','EVAL')]
        gen=[s for s in self.steps if s.name not in ('QA','EVAL')]
        require(not {s.stage.program.script_sha256 for s in qa}&{s.stage.program.script_sha256 for s in gen},'H8_VALIDATOR_GENERATOR_ALIAS')
    @property
    def content_digest(self):return digest(asdict(self))

def run_book(root,output,plan,binding,*,cancel=None):
    require(type(plan) is BookPlan and type(binding) is Binding and binding.policy_digest==plan.content_digest,'H8_BOOK_POLICY_BINDING')
    ancestors=dependency_closure(plan.steps)
    source=check_files(root,plan.source_rows)
    require(not any(r['path']=='book-request.json' or r['path'].startswith('upstream/') for r in source),'H8_RESERVED_SOURCE_PATH')
    require(binding.candidate_digest==digest(source),'H8_BOOK_SOURCE_BINDING')
    out=Path(output).absolute();require(not out.is_relative_to(Path(root).absolute()) and not Path(root).absolute().is_relative_to(out),'H8_BOOK_OUTPUT_OVERLAP')
    out.mkdir(parents=True,exist_ok=False);errors=[];records=[];complete={};run_id=binding.run_id
    if {s.name for s in plan.steps}!=set(STAGES):errors.append('H8_REQUIRED_PIPELINE_STAGES_MISSING')
    if plan.profile=='DIAGNOSTIC':errors.append('H8_DIAGNOSTIC_NOT_NATIVE_E2E')
    for step in plan.steps:
        if cancel is not None and cancel.is_set():errors.append('H8_PIPELINE_CANCELLED');break
        if not set(ancestors[step.name])<=set(complete):errors.append('H8_UPSTREAM_STAGE_UNAVAILABLE');break
        if plan.profile=='NATIVE' and step.stage.native_profile is None:
            errors.append('H8_NATIVE_EXECUTOR_NOT_PROVISIONED');break
        before=copy_verified(root,out/(step.name+'-input'),source)
        upstream=[]
        for dep in ancestors[step.name]:
            prev,folder=complete[dep]
            for r in prev['outputs']:
                data=regular_bytes(folder,r['path']);require(identity(data)==r['sha256'] and len(data)==r['bytes'],'H8_UPSTREAM_CHANGED')
                p=before/'upstream'/dep/r['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            upstream.append({'stage':dep,'output_digest':prev['output_digest']})
        request={'schema_version':'bie.qa.book-stage-request/1','binding':asdict(binding),'stage':step.name,
            'source_digest':digest(source),'source_path':plan.source_path,'upstream':upstream,
            'required_checks':list(step.checks),'profile':plan.profile}
        require(not (before/'book-request.json').exists(),'H8_RESERVED_REQUEST_PATH')
        write_new(before/'book-request.json',request)
        folder=out/(step.name+'-output')
        try:
            record=execute_stage(step.stage,before,folder,run_id)
            records.append({'stage':step.name,'process':record})
            require(not record['error'],'H8_STAGE_EXECUTION_FAILED')
            require({r['path'] for r in record['outputs']}==set(step.stage.output_paths),'H8_STAGE_OUTPUT_CENSUS')
            receipt=strict_object(regular_bytes(folder,'qa-result.json'))
            fields(receipt,('schema_version','stage','run_id','execution_id','request_digest','source_digest','checks'),'H8_STAGE_RECEIPT_FIELDS')
            require(receipt['schema_version']=='bie.qa.book-stage-result/1' and receipt['stage']==step.name,'H8_STAGE_SCHEMA')
            require(receipt['run_id']==run_id and receipt['execution_id']==record['execution_id'] and
                receipt['request_digest']==digest(request) and receipt['source_digest']==digest(source),'H8_STAGE_RECEIPT_BINDING')
            rows=receipt['checks'];require(type(rows) is list and len(rows)==len(step.checks),'H8_CHECK_CENSUS')
            require({r['check_id'] for r in rows}==set(step.checks),'H8_CHECK_CENSUS')
            for row in rows:
                fields(row,('check_id','status'),'H8_CHECK_FIELDS');require(row['status']=='PASS','H8_STAGE_CHECK_FAILED')
            by={r['path']:r for r in record['outputs']}
            for g in step.golden_outputs:require(by[g['path']]==g,'H8_GOLDEN_MISMATCH')
            if plan.profile=='NATIVE':require(record.get('native_executed') is True,'H8_NATIVE_STAGE_NOT_EXECUTED')
            complete[step.name]=(record,folder)
        except (ContractError,OSError,KeyError,ValueError) as exc:
            errors.append('H8_STAGE_VALIDATION_FAILED');records.append({'stage':step.name,'error':str(exc)});break
    require(inventory(root)==source,'H8_PIPELINE_SOURCE_CHANGED')
    if len(complete)!=len(STAGES):errors.append('H8_PIPELINE_INCOMPLETE')
    execution_ids=[r['process']['execution_id'] for r in records if 'process' in r]
    require(len(set(execution_ids))==len(execution_ids),'H8_REPLAYED_EXECUTION')
    result=outcome('BIE-QA-HARD-038',binding,{'required_stages':list(STAGES),'completed_stages':list(complete),
        'source_inventory':source,'pipeline_records':records,'plan_digest':plan.content_digest,
        'native_pipeline_executed':plan.profile=='NATIVE' and len(complete)==len(STAGES) and not errors,
        'observed_learning_proven':False,'eval_handoff_only':True},errors)
    write_new(out/'EVAL_HANDOFF.json',result)
    return result

def inspect_source_passage(root,source_ref,*,page,quote,run_id,revision,policy=None):
    """Actual native BI->KI passage check, not a substitute for the full harness.

    Operator selects exact passage. No OCR or speculative fact extraction. Source
    text, region anchors and native code hashes are retained. All other boundaries
    stay explicitly NOT_RUN, including product video/game and empirical EVAL.
    """
    from ..native_quality_v2.documents import inspect_pdf,verify_document,DocumentPolicy
    from ...knowledge_intelligence.claim_extraction import extract
    from ...knowledge_intelligence.claim_evidence import bind
    import inspect as pyinspect
    policy=DocumentPolicy() if policy is None else policy
    text(quote,'passage.quote',32768);integer(page,'page',1,policy.max_pages)
    binding=Binding(run_id,revision,source_ref.sha256,policy.content_digest)
    snapshot=inspect_pdf(source_ref,root,binding,policy)
    verified=verify_document(snapshot,source_ref,root,binding,policy)
    regions=[r for r in snapshot['regions'] if r['page']==page]
    joined='\n'.join(r['text'] for r in regions)
    require(quote in joined,'H8_SOURCE_PASSAGE_NOT_FOUND')
    # Exact occurrence offsets; ambiguity cannot choose another source region.
    require(joined.count(quote)==1,'H8_SOURCE_PASSAGE_AMBIGUOUS')
    start=joined.index(quote);end=start+len(quote);offset=0;anchors=[]
    for r in regions:
        stop=offset+len(r['text'])
        if offset<end and stop>start:anchors.append(r['region_id'])
        offset=stop+1
    claim=extract([{'id':'passage','anchor_id':anchors[0],'claims':[quote]}])[0]
    evidence=bind(claim['claim_id'],anchors,1)
    hashes={str(Path(pyinspect.getfile(f)).name):identity(Path(pyinspect.getfile(f)).read_bytes()) for f in (inspect_pdf,extract,bind)}
    return {'schema_version':'bie.qa.real-passage/1','source':asdict(source_ref),'page':page,'quote':quote,
        'quote_sha256':identity(quote.encode()),'start':start,'end':end,'anchor_ids':anchors,
        'native_claim':claim,'native_evidence':evidence,'native_evidence_is_identifier_link_only':True,'document_snapshot_digest':snapshot['content_digest'],
        'document_status':verified.status,'native_code_hashes':hashes,
        'stage_status':{s:('EXECUTED_PASSAGE_ONLY' if s in ('BI','KI') else 'NOT_RUN') for s in STAGES},
        'autonomous_knowledge_extraction':False,'source_semantics_verified':False,
        'full_real_book_e2e':False,'product_accepted':False}
