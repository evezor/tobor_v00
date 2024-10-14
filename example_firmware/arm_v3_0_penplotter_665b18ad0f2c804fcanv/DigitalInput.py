"""
Digital Input for ESP32
"""
from floe import FP, make_var
from Parameter import Parameter

from machine import Pin

try:
    import uasyncio as asyncio
except:
    import asyncio
    
class DigitalInput(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, pin: int, invert: bool, pullup: bool | None, debounce: int, edge_detection: str, initial_value: bool, **k):
        super().__init__(**k)

        self.invert = make_var(invert)
        self.debounce = make_var(debounce)
        self.state = initial_value
        self.pin = int(pin)
        
        self.edge_detect = edge_detection if edge_detection != "None" else None
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
    
        if pullup == 'pullup':
            self.pin = Pin(pin, mode=Pin.IN, pull=Pin.PULL_UP)
        elif pullup == 'pulldown':
            self.pin = Pin(pin, mode=Pin.IN, pull=Pin.PULL_DOWN)
        else:
            self.pin = Pin(pin, mode=Pin.IN)

        # self.iris.h.append(self)

    def update_params(self):
        super().update()

    def detect_edge(self):
        if not self.edge_detect:
            return True
        if self.edge_detect == 'falling' and self.state: 
            return False    
        if self.edge_detect == 'rising' and not self.state:
            return False
        return True
    
    async def chk(self):
        while True:
            change = False
            if self.invert.state:
                if self.pin.value() == self.state:
                    self.state = not self.state
                    change = self.detect_edge()
                    # print(self.state)
            else:
                if self.pin.value() != self.state:
                    self.state = not self.state
                    change = self.detect_edge()
                    # print(self.state)
            
            if change:
                self.send()
                await asyncio.sleep_ms(25 + self.debounce.state)
            else:
                await asyncio.sleep_ms(25)
    
    
    
    