"""
Parameter for CNC control
"""
# import floe
from Parameter import Parameter
from floe import make_var
from Gene import Gene
from collections import OrderedDict, deque 
import json, os, sys

try: 
    import utime
except:
    class Utime:
        def __init__(self):
            pass
        def ticks_add(*a, **k):
            pass
        def ticks_ms():
            pass
        def ticks_diff():
            pass
    utime = Utime()
        
try:
    import uasyncio as asyncio
except:
    import asyncio
from floe import FP
from iris import Iris

JSON = str
def wtf(a):
    pass

class Buffer:
    """Buffer object to for sending serial to grbl
       grbl can recv up to 128bytes at once so we can send before we get 'ok' """
    def __init__(self) -> None:
        self.max_buf = 128
        self.buflen = 0
        self.uart = wtf # this has to be injected at grbl.update()
        # self.gene = None       # this has to be injected at grbl.update()
        self.queue = []
        self.mt_buf = False  # set when we're emptying buffer, once buffer is mt we will next gene
        self.planner = 15  # size of grbl planner
        self.max_planner = 15
        self.buffer = 128  # size of grbl buffer ## for now I think that Iris loop is slower than GRBL's so we can't overrrun it by sending single commands
        self.num_sent = 0  # we must count the number of commands sent so we may wait til mtbuf is completed

    def send(self, cmd, mt_buf=False, newline=True):  # -> True|None:
        if newline:
            cmd += '\n'
        
        if mt_buf:
            self.mt_buf = True
            _continue = None
        
        if self.planner:
            self.planner -= 1
            self.num_sent += 1
            # ok to send
            self.uart(cmd)
            _continue = True
        else:
            print('buffer q', cmd)
            self.queue.append(cmd)
            _continue = None
        
        return _continue
    
    def ok(self):
        # we got 'ok' 
        self.num_sent -= 1
        if self.num_sent < 0:
            print('grbl buffer underrun something must have happened')
            self.num_sent = 0
        self.planner += 1
        if self.planner > self.max_planner:
            self.planner = self.max_planner   
              
        if self.queue:
            # print('checking planner', self.planner)
            if self.planner > 10: # let's try and give some time to buffer ok's
                print('sending buffered')
                self.send(self.queue.pop(), newline=False)
                if not self.mt_buf:
                    return True
        else:
            if self.mt_buf and self.planner == self.max_planner:
                print('buf flushed')
                self.mt_buf = False
                return True


class GRBL(Parameter):
    standards = ('x','y','z','a','b','c')
    
    def __init__(self, *, 
                 name: str,
                 iris: Iris, 
                 UART: FP,
                 hbt:int=1000, 
                 x:FP | None, 
                 y:FP | None, 
                 z:FP | None, 
                 a:FP | None, 
                 b:FP | None, 
                 c:FP | None, 
                 webserver_output: bool=True,
                 **k):
        # todo add functions back in? should they be injected somehow else?
        super().__init__(iris=iris, name=name,  **k)
        self.uart: Parameter = UART
        self.buffer = Buffer()  # this is the buffer on the grbl board. buffer_size = 128 bytes
        self.state = 'alarm'
        self.queue = {}
        self.axes = OrderedDict()  # {'theta': GRBLAxis}
        
        for label, axis in zip(self.standards, (x,y,z,a,b,c)):
            if axis is not None:
                self.axes[label] = axis
        
        self.offset = {axis: 0 for axis in self.axes}
        self.offset['name'] = 'machine'
        self.tool_offset = {axis: 0 for axis in self.axes}
        self.positions = {axis: 0 for axis in self.axes}
