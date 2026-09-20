from dataclasses import dataclass
import re
class SceneIRVersionError(ValueError):pass
R=re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
@dataclass(frozen=True,order=True)
class SceneIRVersion:
    major:int;minor:int;patch:int
    @classmethod
    def parse(cls,s):
        m=R.match(s or "")
        if not m:raise SceneIRVersionError("invalid semver")
        return cls(*(int(x) for x in m.groups()))
    def __str__(self):return f"{self.major}.{self.minor}.{self.patch}"
def compatibility(writer,reader):
    w=SceneIRVersion.parse(writer);r=SceneIRVersion.parse(reader)
    if w.major!=r.major:return "INCOMPATIBLE"
    if w.minor>r.minor:return "READER_TOO_OLD"
    return "COMPATIBLE"
def required_bump(kind):
    m={"documentation":"PATCH","bugfix_no_contract_change":"PATCH","add_optional_field":"MINOR","add_element_type":"MINOR","add_required_field":"MAJOR","remove_field":"MAJOR","change_field_semantics":"MAJOR"}
    if kind not in m:raise SceneIRVersionError("unknown change")
    return m[kind]
def next_version(current,bump):
    v=SceneIRVersion.parse(current)
    if bump=="PATCH":return str(SceneIRVersion(v.major,v.minor,v.patch+1))
    if bump=="MINOR":return str(SceneIRVersion(v.major,v.minor+1,0))
    if bump=="MAJOR":return str(SceneIRVersion(v.major+1,0,0))
    raise SceneIRVersionError("bad bump")
