from ra2_support import *

class RootIndependence(h.Temp):
    def setup_keys(self,attribute,value,target):
        ks=tuple(replace(k,**{attribute:value}) if k.key_id==target else k for k in self.k.keys)
        self.session=self.fresh(policy=TrustPolicy('trust','tenant',ks))
    def test_clock_status_same_principal_rejected(self):
        self.setup_keys('principal_id','p-clock0','status0')
        self.error('H39_CLOCK_STATUS_INDEPENDENCE',self.k.establish,self.session)
    def test_clock_status_same_group_rejected(self):
        self.setup_keys('independence_group','g-clock1','status0')
        self.error('H39_CLOCK_STATUS_INDEPENDENCE',self.k.establish,self.session)
    def test_root_group_alias_rejected_in_quorum(self):
        self.setup_keys('independence_group','g-status0','review0');self.ready()
        self.error('H39_ROOT_GROUP_CONTENT',self.session.verify_roles,self.k.roles(self.session,'e'*64),'e'*64)
    def test_disjoint_roots_and_content_pass(self):
        self.ready();self.assertEqual(len(self.session.verify_roles(self.k.roles(self.session,'e'*64),'e'*64)),3)
    def test_empty_required_roles_cannot_skip_authorization(self):
        self.ready();self.error('H39_REQUIRED_ROLES',self.session.verify_roles,(),'e'*64,required=())
    def test_duplicate_required_roles_rejected(self):
        self.ready();self.error('H39_REQUIRED_ROLES_DUPLICATE',self.session.verify_roles,(),'e'*64,required=('review','review'))
    def test_root_role_not_content_quorum(self):
        self.ready();self.error('H39_REQUIRED_ROLES',self.session.verify_roles,(),'e'*64,required=('clock',))
    def test_rejected_establishment_does_not_consume_nonce(self):
        self.setup_keys('principal_id','p-clock0','status0')
        self.error('H39_CLOCK_STATUS_INDEPENDENCE',self.k.establish,self.session)
        with self.journal.transaction() as c:self.assertEqual(c.execute('select count(*) from nonces').fetchone()[0],0)

# Different single-purpose entry points must not bypass group/principal rules.
for purpose in ('capture','review','issuer','rights','memory','eval'):
    def grouped(self,purpose=purpose):
        self.setup_keys('independence_group','g-clock0',purpose+'0');self.ready()
        envelope=self.k.envelope(self.session,purpose,'e'*64,{'diagnostic':True})
        self.error('H39_ROOT_GROUP_CONTENT',self.session.verify,envelope,purpose=purpose,subject_digest='e'*64)
    setattr(RootIndependence,'test_single_'+purpose+'_root_group_rejected',grouped)
    def aliased(self,purpose=purpose):
        self.setup_keys('principal_id','p-status0',purpose+'0');self.ready()
        envelope=self.k.envelope(self.session,purpose,'e'*64,{'diagnostic':True})
        self.error('H8_ROOT_SIGNED_CONTENT',self.session.verify,envelope,purpose=purpose,subject_digest='e'*64)
    setattr(RootIndependence,'test_single_'+purpose+'_root_principal_rejected',aliased)
