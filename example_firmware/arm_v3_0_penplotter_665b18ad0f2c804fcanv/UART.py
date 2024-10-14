"""
ESP32 uart driver
"""

from Parameter import Parameter
import machine
import sys
try:
    import uasyncio as asyncio
except:
    import asyncio

class UART(Parameter):
    def __init__(self, *, bus: int, tx: int, rx: int, baud: int, encode: str, **k):
        super().__init__(**k)
        self.uart = machine.UART(bus, tx=tx, rx=rx, baudrate=baud)
        self.encode = encode  # not sure what this was for anymore
        self.buf = ''
        self.lines = []
        # self.iris.async_hw.append(self)

    def update(self):
        super().update()
        runtime = sys.implementation
        # do not run in pyscripts and other pythons
        if runtime.name == 'cpython':
            return
        if runtime._machine == 'JS with Emscripten':
            return 
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
    def __call__(self, msg: bytes) -> None:
        self.uart.write(msg)
        # if self.blob & 8:  # debug serial
        #     print(f'debug serial[{self.pid}]: {msg}')

    def any(self):
        if self.lines:
            return True
        return False

    def readline(self):
        return self.lines.pop(0)

    async def chk(self):
        while True:
            if self.uart.any():
                self.buf += self.uart.read().decode(self.encode)
                while True:
                    index = self.buf.find('\r\n')
                    if index == -1:
                        break

                    self.lines.append(self.buf[:index])
                    self.buf = self.buf[(index + 2):]
            await asyncio.sleep_ms(0)
            
    # -- async code start -------
    # def __aiter__(self):
    #     return self
    
    # async def __anext__(self):
        
    