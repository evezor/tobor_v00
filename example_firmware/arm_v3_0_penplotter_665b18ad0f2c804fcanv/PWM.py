"""
ESP32 pwm driver    
"""
from floe import FP, make_var, Stater
from Parameter import Parameter
try:
    import machine
except:
    import fakes.machine as machine
try:
    import utime
except:
    import fakes.utime as utime

class PWM(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, pin, freq, duty, duty_min: float, duty_max: float, invert_duty, initial_state=False, **k):
        super().__init__(**k)
        self.pin = pin
        self.freq = make_var(freq)
        self.duty = make_var(duty)
        self.duty_min = make_var(duty_min)
        self.duty_max = make_var(duty_max)
        self.invert_duty = make_var(invert_duty)
        self.state = False
        self.initted = False
        
        
    def __call__(self, state: bool, **k):
        if state is not None:
            if self.state != state:
                self.hw(state)
        super().__call__(state)

    def update(self):
        super().update()
        # Set up hardware
        
        # self.iris.hw_outs.append(self.pid)
        
        self.duty.add_hot(self.set_duty)
        self.freq.add_hot(self.set_freq)
        
    def set_duty(self, state: float):
        if self.state:
            self.pin.duty(self.make_duty(state))
        else:
            self.__call__(True)
    
    def make_duty(self, state):
        if self.invert_duty.state:
            state = -(state - 1)
        dif = self.duty_max.state - self.duty_min.state
        duty = state * dif
        duty += self.duty_min.state
        return int(duty*1023)
        
    
    def set_freq(self, state: int):
        self.pin.freq(state)
                
    def hw(self, state):

        if state:
            if self.initted:
                self.pin.init(freq=self.freq.state, duty=self.make_duty(self.duty.state))
            else:
                
                print(self.duty.state)
                self.pin = machine.PWM(machine.Pin(self.pin), freq=self.freq.state, duty=self.make_duty(self.duty.state))
                self.initted = True
        else:
            if not self.initted:
                return
            self.pin.duty(0)






    