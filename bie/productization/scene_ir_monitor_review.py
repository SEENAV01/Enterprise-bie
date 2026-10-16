"""Exact later monitor authority; no missing-review or historical-only fallback.

This extension is deliberately CLOSED while the actual separate closure record
is pending. Fixed Git bindings will be installed only after actual reassessment;
live file hashes are never used to manufacture expected authority.
"""
from pathlib import Path
from hashlib import sha1
import os
import stat
from .contracts import require,sha,strict_json

DIRECTORY='docs/productization/m1-review/'
REVIEW=DIRECTORY+'MONITOR_REVIEW_EF6D83CC.json'
BINDINGS=DIRECTORY+'MONITOR_BINDINGS_EF6D83CC.json'
REVIEW_SHA='fb64e466b170a6cff981b886c7a8b53f5810683a3070a10e5d3834a776cb6624'
BINDINGS_SHA='217295769b67c5c7801342cf0f835a0fd69c47d19b1c3500fd319cc6821940d5'
DOCUMENT_BYTES={REVIEW:18439,BINDINGS:8819}
CANDIDATE='ef6d83cccb938755890aebad9852a1fc6e246407'
TREE='03bb5d9c501bd39c5bfd40e0239495be50e39ed8'
BASE='5b1cafc766c9df9c3e0748f459e6beb9b8f1f243'
BASE_TREE='ce5044e06c9b2fe8164b7fb15cc59976941f8116'
REVIEWER='/root/source_binding_reviewer_001'
DECISION='APPROVED_FOR_BOUNDED_M1_TASK036_PREREQUISITE'
ORIGINAL_CHAIN_SHA='1b60a9dc298e62b2c34a75c0959222abab2738801ba3d6dc2ce2e22e76f658ed'
WORKER='bie/compiler/chromium_resource_worker.py'
BASELINE_SHA='aeedfc527fb47df33c448ad2bf1a2553574015e3124a14e35fae1e94f75c2963'
ACTIVE_SHA='be4ac9863c6b5153568dec53d052e3d95973b4562e04d1efa2a0d8d5180e0aea'
AMENDMENTS={
    'docs/productization/task036-motion-amendment/AMENDMENT.json':'b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c',
    'docs/productization/task036-monitor-snapshot-amendment/AMENDMENT.json':'e54734d10ab9d0bcecc396c9b48e39496d3fcf3d72a15c1b06de3fc17769b10d',
    'docs/productization/task036-monitor-parse-amendment/AMENDMENT.json':'a60c6bd3c343fcca66b44260040849c93e248fc8dd62a08ee6dbbb5640395df9'}
PATHS=frozenset((WORKER,'.gitattributes','scripts/verify_post_dir.py',
    'scripts/compiler_monitor_snapshot_amendment.py','scripts/compiler_monitor_parse_source_amendment.py',
    'docs/productization/task036-monitor-snapshot-amendment/AMENDMENT.json',
    'docs/productization/task036-monitor-snapshot-amendment/chromium_resource_worker.py.before',
    'docs/productization/task036-monitor-snapshot-amendment/verify_post_dir.py.before',
    'docs/productization/task036-monitor-snapshot-amendment/.gitattributes.before',
    'docs/productization/task036-monitor-parse-amendment/AMENDMENT.json',
    'docs/productization/task036-monitor-parse-amendment/chromium_resource_worker.py.before',
    'docs/productization/task036-monitor-parse-amendment/compiler_monitor_snapshot_amendment.py.before',
    'docs/productization/task036-monitor-parse-amendment/.gitattributes.before',
    'scripts/compiler_monitor_binding_source_amendment.py',
    'docs/productization/task036-monitor-binding-amendment/AMENDMENT.json',
    'docs/productization/task036-monitor-binding-amendment/.gitattributes.before',
    'docs/productization/task036-monitor-binding-amendment/compiler_monitor_parse_source_amendment.py.before'))
