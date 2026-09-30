"""Author Batch002 fixtures. Expected outputs are authored below, NEVER solve().

New problems, small factual event references and hypothetical causal dossiers.
This is NOT an independently reviewed golden or held-out source corpus.
"""
from pathlib import Path
from copy import deepcopy
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import BenchmarkCase,SourceReference
SOURCES={
 'light':('openstax-bio-light','Biology 2e','8.2 water splitting and oxygen evolution','https://openstax.org/books/biology-2e/pages/8-2-the-light-dependent-reactions-of-photosynthesis'),
 'subduction':('usgs-subduction-intro','US Geological Survey','Introduction to subduction zones and volcanic arcs','https://www.usgs.gov/special-topics/subduction-zone-science/science/introduction-subduction-zones-amazing-events'),
 'calvin':('openstax-bio-calvin','Biology 2e','8.3 Calvin cycle resource bookkeeping','https://openstax.org/books/biology-2e/pages/8-3-using-light-energy-to-make-organic-molecules'),
 'inheritance':('openstax-bio-inheritance','Biology 2e','12.3 segregation and independent assortment','https://openstax.org/books/biology-2e/pages/12-3-laws-of-inheritance'),
 'hw':('openstax-bio-population','Biology 2e','19.1 two-allele Hardy-Weinberg model','https://openstax.org/books/biology-2e/pages/19-1-population-evolution'),
 'respiration':('openstax-ap-breathing','Anatomy and Physiology 2e','22.3 ventilation bookkeeping','https://openstax.org/books/anatomy-and-physiology-2e/pages/22-3-the-process-of-breathing'),
 'heart':('openstax-ap-cardiac','Anatomy and Physiology 2e','19.4 cardiac output','https://openstax.org/books/anatomy-and-physiology-2e/pages/19-4-cardiac-physiology'),
 'membrane':('openstax-ap-membrane','Anatomy and Physiology 2e','3.1 plasma membrane and osmosis','https://openstax.org/books/anatomy-and-physiology-2e/pages/3-1-the-cell-membrane'),
 'bonding':('openstax-chem-formal','Chemistry 2e','7.4 formal charge and resonance','https://openstax.org/books/chemistry-2e/pages/7-4-formal-charges-and-resonance'),
 'vsepr':('openstax-chem-vsepr','Chemistry 2e','7.6 molecular structure','https://openstax.org/books/chemistry-2e/pages/7-6-molecular-structure-and-polarity'),
 'mechanism':('openstax-chem-mechanism','Chemistry 2e','12.6 elementary versus net reactions','https://openstax.org/books/chemistry-2e/pages/12-6-reaction-mechanisms'),
 'yield':('openstax-chem-yield','Chemistry 2e','4.4 reaction yields','https://openstax.org/books/chemistry-2e/pages/4-4-reaction-yields'),
 'estates':('versailles-estates-1789','Chateau de Versailles','Estates General opening, 5 May 1789','https://en.chateauversailles.fr/discover/history/key-dates/summoning-estates-general-1789'),
 'oath':('versailles-oath-1789','Chateau de Versailles','Jeu de Paume Oath, 20 June 1789','https://en.chateauversailles.fr/discover/history/key-dates/jeu-paume-oath-1789'),
 'declaration':('elysee-declaration-1789','Elysee historical text','1789 declaration, history and articles 1/16','https://www.elysee.fr/en/french-presidency/the-declaration-of-the-rights-of-man-and-of-the-citizen'),
 'departure':('versailles-departure-1789','Chateau de Versailles','Royal departure from Versailles, 6 October 1789','https://en.chateauversailles.fr/discover/history/key-dates/departure-king-1789'),
 'calendar':('usno-calendars','US Naval Observatory','Introduction to Calendars','https://aa.usno.navy.mil/faq/calendars'),
 'geology':('openstax-astronomy-crust','Astronomy 2e','8.2 plate tectonics and crust','https://openstax.org/books/astronomy-2e/pages/8-2-earths-crust'),
}
RIGHTS='Reference link only. No textbook passages, figures, exercises or fetched source bytes redistributed. Original authored diagnostic problems/code; this entry grants no source-content ingestion or redistribution permission.'
PACKS={};DESCRIPTIONS={}; current=None

def start(task,domain,module,description):
 global current
 current=task;PACKS[task]=[];DESCRIPTIONS[task]={'domain':domain,'module':module,'description':description}

def ok(values):return {'status':'OK','values':values}
def reject(code):return {'status':'REJECTED','error_code':code}
def add(title,inputs,expected,derivation,sources,tags=()):
 sources=list(sources)
 if current=='BIE-EVAL-BIO-001' and 'light' not in sources:sources.append('light')
 if current=='BIE-EVAL-GEO-001' and inputs.get('boundary')=='ocean_continent_convergent':sources.append('subduction')
 i=len(PACKS[current])+1
 case=BenchmarkCase.create(case_id=f'{current}.C{i:03}',task_id=current,
  domain=DESCRIPTIONS[current]['domain'],title=title,
  prompt=f'{title}. Use only the declared structured profile and assumptions. Return the contract-defined structured result or an explicit supported rejection; do not infer production acceptance.',
  inputs=inputs,expected=expected,split='DEVELOPMENT',leakage_group=current+'.authored-family',
  author_id='bie-batch002-local-author',derivation=derivation,
  sources=tuple(SourceReference(*SOURCES[s],rights=RIGHTS) for s in sources),
  tags=tuple([inputs.get('op','boundary'),*tags,'authored-development']),absolute_tolerance=0,relative_tolerance=0)
 PACKS[current].append(case.to_dict())

def claims_out(claim=None,reason=None):
 d=[] if claim is None else [{'claim':claim,'reason':reason}]
 return ok({'consistent':not d,'defects':d,'assessment_scope':'DECLARED_PROPOSITION_PROFILE_ONLY'})
