from __future__ import annotations
from dataclasses import dataclass
from .grammar_registry import VisualGrammarRegistry
from .physics_vector_grammar import PHYSICS_VECTOR_GRAMMAR,plan_physics_vectors
from .field_grammar import FIELD_GRAMMAR,plan_field
from .process_flow_grammar import PROCESS_FLOW_GRAMMAR,plan_process_flow
from .biology_cellular_grammar import BIOLOGY_CELLULAR_GRAMMAR,plan_cellular_diagram
from .chemistry_molecular_grammar import CHEMISTRY_MOLECULAR_GRAMMAR,plan_molecule
from .geography_map_grammar import GEOGRAPHY_MAP_GRAMMAR,plan_map
from .history_timeline_grammar import HISTORY_TIMELINE_GRAMMAR,plan_timeline
from .causal_network_grammar import CAUSAL_NETWORK_GRAMMAR,plan_causal_network
from .mathematics_graph_grammar import MATHEMATICS_GRAPH_GRAMMAR,plan_math_graph
from .geometry_grammar import GEOMETRY_GRAMMAR,plan_geometry
from .data_chart_grammar import DATA_CHART_GRAMMAR,plan_chart
from .layout_contracts import Box as LayoutBox,LayoutNode,make_layout_plan
from .layout_solver import solve_layout
from .safe_area import SafeArea
from .subtitle_safe_layout import SubtitleZone
from .asset_need_detection import detect_asset_need
from .text_contracts import TextIntent
from .on_screen_text_selection import select_on_screen_text
from .access_contracts import VisualAccessIntent
from .contrast import evaluate_contrast
from .readable_size import evaluate_readable_size
from .semantic_alignment_qa import SemanticSpec,evaluate_semantic_alignment
from .layout_qa import LayoutElement,Box as QABox,evaluate_layout_qa
from .clutter_qa import evaluate_clutter_qa
class FamilyWiringError(RuntimeError):pass
ALL=(PHYSICS_VECTOR_GRAMMAR,FIELD_GRAMMAR,PROCESS_FLOW_GRAMMAR,BIOLOGY_CELLULAR_GRAMMAR,CHEMISTRY_MOLECULAR_GRAMMAR,GEOGRAPHY_MAP_GRAMMAR,HISTORY_TIMELINE_GRAMMAR,CAUSAL_NETWORK_GRAMMAR,MATHEMATICS_GRAPH_GRAMMAR,GEOMETRY_GRAMMAR,DATA_CHART_GRAMMAR)
PLANNERS={PHYSICS_VECTOR_GRAMMAR.grammar_id:plan_physics_vectors,FIELD_GRAMMAR.grammar_id:plan_field,PROCESS_FLOW_GRAMMAR.grammar_id:plan_process_flow,BIOLOGY_CELLULAR_GRAMMAR.grammar_id:plan_cellular_diagram,CHEMISTRY_MOLECULAR_GRAMMAR.grammar_id:plan_molecule,GEOGRAPHY_MAP_GRAMMAR.grammar_id:plan_map,HISTORY_TIMELINE_GRAMMAR.grammar_id:plan_timeline,CAUSAL_NETWORK_GRAMMAR.grammar_id:plan_causal_network,MATHEMATICS_GRAPH_GRAMMAR.grammar_id:plan_math_graph,GEOMETRY_GRAMMAR.grammar_id:plan_geometry,DATA_CHART_GRAMMAR.grammar_id:plan_chart}
def build_original_grammar_registry():
 r=VisualGrammarRegistry();r.register_many(ALL);return r
@dataclass(frozen=True)
class FamilyResult:
 grammar_plan:object;layout_plan:object;asset_need:object;text_decisions:tuple;access_decisions:tuple;qa_results:tuple;status:str;review_required:bool=True;accepted:bool=False
def execute_original_family_path(*,domain,representation,tags,grammar_inputs,evidence_refs,reasoning_refs,viewport=1280):
 reg=build_original_grammar_registry();res=reg.resolve(domain=domain,representation=representation,tags=tags);planner=PLANNERS[res.grammar.grammar_id]
 kw=dict(grammar_inputs);kw['evidence_refs']=tuple(evidence_refs);kw['reasoning_refs']=tuple(reasoning_refs);gp=planner(**kw)
 nodes=[];n=max(1,len(gp.elements));cols=2 if n>1 else 1;h=max(.08,min(.18,.62/((n+cols-1)//cols)))
 for i,e in enumerate(gp.elements):
  row,col=divmod(i,cols);x=.08+col*.48;y=.08+row*(h+.05);nodes.append(LayoutNode(e['id'],e['role'],LayoutBox(x,y,.36 if cols==2 else .70,h),tuple(e['source_ids']),70,True,payload={'primitive':e['primitive'],'label':e.get('label')}))
 lp=make_layout_plan(evidence_refs=gp.evidence_refs,reasoning_refs=gp.reasoning_refs,nodes=nodes,constraints=(),warnings=gp.warnings);lp,rep=solve_layout(lp,safe_area=SafeArea(),subtitle_zone=SubtitleZone(),avoid_overlap=True)
 if not rep.solved:raise FamilyWiringError('original layout solver failed')
 role='diagram'
 if 'map' in representation:role='map'
 elif 'timeline' in representation or 'chronology' in representation:role='timeline'
 elif 'graph' in representation or 'chart' in representation:role='graph'
 asset=detect_asset_need(need_id='family:asset',semantic_role=role,evidence_refs=evidence_refs,reasoning_refs=reasoning_refs,representation=role)
 td=[]
 for i,e in enumerate(gp.elements):
  if e.get('label'):td.append(select_on_screen_text(TextIntent(f't:{i}',str(e['label']),'label',tuple(evidence_refs),tuple(reasoning_refs),True,50,90),available_char_budget=90))
 if not td:td.append(select_on_screen_text(TextIntent('t:title','Learning visual','title',tuple(evidence_refs),tuple(reasoning_refs))))
 ac=[]
 for i,_ in enumerate(td):
  ai=VisualAccessIntent(f'a:{i}','body',tuple(evidence_refs),tuple(reasoning_refs));ac.extend((evaluate_contrast(ai,foreground='#111111',background='#FFFFFF'),evaluate_readable_size(ai,font_px=24,viewport_width_px=viewport)))
 concepts=tuple(sorted({e['role'] for e in gp.elements}));relations=tuple(sorted({r['kind'] for r in gp.relations}))
 sem=evaluate_semantic_alignment(SemanticSpec(concepts,relations,tuple(evidence_refs),tuple(reasoning_refs),()),concepts,relations,(),tuple(evidence_refs))
 les=tuple(LayoutElement(x.node_id,x.role,QABox(x.box.x,x.box.y,x.box.width,x.box.height),x.required) for x in lp.nodes);lq=evaluate_layout_qa(les,tuple(evidence_refs),tuple(reasoning_refs));cq=evaluate_clutter_qa(len(lp.nodes),sum(len(t.display_text) for t in td),0,len(gp.relations),0,1,tuple(evidence_refs),tuple(reasoning_refs))
 blocked=not sem.passed or not lq.passed or not cq.passed or any(getattr(a,'action','').endswith('revise') or getattr(a,'action','').startswith('increase') for a in ac)
 return FamilyResult(gp,lp,asset,tuple(td),tuple(ac),(sem,lq,cq),'BLOCKED' if blocked else 'PASS')
