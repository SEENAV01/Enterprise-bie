from __future__ import annotations
import ast
from pathlib import Path
from .contracts import *
from .common import *
BANNED_NAMES={'topic_keyword_game','keyword_game_generator','generate_game_from_keywords','slide_deck_generator','mcq_only_generator'}
BANNED_CALLS={'eval','exec','compile'}
def evaluate(source_root:Path):
    source_root=Path(source_root);findings=[];files=sorted(source_root.rglob('*.py'));scanned=0
    dynamic_imports=[]
    for p in files:
        if '__pycache__' in p.parts:continue
        if p.resolve()==Path(__file__).resolve():continue
        try:tree=ast.parse(p.read_text())
        except SyntaxError as e:findings.append(finding('BIE-GAME-QA-010',len(findings)+1,'SOURCE_SYNTAX_ERROR',p.name+':'+str(e),severity=Severity.CRITICAL));continue
        scanned+=1
        for n in ast.walk(tree):
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name.lower() in BANNED_NAMES:findings.append(finding('BIE-GAME-QA-010',len(findings)+1,'LEGACY_GENERATOR_PRESENT',p.name+':'+n.name,severity=Severity.CRITICAL))
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in BANNED_CALLS:findings.append(finding('BIE-GAME-QA-010',len(findings)+1,'UNSAFE_DYNAMIC_EXECUTION',p.name+':'+n.func.id,severity=Severity.CRITICAL))
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='__import__':dynamic_imports.append(p.name)
            if isinstance(n,ast.If):
                src=ast.unparse(n.test).lower()
                if 'keyword' in src and ('topic' in src or 'text' in src):findings.append(finding('BIE-GAME-QA-010',len(findings)+1,'KEYWORD_ROUTING_PRESENT',p.name+':'+src[:120],severity=Severity.CRITICAL))
    # explicit quality-intent evidence must exist
    q=source_root/'quality_intent.py'
    if not q.exists():findings.append(finding('BIE-GAME-QA-010',900,'QUALITY_INTENT_MISSING','quality_intent.py missing',severity=Severity.CRITICAL))
    else:
        text=q.read_text()
        for token in ('anti_slide_default','mcq_only_core_experience_forbidden','semantic_visuals_required'):
            if token not in text:findings.append(finding('BIE-GAME-QA-010',901,'ANTI_LEGACY_POLICY_MISSING',token))
    if dynamic_imports:findings.append(finding('BIE-GAME-QA-010',950,'STATIC_IMPORT_HARDENING_OBSERVATION',','.join(sorted(set(dynamic_imports))),severity=Severity.WARNING,blocking=False))
    blocking=sum(f.blocking for f in findings);score=1.0 if blocking==0 else max(0,1-.1*blocking);metrics=(QualityMetric('source_files_scanned',float(scanned),1,None,'count'),QualityMetric('blocking_legacy_findings',float(blocking),0,0,'count'),QualityMetric('dynamic_import_observations',float(len(set(dynamic_imports))),0,None,'count'))
    return result('BIE-GAME-QA-010',{'root':source_root.as_posix(),'files':scanned},score,metrics,findings,('source-scan',))