def changed(mapping,**kw):return {**deepcopy(mapping),**kw}
def date(y,m=None,d=None,era='CE'):
 a={'year':y,'era':era,'precision':'day' if d is not None else 'month' if m is not None else 'year','calendar':'proleptic_gregorian'}
 if m is not None:a['month']=m
 if d is not None:a['day']=d
 return a

def q(v,u):return {'value':v,'unit':u}
def species(k,f,c=0):return {'id':k,'formula':f,'charge':c}

start('BIE-EVAL-BIO-001','biology','photosynthesis','Oxygenic net budgets, C3 Calvin resource limits and misconception controls.')
p={'oxygen_source':'water','fixed_carbon_source':'carbon_dioxide','calvin_location':'chloroplast_stroma','light_reaction_location':'thylakoid_membrane','calvin_direct_photon_requirement':False,'calvin_independent_of_atp_nadph_supply':False,'plants_also_respire':True}
for v,c,g in [('1','6','1'),('1/2','3','1/2')]:
 add('Oxygenic net budget '+v,{'op':'net_budget','glucose_mol':v},ok({'net_consumed_mol':{'CO2':c,'H2O':c},'net_produced_mol':{'C6H12O6':g,'O2':c},'oxygen_source':'water','profile':'NET_OXYGENIC_BOOKKEEPING'}),'Net equation coefficients 6:6:1:6; oxygen source is distinguished from net atom cancellation.',['calvin'],['conservation'])
for co2,g,atp,nadph,gross,recycled in [(3,'1','9','6','6','5'),(6,'2','18','12','12','10')]:
 add('Calvin carbon budget '+str(co2),{'op':'calvin_budget','co2_mol':co2},ok({'net_g3p_mol':g,'atp_consumed_mol':atp,'nadph_consumed_mol':nadph,'gross_g3p_reduced_mol':gross,'g3p_recycled_mol':recycled,'rubp_regenerated_mol':str(co2),'profile':'IDEAL_C3_CALVIN_NO_PHOTORESPIRATION'}),'Per net G3P: 3 CO2, 9 ATP, 6 NADPH; five of six reduced G3P recycle.',['calvin'],['gross-versus-net'])
for c,a,n,g,lim,unused in [(9,18,6,'1',['NADPH'],{'CO2':'6','ATP':'9','NADPH':'0'}),(3,9,6,'1',['ATP','CO2','NADPH'],{'CO2':'0','ATP':'0','NADPH':'0'}),(3,0,6,'0',['ATP'],{'CO2':'3','ATP':'0','NADPH':'6'})]:
 add(f'Calvin supplied-pool constraint {c}-{a}-{n}',{'op':'resource_limited_calvin','co2_mol':c,'atp_mol':a,'nadph_mol':n},ok({'net_g3p_mol':g,'limiting_resources':lim,'unused_mol':unused,'profile':'IDEAL_C3_SUPPLIED_POOLS_NOT_KINETIC_PREDICTION'}),'Compare CO2/3, ATP/9 and NADPH/6 capacities; retain ties and all unused pools.',['calvin'],['limiting-resources'])
add('Complete photosynthesis proposition profile',{'op':'audit_concepts','claims':p},claims_out(),'All seven declared propositions agree.',['calvin'])
add('Oxygen-source misconception',{'op':'audit_concepts','claims':changed(p,oxygen_source='carbon_dioxide')},claims_out('oxygen_source','CONTRADICTED_CLAIM'),'Reject carbon dioxide as released oxygen source in oxygenic photosynthesis.',['calvin'],['misconception'])
missing={k:v for k,v in p.items() if k!='plants_also_respire'}
add('Missing respiration proposition',{'op':'audit_concepts','claims':missing},claims_out('plants_also_respire','MISSING_CLAIM'),'An omitted required proposition is not a pass.',['calvin'],['missing-evidence'])
add('Negative net amount',{'op':'net_budget','glucose_mol':-1},reject('QUANTITY_OUT_OF_PROFILE'),'Negative substance amounts are outside this net-production request.',['calvin'])
add('Input cannot inject an answer override',{'op':'calvin_budget','co2_mol':3,'expected':'PASS'},reject('INVALID_FIELDS'),'Closed input schema rejects answer injection.',['calvin'],['answer-injection'])

start('BIE-EVAL-BIO-002','biology','genetics','Exact mono/multilocus Mendelian crosses, allele counting and explicitly conditional H-W expectations.')
def cross(loci):return {'op':'mendelian_cross','loci':loci,'assortment':'independent','dominance':'complete'}
def locus(g,a,b):return {'gene':g,'parent_a':a,'parent_b':b}
def cross_out(gen,phen):return ok({'genotype_probabilities':gen,'phenotype_probabilities':phen,'probability_sum':'1','profile':'INDEPENDENT_DIPLOID_COMPLETE_DOMINANCE'})
add('Heterozygous monohybrid cross',cross([locus('A','Aa','Aa')]),cross_out({'AA':'1/4','Aa':'1/2','aa':'1/4'},{'A_':'3/4','aa':'1/4'}),'Four equiprobable parental allele pairs aggregate to 1:2:1 genotypes and 3:1 phenotypes.',['inheritance'])
add('Monohybrid test cross',cross([locus('A','Aa','aa')]),cross_out({'Aa':'1/2','aa':'1/2'},{'A_':'1/2','aa':'1/2'}),'A or a from one parent meets only a from the other.',['inheritance'])
add('Opposite true-breeding parents',cross([locus('A','AA','aa')]),cross_out({'Aa':'1'},{'A_':'1'}),'Every pair is heterozygous.',['inheritance'])
add('Independent two-locus test cross',cross([locus('A','Aa','aa'),locus('B','Bb','bb')]),cross_out({'AaBb':'1/4','Aabb':'1/4','aaBb':'1/4','aabb':'1/4'},{'A_|B_':'1/4','A_|bb':'1/4','aa|B_':'1/4','aa|bb':'1/4'}),'Multiply two independent one-half probabilities.',['inheritance'],['multilocus'])
assumptions=['random_mating','large_population','no_selection','no_mutation','no_migration']
for value,pv,qv,gen in [('1/2','1/2','1/2',{'AA':'1/4','Aa':'1/2','aa':'1/4'}),('4/5','4/5','1/5',{'AA':'16/25','Aa':'8/25','aa':'1/25'}),(1,'1','0',{'AA':'1','Aa':'0','aa':'0'})]:
 add('Conditional Hardy-Weinberg p='+str(value),{'op':'hardy_weinberg','p':value,'assumptions':assumptions},ok({'p':pv,'q':qv,'genotype_probabilities':gen,'profile':'IDEAL_TWO_ALLELE_HARDY_WEINBERG_NOT_OBSERVED_COUNTS'}),'Under the explicitly supplied model, q=1-p and genotype frequencies are p*p, 2*p*q, q*q.',['hw'])
