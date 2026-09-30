from pathlib import Path
import sys,json,hashlib,math
from copy import deepcopy
import argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
p=argparse.ArgumentParser(description='Rebuild manually authored Batch003 fixtures without invoking domain solvers or metric evaluators.')
p.add_argument('--output-dir',required=True);options=p.parse_args();R=Path(options.output_dir)
R.mkdir(parents=True,exist_ok=False)
from bie.evaluation.benchmarks.models import BenchmarkCase,SourceReference,digest
D=R/'bie/evaluation/benchmarks/data'
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def q(x,u):return {'value':x,'unit':u}
def ok(v):return {'status':'OK','values':v}
def bad(code):return {'status':'REJECTED','error_code':code}
refs={
 'maps':('noaa-coordinates','NOAA National Ocean Service: latitude','Coordinate angle definition and DMS subdivisions','https://oceanservice.noaa.gov/facts/latitude.html'),
 'climate':('nasa-energy-budget','NASA: Climate and Earth energy budget','Global-mean geometry, absorption and thermal radiation','https://science.nasa.gov/earth/earth-observatory/climate-and-earths-energy-budget/'),
 'normal':('noaa-climate-normal','NOAA NCEI: Climate Normals','30-year reference period; this fixture uses a simpler complete annual series','https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals'),
 'civics':('uk-parliament-roles','UK Parliament and Government','Descriptive institution roles, consulted 2026-09-29','https://www.parliament.uk/about/how/role/relations-with-other-institutions/parliament-government/'),
 'bill':('uk-bill-stages','UK Parliament: passage of a Bill','Introductory ordinary two-house legislative procedure','https://www.parliament.uk/about/how/laws/passage-bill/'),
 'data':('nist-central-location','NIST: Measures of Location','Arithmetic mean and even/odd median definitions','https://www.itl.nist.gov/div898/handbook/eda/section3/eda351.htm')}
def source(k):
 a,b,c,d=refs[k];return SourceReference(a,b,c,d,'Reference link only; original authored problems/derivations. No source passages, images or textbook exercises redistributed. No golden or independently reviewed claim.')
CASES={}
def add(task,domain,title,inputs,expected,derivation,refkeys):
 rows=CASES.setdefault(task,[]);idx=len(rows)+1
 case=BenchmarkCase.create(case_id=f'{task}.C{idx:03}',task_id=task,domain=domain,title=title,
     prompt=f'{task} authored diagnostic {idx}: {title}. Evaluate only the explicitly declared {domain} profile; do not infer unstated source facts or conventions.',
     inputs=inputs,expected=expected,split='DEVELOPMENT',leakage_group=task+'.batch003',author_id='bie-author-batch003',
     derivation=derivation,sources=tuple(source(k) for k in refkeys),tags=(inputs['op'],'batch003','authored'),
     absolute_tolerance=1e-8,relative_tolerance=1e-9)
 rows.append(case.to_dict())
