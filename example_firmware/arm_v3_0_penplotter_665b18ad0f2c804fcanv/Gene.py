import json
from floe import Bifrost
from iris import Iris
# from Parameter import Parameter
try:
    import uasyncio as asyncio
except:
    import asyncio

class _Pass:
    def __init__(self):
        self.sub = None

class Continue:
    def __init__(self):
        pass
    
class Sleep:
    def __init__(self):
        pass

Pass = _Pass()


class Loader:
    """
    returns generator objects for Saga Routines
    """

    def __init__(self, **k):
        pass

    def __call__(self, iterable, *args, **kwargs):
        # print(type(iterable))
        if type(iterable) is str:
            print('we have a filename')
            return self._open(iterable)
        elif type(iterable) is list:
            return self._load(iterable)
        elif iterable.__class__.__name__ == 'function':
            print('got a function!!!!')
            return iterable(*args, **kwargs)
        elif iterable.__class__.__name__ == 'generator':
            try:
                return iterable(*args, **kwargs)  # upython handles this poorly
            except TypeError:
                return iterable
        elif iterable.__class__.__name__ == 'bound_method':
            try:
                return iterable(*args, **kwargs)  # upython handles this poorly
            except TypeError:
                return iterable

    @staticmethod
    def _load(_list):
        yield from _list

    @staticmethod
    def _open(file, num_bits=None):  #
        print('opening', file)
        if not num_bits:
            with open(file, 'r') as f:
                for line in f:
                    yield line
        else:
            with open(file, 'r') as f:
                while True:
                    yield f.read(num_bits)

