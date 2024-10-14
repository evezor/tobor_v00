
# --------------------------------------
name = 'arm_v3_0_penplotter'
canvas_id = '665b18ad0f2c804fcanv'
# __version__ = TODO: add this
# --------------------------------------
def cb36199(event, grbl):
    import struct
    x, y = struct.unpack('ff', event)
    grbl.move_linear(JSON(x=x, y=y))

def send_tp(event):
    import struct
    if event: # event is a remote button push
        pos = grbl.get_pos()
        msg = struct.pack('ff', pos['x'], pos['y'])
        return msg

def jog(event, jog_x_plus, jog_x_minus, jog_y_plus, jog_y_minus, grbl):
    buttons = [jog_x_plus, jog_x_minus, jog_y_plus, jog_y_minus]
    
    def find_button():
        # check the buttons and find the one that has been pressed 
        for button in buttons:
            if button.state == True: 
                return button
    if not event:
        grbl.funcs['jog_cancel']
    else:
        button = find_button()
        jog, axis, direction = button.name.split('_')
        

def cb41942(event):
    # pen down on check, else pen up
    if event:
        return 0
    return 1


def on_startup(event, grbl):
    print('I thought I wanted to inject something here, but I dont now')
from floe import FP

from Rainbow import Rainbow
from AS5048BEncoder import AS5048BEncoder
from ColorChase import ColorChase
from NeoPixel import NeoPixel
from PWM import PWM
from SDCard import SDCard
from DigitalOutput import DigitalOutput
from DigitalInput import DigitalInput
from GRBLScara import GRBLScara
from WebsocketServer import WebsocketServer
from GRBLAxis import GRBLAxis
from UART import UART
from ScaraKinematics import ScaraKinematics
from ESP32Core import ESP32Core
from I2C import I2C
from Variable import Variable
from Zorg import Zorg
from CodeBlock import CodeBlock
from CANBus import CANBus
from GuiCheckbox import GuiCheckbox
from GuiSlider import GuiSlider
def setup(iris):

  AS5048BEncoder(name='phi_encoder', pid=25434, adr=67, invert=False, offset=0, ring_size=8, i2c=FP(15357), datatype="float32", debug=False, active=True, bcast=True, iris=iris)
  AS5048BEncoder(name='theta_encoder', pid=51140, adr=64, invert=True, offset=0, ring_size=8, i2c=FP(15357), datatype="float32", debug=False, active=True, bcast=True, iris=iris)
  CANBus(name='CANBus', pid=6545, rx=2, tx=4, adr=15, bus=0, baud=250000, rx_queue=25, terminal_debug=False, debug=False, active=True, bcast=False, iris=iris)
  CodeBlock(name='cb36199', pid=36199, code=cb36199, kwargs=[FP(47847)], datatype="None", iris=iris)
  CodeBlock(name='cb41942', pid=41942, code=cb41942, kwargs=[], datatype="None", iris=iris)
  CodeBlock(name='jog', pid=43637, code=jog, kwargs=[FP(48110), FP(22010), FP(51436), FP(13560), FP(47847)], datatype="None", iris=iris)
  CodeBlock(name='on_startup', pid=14702, code=on_startup, kwargs=[FP(47847)], datatype="None", iris=iris)
  CodeBlock(name='send_tp', pid=35085, code=send_tp, kwargs=[], datatype="None", iris=iris)
  ColorChase(name='ColorChase', pid=54271, dot_color=None, fill_color=None, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  DigitalInput(name='button_a', pid=18936, pin=34, pullup='pullup', edge_detection='None', debounce=200, invert=True, initial_value=False, datatype="bool", debug=True, active=True, bcast=False, iris=iris)
  DigitalInput(name='function_button', pid=2276, pin=36, pullup='None', edge_detection='None', debounce=200, invert=True, initial_value=False, datatype="bool", debug=False, active=True, bcast=True, iris=iris)
  DigitalOutput(name='phi_reset', pid=9179, pin=33, invert=True, initial_value=False, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  DigitalOutput(name='theta_reset', pid=62656, pin=32, invert=True, initial_value=False, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  ESP32Core(name='ESP32Core', pid=6074, wifi=True, hbt_led=None, neo_status=FP(47403), function_button=FP(2276), bus=FP(6545), zorg=FP(21885), webserver=FP(24032), debug=False, active=True, bcast=False, iris=iris)
  GRBLAxis(name='a', pid=20957, move=None, max=None, min=None, home=None, reset=None, debug=False, active=True, bcast=False, iris=iris)
  GRBLAxis(name='p', pid=1410, move=None, max=None, min=None, home=None, reset=FP(9179), debug=False, active=True, bcast=False, iris=iris)
  GRBLAxis(name='t', pid=23147, move=None, max=None, min=None, home=None, reset=FP(62656), debug=False, active=True, bcast=False, iris=iris)
  GRBLAxis(name='z', pid=16570, move=None, max=None, min=None, home=None, reset=None, debug=False, active=True, bcast=False, iris=iris)
  GRBLScara(name='grbl', pid=47847, webserver_output=True, theta_encoder=FP(51140), phi_encoder=FP(25434), UART=FP(30101), x=FP(23147), y=FP(1410), z=FP(16570), a=FP(20957), b=None, c=None, kinematics=FP(52123), debug=False, active=True, bcast=False, iris=iris)
  GuiCheckbox(name='set_pen', pid=26695, initial_value=False, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  GuiSlider(name='animation', pid=6128, max=2, min=0, initial_value=1, output_float=False, invert=False, datatype="int", debug=False, active=True, bcast=True, iris=iris)
  GuiSlider(name='animation_speed', pid=39239, max=185, min=10, initial_value=185, output_float=True, invert=False, datatype="int", debug=False, active=True, bcast=True, iris=iris)
  GuiSlider(name='pen_position', pid=48901, max=100, min=0, initial_value=0, output_float=True, invert=False, datatype="int", debug=False, active=True, bcast=False, iris=iris)
  I2C(name='I2C', pid=15357, sda=26, scl=25, bus=0, baud=100000, debug=False, active=True, bcast=False, iris=iris)
  NeoPixel(name='neo_ring', pid=41456, pin=15, number_of_pixels=8, animation=FP(6128), delay=FP(39239), animations=[FP(63993), FP(54271)], datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  NeoPixel(name='neo_status', pid=47403, pin=12, number_of_pixels=1, animation=0, delay=200, animations=None, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  PWM(name='PWM', pid=56720, pin=21, freq=100, duty=FP(48901), duty_min=0.06, duty_max=0.15, invert_duty=False, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  Rainbow(name='Rainbow', pid=63993, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  SDCard(name='SDCard', pid=25805, slot=2, auto_mount=True, debug=False, active=True, bcast=False, iris=iris)
  ScaraKinematics(name='kin', pid=52123, theta_length=200, phi_length=200, max_segment_size=1.0, right_handed=True, debug=False, active=True, bcast=False, iris=iris)
  UART(name='UART', pid=30101, rx=14, tx=27, bus=1, baud=115200, encode='utf8', debug=False, active=True, bcast=False, iris=iris)
  Variable(name='capture_point', pid=38352, state=False, datatype="bool", constant=False, debug=False, active=True, bcast=True, iris=iris)
  Variable(name='jog_x_minus', pid=22010, state=False, datatype="bool", constant=False, debug=False, active=True, bcast=True, iris=iris)
  Variable(name='jog_x_plus', pid=48110, state=False, datatype="bool", constant=False, debug=False, active=True, bcast=True, iris=iris)
  Variable(name='jog_y_minus', pid=13560, state=False, datatype="bool", constant=False, debug=False, active=True, bcast=True, iris=iris)
  Variable(name='jog_y_plus', pid=51436, state=False, datatype="bool", constant=False, debug=False, active=True, bcast=True, iris=iris)
  Variable(name='move_tp', pid=57283, state='', datatype="bytes", constant=False, debug=False, active=True, bcast=True, iris=iris)
  Variable(name='send_self_tp', pid=29286, state='', datatype="bytes", constant=False, debug=False, active=True, bcast=True, iris=iris)
  WebsocketServer(name='WebsocketServer', pid=24032, datatype="null", debug=False, active=True, bcast=False, iris=iris)
  Zorg(name='Zorg', pid=21885, debug=False, active=True, bcast=False, iris=iris)
  iris.add_hots({"26695": [2276], "48901": [41942], "29286": [35085], "36199": [57283], "35085": [38352], "43637": [22010, 48110, 51436, 13560], "41942": [26695]})
  iris.set_info(canvas_id, name)