t='BIE-EVAL-GEO-002'
a=lambda title,i,e,d:add(t,'maps',title,i,e,d,['maps'])
a('Printed length to ground distance',{'op':'scale_distance','map_length':q(2,'cm'),'scale_denominator':50000},ok({'ground_m':'1000','profile':'PRINTED_REPRESENTATIVE_FRACTION'}),'0.02 m times 50000 = 1000 m; no map resizing assumed.')
a('A fractional centimetre remains exact',{'op':'scale_distance','map_length':q('1/3','cm'),'scale_denominator':30000},ok({'ground_m':'100','profile':'PRINTED_REPRESENTATIVE_FRACTION'}),'(1/3)/100 times 30000 = 100 m.')
a('Area scales by the square',{'op':'scale_area','map_area':q(4,'cm2'),'scale_denominator':10000},ok({'ground_m2':'40000','profile':'UNIFORM_PLANAR_SCALE_AREA'}),'4/10000 square metre times 10000 squared = 40000.')
a('West DMS is negative longitude',{'op':'dms','axis':'longitude','degrees':73,'minutes':30,'seconds':0,'hemisphere':'W'},ok({'decimal_degrees':'-147/2','axis':'longitude'}),'West negates 73+30/60.')
a('South pole accepts zero smaller parts',{'op':'dms','axis':'latitude','degrees':90,'minutes':0,'seconds':0,'hemisphere':'S'},ok({'decimal_degrees':'-90','axis':'latitude'}),'The signed pole coordinate is -90 degrees.')
a('Identical spherical endpoints',{'op':'spherical_distance','a':{'latitude_deg':0,'longitude_deg':0},'b':{'latitude_deg':0,'longitude_deg':0},'sphere_radius_m':1000},ok({'distance_m':0.0,'central_angle_rad':0.0,'profile':'DECLARED_SPHERE_NOT_ELLIPSOID'}),'Coincident endpoints have zero central angle.')
a('Quarter circle on a supplied sphere',{'op':'spherical_distance','a':{'latitude_deg':0,'longitude_deg':0},'b':{'latitude_deg':0,'longitude_deg':90},'sphere_radius_m':1000},ok({'distance_m':1570.7963267948965,'central_angle_rad':1.5707963267948966,'profile':'DECLARED_SPHERE_NOT_ELLIPSOID'}),'90 degrees = pi/2 radians; arc length =1000 pi/2.')
a('East is clockwise bearing ninety',{'op':'planar_bearing','delta_east_m':3,'delta_north_m':0},ok({'bearing_deg':90.0,'distance_m':3.0,'profile':'CLOCKWISE_FROM_GRID_NORTH'}),'Positive east with zero north is 90 degrees from grid north.')
a('Zero representative-fraction denominator rejected',{'op':'scale_distance','map_length':q(2,'cm'),'scale_denominator':0},bad('QUANTITY_OUT_OF_PROFILE'),'Scale must be strictly positive.')
a('Pole overflow rejected',{'op':'dms','axis':'latitude','degrees':90,'minutes':0,'seconds':1,'hemisphere':'N'},bad('INVALID_DMS'),'90 degrees plus a positive second exceeds the latitude bound.')
a('Undefined zero-displacement bearing rejected',{'op':'planar_bearing','delta_east_m':0,'delta_north_m':0},bad('BEARING_UNDEFINED_AT_ZERO_DISTANCE'),'A zero vector has no bearing.')
a('Square-length unit cannot be used for map length',{'op':'scale_distance','map_length':q(2,'m2'),'scale_denominator':100},bad('UNSUPPORTED_ENUM'),'Length and area units are distinct typed inputs.')
t='BIE-EVAL-GEO-003'
a=lambda title,i,e,d,rs=['climate']:add(t,'climate',title,i,e,d,rs)
baseline={'op':'temperature_anomaly','baseline_start':1991,'baseline_end':2020,'annual_means':[{'year':y,'temperature':q(10,'degC')} for y in range(1991,2021)],'observation':q(12,'degC')}
planet={'op':'planetary_budget','solar_constant_W_m2':1000,'albedo':1,'emissivity':1}
a('Perfect reflection yields zero ideal absorbed flux',planet,ok({'absorbed_W_m2':'0','reflected_W_m2':'250','effective_radiating_temperature_K':0.0,'profile':'GLOBAL_MEAN_STEADY_STATE_EFFECTIVE_NOT_SURFACE'}),'Global mean incident flux is 1000/4. Albedo one reflects it all in this ideal model.')
a('Catchment storage accumulation',{'op':'water_budget','precipitation':q(10,'cm'),'evapotranspiration':q(40,'mm'),'runoff':q(30,'mm')},ok({'storage_change_mm':'30','profile':'CLOSED_CATCHMENT_INTERVAL_NO_LATERAL_IMPORT'}),'100 - 40 - 30 =30 mm.')
a('Catchment storage drawdown',{'op':'water_budget','precipitation':q(20,'mm'),'evapotranspiration':q(40,'mm'),'runoff':q(10,'mm')},ok({'storage_change_mm':'-30','profile':'CLOSED_CATCHMENT_INTERVAL_NO_LATERAL_IMPORT'}),'20 -40 -10 = -30 mm; storage can decrease.')
a('Complete thirty-year baseline anomaly',baseline,ok({'baseline_mean_degC':'10','anomaly_degC':'2','profile':'COMPLETE_EQUAL_YEAR_MEANS_NO_HOMOGENIZATION'}),'All thirty annual means are 10; observation minus mean is 2.', ['normal'])
b=deepcopy(baseline);b['observation']=q('5703/20','K')
a('Absolute temperature unit converted before anomaly',b,ok({'baseline_mean_degC':'10','anomaly_degC':'2','profile':'COMPLETE_EQUAL_YEAR_MEANS_NO_HOMOGENIZATION'}),'285.15 K =12 C; anomaly is 2 C.', ['normal'])
a('Area-weighted means are not unweighted means',{'op':'area_weighted_temperature','regions':[{'id':'small','area_km2':1,'temperature':q(0,'degC')},{'id':'large','area_km2':3,'temperature':q(20,'degC')}]},ok({'mean_degC':'15','total_area_km2':'4','profile':'DECLARED_NONOVERLAPPING_AREA_WEIGHTS'}),'(1*0+3*20)/4=15 C.')
a('Declared two-negative feedback is reinforcing',{'op':'feedback_loop','links':[{'from':'a','to':'b','sign':'-'},{'from':'b','to':'a','sign':'-'}]},ok({'loop_sign':1,'feedback':'reinforcing','profile':'DECLARED_LINK_POLARITY_NOT_EMPIRICAL_ATTRIBUTION'}),'Two negative factors multiply to positive; no empirical attribution follows.')
a('Declared single-negative feedback is balancing',{'op':'feedback_loop','links':[{'from':'a','to':'b','sign':'+'},{'from':'b','to':'a','sign':'-'}]},ok({'loop_sign':-1,'feedback':'balancing','profile':'DECLARED_LINK_POLARITY_NOT_EMPIRICAL_ATTRIBUTION'}),'The sign product is negative.')
b=deepcopy(baseline);b['annual_means'][0]['year']=1992
a('Duplicate year cannot conceal a missing baseline year',b,bad('DUPLICATE_YEAR'),'Two copies of 1992 do not supply 1991.', ['normal'])
b=deepcopy(baseline);b['baseline_end']=2019
a('Twenty-nine years are not the declared thirty-year profile',b,bad('EXACT_30_YEAR_BASELINE_REQUIRED'),'Inclusive 1991 through 2019 covers only 29 years.', ['normal'])
b=deepcopy(planet);b['emissivity']=0
a('Zero emissivity fails the thermal equilibrium model',b,bad('ZERO_EMISSIVITY'),'Radiative temperature formula divides by a strictly positive emissivity.')
a('Temperature below absolute zero rejected',{'op':'area_weighted_temperature','regions':[{'id':'r','area_km2':1,'temperature':q(-1,'K')}]},bad('BELOW_ABSOLUTE_ZERO'),'Kelvin must not be negative.')
t='BIE-EVAL-CIV-001'
a=lambda title,i,e,d,rs=['civics']:add(t,'civics',title,i,e,d,rs)
profile='UK_INTRO_2026-09-29';roles={'government_and_parliament_identical':False,'day_to_day_public_administration':'government','scrutinises_government':'parliament','ministers_can_also_sit_in_parliament':True,'bill_is_already_an_act':False}
def ra(claims,defects):return ok({'consistent':not defects,'defects':defects,'assessment_scope':'DECLARED_PROPOSITION_PROFILE_ONLY','jurisdiction':'UK','reference_profile':profile})
a('Descriptive institutional roles match selected official profile',{'op':'audit_roles','profile':profile,'claims':roles},ra(roles,[]),'Compare five typed educational propositions with the consulted introductory institutional-role profile. No political merit is judged.')
b=deepcopy(roles);b['government_and_parliament_identical']=True
a('Government and parliament are not identical',{'op':'audit_roles','profile':profile,'claims':b},ra(b,[{'claim':'government_and_parliament_identical','reason':'CONTRADICTED_CLAIM'}]),'The selected official introductory source distinguishes their roles.')
b=deepcopy(roles);del b['scrutinises_government']
a('Omitted scrutiny proposition remains a defect',{'op':'audit_roles','profile':profile,'claims':b},ra(b,[{'claim':'scrutinises_government','reason':'MISSING_CLAIM'}]),'Required descriptive assertions cannot be omitted to appear correct.')
def trace(events,e):a('Ordinary bill trace: '+','.join(events),{'op':'ordinary_bill_trace','profile':profile,'route':'ordinary_two_house_bill','events':events},ok(e),'Apply introduction, both-house agreement and assent dependencies only within the stated ordinary route.', ['bill'])
trace(['introduced','commons_agreed','lords_agreed','royal_assent'],{'trace_consistent':True,'act_in_this_profile':True,'defects':[],'profile':'ORDINARY_TWO_HOUSE_BILL_NOT_EXCEPTIONS'})
trace(['introduced','lords_agreed','commons_agreed','royal_assent'],{'trace_consistent':True,'act_in_this_profile':True,'defects':[],'profile':'ORDINARY_TWO_HOUSE_BILL_NOT_EXCEPTIONS'})
trace(['introduced','commons_agreed'],{'trace_consistent':True,'act_in_this_profile':False,'defects':[],'profile':'ORDINARY_TWO_HOUSE_BILL_NOT_EXCEPTIONS'})
trace(['introduced','royal_assent'],{'trace_consistent':False,'act_in_this_profile':False,'defects':[{'event':'royal_assent','reason':'BOTH_HOUSES_AGREEMENT_REQUIRED_IN_PROFILE'}],'profile':'ORDINARY_TWO_HOUSE_BILL_NOT_EXCEPTIONS'})
b={'op':'fictional_competence','jurisdiction':'FICTIONAL_EDUCATIONAL_SCENARIO','institutions':[{'id':'assembly','powers':['make_statute']},{'id':'council','powers':['run_services']}],'request':{'institution':'council','power':'run_services'}}
a('Assigned power in an explicitly fictional scenario',b,ok({'assigned_in_supplied_scenario':True,'jurisdiction':'FICTIONAL_EDUCATIONAL_SCENARIO','policy_merit_evaluated':False}),'Set membership in the supplied fictional rule table, not a real legal opinion.')
b=deepcopy(b);b['request']['power']='make_statute'
a('Unassigned power in the same fictional scenario',b,ok({'assigned_in_supplied_scenario':False,'jurisdiction':'FICTIONAL_EDUCATIONAL_SCENARIO','policy_merit_evaluated':False}),'The supplied council powers do not include make_statute.')
a('Unknown country profile rejected',{'op':'audit_roles','profile':'ANY_COUNTRY','claims':roles},bad('UNSUPPORTED_ENUM'),'A UK-specific profile is not universal.')
a('Special legislative routes are not silently approximated',{'op':'ordinary_bill_trace','profile':profile,'route':'special_route','events':['introduced']},bad('UNSUPPORTED_ENUM'),'Special routes require separately reviewed fixtures.')
a('Duplicate legislative events rejected',{'op':'ordinary_bill_trace','profile':profile,'route':'ordinary_two_house_bill','events':['introduced','introduced']},bad('DUPLICATE_EVENT'),'Repeated events are malformed traces.')
t='BIE-EVAL-DATA-001'
a=lambda title,i,e,d:add(t,'tables_charts',title,i,e,d,['data'])
rows=lambda vs:[{'id':f'r{i}','value':v} for i,v in enumerate(vs)]
a('Odd-sample mean and median differ',{'op':'summary','rows':rows([1,2,9]),'missing_policy':'reject'},ok({'sum':'12','mean':'4','median':'2','observed_count':3,'missing_count':0,'excluded_ids':[]}),'Sorted [1,2,9] has midpoint 2 and mean12/3.')
a('Even-sample median averages the middle pair',{'op':'summary','rows':rows([4,1,9,2]),'missing_policy':'reject'},ok({'sum':'16','mean':'4','median':'3','observed_count':4,'missing_count':0,'excluded_ids':[]}),'Sorted [1,2,4,9] has middle-pair mean3.')
a('Explicit missing-value exclusion reports its denominator',{'op':'summary','rows':rows([None,0,4]),'missing_policy':'exclude_explicit'},ok({'sum':'4','mean':'2','median':'2','observed_count':2,'missing_count':1,'excluded_ids':['r0']}),'Missing r0 is excluded, not treated as observed zero.')
a('Negative relative change',{'op':'percent_change','before':100,'after':80},ok({'absolute_change':'-20','percent_change':'-20','profile':'POSITIVE_BASE_RELATIVE_CHANGE'}),'(80-100)/100 times100=-20%.')
a('Fractional relative increase',{'op':'percent_change','before':3,'after':4},ok({'absolute_change':'1','percent_change':'100/3','profile':'POSITIVE_BASE_RELATIVE_CHANGE'}),'A one-unit rise on a base of3 is100/3 percent.')
a('Weights change the mean',{'op':'weighted_mean','rows':[{'id':'a','value':10,'weight':1},{'id':'b','value':20,'weight':3}]},ok({'weighted_mean':'35/2','total_weight':'4'}),'(10+60)/4=17.5.')
chart={'op':'chart_fidelity','source_rows':rows([10,20]),'chart_points':list(reversed(rows([10,20]))),'source_unit':'count','chart_unit':'count','chart_type':'bar','y_axis':{'minimum':0,'maximum':25,'scale':'linear'}}
a('Chart correspondence uses row identity rather than row order',chart,ok({'data_faithful':True,'defects':[],'presentation_warnings':[],'profile':'STRUCTURED_DATA_FIDELITY_NOT_RENDER_INSPECTION'}),'Row IDs and cell values agree despite the displayed order.')
b=deepcopy(chart);b['y_axis']['minimum']=5
a('Truncated bar baseline is explicit presentation warning',b,ok({'data_faithful':True,'defects':[],'presentation_warnings':['BAR_ZERO_BASELINE_NOT_VISIBLE'],'profile':'STRUCTURED_DATA_FIDELITY_NOT_RENDER_INSPECTION'}),'All values match and fit the axis, but zero is not visible; do not claim overall visual fidelity.')
a('Missing cells rejected under strict policy',{'op':'summary','rows':rows([1,None]),'missing_policy':'reject'},bad('MISSING_CELL'),'Strict policy refuses imputation.')
a('All-missing table cannot claim a zero mean',{'op':'summary','rows':rows([None,None]),'missing_policy':'exclude_explicit'},bad('NO_OBSERVED_VALUES'),'No observed denominator exists.')
a('Relative percent change from zero is undefined here',{'op':'percent_change','before':0,'after':10},bad('QUANTITY_OUT_OF_PROFILE'),'The positive-base profile refuses zero.')
a('Zero total weight cannot produce a mean',{'op':'weighted_mean','rows':[{'id':'a','value':2,'weight':0}]},bad('ZERO_TOTAL_WEIGHT'),'Weighted means require positive total weight.')
for task,cs in CASES.items():
 assert len(cs)==12;write(D/(task+'.json'),cs)
