class FencingTokens:
    def __init__(self):
        self._tokens={}

    def issue(self, artifact_id):
        n=self._tokens.get(artifact_id,0)+1
        self._tokens[artifact_id]=n
        return n

    def valid(self, artifact_id, token):
        return self._tokens.get(artifact_id)==token
