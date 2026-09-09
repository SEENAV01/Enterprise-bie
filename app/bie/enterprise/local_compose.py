
class DeployError(ValueError):pass
def compose_spec():
 return {"version":"3.9","services":{
  "api":{"image":"bie-api:local","depends_on":["postgres","objectstore"]},
  "worker":{"image":"bie-worker:local","depends_on":["postgres","objectstore"]},
  "postgres":{"image":"postgres:16","healthcheck":True},
  "objectstore":{"image":"minio/minio","healthcheck":True}}}
def validate(s):
 req={"api","worker","postgres","objectstore"}
 if set(s.get("services",{}))!=req:raise DeployError("required local services missing")
 return True
