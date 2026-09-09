
CAPABILITIES=frozenset({"text","structured_output","tool_calling","vision","multimodal","embeddings","reasoning","long_context","streaming"})
class CapabilityError(ValueError):pass
def validate_capabilities(xs):
 unknown=set(xs)-CAPABILITIES
 if unknown:raise CapabilityError("unknown capabilities: "+",".join(sorted(unknown)))
 return frozenset(xs)
def satisfies(offered,required):return validate_capabilities(required).issubset(validate_capabilities(offered))
