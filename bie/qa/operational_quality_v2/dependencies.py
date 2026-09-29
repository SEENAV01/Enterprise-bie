"""HARD031 installed-byte/lock closure and finite vulnerability-review contracts.

No package is imported. Versions alone do not clear vulnerabilities. Review
inventories are independently pinned, exact and dated; unsupported ranges remain
explicitly UNKNOWN. This is not an online vulnerability feed or legal clearance.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from email.parser import Parser
from .common import *

@dataclass(frozen=True)
class DependencyPolicy:
    file_rows:tuple[dict,...]
    packages:tuple[dict,...]
    allowed_scripts:tuple[tuple[str,str,str],...]=()
    max_review_age:int=86400
    def __post_init__(self):
        require(type(self.file_rows) is tuple and bool(self.file_rows),'H7_DEP_FILES')
        paths=[]
        for r in self.file_rows:
            fields(r,('path','sha256','bytes'),'H7_DEP_FILE_FIELDS');safe_relative_path(r['path']);sha256(r['sha256'],'file')
            integer(r['bytes'],'bytes',0,64*1024*1024);paths.append(r['path'])
        require(len(paths)==len(set(paths)),'H7_DEP_FILE_ALIAS')
        require(type(self.packages) is tuple and bool(self.packages),'H7_DEP_PACKAGES')
        names=[];owned=[]
        for p in self.packages:
            fields(p,('package_id','ecosystem','name','version','metadata_path','paths','dependencies'),'H7_PACKAGE_FIELDS')
            token(p['package_id'],'package_id');names.append(p['package_id'])
            require(p['ecosystem'] in ('npm','PyPI','SYSTEM'),'H7_ECOSYSTEM')
            text(p['name'],'package name',256);text(p['version'],'version',128)
            safe_relative_path(p['metadata_path']);require(p['metadata_path'] in p['paths'],'H7_METADATA_UNOWNED')
            require(type(p['paths']) in (list,tuple) and p['paths'],'H7_PACKAGE_PATHS')
            for path in p['paths']:safe_relative_path(path);owned.append(path)
            require(type(p['dependencies']) in (list,tuple),'H7_DEPENDENCIES')
        require(len(names)==len(set(names)),'H7_PACKAGE_ALIAS')
        require(len(owned)==len(set(owned)) and set(owned)==set(paths),'H7_DEP_OWNERSHIP_CENSUS')
        for p in self.packages:
            require(len(p['dependencies'])==len(set(p['dependencies'])) and set(p['dependencies'])<=set(names),'H7_UNRESOLVED_DEPENDENCY')
        require(type(self.allowed_scripts) is tuple and len(self.allowed_scripts)==len(set(self.allowed_scripts)),'H7_SCRIPTS')
        for pid,key,cmd in self.allowed_scripts:
            require(pid in names,'H7_SCRIPT_PACKAGE');text(key,'script name',128);text(cmd,'script command',4096)
        integer(self.max_review_age,'age',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))


def verify_dependencies(root,policy,review,*,approved_review_digest,now):
    require(type(policy) is DependencyPolicy,'H7_DEP_POLICY');integer(now,'now')
    actual=inventory(root);require(actual==list(policy.file_rows),'H7_INSTALLED_BYTE_DRIFT')
    pids={p['package_id']:p for p in policy.packages}
    # Independent recipe is the lock. Actual metadata must agree, including all
    # named requirements and package scripts. Unknown markers/ranges need review.
    for p in policy.packages:
        raw=regular_bytes(root,p['metadata_path']);deps={pids[d]['name'] for d in p['dependencies']}
        if p['ecosystem']=='npm':
            m=strict_object(raw)
            require((m.get('name'),m.get('version'))==(p['name'],p['version']),'H7_INSTALLED_VERSION_DRIFT')
            merged={}
            for key in ('dependencies','optionalDependencies','peerDependencies'):
                v=m.get(key,{})
                require(type(v) is dict and all(type(k) is str and type(x) is str for k,x in v.items()),'H7_NPM_DEP_METADATA')
                merged.update(v)
            require(set(merged)==deps,'H7_UNRESOLVED_IMPORT_CLOSURE')
            for dep_id in p['dependencies']:
                d=pids[dep_id]
                require(merged[d['name']]==d['version'],'H7_UNSUPPORTED_DEPENDENCY_RANGE')
            scripts=m.get('scripts',{});require(type(scripts) is dict,'H7_NPM_SCRIPTS')
            require({(p['package_id'],k,v) for k,v in scripts.items()}=={x for x in policy.allowed_scripts if x[0]==p['package_id']},'H7_UNAPPROVED_INSTALL_SCRIPT')
        elif p['ecosystem']=='PyPI':
            m=Parser().parsestr(raw.decode('utf-8'))
            require((m.get('Name'),m.get('Version'))==(p['name'],p['version']),'H7_INSTALLED_VERSION_DRIFT')
            # Requires-Dist parsing is deliberately exact-name or exact == only.
            observed=set()
            for req in m.get_all('Requires-Dist',[]):
                parts=req.split('==')
                require(len(parts) in (1,2) and not any(c in req for c in ';[<>~!'),'H7_PYTHON_REQUIREMENT_REVIEW')
                name=parts[0].strip();observed.add(name)
                matched=[pids[x] for x in p['dependencies'] if pids[x]['name']==name]
                require(len(matched)==1,'H7_UNRESOLVED_IMPORT_CLOSURE')
                if len(parts)==2:require(parts[1].strip()==matched[0]['version'],'H7_INSTALLED_VERSION_DRIFT')
            require(observed==deps,'H7_UNRESOLVED_IMPORT_CLOSURE')
        else:
            m=strict_object(raw)
            require(m=={'name':p['name'],'version':p['version'],'dependencies':sorted(deps)},'H7_SYSTEM_METADATA')
    fields(review,('schema_version','policy_digest','created_at','expires_at','snapshot_kind','packages'),'H7_REVIEW_FIELDS')
    require(digest(review)==approved_review_digest,'H7_REVIEW_AUTHORITY_DIGEST')
    require(review['schema_version']=='bie.qa.dependency-review/1' and review['policy_digest']==policy.content_digest,'H7_REVIEW_BINDING')
    for k in ('created_at','expires_at'):integer(review[k],k)
    require(review['created_at']<=now<review['expires_at'] and now-review['created_at']<=policy.max_review_age,'H7_REVIEW_STALE')
    require(review['snapshot_kind'] in ('SYNTHETIC','INDEPENDENT_REVIEW'),'H7_REVIEW_KIND')
    rows=review['packages'];require(type(rows) is list and len(rows)==len(pids),'H7_REVIEW_CENSUS')
    require(len({r['package_id'] for r in rows})==len(rows) and {r['package_id'] for r in rows}==set(pids),'H7_REVIEW_CENSUS')
    blockers=[];unknown=[]
    for r in rows:
        fields(r,('package_id','version','status','advisory_ids'),'H7_REVIEW_PACKAGE_FIELDS')
        p=pids[r['package_id']];require(r['version']==p['version'],'H7_REVIEW_VERSION')
        require(r['status'] in ('NO_KNOWN_FINDINGS','AFFECTED','UNKNOWN'),'H7_REVIEW_VERDICT')
        require(type(r['advisory_ids']) is list and len(set(r['advisory_ids']))==len(r['advisory_ids']),'H7_ADVISORIES')
        if r['status']=='AFFECTED':require(bool(r['advisory_ids']),'H7_ADVISORY_EVIDENCE');blockers.append(p['package_id'])
        if r['status']=='UNKNOWN':unknown.append(p['package_id'])
    return dict(schema_version='bie.qa.dependency-closure/1',policy_digest=policy.content_digest,inventory_digest=digest(actual),
        review_digest=approved_review_digest,blocked_packages=sorted(blockers),unknown_packages=sorted(unknown),
        status='BLOCKED' if blockers else 'REVIEW_REQUIRED',installed_bytes_verified=True,
        vulnerability_clearance=False,snapshot_kind=review['snapshot_kind'],product_accepted=False)


def review_osv_exact(snapshot,package,version):
    """Finite explicit affected.versions support. Ranges never guessed or normalized."""
    require(type(snapshot) is list,'H7_OSV_LIST');hits=[];unknown=[]
    for advisory in snapshot:
        require(type(advisory) is dict and type(advisory.get('id')) is str,'H7_OSV_RECORD')
        if advisory.get('withdrawn'):continue
        for r in advisory.get('affected',[]):
            if r.get('package',{}).get('name')!=package:continue
            if version in r.get('versions',[]):hits.append(advisory['id'])
            elif r.get('ranges') or not r.get('versions'):unknown.append(advisory['id'])
    return dict(status='AFFECTED' if hits else 'UNKNOWN' if unknown else 'NO_EXPLICIT_MATCH',advisory_ids=sorted(set(hits)),unsupported_range_ids=sorted(set(unknown)),clearance=False)