#         self.move = Move(self)
        self.default_feedrate = '500'
        self.rapid_feedrate = '3500'
            
        self.status = {
            'state': 'Sleep',
            'MPos': {axis: 0 for axis in self.axes},
            'limits': ''
        }
        
        #  self.f = functions  # example {'home_x', pid}
        self.funcs = {
            'home_x': lambda *_: self.home('x'),
            'home_y': lambda *_: self.home('y'),
            'home_z': lambda *_: self.home('z'),
            'home_a': lambda *_: self.home('a'),
            'home_b': lambda *_: self.home('b'),
            'home_c': lambda *_: self.home('c'),
            'home': self.home,
            'term': lambda line: self.buffer.send(line['msg']),
            'machine': self.machine,
            'set_work_offset': self.set_work_offset,
            'unlock': lambda *_: self.send_g('$X'),
            'disable_motors': lambda *_: self.send_g('$MD'),
            'jog_cancel': lambda *_: self.send_g(b'\x85'),
            'get_status': lambda *_: self.uart('?'),
            'enable_motors': lambda *_: self.send_g('$ME'), 
            'feed_hold': lambda *_: self.send_g(b'!'), # TODO: probably handle this better?
            'send_raw_line': lambda line: self.send_g(line),
            'move.linear': self.move_linear,
            'move.rapid': self.move_linear,
            'listdir': self.listdir,
            'mt_buf': self.mt_buf,
            'req_w_offset': self.req_w_offset,
            'run': self.run,
        }
        
        self.bifrost = None
        if webserver_output:
            self.bifrost = True
            
        self.gene = Gene(iris=iris, bifrost=iris.bifrost, pid=69)
        self.scripts = {}  # scripts for Gene
        
        self.hbt_int = hbt
        self.next_hbt = utime.ticks_add(utime.ticks_ms(), self.hbt_int)
        self.webstuff = {'name': name, 'pid': self.pid, 'type': 'GRBL'}
        
    def update(self):
        super().update()
        axes = OrderedDict()
        for label, axis in self.axes.items():
            axes[label] = self.iris.p[axis.pid]
        self.axes = axes
        self.axes_map = {axis.name: label for label, axis in self.axes.items()} # {axis name: standard}
        self.gene.register_functions(self, list(self.funcs.keys()), param_is_cnc=True)
        self.buffer.uart = self.uart

        runtime = sys.implementation
        # do not run async in pyscripts and other pythons
        if runtime.name == 'cpython':
            return
        if runtime._machine == 'JS with Emscripten':
            return 
        self.buffer.send('$10=2\n') # add thing for extra debug from status query
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())


    def gui(self):
        return {'name': self.name, 'pid': self.pid, 'type': 'GRBL'}
 
    def __call__(self, state: dict | JSON | bytes, gui=False):
        # example: {'cmd': function, 'data': argument} 
        if isinstance(state, bytes):
            state = state.decode('utf-8')
        if isinstance(state, str):
            state = json.loads(state)
        cmd = state.pop('cmd')
        if state != {}:
            return self.funcs[cmd](state)
        else:
            return self.funcs[cmd]()
    
    def get_pos(self, *, kinematics='cartesian'):
        return self.positions

    async def chk(self):
        while True:
            # do heartbeat, poll grbl
            if utime.ticks_diff(self.next_hbt, utime.ticks_ms()) <= 0:
                self.uart('?')  # this bypasses the buffer, grbl executes on recv
                self.next_hbt = utime.ticks_add(self.next_hbt, self.hbt_int)

            self.check_uart()
            await asyncio.sleep(0)
    
    def check_uart(self):
        while self.uart.any():
            msg = self.uart.readline()
            
            if msg == '':
                return

            if msg[0] == '<': # grbl info line
                self.parse_status(msg)

            elif msg == 'ok':
                if self.buffer.ok():
                    self.gene(None)
                return

            else:
                if self.iris.bifrost is not None:
                    self.iris.bifrost.send(self.pid, {'cmd': 'post', 'data': msg})

    def run(self, script: str | list):
        if isinstance(script, str):
            if script in self.scripts:
                self.gene.load(self.scripts[script])
            else:        
                self.gene.load(script)
        elif isinstance(script, dict):
            #TODO parse this better if there are more kwargs
            self.gene.load(script['script'])
        else:
            self.gene.load(script)

    def mt_buf(self):
        # print('mt_buf')
        self.buffer.send('G4 P.01', mt_buf=True)
        
    def move_linear(self, cmd: dict):
        # example: {'cmd': 'move.linear', 'x': 5, 'y': None}
        if 'comment' in cmd:
            self.send_bf(cmd.pop('comment'))
        
        if 'feed' in cmd:
            feed = str(cmd.pop('feed'))
        else:
            feed = self.default_feedrate
        feed = f'F{feed}'
        
        # clean empty values
        cmd = {axis: float(val) for axis, val in cmd.items() if val != ''}
        
        # apply offset
        for axis, val in cmd.items():
            cmd[axis] = val + self.offset[axis]
        
        line = ['G1']
        line.extend([f"{k.upper()}{v}" for k,v in cmd.items()])
        line.append(feed)
        
        line = ' '.join(line)

        self.state = 'run'
        # self.send_g(line)
        _continue = self.buffer.send(line)
        # if this is called by Gene then we want to return true so we may continue running    
        return _continue

    def set_work_offset(self, line):
        if 'cmd' in line:
            line.pop('cmd')
        self.offset = line
        self.iris.bifrost.send(self.pid, {'cmd': 'set_work_offset', 'data': self.offset})
    
    def machine(self, raw_cmd: dict):
        '''portal to GRBL machine for setting and getting parameters
        {cmd: "machine", action: "set", command: "$/axes/x/steps_per_mm", value: 100}
        '''
        command = raw_cmd['command']
        if raw_cmd['action'] == 'set':
            command += f"={raw_cmd['value']}"
        print(command)
                
        self.buffer.send(command)
    
    def home(self, axis):
        self.send_g('$H{}'.format(axis.upper()))
        
    def jog(self, axis, dir):
        destination = 1000.0
        ax = axis.upper()
        if dir == 'minus':
            destination = -destination
        self.send_g(f'$J={ax}{destination} F500')
        
    def send_g(self, cmd):
        self.buffer.send(cmd)
                    
    def send_bf(self, msg: str):  # send message to self terminal bifrost
        if self.bifrost is not None:
            self.iris.bifrost.send(self.pid, msg)

    def listdir(self, *args, **kwargs):
        files = os.listdir()
        if 'sd' in files:
            files.extend([f'sd/{file}' for file in os.listdir('sd')])
        files = {'cmd': 'post', 'data': '\n'.join(files)}
        self.iris.bifrost.send(self.pid, files)
        
    def parse_status(self, msg: str) -> None:
        def status_str() -> str:
            l = [self.status['state']]
            for axis, pos in self.positions.items():
                l.append(f'{axis}{round(pos, 3)}')
            l.append(self.status['limits'])
            return ' '.join(l)
        
        # example: <Idle|MPos:0.000,0.000,0.000|FS:0,0>
        msg = msg.strip('<>').split('|')
        self.status['state'] = msg[0]
        mpos = msg[1][5:].split(',')  # remove Mpos:
        
        for i, axis in enumerate(self.axes):
            self.status['MPos'][axis] = float(mpos[i])
            self.positions[axis] = self.status['MPos'][axis] - self.offset[axis]
            
        # self.status['limits'] = msg[3]
        # print(status_str())
        if self.bifrost:
            msg = {'cmd': 'status'}
            msg.update(self.positions)
            msg['state'] = self.status['state']
            self.send_bf(msg)

    def req_w_offset(self, data: dict):
        off_id = data['off_id']
        data = {'mpos': self.status['MPos'], 'off_id': off_id}
        self.iris.bifrost.send(self.pid, {'cmd': 'set_w_offset', 'data': data})
        
# $/axes/x/acceleration_mm_per_sec2=100







    