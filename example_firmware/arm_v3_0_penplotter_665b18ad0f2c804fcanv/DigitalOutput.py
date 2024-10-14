"""
Digital Output for ESP32
"""
from floe import FP, make_var
from Parameter import Parameter

from machine import Pin

class DigitalOutput(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, pin: int, invert: bool | FP, initial_value: bool, **k):
        super().__init__(**k)
        self.invert = make_var(invert)
        self.state = initial_value
        self._pin = int(pin)
        self.pin = None
        # self.iris.hw_outs.append(self)

    def __call__(self, state) -> None:
        super().__call__(state)
        self.hw()

    def update(self):
        super().update()
        if self.invert.state:
            self.pin = Pin(self._pin, mode=Pin.OUT, value=not self.state)
        else:
            self.pin = Pin(self._pin, mode=Pin.OUT, value=self.state)
        
    def on(self):
        self.__call__(True)
    
    def off(self):
        self.__call__(False) 

    def hw(self):
        if self.invert.state:
            self.pin.value(not self.state)
        else:
            self.pin.value(self.state)

    