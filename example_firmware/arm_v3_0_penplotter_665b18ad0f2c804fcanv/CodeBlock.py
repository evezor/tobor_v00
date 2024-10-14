from Parameter import Parameter
from floe import make_var, FP
import sys

class CodeBlock(Parameter):
    def __init__(self, *, code: callable, kwargs: list[FP], include_iris: bool=False, **k):
        super().__init__(**k)
        self.kwargs = kwargs
        self.code = code
        self.state = None
        self.include_iris = include_iris
        self.blob = 1 # this is hack
        
    def __call__(self, event):
        if event is not None:
            try:
                self.state = self.code(event, *self.kwargs)
                if self.state is None:
                    return
            except Exception as e:
                print(e)
                print(sys.print_exception(e))
                self.iris.bifrost.post(e)
                return        
        self.send()
        
    def update(self):
        self.kwargs = [self.iris.p[fp.pid] for fp in self.kwargs]
        if self.include_iris:
            self.kwargs.append(self.iris)