# Metric fixture references and expectations are authored here independently of
# evaluator execution; changing the evaluator never regenerates expected scores.
M=R/'bie/evaluation/benchmarks/metrics/fixtures';M.mkdir(parents=True,exist_ok=True)
def env(mid,payload,desc):return {'schema_version':'1.0.0','metric_id':mid,'rubric_id':mid+'.development-v1','version':'1.0.0','reference_owner_id':'bie-author-batch003','evidence_grade':'AUTHORED_DIAGNOSTIC','source_refs':[{'id':'authored-basis','locator':desc,'basis_sha256':hashlib.sha256(desc.encode()).hexdigest()}],'payload':payload}
def fixture(mid,payload,good,mutations,desc,artifacts={}):
 cs=[{'id':'positive','candidate':deepcopy(good),'expected_outcome':'PASS','expected_score_exact':'1','expected_reason':None}]
 for name,fn,score,reason in mutations:
  c=deepcopy(good);fn(c);cs.append({'id':name,'candidate':c,'expected_outcome':'FAIL','expected_score_exact':score,'expected_reason':reason})
 obj={'reference':env(mid,payload,desc),'source_artifacts':artifacts,'cases':cs,'fixture_origin':'ORIGINAL_AUTHORED_DEVELOPMENT_NOT_GOLDEN','expected_values_authored_without_calling_evaluator':True}
 write(M/(mid+'.json'),obj)
