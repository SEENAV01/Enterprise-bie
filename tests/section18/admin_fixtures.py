"""Native inspection and a registry-only test port; never live credentials."""
from structural_pdf_fixtures import hierarchy_pdf_with_outline
from bie.model_gateway.provider_registry import ProviderDescriptor

class RegistryOnly:
    def invoke(self,request):raise AssertionError('LIVE_CALL_NOT_ALLOWED')

def prepare(service,p,success_source):
    service.administration.provision_provider(p,ProviderDescriptor('synthetic-local','registry-only',frozenset({'text'})),
                                              RegistryOnly(),evidence_origin='SYNTHETIC_TEST')
    success=service.create(p,success_source['source_id'],{},'admin-success')['run_id']
    assert service.work_once(p,success)['outcome']=='ACKED'
    # Native ingestion accepts structural pages. An actual invalid empty-title
    # bookmark is rejected by the canonical outline adapter, not a mock producer.
    invalid=service.import_pdf(p,hierarchy_pdf_with_outline(((' ',0,None),)))
    failed=service.create(p,invalid['source_id'],{},'admin-empty-outline-negative')['run_id']
    assert service.work_once(p,failed)['outcome']=='FAILED'
    assert service.status(p,failed)['queue_state']=='DEAD_LETTER'
    return dict(success=success,failed=failed)
