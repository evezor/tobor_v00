datatypes = {
        'bool': '?',
        'byte': 'b',
        'unbyte': 'B',
        'int16': 'h',
        'unint16': 'H',
        'int': 'i',
        'unint': 'I',
        'int64': 'q',
        'unint64': 'Q',
        'float': 'f',
        'double': 'd',
        'buf': 'e',
        'utf8': 'u',
        'string': 'u',
        'nibble': 'u',
        'rgb': '3b',
        'JSON': 'j'
    }


namespace = {}

class Board:
    def __init__(self, name, adr):
        self.name = name
        self.adr = adr
        namespace[name] = self
    
    # def send(self, state):
    #     self.iris.send(
    #         pid=self.blob[1],
    #         load=self.iris.msg.bundle(self.state, self.struct),
    #         type=1,
    #         adr=self.blob[0]
    #         )
    
    

class Namespace:
    def __init__(self, adr, pid, struct, iris) -> None:
        self.pid = pid
        self.struct = datatypes[struct] if struct in datatypes else struct
        self.adr = adr
        self.iris = iris

    def set(self, state):
        self._send(state, self.pid, self.struct)
        
    def _send(self, state, pid, struct):
        print(state, pid, self.adr, struct)
        self.iris.send(
            pid=pid,
            load=self.iris.msg.bundle(state, self.struct),
            type=1,
            adr=self.adr
        )
        
    def __call__(self, state):
        self._send(state, self.pid, self.struct)

class Bool(Namespace):
    def __init__(self, adr, pid, iris) -> None:
        super().__init__(pid, '?', adr, iris)
    
    def on(self):
        self.set(True)
    
    def off(self):
        self.set(False)






        