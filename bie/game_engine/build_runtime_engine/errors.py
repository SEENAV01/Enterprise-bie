class GameBuildError(ValueError):
    def __init__(self,code,detail=''):
        self.code=code;self.detail=detail;super().__init__(code+(': '+detail if detail else ''))
