"""
ESP32 i2c driver    
"""

from Parameter import Parameter, Iris
try:
    import machine
except:
    import fakes.machine as machine

class I2C: 
    def __init__(self, *, sda:int, scl:int, bus:int, baud:int, pid: int, iris: Iris, **k):
        self.i2c = machine.I2C(bus, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=baud)
        iris.p[pid] = self
        
    def update(self):
        pass
    
    def gui(self):
        return None
    