def change(c,path,v):
 for p in path[:-1]:c=c[p]
 c[path[-1]]=v
texts={'doc':'A force vector has magnitude and direction. An ideal isolated system conserves momentum.'}
h=lambda s:hashlib.sha256(s.encode()).hexdigest()
split=texts['doc'].index(' An')
prop1={'subject':'force','predicate':'has','object':'magnitude_and_direction'};prop2={'subject':'isolated_system','predicate':'conserves','object':'momentum'}
gp={'sources':[{'id':'doc','text_sha256':h(texts['doc']),'locator':'Original authored explanatory text, Unicode codepoint offsets'}],
    'claims':[{'id':'c1','weight':2,'proposition':prop1,'supports':[{'source_id':'doc','start':0,'end':split,'span_sha256':h(texts['doc'][:split])}]},
              {'id':'c2','weight':1,'proposition':prop2,'supports':[{'source_id':'doc','start':split+1,'end':len(texts['doc']),'span_sha256':h(texts['doc'][split+1:])}]}]}
good={'claims':[{'id':'c1','proposition':prop1,'citations':[{'source_id':'doc','start':0,'end':split}]},{'id':'c2','proposition':prop2,'citations':[{'source_id':'doc','start':split+1,'end':len(texts['doc'])}]}]}
fixture('BIE-EVAL-METRIC-001',gp,good,[
 ('wrong_proposition',lambda c:change(c,['claims',0,'proposition','object'],'magnitude_only'),'1/3','PROPOSITION_MISMATCH'),
 ('missing_claim',lambda c:c['claims'].pop(0),'1/3','MISSING_CLAIM'),
 ('missing_citation',lambda c:change(c,['claims',0,'citations'],[]),'1/3','UNCITED_CLAIM'),
 ('unannotated_span',lambda c:change(c,['claims',0,'citations',0,'end'],split-1),'1/3','CITATION_NOT_ANNOTATED_SUPPORT'),
 ('empty_output',lambda c:change(c,['claims'],[]),'0','MISSING_CLAIM')],
 'Two original typed claims manually bound to authored explanatory spans; weights2 and1; exact span binding is not automatic entailment.',texts)