add('Observed allele counts do not prove equilibrium',{'op':'allele_frequency','AA':20,'Aa':10,'aa':20},ok({'p':'1/2','q':'1/2','individuals':50,'equilibrium_established':False}),'Count 50 A alleles and 50 a alleles among 100; do not infer equilibrium from p alone.',['hw'])
add('Linked loci must not use independent profile',changed(cross([locus('A','Aa','Aa')]),assortment='linked'),reject('UNSUPPORTED_ENUM'),'Linkage needs a separate model; independent assortment cannot be silently assumed.',['inheritance'])
add('Wrong locus alphabet',cross([locus('A','AB','Aa')]),reject('INVALID_DIPLOID_GENOTYPE'),'Both symbols must be alleles of the declared locus.',['inheritance'])
add('Missing H-W assumption',{'op':'hardy_weinberg','p':'1/2','assumptions':assumptions[:-1]},reject('COLLECTION_SIZE_OR_TYPE'),'The declared five-assumption set is mandatory.',['hw'])
add('Allele probability above one',{'op':'hardy_weinberg','p':2,'assumptions':assumptions},reject('INVALID_PROBABILITY'),'p is a probability, not an arbitrary positive number.',['hw'])

start('BIE-EVAL-BIO-003','biology','physiology','Educational flow, ventilation, adult circulation, osmosis and definition checks; no medical recommendations.')
for v,u in [(75,'mL'),('3/40','L')]:
 add('Cardiac flow '+str(v)+u,{'op':'cardiac_output','stroke_volume':q(v,u),'heart_rate':q(64,'per_min')},ok({'cardiac_output_L_per_min':'24/5','profile':'STEADY_PER_VENTRICLE_EDUCATIONAL_FLOW'}),'75 mL times 64/min = 4800 mL/min = 4.8 L/min.',['heart'],['unit-conversion'])
add('Alveolar versus total minute ventilation',{'op':'ventilation','tidal_volume':q(600,'mL'),'dead_space':q(150,'mL'),'breathing_rate':q(10,'per_min')},ok({'minute_ventilation_L_per_min':'6','alveolar_ventilation_L_per_min':'9/2','profile':'FIXED_DEAD_SPACE_EDUCATIONAL_MODEL'}),'Total=600*10/1000; alveolar=(600-150)*10/1000.',['respiration'])
add('All tidal volume is dead space',{'op':'ventilation','tidal_volume':q(150,'mL'),'dead_space':q(150,'mL'),'breathing_rate':q(12,'per_min')},ok({'minute_ventilation_L_per_min':'9/5','alveolar_ventilation_L_per_min':'0','profile':'FIXED_DEAD_SPACE_EDUCATIONAL_MODEL'}),'The fixed-volume model gives zero alveolar ventilation when both volumes are equal.',['respiration'])
for circuit,route in [('systemic',['left_ventricle','systemic_arteries','systemic_capillaries','systemic_veins','right_atrium']),('pulmonary',['right_ventricle','pulmonary_arteries','pulmonary_capillaries','pulmonary_veins','left_atrium'])]:
 add('Adult '+circuit+' flow order',{'op':'circulation_route','circuit':circuit},ok({'route':route,'profile':'ADULT_POSTNATAL_NORMAL_CIRCULATION'}),'Ordered major compartments in the declared adult postnatal circuit; fetal shunts excluded.',['heart'])
for outside,tonic,direction in [(450,'hypertonic','out_of_cell'),(300,'isotonic','no_net_flow'),(150,'hypotonic','into_cell')]:
 add('Nonpenetrating outside osmolarity '+str(outside),{'op':'osmosis','inside':q(300,'mOsm/L'),'outside':q(outside,'mOsm/L'),'solute_profile':'nonpenetrating_ideal'},ok({'outside_relative_tonicity':tonic,'water_direction':direction,'profile':'INITIAL_IDEAL_NONPENETRATING_SOLUTE_EQUAL_PRESSURE'}),'For equal pressure and nonpenetrating solute, initial net water flow is toward higher solute concentration.',['membrane'])
add('Dead space exceeds tidal input',{'op':'ventilation','tidal_volume':q(100,'mL'),'dead_space':q(150,'mL'),'breathing_rate':q(12,'per_min')},reject('DEAD_SPACE_EXCEEDS_TIDAL_VOLUME'),'Do not report negative alveolar ventilation as a valid modeled flow.',['respiration'])
add('Pressure cannot stand in for volume',{'op':'cardiac_output','stroke_volume':q(75,'mmHg'),'heart_rate':q(64,'per_min')},reject('UNSUPPORTED_ENUM'),'Volume profile accepts mL/L only.',['heart'])
pc={'artery_defined_by':'oxygen_rich_blood','vein_defined_by':'flow_towards_heart','pulmonary_artery_relative_oxygen':'lower','pulmonary_vein_relative_oxygen':'higher','negative_feedback_response':'opposes_deviation'}
add('Artery definition misconception',{'op':'audit_concepts','claims':pc},claims_out('artery_defined_by','CONTRADICTED_CLAIM'),'Arteries are defined by flow direction, not by oxygen content.',['heart'],['misconception'])