def advance(num):
    """decorator will advance a consumer generator until proper yield statement"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            gen = func(*args, **kwargs)
            for _ in range(num):
                # print('nexting')
                next(gen)
            return gen
        return wrapper
    return decorator

@advance(4)
def wait_until(expression, subscription):
    global Pass
    Pass.sub = subscription
    print('subscription', subscription)
    while True:
        this = yield
        if expression(this):
            yield Continue
            break
        else:
            yield Pass

# @advance(1)
def IF(ifs: dict, default=Pass, loop=False):
    result = yield
    if result in ifs:
        yield ifs[result]
    elif default:
        yield default


class Gene:
    def __init__(self, *, 
                 iris: Iris, 
                 bifrost: Bifrost = None, 
                 debug: bool = False, 
                 pid: int = 69):
        
        self.subscription = None
        self.iris = iris
        self.pid = pid
        self.loader = Loader()
        self.bifrost = bifrost
        self.debug = debug
        
        
        self.gens = []
        self.gen = None
        self.queue = []
        self.log = []
        self.running = False
        
        # stuff for GRBL 
        self.foreign_funcs: dict[str, callable] = {}    
        self.enqueue = False
        self.lock = False
        
        iris.p[pid] = self
    
    def gui(self):
        pass
        
    def sleep(self, seconds: float):
        """ actual function call """
        self.bf_post(f'sleeping for {seconds} seconds')
        return self.make_sleep(seconds)
    
    def make_sleep(self, time):
        """ creates async coroutine with callback """
        async def sleepytime(gene, time):
            await asyncio.sleep(time)
            gene.next(None)
        asyncio.create_task(sleepytime(self, time))
        yield Sleep
        
    def make_sleepytime(self, seconds):
        """ creates generator object for cmd call, eg. {'cmd': 'sleep', 'seconds': 2.5}"""
        yield {'cmd': 'sleepyhack'}
        yield from self.sleep(seconds)
        # yield {'cmd': 'sleepyhack2'}

    def update(self):
        pass  # because it's a parameter
    
    def bf_post(self, msg: str):
        if self.bifrost:
            self.bifrost.post(msg)
        if self.debug:    
            print(msg)
            
    def subscribe(self, sub: tuple[str|int, str]):
        print('subbing', sub)
        if sub is not self.subscription:  # are we already subscribed?
            self.iris.subscribe(header=sub[0], pid=self.pid, bundle=sub[1])
            self.subscription = sub
        
    def unsubscribe(self):
        self.iris.unsubscribe(self.subscription[0])
        self.subscription = None

    def load(self, *args, **kwargs):
        '''this will load whatever and begin executing immediately'''
        if self.running:
            self.bf_post('busy running routine. try again later')
            return
        print('loadinggg', *args)
        self.running = True
        self._load(*args, **kwargs)

    def _load(self, iterable, config: dict[any]=None):
        if config:
            _gen = self.loader(iterable, **config)
        else: 
            _gen = self.loader(iterable)
        
        if self.gen is not None:
            self.gens.append(self.gen)
            print('queuing gen', self.gen)
        self.gen = _gen
        # print('we have a gen', self.gen)
        if self.execute(next(self.gen)) is True: # must always do first next in case first yield is consumer
            # print('continuing?')
            self.next(None)  #  continue as normal


    def auto_advance(self, arg) -> any:
        while True:
            result = self.gen.send(arg)
            if result is Continue:
                print('clearing subscription')
                self.unsubscribe()
                return next(self.gen)
            elif result is Pass:
                print(f'creating subscription: {Pass.sub}')
                self.subscribe(Pass.sub)
                if self.enqueue:
                    # We are in the middle of a cnc move and must wait until it's finished before coninuing
                    cmd = {'cmd': 'unlock'}
                    self.bf_post(f'enqueuing {cmd}')
                    self.queue.append(cmd)  
                    self.cnc({'cmd': 'mt_buf'})
                    self.enqueue = False
                    self.lock = True
                return result
            elif result is not None:
                return result
    
    def __call__(self, arg):
        self.next(arg)
        
    def next(self, arg):
        """execute until next yield statement"""
        # print('nexting', arg)
        if self.gen is None:
            error = 'no currently running item'
            print(error)
            self.bf_post(error)
            return
        
        elif self.lock:  # lock is set when we hit an IF while grbl is executing 
            if arg != 'secret_key':
                self.bf_post('locked, come back later')
                return
            self.bf_post('secret key accepted')
            self.lock = False
        
        arg_once = arg  # we only want to send our arg for a single yield, rest should be None
        # self.log.append(arg)
        while True:
            should_break = self._next(arg_once)
            if should_break is None:
                # print('breaking')
                break
            arg_once = None           
    
    def _next(self, arg):
        try:            
            if self.queue:  # grbl is executing, next command is queued for when it completes
                line = self.queue.pop(0)
                self.enqueue = False
                self.bf_post(f'executing queued {line}')
            
            else:
                line = self.auto_advance(arg)
                if line == Pass:
                    self.bf_post('Pass')
                    return None

                if line == Sleep:
                    return None
            
            if self.execute(line) is None:
                # keep executing commands until we reach a callback type
                return None
            else:
                return True

        except StopIteration:
            if self.gens:  # do we have any generators in queue? if so execute them in order
                # print('getting queued gen', self.gens)
                self.gen = self.gens.pop()
                # print(self.gens)
                self.next(arg)
            else:
                self.bf_post('job complete')
                print('job_complete')
                # bifrost.post(str(self.log))
                self.log.clear()
                self.gen.close()
                self.gen = None
                self.running = False
                return None
        
    def execute(self, line) -> bool | None:
        # if execute() returns True it will trigger return to the autoadvancer, else gene.send() will have to be called from outside to continue

        if type(line) is str:  # are we reading from a file?
            line = json.loads(line)
        # print('line', line)
        
        cmd = line['cmd']

        if cmd in self.foreign_funcs.keys():  # command is something like 'move.linear' from grbl
            # just send the whole dict to the param
            self.bf_post(json.dumps(line))
            # print('grbl', line)
            param = self.foreign_funcs[cmd]
            keep_running = param(line)
            if param is self.cnc:  
                self.enqueue = True
            return keep_running
        
        
        elif cmd == 'unlock':
            self.lock = False
            self.bf_post('unlocking')
            return None
        
        elif self.enqueue:
            # we have gotten the first non-move command. we will send command and wait til cnc buffer is emptied
            self.bf_post(f'enqueuing {line}')
            print(f'enqueuing {line}')
            self.queue.append(line)  
            self.cnc({'cmd': 'mt_buf'})
            self.enqueue = False            
            return None

        elif cmd == 'call':
            self.bf_post(json.dumps(line))
            print('call', json.dumps(line))
            self.iris.p[line['pid']](line['arg'])
            return True
            
        elif cmd == 'load':
            # load new script from script itself, this should be a filename if I'm not mistaken
            print(f'loading {line["script"]}')
            self._load(line['script'])
            # Nones get stacked up here as we (not recursively) keep going deeper. not sure if this is a problem
            return None
        
        elif cmd == 'sleep':
            self._load(self.make_sleepytime(line['seconds']))
            return None
        
        elif cmd == 'eval':
            eval(line['eval'], globals(), self.iris.locals)
            return True
        else:
            # print(line)
            self.bf_post(f'unkn cmd: {json.dumps(line)}')
            return True
            
    def register_functions(self, 
                           parameter, # Parameter 
                           funcs: list[str], 
                           param_is_cnc=False):
        # eg *.add_funcs(parameter:callable=self.func, funcs:str=['move.linear, move.rapid], param_is_cnc:bool=True)
        for func in funcs:
            self.foreign_funcs[func] = parameter
        if param_is_cnc:
            self.cnc = parameter
            print('registering cnc', parameter)
        # print(self.foreign_funcs)


if __name__ == '__main__':
    g = Gene(iris=Iris(), debug=True, bifrost=None)
    # def this_gen():
    #     yield stk_light.blue(1)
    #     yield stk_light.buzzer(1)
    #     yield from wait_until(lambda m: m == 1)
    #     yield stk_light.buzzer(0)
    #     this = yield
    #     if this == 2:
    #         yield mosfet.fet_1(1)
    #     elif this == 3:
    #         yield mosfet.fet_2(1)
    #     else:
    #         yield from (i for i in range(3))

    #     yield from IF({1: {'cmd': 1},
    #                 2: {'cmd': 2},
    #                 3: {'cmd': 3},
    #                 4: {'cmd': 4}
    #                 })
    #     yield 'I have spoken'
    # print(g)
    script2 = [
        {'cmd': 'script1'},
        {'cmd': 'script2'},
        {'cmd': 'script3'},
    ]

    test_script = [
    {'cmd': 'message1'},
    {'cmd': 'message2'},
    # {'cmd': 'load', 'script': 'test.evzr'},
    {'cmd': 'message3'},
    {'cmd': 'load', 'script': script2},
    {'cmd': 'message4'}
    ]
    
    def some_new():
        yield {'cmd': 'message1'}
        yield {'cmd': 'message2'}

        yield from g.sleep(2)
        yield {'cmd': "before load"}
        yield {'cmd': 'load', 'script': script2}
        yield {'cmd': 'message3'}
        yield {'cmd': 'sleep', 'time': 4}
        yield from script2
        yield {'cmd': 'message4'}
        

    # print(g.load(this_gen))
    g.load(some_new)
    



    