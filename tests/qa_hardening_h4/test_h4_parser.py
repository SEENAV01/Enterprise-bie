import unittest
from bie.qa.domain_quality_v2.parser import *
from bie.qa.math_v2.expression import parse as baseline
class ParserChecks(unittest.TestCase):
    def test_native_bug_preserved_and_detected(self):
        r=inspect_parser('x * y + z');self.assertTrue(r['native_mismatch']);self.assertEqual(r['complete_ast']['value'],'+');self.assertEqual(r['native_ast']['value'],'*');self.assertFalse(r['native_overwritten'])
    def test_right_power(self):
        n=parse_complete(tokenize('x^2^3'))
        self.assertEqual(n.value,'^');self.assertEqual(n.children[1].value,'^')
        with self.assertRaises(ContractError):checked_expression('x^2^3')
    def test_native_matching_atomic(self):self.assertFalse(inspect_parser('x')['native_mismatch'])
    def test_explicit_full_consumption(self):
        with self.assertRaises(ContractError):parse_complete(['x','y'])
    def test_roundtrip_generated_polynomials(self):
        for a in ('x','y','3','-2'):
            for b in ('x','4','(y+z)'):
                for op in ('+','-','*','/'):
                    x=a+op+b;n=parse_complete(tokenize(x));self.assertEqual(parse_complete(tokenize(node_text(n))),n)
    def test_token_not_atomic(self):
        with self.assertRaises(ContractError):parse_complete(['x + y'])
    def test_type_list_required(self):
        with self.assertRaises(ContractError):parse_complete(('x',))
    def test_bool_token(self):
        with self.assertRaises(ContractError):parse_complete([True])
    def test_node_type(self):
        with self.assertRaises(ContractError):node_text({'kind':'atom'})
    def test_native_tree_cannot_hide_tail(self):
        from bie.qa.math_v2.adapters import import_node
        with self.assertRaises(ContractError):import_node(legacy_parse(['x','*','y','+','z']),'x*y+z')
GOOD={'mixed_precedence':'x*y+z','nested_group':'(x+y)*z','subtract_left':'x-y-z','divide_left':'x/y/z','negative_power':'x^-2','negative_square':'-x^2','signed_group':'(-x)^2','decimal':'1.25*x+2e-3','unary_plus':'+x+y','trailing_space':' x + y ','constant_fraction':'1/3+x','integer':'125','chained':'x+y*z-2*x'}
for name,value in GOOD.items():
    def check(self,value=value):self.assertEqual(checked_expression(value),baseline(value))
    setattr(ParserChecks,'test_'+name,check)
BAD={'missing_operand':'x+','double_operator':'x*/y','extra_tail':'x y','implicit_mult':'2(x+1)','open_parenthesis':'(x+y','close_parenthesis':'x+y)','semicolon':'x;y','attribute':'x.__class__','list':'[x]','unknown_symbol':'x@2','newline_extra':'x\ny','empty':' ','function_not_profile':'sin(x)','comma':'x,y','control':'x\x00+y','very_long':'x'*2049,'deep':'('*30+'x'+')'*30,'too_many_tokens':'+'.join(['x']*150),'oversized_number':'9'*161,'unknown_equality':'x=2'}
for name,value in BAD.items():
    def check(self,value=value):
        with self.assertRaises((ContractError,ValueError)):parse_complete(tokenize(value))
    setattr(ParserChecks,'test_reject_'+name,check)