start('BIE-EVAL-CHEM-001','chemistry','bonding','Lewis graph electron/charge accounting, VSEPR and conceptual defects.')
def atom(k,e,n):return {'id':k,'element':e,'nonbonding_electrons':n}
def bond(a,b,o=1):return {'a':a,'b':b,'order':o}
water={'op':'lewis_audit','atoms':[atom('O','O',4),atom('H1','H',0),atom('H2','H',0)],'bonds':[bond('O','H1'),bond('O','H2')],'total_charge':0}
def lewis_out(fc,drawn,required,shells,defects=[]):return ok({'formal_charges':fc,'formal_charge_sum':sum(fc.values()),'drawn_valence_electrons':drawn,'required_valence_electrons':required,'shell_electrons':shells,'defects':defects,'profile':'LEWIS_BOOKKEEPING_NOT_STABILITY_PROOF'})
add('Water Lewis electron inventory',water,lewis_out({'H1':0,'H2':0,'O':0},8,8,{'H1':2,'H2':2,'O':8}),'O has 6-4-2=0 formal charge; 4 nonbonding and 4 bond electrons total 8.',['bonding'])
carbon={'op':'lewis_audit','atoms':[atom('C','C',0),atom('O1','O',4),atom('O2','O',4)],'bonds':[bond('C','O1',2),bond('C','O2',2)],'total_charge':0}
add('Carbon dioxide double-bond inventory',carbon,lewis_out({'C':0,'O1':0,'O2':0},16,16,{'C':8,'O1':8,'O2':8}),'Two double bonds use eight electrons; two O lone-pair sets use eight more.',['bonding'])
ammonium={'op':'lewis_audit','atoms':[atom('N','N',0)]+[atom('H'+str(i),'H',0) for i in range(1,5)],'bonds':[bond('N','H'+str(i)) for i in range(1,5)],'total_charge':1}
add('Ammonium formal charge',ammonium,lewis_out({'H1':0,'H2':0,'H3':0,'H4':0,'N':1},8,8,{'H1':2,'H2':2,'H3':2,'H4':2,'N':8}),'N formal charge=5-0-4=+1; positive molecular charge removes one electron.',['bonding'])
add('Incorrect total charge is exposed',changed(ammonium,total_charge=0),lewis_out({'H1':0,'H2':0,'H3':0,'H4':0,'N':1},8,9,{'H1':2,'H2':2,'H3':2,'H4':2,'N':8},['TOTAL_CHARGE_MISMATCH']),'An electron graph drawing with net +1 cannot be reported as neutral.',['bonding'])
for b,l,eg,mg in [(2,0,'linear','linear'),(2,2,'tetrahedral','bent'),(3,1,'tetrahedral','trigonal_pyramidal')]:
 add(f'VSEPR bonded={b} lone={l}',{'op':'vsepr','bonded_domains':b,'lone_pairs':l},ok({'electron_geometry':eg,'molecular_geometry':mg,'electron_domains':b+l,'profile':'MAIN_GROUP_2_TO_4_DOMAINS'}),'Electron domains count bonds as single domains; molecular shape excludes lone-pair positions.',['vsepr'])
bc={'formal_charge_is_partial_charge':False,'resonance_is_temporal_switching':True,'multiple_bond_vsepr_domains':'one','polar_bonds_always_imply_polar_molecule':False}
add('Resonance switching misconception',{'op':'audit_concepts','claims':bc},claims_out('resonance_is_temporal_switching','CONTRADICTED_CLAIM'),'Resonance structures are not distinct molecules toggling in time.',['bonding'])
add('Duplicate bond cannot double count electrons',changed(water,bonds=water['bonds']+[bond('H1','O')]),reject('DUPLICATE_BOND'),'An undirected edge and its reverse are the same bond.',['bonding'])
add('Dangling atom reference',changed(water,bonds=[bond('O','absent')]),reject('DANGLING_BOND'),'Every bond endpoint must resolve to a declared atom.',['bonding'])
radical=deepcopy(water);radical['atoms'][0]['nonbonding_electrons']=3
add('Radical deliberately outside closed-shell profile',radical,reject('RADICAL_OUTSIDE_PROFILE'),'Odd nonbonding electron count requires a separate radical model.',['bonding'])
add('Octahedral input is not silently approximated',{'op':'vsepr','bonded_domains':4,'lone_pairs':2},reject('GEOMETRY_OUTSIDE_PROFILE'),'This VSEPR profile is explicitly restricted to 2-4 electron domains.',['vsepr'])

start('BIE-EVAL-CHEM-002','chemistry','mechanisms','Conserved step sums, intermediates/catalysts, elementary-rate-law guard and energy differences.')
steps={'op':'audit_steps','species':[species('R','H2O2'),species('W','H2O'),species('O','O2'),species('I','HO')],
 'steps':[{'reactants':{'R':1},'products':{'I':2}},{'reactants':{'I':2,'R':1},'products':{'W':2,'O':1}}]}
mechanism_out={'net_reactants':{'R':2},'net_products':{'O':1,'W':2},'intermediates':['I'],'catalysts':[],'spectators':[],'mechanism_experimentally_established':False,'profile':'DECLARED_STEP_SEQUENCE_CONSERVATION_ONLY'}
add('Hypothetical conserved intermediate pathway',steps,ok(mechanism_out),'Authored formal atom-conserving pathway only, not a claim of an actual laboratory mechanism: add steps and cancel two I.',['mechanism'],['synthetic-not-experimental'])
# Isomer-like abstract species with identical formulas are distinguished by IDs.
cat={'op':'audit_steps','species':[species('A','H2'),species('B','H2'),species('K','He'),species('AK','H2He')],
 'steps':[{'reactants':{'A':1,'K':1},'products':{'AK':1}},{'reactants':{'AK':1},'products':{'B':1,'K':1}}]}
