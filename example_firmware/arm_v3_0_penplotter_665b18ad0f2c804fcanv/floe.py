import json
try:
    import uasyncio as asyncio
except:
    import asyncio

PID = int

class Stater:
    def __init__(self, state: any):
        """ stored constant for use when a remote parameter is not wanted """    
        self.state = state
        self.hot = None
        
    def __call__(self, state) -> None:
        self.state = state
        if self.hot:
                if type(self.hot) is tuple:
                    for h in self.hot:
                        h(self.state)
                else:
                    self.hot(self.state)

    def add_hot(self, hot: callable):
        if self.hot:
            if self.hot is tuple:
                _hot = list(self.hot)
                _hot.append(hot)
                self.hot = tuple(_hot)
            else:
                self.hot = (self.hot, hot)
        else:
            self.hot = hot        
    
class FP:
    '''Future Param, is a holder until all params created then updated with references with update method
    '''
    def __init__(self, pid) -> None:
        self.pid = pid
        
def make_var(item: any) -> Stater | FP:
    """
    Parameter will expect to get value by requesting item.state
    """
    if isinstance(item, FP):
        return item
    return Stater(item)

class Bifrost:
    """ bifrost is the bridge for the gods. busses and other things are shuffled behind the scenes to the websocket"""
    def __init__(self) -> None:
        self.bifrost = []
        self._checked = [] # to be injected once known to be true
        self.funcs = {}
    
    def active(self):
        if self._checked != []:
            return True
        return False
    
    def send(self, pid: int, msg: str | dict):
        if self.active():
            if isinstance(msg, dict):
                msg = json.dumps(msg)
            self.bifrost.append(f'{pid},{msg}')
        else:
            print(f"{msg}")

    def post(self, msg: str):
        self.send('term', msg)

    def write(self, msg:str):
        # method for when std_out is redirected
        if msg == "\n" or msg == "":
            return
        self.send('term', f"print: {msg}")
    
    def any(self) -> bool:
        if self.bifrost != []:
            return True
        return False
    
    def pop(self) -> str: 
        return self.bifrost.pop(0)
        
    # methods below are for cpython, in upython bifrost is handled in server.process_all
    def add_socket(self, manager):
        self.manager = manager
        self._checked = manager.active_connections

    async def chk(self):
        while True:
            if self.any():
                await self.manager.broadcast(self.pop())
            await asyncio.sleep(.01)
            # await asyncio.sleep(.02)
    
    # method for pyscript
    async def pyscript_chk(self, callback, iris, core_type: str):
        import sys
        if core_type == 'py': # pyscript python core type
            # micropython has stdout hardcoded and cannot be changed yet?
            sys.stdout = iris.bifrost
        self._checked = True
        while True:
            if self.any():
                callback(self.pop())
            await asyncio.sleep(.005)


if __name__ == '__main__':
    print('testing')