sp={'concepts':[{'id':'vector','weight':2,'facets':{'has_magnitude':True,'has_direction':True}},{'id':'force','weight':1,'facets':{'is_vector':True}}],
    'relations':[{'id':'r','weight':1,'from':'force','predicate':'instance_of','to':'vector'}]}
good={'concepts':[{'id':'vector','facets':{'has_magnitude':True,'has_direction':True}},{'id':'force','facets':{'is_vector':True}}],
      'relations':[{'id':'r','from':'force','predicate':'instance_of','to':'vector'}]}
fixture('BIE-EVAL-METRIC-002',sp,good,[
 ('wrong_facet',lambda c:change(c,['concepts',0,'facets','has_direction'],False),'3/4','INCORRECT_FACET:has_direction'),
 ('missing_concept',lambda c:c['concepts'].pop(0),'1/4','MISSING_CONCEPT'),
 ('wrong_relation',lambda c:change(c,['relations',0,'to'],'force'),'3/4','RELATION_MISMATCH'),
 ('missing_facet',lambda c:c['concepts'][0]['facets'].pop('has_direction'),'3/4','MISSING_FACET:has_direction'),
 ('empty_output',lambda c:(change(c,['concepts'],[]),change(c,['relations'],[])),'0','MISSING_CONCEPT')],
 'Manually annotated vector/force facets; concept weights2+1 and relation1. Facet credit is matched fraction per concept, not string similarity.')