add('Hypothetical catalyst regenerated',cat,ok({'net_reactants':{'A':1},'net_products':{'B':1},'intermediates':['AK'],'catalysts':['K'],'spectators':[],'mechanism_experimentally_established':False,'profile':'DECLARED_STEP_SEQUENCE_CONSERVATION_ONLY'}),'Formal species ledger: K is first consumed and regenerated; AK is first formed and consumed. Not a physical reaction claim.',['mechanism'],['synthetic-not-experimental'])
for reactants,order in [({'A':1},1),({'A':1,'B':1},2),({'A':2},2)]:
 add('Declared elementary mass-action '+str(reactants),{'op':'elementary_rate_law','reactants':reactants,'is_elementary':True},ok({'concentration_exponents':reactants,'overall_order':order,'profile':'DECLARED_ELEMENTARY_MASS_ACTION'}),'For an explicitly elementary step, exponents equal molecularities. No net-reaction inference.',['mechanism'])
add('Net equation is insufficient for a rate law',{'op':'elementary_rate_law','reactants':{'A':2},'is_elementary':False},reject('ELEMENTARY_STEP_REQUIRED'),'Reject assuming that stoichiometric coefficients determine an arbitrary net rate law.',['mechanism'],['misconception'])
for energies,f,r,net in [([0,40,-10],['40'],['50'],'-10'),([0,25,5,45,-15],['25','40'],['20','60'],'-15')]:
 add('Energy profile '+str(energies),{'op':'energy_profile','energies_kJ_per_mol':energies},ok({'forward_barriers_kJ_per_mol':f,'reverse_barriers_kJ_per_mol':r,'net_energy_change_kJ_per_mol':net,'rate_determining_step_inferred':False,'profile':'ENERGY_DIFFERENCES_NOT_FULL_KINETICS'}),'Subtract each adjacent minimum from its transition-state energy; endpoint difference is not an activation barrier.',['mechanism'])
bad=deepcopy(steps);bad['steps'][1]['products']['W']=1
add('Atom-imbalanced step rejected',bad,reject('UNBALANCED_ELEMENTARY_STEP'),'A conserved net label cannot excuse a nonconserving declared elementary step.',['mechanism'])
add('Unreferenced species refused',changed(steps,species=steps['species']+[species('X','Na')]),reject('UNUSED_SPECIES'),'All declared species must participate in the step ledger.',['mechanism'])
add('Candidate cannot inject elementary flag as string',{'op':'elementary_rate_law','reactants':{'A':1},'is_elementary':'true'},reject('ELEMENTARY_STEP_REQUIRED'),'Only the literal boolean True acknowledges the elementary profile.',['mechanism'])
add('Transition state below product refused',{'op':'energy_profile','energies_kJ_per_mol':[0,10,15]},reject('TRANSITION_STATE_NOT_MAXIMUM'),'An alternating maximum must exceed both adjacent minima.',['mechanism'])

start('BIE-EVAL-CHEM-003','chemistry','stoichiometry','Unique positive balancing with charge conservation, limiting feeds and molar yield.')
water_eq={'op':'balance','reactants':[species('hydrogen','H2'),species('oxygen','O2')],'products':[species('water','H2O')]}
add('Water primitive equation balance',water_eq,ok({'reactants':{'hydrogen':2,'oxygen':1},'products':{'water':2},'profile':'PRIMITIVE_INTEGER_ATOM_AND_CHARGE_BALANCE'}),'Hydrogen and oxygen conservation require primitive coefficients 2:1:2.',['yield'])
add('Parenthesized formula balance',{'op':'balance','reactants':[species('base','Ca(OH)2'),species('acid','HCl')],'products':[species('salt','CaCl2'),species('water','H2O')]},ok({'reactants':{'acid':2,'base':1},'products':{'salt':1,'water':2},'profile':'PRIMITIVE_INTEGER_ATOM_AND_CHARGE_BALANCE'}),'Ca=1, Cl=2, O=2, H=4 on each side.',['yield'])
add('Ionic charges are conserved',{'op':'balance','reactants':[species('H','H',1),species('OH','OH',-1)],'products':[species('water','H2O')]},ok({'reactants':{'H':1,'OH':1},'products':{'water':1},'profile':'PRIMITIVE_INTEGER_ATOM_AND_CHARGE_BALANCE'}),'One +1 and one -1 species sum to neutral water with conserved atoms.',['yield'])
for feed,ex,lim,cons,remain,prod in [({'hydrogen':5,'oxygen':2},'2',['oxygen'],{'hydrogen':'4','oxygen':'2'},{'hydrogen':'1','oxygen':'0'},'4'),({'hydrogen':4,'oxygen':2},'2',['hydrogen','oxygen'],{'hydrogen':'4','oxygen':'2'},{'hydrogen':'0','oxygen':'0'},'4'),({'hydrogen':0,'oxygen':2},'0',['hydrogen'],{'hydrogen':'0','oxygen':'0'},{'hydrogen':'0','oxygen':'2'},'0')]:
 inp=changed(water_eq,op='reaction_extent',coefficients={'hydrogen':2,'oxygen':1,'water':2},feed_mol=feed)
 add('Limiting feed '+str(feed),inp,ok({'extent_mol':ex,'limiting_reactants':lim,'consumed_mol':cons,'remaining_mol':remain,'produced_mol':{'water':prod},'profile':'IDEAL_COMPLETE_CONVERSION_NO_SIDE_REACTIONS'}),'Extent=min(n_hydrogen/2,n_oxygen); multiply by each stoichiometric coefficient.',['yield'])