OVERLAY_PATHS=frozenset(('.gitattributes','scripts/compiler_monitor_parse_source_amendment.py',
    'scripts/compiler_monitor_binding_source_amendment.py',
    'docs/productization/task036-monitor-binding-amendment/AMENDMENT.json',
    'docs/productization/task036-monitor-binding-amendment/.gitattributes.before',
    'docs/productization/task036-monitor-binding-amendment/compiler_monitor_parse_source_amendment.py.before'))
REVIEW_FIELDS=frozenset(('schema','reviewer','owner_appointment','candidate','tree','base','base_tree',
    'decision','blocking_findings_remaining','timestamp_utc','amendments','evidence','source_review',
    'checks_performed','checks_not_performed','residual_risks','historical_unknowns','product_accepted'))
AMENDMENT_DIRECTORIES={
    'docs/productization/task036-monitor-snapshot-amendment':frozenset((
        'AMENDMENT.json','chromium_resource_worker.py.before','verify_post_dir.py.before','.gitattributes.before')),
    'docs/productization/task036-monitor-parse-amendment':frozenset((
        'AMENDMENT.json','chromium_resource_worker.py.before','compiler_monitor_snapshot_amendment.py.before',
        '.gitattributes.before')),
    'docs/productization/task036-monitor-binding-amendment':frozenset((
        'AMENDMENT.json','compiler_monitor_parse_source_amendment.py.before','.gitattributes.before'))}

def exact_amendment_namespaces(root):
    """Bounded flat census of authenticated namespaces, never a wildcard exemption."""
    try:
        for relative,expected in AMENDMENT_DIRECTORIES.items():
            directory=Path(root)
            for part in Path(relative).parts:
                directory=directory/part
                metadata=directory.lstat()
                require(stat.S_ISDIR(metadata.st_mode) and not directory.is_symlink() and
                    not (getattr(metadata,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0)),
                    'scene_ir_m1_monitor_source_identity')
            names=set()
            with os.scandir(directory) as entries:
                for entry in entries:
                    require(len(names)<len(expected) and entry.name in expected and entry.name not in names and
                        not entry.is_symlink() and entry.is_file(follow_symlinks=False),
                        'scene_ir_m1_monitor_source_identity')
                    metadata=entry.stat(follow_symlinks=False)
                    require(not (getattr(metadata,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0)),
                        'scene_ir_m1_monitor_source_identity')
                    names.add(entry.name)
            require(names==expected,'scene_ir_m1_monitor_source_identity')
    except OSError:
        require(False,'scene_ir_m1_monitor_source_identity')

def identities():
    """Configuration constants only, never admission without verified_review."""
    return dict(m1_monitor_review=REVIEW_SHA,m1_monitor_bindings=BINDINGS_SHA)

def document(root,path,expected,read):
    require(path in DOCUMENT_BYTES and type(DOCUMENT_BYTES[path]) is int and
        0<DOCUMENT_BYTES[path]<=262144 and type(expected) is str and len(expected)==64,
        'scene_ir_m1_monitor_review_required')
    raw=read(root,path,DOCUMENT_BYTES[path])
    require(len(raw)==DOCUMENT_BYTES[path] and sha(raw)==expected,'scene_ir_m1_monitor_review_identity')
    return strict_json(raw)

