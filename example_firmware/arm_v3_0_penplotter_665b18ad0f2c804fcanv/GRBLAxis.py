from floe import FP
from iris import Iris

class GRBLAxis:
    def __init__(self, *, 
                 name: str,
                 pid: int|str,
                 move: float | None,
                 max: float | None,
                 min: float | None,
                 home: any,
                 reset: FP | None,
                 iris: Iris,
                 **k
                 ) -> None:
        self.name = name
        self.pid = int(pid)
        self.move = move
        self.max = max
        self.min = min
        self.home = home
        self.reset = reset
        
        iris.p[self.pid] = self
        self.iris = iris

    def update(self):
        if self.reset:
            self.reset = self.iris.p[self.reset.pid]
    
    def gui(self):
        pass
    