add('Pure product molar yield',{'op':'percent_yield','actual_mol':3,'theoretical_mol':4},ok({'percent_yield':'75','profile':'PURE_PRODUCT_SAME_SPECIES_MOLAR_YIELD'}),'100*3/4=75 percent for the same pure product.',['yield'])
add('Percent above pure theoretical yield',{'op':'percent_yield','actual_mol':5,'theoretical_mol':4},reject('PURE_PRODUCT_YIELD_EXCEEDS_THEORY'),'Observed apparent yields above 100 need a different measurement/impurity model.',['yield'])
add('Charge cannot disappear',{'op':'balance','reactants':[species('ion','H',1)],'products':[species('neutral','H')]},reject('NO_NONZERO_BALANCE'),'Atom conservation permits equal counts, but charge conservation forces zero; no nonzero balance.',['yield'])
add('Multiple possible equation balances refused',{'op':'balance','reactants':[species('carbon','C'),species('oxygen','O2')],'products':[species('CO','CO'),species('CO2','CO2')]},reject('BALANCE_NOT_UNIQUE'),'Two carbon products create more than one independent stoichiometric solution; do not invent a ratio.',['yield'])
add('Unbalanced supplied coefficients',changed(water_eq,op='reaction_extent',coefficients={'hydrogen':1,'oxygen':1,'water':1},feed_mol={'hydrogen':2,'oxygen':2}),reject('UNBALANCED_REACTION'),'Declared coefficients must conserve atoms before limiting-feed arithmetic.',['yield'])
add('Unsupported hydrate syntax must be explicit',{'op':'balance','reactants':[species('hydrate','CuSO4.5H2O')],'products':[species('salt','CuSO4'),species('water','H2O')]},reject('UNSUPPORTED_FORMULA_SYNTAX'),'The bounded parser does not silently misread dot hydrate notation.',['yield'])

start('BIE-EVAL-HIST-001','history','french_revolution','Referenced 1789 event profile, source-bound dates and normative versus factual versus interpretive claims.')
events={
'estates_general_opening':{'date':'1789-05-05','place':'Versailles','source_ref':'versailles-estates-1789'},
 'tennis_court_oath':{'date':'1789-06-20','place':'Versailles','source_ref':'versailles-oath-1789'},
 'declaration_1789_text':{'date':'1789-08-26','source_ref':'elysee-declaration-1789'},
 'royal_departure_versailles':{'date':'1789-10-06','place':'Versailles','source_ref':'versailles-departure-1789'}}
for key,src in zip(events,['estates','oath','declaration','departure']):
 add('Reference event '+key,{'op':'event_facts','event_ids':[key]},ok({'events':[{'event_id':key,**events[key]}],'profile':'FOUR_REFERENCED_1789_EVENTS_NOT_COMPLETE_HISTORY'}),'Small dated-event record is sourced to the referenced institutional history; no motive or evaluative judgment.',['estates'] if src=='estates' else [src])
entry={'event_id':'tennis_court_oath','date':date(1789,6,20),'source_ref':'versailles-oath-1789'}
timeline={'op':'audit_timeline','entries':[entry],'required_event_ids':['tennis_court_oath']}
def timeline_out(defects):return ok({'consistent':not defects,'defects':defects,'references_are_links_not_captured_passages':True})
add('Dated and referenced oath entry',timeline,timeline_out([]),'Day and source reference both match the declared event record.',['oath'])
wrong=deepcopy(timeline);wrong['entries'][0]['date']=date(1789,6,21)
add('One-day chronology defect',wrong,timeline_out([{'event_id':'tennis_court_oath','reason':'DATE_MISMATCH_OR_INSUFFICIENT_PRECISION'}]),'A one-day displacement is a factual date mismatch.',['oath'])
wrong=deepcopy(timeline);wrong['entries'][0]['date']=date(1789)
add('Year-only input cannot impersonate exact date',wrong,timeline_out([{'event_id':'tennis_court_oath','reason':'DATE_MISMATCH_OR_INSUFFICIENT_PRECISION'}]),'Containment of the actual date in a broad year range is not an exact-date answer.',['oath'])
wrong=deepcopy(timeline);wrong['entries'][0]['source_ref']='elysee-declaration-1789'
add('Citation must match event',wrong,timeline_out([{'event_id':'tennis_court_oath','reason':'SOURCE_EVENT_MISMATCH'}]),'A valid reference ID for another event does not support this date.',['oath'])
add('Omitted required event',changed(timeline,entries=[]),timeline_out([{'event_id':'tennis_court_oath','reason':'MISSING_EVENT'}]),'Empty timeline cannot pass against a nonempty frozen event roster.',['oath'])
for claim,category,source,refs in [('declaration_article1_equal_rights_principle','TEXTUAL_PRINCIPLE','elysee-declaration-1789',['declaration']),('financial_crisis_contributed_to_convocation','ATTRIBUTED_INTERPRETATION','versailles-estates-1789',['estates'])]:
 add('Claim kind '+claim,{'op':'classify_claim','claim_id':claim,'source_ref':source},ok({'claim_type':category,'source_ref':source,'historical_practice_established_by_normative_text':False,'profile':'DECLARED_SOURCE_LINKED_CLAIM_TYPE_NOT_ENTAILMENT'}),'A stated principle is not proof of implementation; a historical explanation remains attributed. ',refs)
add('Unknown event cannot be hallucinated',{'op':'event_facts','event_ids':['unregistered_event']},reject('EVENT_OUTSIDE_REFERENCE_PROFILE'),'No fabricated fallback date for an event outside the bounded reference profile.',['estates'])