def verified_review(root,*,read):
    review=document(root,REVIEW,REVIEW_SHA,read)
    require(type(review) is dict and set(review)==REVIEW_FIELDS and
        type(review['reviewer']) is dict and set(review['reviewer'])=={'execution_identity',
            'implementation_execution','type','role','human_signature','PR_review_submission'} and
        review['reviewer']['role']=='M1-EXTERNAL-TECHNICAL-REVIEWER-001' and
        review['schema']=='bie.task036.m1.monitor-closure-review/1' and
        review['decision']==DECISION and type(review['blocking_findings_remaining']) is int and
        review['blocking_findings_remaining']==0 and review['reviewer']['execution_identity']==REVIEWER and
        review['reviewer']['implementation_execution']=='/root' and
        review['reviewer']['type']=='GENUINELY_SEPARATE_READ_ONLY_AI_ASSISTED_EXECUTION' and
        review['reviewer']['human_signature'] is False and review['reviewer']['PR_review_submission'] is False and
        review['candidate']==CANDIDATE and review['tree']==TREE and review['base']==BASE and
        review['base_tree']==BASE_TREE and review['amendments']==AMENDMENTS and
        review['product_accepted'] is False,'scene_ir_m1_monitor_review_required')
    binding=document(root,BINDINGS,BINDINGS_SHA,read)
    require(type(binding) is dict and set(binding)=={'schema','role','candidate','tree','review_sha256',
        'original_source_chain_sha256','amendments','files','product_accepted'} and
        binding['schema']=='bie.task036.reviewed-monitor-source-bindings/1' and
        binding['role']=='REVIEWED_NATIVE_PARENT_AND_EXACT_ADMISSION_OVERLAY_NOT_AN_APPROVAL' and
        binding['candidate']==CANDIDATE and binding['tree']==TREE and
        binding['review_sha256']==REVIEW_SHA and binding['original_source_chain_sha256']==ORIGINAL_CHAIN_SHA and
        binding['amendments']==AMENDMENTS and binding['product_accepted'] is False,
        'scene_ir_m1_monitor_source_identity')
    exact_amendment_namespaces(root)
    rows=binding['files']
    require(type(rows) is list and len(rows)==len(PATHS) and all(type(r) is dict for r in rows),
        'scene_ir_m1_monitor_source_identity')
    indexed={r['path']:r for r in rows}
    require(len(indexed)==len(rows) and set(indexed)==PATHS,'scene_ir_m1_monitor_source_identity')
    for path,row in indexed.items():
        require(set(row)=={'path','git_blob','raw_git_bytes','raw_git_sha256','mode','bytes','sha256','origin'} and
            row['origin']==('EXACT_REVIEWED_PROSPECTIVE_ADMISSION_OVERLAY' if path in OVERLAY_PATHS else
                'REVIEWED_PARENT_GIT'),
            'scene_ir_m1_monitor_source_identity')
        mode='RAW_IMMUTABLE' if path.startswith('docs/') else 'CRLF_TO_LF_ONLY'
        require(row['mode']==mode and type(row['bytes']) is int and type(row['raw_git_bytes']) is int,
            'scene_ir_m1_monitor_source_identity')
        raw=read(root,path);data=raw if mode=='RAW_IMMUTABLE' else raw.replace(b'\r\n',b'\n')
        require(len(data)==row['bytes'] and sha(data)==row['sha256'],'scene_ir_m1_monitor_source_identity')
        if mode=='RAW_IMMUTABLE':
            require(len(raw)==row['raw_git_bytes'] and sha(raw)==row['raw_git_sha256'] and
                sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob'],
                'scene_ir_m1_monitor_source_identity')
    require(indexed[WORKER]['sha256']==ACTIVE_SHA,'scene_ir_m1_monitor_source_identity')
    # Complete fixed amendment rows already bind both sealed preimages and all
    # active audit seams. Require their actual manifest identities as well.
    for path,expected in AMENDMENTS.items():
        require(sha(read(root,path))==expected,'scene_ir_m1_monitor_source_identity')
    source=review['source_review']
    require(type(source) is dict and set(source)=={'source_bindings','original_review_sha256',
        'original_final_review_sha256','original_binding_sha256','original_chain_sha256',
        'native_scope','admission_overlay_scope'} and source['source_bindings']==rows and
        source['original_review_sha256']=='33458799eaf58951aa474a08d412b6b56361ec2f08aebdc23f150976a92410a5' and
        source['original_final_review_sha256']=='9eb3ff17a7e128d5dd9ac6da6210c9461dfbecf6002c33bb499c8215a492612a' and
        source['original_binding_sha256']=='dbed506a90958c88263dad9280eb2575ec285e79a960952c5c62b4c9f8da53ad' and
        source['original_chain_sha256']==ORIGINAL_CHAIN_SHA and
        source['native_scope']==dict(commit=CANDIDATE,tree=TREE,worker_sha256=ACTIVE_SHA) and
        source['admission_overlay_scope']=='EXACT_READ_ONLY_ADMISSION_AND_RAW_RECORD_EOL_ONLY',
        'scene_ir_m1_monitor_source_identity')
    return {key:value for key,value in indexed[WORKER].items() if key!='origin'}
