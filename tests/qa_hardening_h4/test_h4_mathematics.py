from h4_support import *
class MathChecks(TempCase):
    def run_case(self,c):
        p=MathPolicy((c['case_id'],));b=binding(p);d=payload('BIE-QA-HARD-014',b,cases=[c]);r,_=evaluate_math(save(self.root,'case.json',d),self.root,b,p);return r
    def test_bad_binding(self):
        p=MathPolicy(('a',));b=binding(p);d=payload('BIE-QA-HARD-014',b,cases=[]);d['binding']['run_id']='wrong'
        with self.assertRaises(ContractError):evaluate_math(save(self.root,'case.json',d),self.root,b,p)
    def test_missing_cases(self):
        p=MathPolicy(('a','b'));b=binding(p);d=payload('BIE-QA-HARD-014',b,cases=[dict(case_id='a',kind='unknown',description='review')])
        with self.assertRaises(ContractError):evaluate_math(save(self.root,'case.json',d),self.root,b,p)
    def test_duplicate_cases(self):
        p=MathPolicy(('a',));b=binding(p);c=dict(case_id='a',kind='unknown',description='review');d=payload('BIE-QA-HARD-014',b,cases=[c,c])
        with self.assertRaises(ContractError):evaluate_math(save(self.root,'case.json',d),self.root,b,p)
    def test_source_bytes_tampered(self):
        p=MathPolicy(('a',));b=binding(p);ref=save(self.root,'case.json',payload('BIE-QA-HARD-014',b,cases=[]));(self.root/'case.json').write_text('{}')
        with self.assertRaises(ContractError):evaluate_math(ref,self.root,b,p)
    def test_polynomial_coefficient_properties(self):
        for n in range(1,8):
            for c in range(-3,4):self.assertEqual(derivative(polynomial(f'{c}*x^{n}'),'x'),polynomial(f'{c*n}*x^{n-1}') if n>1 else polynomial(str(c)))
GOOD=[('derivative',dict(expression='x^3+2*x',variable='x',result='3*x^2+2')),
('partial',dict(kind='derivative',expression='x^2*y+3*y',variable='x',result='2*x*y')),
('zero_derivative',dict(kind='derivative',expression='7',variable='x',result='0')),
('antiderivative',dict(expression='2*x+3',variable='x',result='x^2+3*x+9')),
('definite_integral',dict(expression='x^2',variable='x',lower='0',upper='3',result='9')),
('integral_parameter',dict(kind='definite_integral',expression='x*y',variable='x',lower='0',upper='2',result='2*y')),
('matrix_product',dict(a=[['1','2'],['3','4']],b=[['2','0'],['0','2']],result=[['2','4'],['6','8']])),
('linear_solve',dict(a=[['2','1'],['1','-1']],b=[['5'],['1']],result=[['2'],['1']])),
('pivot_swap',dict(kind='linear_solve',a=[['0','1'],['1','1']],b=[['2'],['3']],result=[['1'],['2']])),
('dot',dict(a=['1','2','3'],b=['4','5','6'],frame_a='world',frame_b='world',result='32')),
('cross',dict(a=['1','0','0'],b=['0','1','0'],frame_a='world',frame_b='world',result=['0','0','1'])),
('units',dict(value='36',from_unit='km/h',to_unit='m/s',result='10',absolute_tolerance='0')),
('litres',dict(kind='units',value='2',from_unit='L',to_unit='mL',result='2000',absolute_tolerance='0')),
('area_units',dict(kind='units',value='1',from_unit='m2',to_unit='cm2',result='10000',absolute_tolerance='0')),
('percent',dict(kind='units',value='25',from_unit='percent',to_unit='ratio',result='1/4',absolute_tolerance='0')),
('roots',dict(expression='x^2-1',variable='x',roots=['-1','1'])),
('repeated_root',dict(kind='roots',expression='x^2-2*x+1',variable='x',roots=['1'])),
('no_real_roots',dict(kind='roots',expression='x^2+1',variable='x',roots=[])),
('linear_root',dict(kind='roots',expression='3*x-1',variable='x',roots=['1/3']))]
for name,row in GOOD:
    c=dict(case_id='a',kind=row.get('kind',name),**{k:v for k,v in row.items()if k!='kind'})
    def good(self,c=c):self.assertEqual(self.run_case(c).status,'REVIEW_REQUIRED')
    setattr(MathChecks,'test_exact_'+name,good)
    bad=copy.deepcopy(c)
    if bad['kind']=='roots':bad['roots']=['99']
    elif type(bad['result'])is str:bad['result']='99'
    elif type(bad['result'][0])is list:bad['result'][0][0]='99'
    else:bad['result'][0]='99'
    def failure(self,c=bad):self.blocked(self.run_case(c),'MATHEMATICAL_COUNTEREXAMPLE')
    setattr(MathChecks,'test_counterexample_'+name,failure)
REVIEWS=[dict(kind='derivative',expression='sin(x)',variable='x',result='cos(x)'),dict(kind='derivative',expression='x/x',variable='x',result='0'),
 dict(kind='linear_solve',a=[['1','1'],['1','1']],b=[['1'],['1']],result=[['1'],['0']]),
 dict(kind='roots',expression='x^2-2',variable='x',roots=[]),dict(kind='roots',expression='x^3-1',variable='x',roots=['1']),dict(kind='tensor',description='Unsupported tensor calculation')]
for i,c in enumerate(REVIEWS):
    def review(self,c=c):r=self.run_case(dict(case_id='a',**c));self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertGreater(len(r.findings),1)
    setattr(MathChecks,'test_unsupported_profile_'+str(i),review)
INVALID=[dict(kind='units',value='1',from_unit='m',to_unit='s',result='1',absolute_tolerance='0'),dict(kind='units',value='1',from_unit='m',to_unit='m',result='1',absolute_tolerance='0.1'),
 dict(kind='dot',a=['1'],b=['1'],frame_a='world',frame_b='other',result='1'),dict(kind='matrix_product',a=[['1','2']],b=[['1','2']],result=[['1']]),
 dict(kind='definite_integral',expression='x',variable='x',lower='2',upper='1',result='0'),dict(kind='roots',expression='x-1',variable='x',roots=['1','1'])]
for i,c in enumerate(INVALID):
    def invalid(self,c=c):
        with self.assertRaises(ContractError):self.run_case(dict(case_id='a',**c))
    setattr(MathChecks,'test_malformed_'+str(i),invalid)
