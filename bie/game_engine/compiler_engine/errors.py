class GameCompilerError(ValueError):
    def __init__(self, code:str, detail:str=''):
        self.code=code;self.detail=detail;super().__init__(code+(': '+detail if detail else ''))
