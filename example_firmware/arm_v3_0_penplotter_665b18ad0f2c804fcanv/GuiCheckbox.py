from Parameter import Parameter

class GuiCheckbox(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, name: str = "", initial_value=False, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.state = initial_value
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        super().__call__(state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
        
    def on(self):
        self.__call__(True)
    
    def off(self):
        self.__call__(False)
    
    def gui(self):
        return {"name": self.name, "pid": self.pid, "type": "GuiCheckbox", "initial_value": self.state}

    