pp={'nodes':['charge','vector','force'],'edges':[{'id':'qf','weight':2,'prerequisite':'charge','dependent':'force'},{'id':'vf','weight':1,'prerequisite':'vector','dependent':'force'}],
    'targets':['force'],'known_prior':[]}
good={'teaching_order':['charge','vector','force']}
fixture('BIE-EVAL-METRIC-003',pp,good,[
 ('reversed_order',lambda c:change(c,['teaching_order'],['force','charge','vector']),'1/2','PREREQUISITE_NOT_BEFORE_USE'),
 ('missing_prerequisite',lambda c:change(c,['teaching_order'],['vector','force']),'1/2','REQUIRED_NODE_MISSING'),
 ('only_target',lambda c:change(c,['teaching_order'],['force']),'1/6','PREREQUISITE_NOT_BEFORE_USE'),
 ('missing_target',lambda c:change(c,['teaching_order'],['charge','vector']),'1/3','DEPENDENT_NOT_TAUGHT'),
 ('empty_output',lambda c:change(c,['teaching_order'],[]),'0','REQUIRED_NODE_MISSING')],
 'Illustrative trusted prerequisite DAG, not claimed universal pedagogy. Three node requirements weight1 plus edges weights2+1; total6.')
rp={'facts':[{'id':'f1','atom':'P'},{'id':'f2','atom':'Q'}],'rules':[{'id':'r1','antecedents':['P'],'consequent':'R'},{'id':'r2','antecedents':['R','Q'],'consequent':'S'}],
    'goals':[{'id':'g1','atom':'R','weight':1},{'id':'g2','atom':'S','weight':2}]}
