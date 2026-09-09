class RequiredArtifactGate:
    def __init__(self, name, key):
        self.name = name
        self.key = key

    def check(self, ctx):
        value = ctx.artifacts.get(self.key)
        ok = value is not None
        if not ok:
            ctx.errors.append(f"{self.name}: missing {self.key}")
        return ok
