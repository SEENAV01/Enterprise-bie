from dataclasses import replace, FrozenInstanceError
from fractions import Fraction
from sem_helpers import *
from bie.qa.semantic_v2.models import number
from bie.qa.semantic_v2.logic import compare, conflict, validate_rule


class ModelTests(FixtureCase):
    def test_invalid_decimal_cases(self):
        for v in ('01','1.0','-0','1e2','NaN','Infinity','+5','.5',' 5','5 ',5,5.0,True,None,'0.1234567891','1000000000000'):
            with self.subTest(value=v), self.assertRaises(ContractError): number(v)
    def test_exact_decimal_cases(self):
        for s in ('0','-1','0.1','999999999999','0.000000001','-0.05'):
            with self.subTest(value=s):self.assertEqual(number(s),Fraction(s))
    def test_reversed_range(self):
        with self.assertRaises(ContractError): Value('quantity',lower='7',upper='5',unit='W')
    def test_symbol_extra_fields(self):
        for field,value in [('lower','1'),('upper','1'),('unit','W')]:
            with self.subTest(field=field),self.assertRaises(ContractError):Value('symbol','on',**{field:value})
    def test_quantity_symbol_field(self):
        with self.assertRaises(ContractError):Value('quantity','on','1','2','W')
    def test_negative_quantity(self):
        with self.assertRaises(ContractError):quantity(polarity='negative')
    def test_context_duplicates(self):
        with self.assertRaises(ContractError):quantity(context=(('domain','a'),('domain','b')))
    def test_context_canonical_order(self):
        with self.assertRaises(ContractError):quantity(context=tuple(reversed(CONTEXT)))
    def test_context_mutable_rejected(self):
        with self.assertRaises(ContractError):quantity(context=list(CONTEXT))
    def test_duplicate_normalized_atoms(self):
        with self.assertRaises(ContractError):Normalization('claim-1',(quantity(),quantity()))
    def test_duplicate_normalizations(self):
        with self.assertRaises(ContractError):replace(self.request,normalizations=self.request.normalizations*2)
    def test_duplicate_reference_ids(self):
        with self.assertRaises(ContractError):replace(self.request,references=self.request.references*2)
    def test_subject_namespace_collision(self):
        with self.assertRaises(ContractError):replace(self.request,references=(replace(self.request.references[0],reference_id='claim-1'),))
    def test_reserved_subject_id(self):
        with self.assertRaises(ContractError):replace(self.request,coverage_links=(replace(self.request.coverage_links[0],link_id='semantic-scope'),))
    def test_duplicate_link_content_different_ids(self):
        with self.assertRaises(ContractError):replace(self.request,coverage_links=self.request.coverage_links+(replace(self.request.coverage_links[0],link_id='link-2'),))
    def test_empty_operator_requirements(self):
        with self.assertRaises(ContractError):replace(self.policy,requirements=())
    def test_empty_reference_inventory(self):
        with self.assertRaises(ContractError):replace(self.policy,expected_reference_ids=())
    def test_duplicate_concept_facet(self):
        with self.assertRaises(ContractError):replace(self.policy,requirements=self.policy.requirements+(replace(self.policy.requirements[0],requirement_id='req-2'),))
    def test_rule_numeric_multivalued_rejected(self):
        with self.assertRaises(ContractError):replace(self.policy.predicates[0],cardinality='multi')
    def test_boolean_is_not_integer(self):
        for field in ('minimum_confidence_ppm','minimum_weighted_coverage_ppm','max_comparisons','minimum_independent_assessors'):
            with self.subTest(field=field),self.assertRaises(ContractError):replace(self.policy,**{field:True})
    def test_policy_floors(self):
        for kwargs in ({'minimum_confidence_ppm':899999},{'minimum_weighted_coverage_ppm':949999},{'max_comparisons':1000001}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ContractError):replace(self.policy,**kwargs)
    def test_requirement_must_exceed_mention(self):
        with self.assertRaises(ContractError):replace(self.policy.requirements[0],minimum_depth=1)
    def test_frozen_records(self):
        with self.assertRaises(FrozenInstanceError):self.request.schema_version='2'
    def test_unknown_version(self):
        with self.assertRaises(ContractError):replace(self.request,schema_version='2.0.0')


