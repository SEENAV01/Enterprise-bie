from component_registry import get_contract
from performance import performance_policy
from quality import quality_checks

def compile_component(component):
    kind=component.get("type")
    contract=get_contract(kind)
    if not contract:
        raise ValueError("UNREGISTERED_COMPONENT")
    q=quality_checks(component)
    return {
      "component_contract":contract,
      "spec":component,
      "quality":q
    }

def system_policy():
    return {
      "component_api_version":"1.0",
      "semantic_components":True,
      "reusable_components":True,
      "renderer_can_be_upgraded_without_changing_pedagogy":True,
      "performance":performance_policy()
    }
