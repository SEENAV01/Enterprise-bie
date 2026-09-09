from states import STATES, TERMINAL_STATES, can_transition

class LessonOrchestrator:
    def __init__(self, job):
        self.job = job
        self.events = []

    @property
    def state(self):
        return self.job["state"]

    def transition(self, target, reason, artifact_refs=None, evidence_refs=None):
        if self.state in TERMINAL_STATES:
            raise ValueError("TERMINAL_STATE")
        if target not in STATES or not can_transition(self.state, target):
            raise ValueError("INVALID_STATE_TRANSITION")
        from_state = self.state
        self.job["state"] = target
        self.events.append({
            "from_state":from_state,"to_state":target,
            "reason":reason,"artifact_refs":artifact_refs or [],
            "evidence_refs":evidence_refs or []
        })
        return self.job

    def run_happy_path(self):
        path = [
            "UNDERSTOOD","PLANNED","SCRIPTED","STORYBOARDED",
            "ASSETS_READY","AUDIO_READY","COMPOSED","RENDERED",
            "QA_EVALUATED","VERIFIED"
        ]
        for target in path:
            self.transition(target, "stage_completed")
        return self.job

def valid_state(s):
    return s in STATES
