from .models import RunContext

class Pipeline:
    def __init__(self, stages, gates_by_stage=None):
        self.stages = stages
        self.gates_by_stage = gates_by_stage or {}

    def run(self, ctx):
        ctx.emit("pipeline", "STARTED")
        for stage in self.stages:
            ctx.emit(stage.name, "STARTED")
            try:
                ctx = stage.execute(ctx)
            except Exception as exc:
                ctx.errors.append(f"{stage.name}: {exc}")
                ctx.emit(stage.name, "FAILED", error=str(exc))
                return ctx

            for gate in self.gates_by_stage.get(stage.name, []):
                if not gate.check(ctx):
                    ctx.emit(stage.name, "BLOCKED", gate=gate.name)
                    return ctx

            ctx.emit(stage.name, "COMPLETED")
        return ctx
