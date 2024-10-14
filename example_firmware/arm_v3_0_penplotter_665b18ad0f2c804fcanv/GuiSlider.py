from Parameter import Parameter

class GuiSlider(Parameter):
    
    
    def __init__(self, *, name: str = "", min: int=0, max: int=100, initial_value=0, output_float, invert, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.max = max
        self.min= min
        self.state = initial_value
        self.output_float = output_float
        self.invert = invert
        if self.output_float:
            self.struct = 'f'  # float
        else:
            self.struct = 'i'  # int
        
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if gui:
            if isinstance(state, str):
                state = int(state)
            else:
                state = int(state.decode('utf8'))
            print(state)    
            if self.output_float:
                    state = state/100
                    # state = (self.max - self.min) * state + self.min
            print(state)
        super().__call__(state)
        
        # print(self.name, self.state)
        if not gui:
            if self.output_float:
                self.iris.bifrost.send(self.pid, self.state * 100)
            else:
                self.iris.bifrost.send(self.pid, self.state)
       
    def gui(self):
        return {"name": self.name, "pid": self.pid, "min": self.min, "max": self.max, "initial_value": self.state, "type": "GuiSlider"}



    