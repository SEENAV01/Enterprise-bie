"""Finite COMP closure register. Implementation and execution/acceptance stay separate.

This evaluator records an audit conclusion; it is NOT a renderer authorization
or permission to claim correctness based on a caller's JSON.
"""
from .qa_common import CompilerQAError,digest

REQUIRED = ('dynamic_asset_repair','specialized_contracts','paint_producer','operational_isolation','installed_identity','pinned_compile','actual_render')
STATUSES = {'IMPLEMENTED_TESTED','VERIFIED_ACTUAL','BLOCKED_ENVIRONMENT','OPEN_IMPLEMENTATION','OUT_OF_SCOPE'}

def evaluate_section_closure(findings):
    if not isinstance(findings,list) or len(findings)!=len(REQUIRED):raise CompilerQAError('CLOSURE_COVERAGE_REQUIRED')
    seen={};open_items=[];blocked=[]
    for item in findings:
        if not isinstance(item,dict) or set(item)!={'capability','status','evidence','remaining'}:raise CompilerQAError('CLOSURE_FIELDS_REQUIRED')
        name,status=item['capability'],item['status']
        if name not in REQUIRED or name in seen or status not in STATUSES:raise CompilerQAError('CLOSURE_IDENTITY_INVALID')
        if status=='OUT_OF_SCOPE':raise CompilerQAError('CLOSURE_REQUIRED_CAPABILITY_CANNOT_BE_REMOVED')
        evidence=item['evidence'];remaining=item['remaining']
        if not isinstance(evidence,list) or any(not isinstance(v,str) or not v.strip() for v in evidence):raise CompilerQAError('CLOSURE_EVIDENCE_INVALID')
        if not isinstance(remaining,list) or any(not isinstance(v,str) or not v.strip() for v in remaining):raise CompilerQAError('CLOSURE_REMAINING_INVALID')
        if status in {'IMPLEMENTED_TESTED','VERIFIED_ACTUAL'} and (not evidence or remaining):raise CompilerQAError('CLOSURE_UNSUPPORTED_COMPLETE_CLAIM')
        if status in {'OPEN_IMPLEMENTATION','BLOCKED_ENVIRONMENT'} and not remaining:raise CompilerQAError('CLOSURE_OPEN_REASON_REQUIRED')
        if name in {'pinned_compile','actual_render'} and status=='IMPLEMENTED_TESTED':raise CompilerQAError('CLOSURE_REAL_EXECUTION_REQUIRED')
        if status=='OPEN_IMPLEMENTATION':open_items.append(name)
        if status=='BLOCKED_ENVIRONMENT':blocked.append(name)
        seen[name]=item
    return {'schema_version':'bie.comp-section-audit.v1','register_sha256':digest(findings),
            'implementation_complete':not open_items,'open_implementation':open_items,'blocked_execution':blocked,
            'section_exit_permitted':not open_items and not blocked,
            'status':'OPEN_IMPLEMENTATION' if open_items else 'IMPLEMENTED_NOT_RUNTIME_VERIFIED' if blocked else 'SECTION_SCOPE_VERIFIED_NOT_PRODUCT_ACCEPTED',
            'actual_render_authorization':False,'product_accepted':False,
            'note':'Audit register only; cannot substitute process-owned render evidence or downstream real-book acceptance.'}