good={'steps':[{'id':'s1','rule_id':'r1','premises':['f1'],'conclusion':'R'},{'id':'s2','rule_id':'r2','premises':['s1','f2'],'conclusion':'S'}]}
fixture('BIE-EVAL-METRIC-004',rp,good,[
 ('missing_last_step',lambda c:c['steps'].pop(),'1/3','GOAL_NOT_DERIVED'),
 ('unlicensed_rule',lambda c:change(c,['steps',0,'rule_id'],'invented'),'0','UNLICENSED_RULE'),
 ('missing_premise',lambda c:change(c,['steps',1,'premises'],['s1']),'1/3','RULE_ANTECEDENTS_MISMATCH'),
 ('extra_invalid_step',lambda c:c['steps'].append({'id':'bad','rule_id':'fake','premises':[],'conclusion':'X'}),'1','UNLICENSED_RULE'),
 ('empty_output',lambda c:change(c,['steps'],[]),'0','GOAL_NOT_DERIVED')],
 'Finite Horn proof P->R and R,Q->S with trusted P,Q; required R weight1, S weight2. Invalid extra steps still cause FAIL even at full goal credit.')
def ck(i,w,k,v):return {'id':i,'weight':w,'kind':k,'expected':v,'absolute_tolerance':0,'relative_tolerance':0}
mp={'checks':[ck('length',1,'quantity',q(1,'m')),ck('poly',1,'polynomial',[1,2,1]),ck('rf',2,'rational_function',{'numerator':[-1,0,1],'denominator_roots':[1],'excluded_values':[1]})]}
good={'checks':[{'id':'length','value':q(100,'cm')},{'id':'poly','value':[1,2,1,0]},{'id':'rf','value':{'numerator':[1,1],'denominator_roots':[],'excluded_values':[1]}}]}
fixture('BIE-EVAL-METRIC-005',mp,good,[
 ('wrong_dimension',lambda c:change(c,['checks',0,'value','unit'],'s'),'3/4','DIMENSION_MISMATCH'),
 ('lost_domain_hole',lambda c:change(c,['checks',2,'value','excluded_values'],[]),'1/2','DOMAIN_EXCLUSIONS_MISMATCH'),
 ('missing_length',lambda c:c['checks'].pop(0),'3/4','MISSING_MATH_CHECK'),
 ('wrong_polynomial',lambda c:change(c,['checks',1,'value'],[1,1,1]),'3/4','POLYNOMIAL_IDENTITY_MISMATCH'),
 ('empty_output',lambda c:change(c,['checks'],[]),'0','MISSING_MATH_CHECK')],
 '100cm=1m; (1+x)^2=1+2x+x^2. (x^2-1)/(x-1)=x+1 only with x=1 excluded. Check weights1,1,2.')
