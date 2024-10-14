"""
Neopixel Parameter for ESP32
"""

from Parameter import Parameter
from floe import FP, make_var
import machine
from neopixel import NeoPixel as NP

try:
    import uasyncio as asyncio
except:
    import asyncio
    
class NeoPixel(Parameter):
    struct = 'e'  # bytearray[3]
    
    def __init__(self, *, number_of_pixels: int, pin: int, animation: int, animations: list[FP], delay: int, **k):
        super().__init__(**k)
        self.num_pix = int(number_of_pixels)
        _pin = machine.Pin(pin, machine.Pin.OUT)
        self.neo = NP(_pin, number_of_pixels)
        self.off()
        
        self.animation = make_var(animation)
        self.animations = animations
        self.delay = make_var(delay)
        self.index = 0
        
        self.loop = None

    def __call__(self, state: bytearray):
        if state is not None:
            self.state = state
        self.fill(state)
        super().__call__(state)
        
    async def chk(self):
        while True:
            self.animations[self.animation.state - 1].animate(self, self.index)
            self.index += 1
            await asyncio.sleep_ms(self.delay.state)
    
    def update(self):
        super().update()        
        if self.animations is None:
            return
        
        if not isinstance(self.animations, list):
            self.animations = [self.animations]
        self.animations = [self.iris.p[animation.pid] for animation in self.animations]
        self.animation.add_hot(self.change_animation)
        if self.animation.state != 0:
            self.change_animation(self.animation.state)
        
    
    def fill(self, color: tuple[int, int, int]):
        for pix in range(self.num_pix):  # fill the strip/ring
            self.neo[pix] = color
            self.neo.write()
            
    def off(self):
        self.fill((0,0,0))
        
    async def _lightshow(self):
        red = (5,0,0)
        green = (0,5,0)
        blue = (0,0,5)
        self.fill(red)
        await asyncio.sleep(.5)
        self.fill(green)
        await asyncio.sleep(.5)
        self.fill(blue)
        await asyncio.sleep(.5)
        self.off()
        self.loop = None
        
    def lightshow(self):
        if not self.loop:
            loop = asyncio.get_event_loop()
            self.loop = loop.create_task(self._lightshow())

    def change_animation(self, animation: int): 
        if animation == 0:
            if self.loop:
                self.loop.cancel()
                self.loop = None
            self.off()
        else:
            self.animation.state = animation
            self.index = 0
            if not self.loop:
                loop = asyncio.get_event_loop()
                self.loop = loop.create_task(self.chk())



    