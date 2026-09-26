from .workspace import build_workspace
def execute(ctx,asset_blobs,root,policy=None):
 from .contracts import BuildPolicy
 return build_workspace(ctx,asset_blobs,root,policy or BuildPolicy()).manifest