cp={'model':[{'id':'U','intercept':2,'noise':0,'parents':[]},{'id':'X','intercept':0,'noise':0,'parents':[{'node':'U','coefficient':1}]},
             {'id':'Y','intercept':0,'noise':0,'parents':[{'node':'X','coefficient':3},{'node':'U','coefficient':4}]}],
    'queries':[{'id':'q1','weight':2,'interventions':{'X':0},'target':'Y','inference_kind':'intervention'},
               {'id':'q2','weight':1,'interventions':{'X':1},'target':'Y','inference_kind':'counterfactual_fixed_noise'}]}
good={'edges':[{'from':'U','to':'X'},{'from':'X','to':'Y'},{'from':'U','to':'Y'}],
      'queries':[{'id':'q1','value':8,'inference_kind':'intervention'},{'id':'q2','value':11,'inference_kind':'counterfactual_fixed_noise'}]}
fixture('BIE-EVAL-METRIC-006',cp,good,[
 ('confounder_dropped',lambda c:change(c,['queries',0,'value'],0),'2/3','INTERVENTION_VALUE_MISMATCH'),
 ('missing_graph',lambda c:change(c,['edges'],[]),'1/2','CAUSAL_EDGE_MISSING_OR_REVERSED'),
 ('reversed_edge',lambda c:change(c,['edges',0],{'from':'X','to':'U'}),'5/6','UNSUPPORTED_CAUSAL_EDGE'),
 ('association_not_intervention',lambda c:change(c,['queries',0,'inference_kind'],'association'),'2/3','INFERENCE_KIND_MISMATCH'),
 ('empty_output',lambda c:(change(c,['edges'],[]),change(c,['queries'],[])),'0','MISSING_CAUSAL_QUERY')],
 'Original deterministic SCM U=2,X=U,Y=3X+4U. do(X=0) yields8; do(X=1) with fixed noise yields11. Three edges weight1 plus queries2+1.')
write(R/'metadata/section17/BATCH003_REFERENCE_CATALOG.json',{'consulted_date':'2026-09-29','reference_only':True,'reference_entries':[{'key':k,'id':v[0],'title':v[1],'locator':v[2],'url':v[3]} for k,v in refs.items()],
 'additional_primary_references':[{'title':'Python fractions documentation','url':'https://docs.python.org/3/library/fractions.html','scope':'Exact rational arithmetic and binary-float distinction'},
 {'title':'W3C PROV-DM','url':'https://www.w3.org/TR/prov-dm/','scope':'Provenance vocabulary inspiration, not a claim of PROV conformance'}],
 'captured_external_text_redistributed':False,'metric_rubrics_origin':'Original authored mathematical/structured diagnostics; not validated external benchmark standard','rights':'No external source passages, figures or exercise text included.'})
print({t:len(v) for t,v in CASES.items()})
