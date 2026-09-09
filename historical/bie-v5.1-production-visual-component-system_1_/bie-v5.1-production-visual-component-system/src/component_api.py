COMPONENT_API_VERSION="1.0"

BASE_PROPS={
"visible":True,
"opacity":1.0,
"zIndex":0,
"transform":{},
"accessibility":{}
}

def component_contract(name, semantic_role, required_props=None):
    return {
      "name":name,
      "semantic_role":semantic_role,
      "required_props":required_props or [],
      "base_props":BASE_PROPS,
      "api_version":COMPONENT_API_VERSION
    }
