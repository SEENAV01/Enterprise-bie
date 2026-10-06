"""Single exact preservation row, not a waiver or sealed-ledger edit."""
import hashlib
import json
from pathlib import Path

LEDGER="manifests/lossless_migration.csv"
LEDGER_SHA="f981c9c11834f4136052306613de16bbb241ca4d980b96fec675d3ca767b76d1"
FILE_ID="9e607fb41ef0fd7ef7e602bb67773d29446d1d0649ef56c648a7785ebd636074"
OLD_SHA="ddb18edf2483bbcc98bb16ad9aa70c872d789b08df0a2ad0cb29af7a86f995d2"
NEW_SHA="dbe9df946b92fa28b539559bd6d7aead915d1f67b360be427108a616008fe464"
OLD="bie/infrastructure/execution_graph_v1.py"
ACTIVE="bie/infrastructure/execution_graph.py"


def regular(root,name):
    path=root/name
    if not path.resolve().is_relative_to(root.resolve()):raise ValueError("MATH_GRAPH_AMENDMENT_PATH")
    for part in (path,*path.parents):
        if part==root:break
        if part.is_symlink():raise ValueError("MATH_GRAPH_AMENDMENT_SYMLINK")
    return path.read_bytes()


def resolve(root,rows):
    root=Path(root).resolve()
    if hashlib.sha256(regular(root,LEDGER)).hexdigest()!=LEDGER_SHA:raise ValueError("MATH_GRAPH_AMENDMENT_LEDGER")
    expected=dict(schema="bie.product.graph-migration/1",task_id="BIE-PROD-031",
        base_sha="b9b65f423355b0856182b9f0e5c23cbff08e890b",ledger_sha256=LEDGER_SHA,
        file_id=FILE_ID,active_path=ACTIVE,active_git_lf_sha256=NEW_SHA,
        preserved_path=OLD,preserved_sha256=OLD_SHA,product_accepted=False)
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError("MATH_GRAPH_AMENDMENT_DUPLICATE")
            result[k]=v
        return result
    document=json.loads(regular(root,"manifests/task031_graph_migration.json"),object_pairs_hook=pairs)
    if document!=expected:raise ValueError("MATH_GRAPH_AMENDMENT_IDENTITY")
    selected=[r for r in rows if r["file_id"]==FILE_ID]
    if len(selected)!=1:raise ValueError("MATH_GRAPH_AMENDMENT_COVERAGE")
    row=selected[0]
    if (row["canonical_path"],row["canonical_sha256"],row["sha256"],row["bytes"],row["archive"],row["disposition"]) != (
        ACTIVE,OLD_SHA,OLD_SHA,"7618","BIE_INFRA_INTEGRATION_001.zip","MIGRATED"):
        raise ValueError("MATH_GRAPH_AMENDMENT_ORIGINAL_IDENTITY")
    if hashlib.sha256(regular(root,OLD)).hexdigest()!=OLD_SHA:raise ValueError("MATH_GRAPH_AMENDMENT_BEFORE_BYTES")
    # Git LF code identity; unlike ledger predecessor, new code has no old raw-byte obligation.
    if hashlib.sha256(regular(root,ACTIVE).replace(b"\r\n",b"\n")).hexdigest()!=NEW_SHA:
        raise ValueError("MATH_GRAPH_AMENDMENT_ACTIVE_BYTES")
    return [dict(r,canonical_path=OLD,reason="Task031 graph migration preserves exact v1 source/profile contract",
                 transform="governed Math graph v2; legacy source retained byte-exact") if r["file_id"]==FILE_ID else r for r in rows]