class LogicTests(FixtureCase):
    def c(self,r,c):return compare(r,c,self.policy.predicates[0])
    def sym(self,value='on',sign='positive',context=CONTEXT):
        return Proposition('lamp','status',Value('symbol',value),sign,context)
    def rule(self,cardinality='single'):return PredicateRule('status','symbol',cardinality,'',('domain','trial'))
    def test_exact_quantity_entails(self):self.assertEqual(self.c(quantity(),quantity()),'ENTAILS')
    def test_disjoint_quantity_conflict(self):self.assertEqual(self.c(quantity('5'),quantity('7')),'CONTRADICTS')
    def test_uncertainty_not_erased(self):self.assertEqual(self.c(quantity('4','6'),quantity('5')),'UNKNOWN')
    def test_weaker_interval_claim_supported(self):self.assertEqual(self.c(quantity('5'),quantity('4','6')),'ENTAILS')
    def test_overlap_not_support(self):self.assertEqual(self.c(quantity('4','6'),quantity('5','7')),'UNKNOWN')
    def test_touching_closed_intervals_not_conflict(self):self.assertFalse(conflict(quantity('4','5'),quantity('5','6'),self.policy.predicates[0]))
    def test_decimal_precision(self):self.assertEqual(self.c(quantity('0.1'),quantity('0.1')),'ENTAILS')
    def test_different_trial_not_compared(self):self.assertEqual(self.c(quantity(),quantity('7',context=(('domain','synthetic-demonstration'),('trial','B')))),'DIFFERENT_SCOPE')
    def test_different_entity_not_compared(self):self.assertEqual(self.c(quantity(),quantity('7',entity_id='other')),'DIFFERENT_SCOPE')
    def test_missing_context_not_inferred(self):
        with self.assertRaises(ContractError):self.c(quantity(),quantity(context=(('domain','synthetic-demonstration'),)))
    def test_units_not_silently_converted(self):
        with self.assertRaises(ContractError):self.c(quantity(),quantity(value=Value('quantity',lower='0.005',upper='0.005',unit='kW')))
    def test_single_value_exclusivity(self):self.assertTrue(conflict(self.sym('on'),self.sym('off'),self.rule()))
    def test_multi_value_not_exclusive(self):self.assertFalse(conflict(self.sym('red'),self.sym('blue'),self.rule('multi')))
    def test_explicit_negation_conflicts(self):self.assertTrue(conflict(self.sym(),self.sym(sign='negative'),self.rule('multi')))
    def test_two_negative_different_symbols_not_conflict(self):self.assertFalse(conflict(self.sym('on','negative'),self.sym('off','negative'),self.rule()))
    def test_negative_does_not_establish_positive_alternative(self):self.assertEqual(compare(self.sym('on','negative'),self.sym('off'),self.rule()),'UNKNOWN')
    def test_single_positive_entails_different_negative(self):self.assertEqual(compare(self.sym('on'),self.sym('off','negative'),self.rule()),'ENTAILS')
    def test_multi_positive_does_not_entail_other_negative(self):self.assertEqual(compare(self.sym('red'),self.sym('blue','negative'),self.rule('multi')),'UNKNOWN')
    def test_conflict_symmetry_exhaustive_small_domain(self):
        for card in ('single','multi'):
            for v1 in ('a','b'):
                for v2 in ('a','b'):
                    for p1 in ('positive','negative'):
                        for p2 in ('positive','negative'):
                            with self.subTest(card=card,v1=v1,v2=v2,p1=p1,p2=p2):
                                a,b=self.sym(v1,p1),self.sym(v2,p2)
                                self.assertEqual(conflict(a,b,self.rule(card)),conflict(b,a,self.rule(card)))
    def test_interval_lattice_semantics(self):
        for lo in range(-2,3):
            for hi in range(lo,3):
                for c in range(-2,3):
                    with self.subTest(lo=lo,hi=hi,c=c):
                        status=self.c(quantity(str(lo),str(hi)),quantity(str(c)))
                        self.assertEqual(status,'CONTRADICTS' if not lo<=c<=hi else 'ENTAILS' if lo==hi else 'UNKNOWN')
