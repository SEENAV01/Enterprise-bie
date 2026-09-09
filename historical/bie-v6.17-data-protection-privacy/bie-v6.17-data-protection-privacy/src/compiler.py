from classification import classification,is_restricted
from encryption import encryption_policy,protected
from field_protection import field_protection,protects
from redaction import redaction,redact
from retention import retention_policy,deletable
from deletion import deletion_request,approve,complete
from privacy_boundary import privacy_boundary,purpose_allowed
from access_audit import protected_access,allowed
from masking import masking_policy,apply

def compile_privacy():
    cls=classification("customer-42","RESTRICTED",
                        ["PERSONAL"],"tenant-a")
    enc=encryption_policy("customer-42",
                           "AES-256-GCM",
                           "key://customer-data")
    fp=field_protection("customer-42",
                         ["email","phone"],"TOKENIZE")
    red=redaction("customer-42",["ssn"])
    ret=retention_policy("customer-42",1000,False,
                          "business-retention")
    deletion=complete(approve(
        deletion_request("del-1","customer-42",
                         "privacy-service","retention-expired")))
    boundary=privacy_boundary(
        "customer-42","tenant-a",
        ["customer-support","fraud-review"],True)
    audit=protected_access(
        "access-1","user-1","customer-42",
        "customer-support","ALLOW","tenant-a")
    masking=masking_policy("customer-42",
                           ["phone"],4)
    return {"schema_version":"6.17",
            "classification":cls,
            "encryption":enc,
            "field_protection":fp,
            "redaction":red,
            "retention":ret,
            "deletion":deletion,
            "privacy_boundary":boundary,
            "access_audit":audit,
            "masking":masking,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "restricted":is_restricted(cls),
              "encrypted":protected(enc),
              "field_protected":protects(fp,"email"),
              "retention_expired":deletable(ret,1000),
              "purpose_allowed":purpose_allowed(
                   boundary,"customer-support"),
              "access_allowed":allowed(audit),
              "masked":apply(masking,{"phone":"1234567890"})
            }}