start('BIE-EVAL-HIST-002','history','historical_causality','Audits annotated causal arguments and graphs while retaining uncertainty and source-review requirements.')
link={'op':'assess_link','cause':{'id':'A','date':date(1788)},'effect':{'id':'B','date':date(1789)},'relation_claim':'contributes_to','evidence':[{'id':'E1','cause_id':'A','effect_id':'B','kind':'mechanism_account','source_ref':'synthetic-dossier-1'}],'alternatives_considered':['C']}
def causal_out(issues=[],order='BEFORE',ids=['E1']):return ok({'status':'REVIEW_REQUIRED' if issues else 'ANNOTATED_INTERPRETATION_STRUCTURALLY_SUPPORTED','time_relation':order,'issues':issues,'evidence_ids':ids,'causality_proven':False,'annotations_independently_verified':False,'profile':'ANNOTATED_ARGUMENT_AUDIT_NOT_SOURCE_VERIFICATION'})
add('Synthetic annotated contributing-cause argument',link,causal_out(),'A hypothetical A-before-B dossier supplies a mechanism annotation and an alternative. This checks argument form, not historical source truth.',['estates','calendar'],['synthetic-dossier'])
wrong=deepcopy(link);wrong['evidence'][0]['kind']='temporal_record'
add('Temporal succession alone',wrong,causal_out(['SEQUENCE_ALONE_DOES_NOT_ESTABLISH_CAUSATION']),'Temporal records alone lack a supplied causal interpretation/mechanism. Hypothetical data.',['estates','calendar'],['synthetic-dossier'])
for claim in ['sole_cause','necessary','sufficient']:
 add('Overstrong '+claim+' claim',changed(link,relation_claim=claim),causal_out(['OVERSTRONG_CAUSAL_CLAIM']),'This annotated contributing-cause profile cannot establish sole, necessary or sufficient causation.',['estates','calendar'],['synthetic-dossier'])
add('Missing alternative explanations',changed(link,alternatives_considered=[]),causal_out(['ALTERNATIVES_NOT_CONSIDERED']),'The defined diagnostic requires at least one distinct alternative for review.',['estates','calendar'],['synthetic-dossier'])
wrong=deepcopy(link);wrong['cause']['date']=date(1790)
add('Cause after claimed effect',wrong,causal_out(['TEMPORAL_REVERSAL'],order='AFTER'),'The cause interval lies wholly after its effect interval.',['calendar'],['synthetic-dossier'])
wrong=deepcopy(link);wrong['cause']['date']=date(1789)
add('Unresolved same-year ordering',wrong,causal_out(['TIME_ORDER_UNRESOLVED'],order='OVERLAPPING_OR_UNCERTAIN'),'Year precision cannot establish within-year causal precedence.',['calendar'],['synthetic-dossier'])
wrong=deepcopy(link);wrong['evidence'].append({'id':'E2','cause_id':'A','effect_id':'B','kind':'counter_evidence','source_ref':'synthetic-dossier-2'})
add('Counterevidence retained',wrong,causal_out(['COUNTEREVIDENCE_REQUIRES_REVIEW'],ids=['E1','E2']),'Counterevidence must remain visible even when a supportive annotation exists.',['estates','calendar'],['synthetic-dossier'])
add('No supplied evidence',changed(link,evidence=[]),causal_out(['NO_EVIDENCE','SEQUENCE_ALONE_DOES_NOT_ESTABLISH_CAUSATION'],ids=[]),'Do not infer evidentiary support from chronological placement.',['calendar'],['synthetic-dossier'])
wrong=deepcopy(link);wrong['evidence'][0]['effect_id']='C'
add('Evidence about a different effect',wrong,reject('EVIDENCE_ENDPOINT_MISMATCH'),'Evidence endpoints must match the particular cause/effect proposition.',['calendar'],['synthetic-dossier'])
add('Duplicate evidence cannot inflate support',changed(link,evidence=link['evidence']*2),reject('DUPLICATE_EVIDENCE'),'Repeated evidence identity is not additional support.',['calendar'],['synthetic-dossier'])

start('BIE-EVAL-HIST-003','history','chronology','Precision-preserving Gregorian date intervals, BCE/CE year arithmetic and partial orders.')
def cmp_out(rel,lo,hi):return ok({'relation':rel,'b_minus_a_days_min':lo,'b_minus_a_days_max':hi,'profile':'PROLEPTIC_GREGORIAN_INTERVAL_ARITHMETIC_NOT_CAUSALITY'})
for a,b,rel,lo,hi,title in [(date(1789,6,20),date(1789,6,21),'BEFORE',1,1,'Adjacent CE dates'),(date(1789,6,21),date(1789,6,20),'AFTER',-1,-1,'Reverse CE dates'),(date(1789,6,20),date(1789,6,20),'SAME_DAY',0,0,'Same exact day'),(date(2000,2,28),date(2000,3,1),'BEFORE',2,2,'Gregorian 400-year leap rule'),(date(1900,2,28),date(1900,3,1),'BEFORE',1,1,'Gregorian century non-leap rule'),(date(1789),date(1789),'OVERLAPPING_OR_UNCERTAIN',-364,364,'Equal year labels do not establish simultaneity')]:
 add(title,{'op':'compare_dates','a':a,'b':b},cmp_out(rel,lo,hi),'Calendar interval arithmetic under an explicit proleptic Gregorian model; uncertain dates stay ranges.',['calendar'])
for ay,ae,by,be,difference in [(1,'BCE',1,'CE',1),(2,'BCE',1,'BCE',1),(10,'CE',10,'BCE',-19)]:
 add(f'No-year-zero difference {ay}{ae}-{by}{be}',{'op':'year_difference','a_year':ay,'a_era':ae,'b_year':by,'b_era':be},ok({'signed_year_number_difference':difference,'profile':'YEAR_LABEL_DIFFERENCE_NOT_PRECISE_ELAPSED_DURATION'}),'Convert BCE year y to astronomical year 1-y before subtracting; label difference is not precise elapsed duration.',['calendar'])
add('Partial order retains overlapping intervals',{'op':'partial_order','events':[{'id':'A','date':date(1788)},{'id':'B','date':date(1789)},{'id':'C','date':date(1789,6,20)}]},ok({'definitely_before':[['A','B'],['A','C']],'overlapping_or_uncertain':[['B','C']],'same_day':[],'unique_total_order':False,'profile':'PRECISION_PRESERVING_PARTIAL_ORDER'}),'A definitely precedes B and C; B year-range overlaps the exact C date, so do not impose a total order.',['calendar'])
add('Civil year zero rejected',{'op':'year_difference','a_year':0,'a_era':'BCE','b_year':1,'b_era':'CE'},reject('INVALID_INTEGER'),'Civil BCE/CE input excludes year zero.',['calendar'])
add('Invalid non-leap date rejected',{'op':'compare_dates','a':date(1900,2,29),'b':date(1900,3,1)},reject('INVALID_INTEGER'),'1900 is divisible by 100 but not 400, so February has only 28 days in this profile.',['calendar'])

start('BIE-EVAL-GEO-001','geography','plate_tectonics','Directed boundary projections, half/full spreading rates, ridge age and tectonic misconception checks.')
def vel(x,y,u='cm/yr'):return {'values':[x,y],'unit':u}
for b,n,sep,shear,motion in [(vel(4,0),[1,0],'4','0','divergent'),(vel(-4,0),[1,0],'-4','0','convergent'),(vel(0,3),[1,0],'0','3','transform'),(vel(4,3),[1,0],'4','3','oblique_divergent')]:
 add('Directed boundary '+motion,{'op':'boundary_motion','velocity_a':vel(0,0),'velocity_b':b,'normal_a_to_b':n},ok({'separation_cm_per_yr':sep,'tangential_cm_per_yr':shear,'motion':motion,'profile':'LOCAL_PLANAR_DIRECTED_UNIT_NORMAL'}),'Project relative velocity vB-vA onto the A-to-B normal and its +90-degree tangent.',['geology'])
for rate,kind in [(3,'half'),(6,'full')]:
 add(f'Symmetric spreading {rate} {kind}',{'op':'spreading_distance','rate':q(rate,'cm/yr'),'rate_kind':kind,'duration':q(2,'Myr')},ok({'one_flank_km':'60','total_separation_km':'120','profile':'CONSTANT_SYMMETRIC_SPREADING'}),'One cm/year over one million years is ten km; full rate is twice the half rate.',['geology'],['half-versus-full'])
add('Ridge age from half rate',{'op':'age_from_ridge','distance':q(90,'km'),'half_rate':q(3,'cm/yr')},ok({'age_Myr':'3','profile':'CONSTANT_HALF_RATE_PER_FLANK'}),'Age=90/(10*3)=3 Myr for the constant-rate single flank.',['geology'])
add('Ideal transform boundary inventory',{'op':'boundary_features','boundary':'transform'},ok({'oceanic_lithosphere_created':False,'oceanic_lithosphere_consumed':False,'landform':'strike_slip_fault_zone','profile':'IDEALIZED_OCEANIC_LITHOSPHERE_BUDGET_NOT_TOTAL_CRUST_BUDGET'}),'Ideal transform motion does not create or consume crust.',['geology'])
add('Ideal ocean-continent convergence',{'op':'boundary_features','boundary':'ocean_continent_convergent'},ok({'oceanic_lithosphere_created':False,'oceanic_lithosphere_consumed':True,'landform':'trench_and_continental_arc','profile':'IDEALIZED_OCEANIC_LITHOSPHERE_BUDGET_NOT_TOTAL_CRUST_BUDGET'}),'The simplified subduction-boundary inventory tracks consumed oceanic crust, not a whole-Earth crust budget.',['geology'])
add('Nonunit normal refused',{'op':'boundary_motion','velocity_a':vel(0,0),'velocity_b':vel(4,0),'normal_a_to_b':[2,0]},reject('EXACT_UNIT_NORMAL_REQUIRED'),'Normal length must be exactly one in the rational input profile to avoid scaled projection errors.',['geology'])
add('Zero ridge spreading rate cannot define age',{'op':'age_from_ridge','distance':q(90,'km'),'half_rate':q(0,'cm/yr')},reject('QUANTITY_OUT_OF_PROFILE'),'The inversion requires a positive half-spreading rate.',['geology'])
gc={'plate_material':'crust_and_rigid_uppermost_mantle','mantle_entirely_liquid':True,'transform_creates_new_crust_in_ideal_model':False,'seafloor_age_increases_away_from_ridge_in_simple_model':True,'average_plate_speed_predicts_exact_earthquake_time':False}
add('Wholly liquid mantle misconception',{'op':'audit_concepts','claims':gc},claims_out('mantle_entirely_liquid','CONTRADICTED_CLAIM'),'The declared tectonic model does not treat the whole mantle as liquid.',['geology'],['misconception'])

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output-dir',required=True,help='New external directory; never rewrites installed fixtures')
 args=parser.parse_args()
 output_root=Path(args.output_dir).resolve()
 output_root.mkdir(parents=True,exist_ok=False)
 data_dir=output_root/'bie/evaluation/benchmarks/data'
 data_dir.mkdir(parents=True)
 for task,cases in PACKS.items():
  assert len(cases)==12,(task,len(cases))
  (data_dir/(task+'.json')).write_text(json.dumps(cases,indent=2,ensure_ascii=False)+'\n')
 meta=output_root/'metadata/section17'
 meta.mkdir(parents=True)
 (meta/'BATCH002_TASK_DESCRIPTIONS.json').write_text(json.dumps(DESCRIPTIONS,indent=2)+'\n')
 (meta/'BATCH002_REFERENCE_CATALOG.json').write_text(json.dumps({'review_date':'2026-09-29','sources':[{ 'reference_id':v[0],'title':v[1],'locator':v[2],'url':v[3],'rights':RIGHTS,'evidence_kind':'REFERENCE_ONLY'} for v in SOURCES.values()],'independent_review':False,'source_bytes_bundled':False,'source_ingestion_rights_granted':False},indent=2)+'\n')
 print('Authored packs:',len(PACKS),'cases:',sum(map(len,PACKS.values())))
