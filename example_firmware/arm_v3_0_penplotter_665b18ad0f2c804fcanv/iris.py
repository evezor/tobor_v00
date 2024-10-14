
# import struct
try:
    import uasyncio as asyncio
# except (ModuleNotFoundError, ImportError): # TODO: make pyscript mpy have correct exceptions
except:
    import asyncio
import message
import nwk, os, collections, json, time
from floe import Bifrost
# from floe.network import base_parameters

class CanHeader:
    def __init__(self, *, 
                 adr: int, 
                 s: dict, 
                 header_bits: int=29, 
                 ad_bits: int=8, 
                 priority_bits: int=5, 
                #  fault_bits: int=8,  
                 packet_size=8, 
                 type_bits: int=5,
                 **k):
        """
        package [parameter priority bits: 5][address bits: 8][parameter bits: 11 ][type: 5 bits]
        parameter bits [pid][rr/rc/s/w]
        
        adr:0 -> EMCY
        adr:1 -> NETWORK
        adr:2 -> ZORG
        
        """
        self.s = s  # subscription list

        self.adr = adr  # this board's address
        self.header_bits = header_bits  # total # of bits
        self.ad_bits = ad_bits  # bits in address field
        self.num_adr = 2 ** ad_bits - 1
        self.priority_bits = priority_bits  # number of bits above address bits
        self.ad_mask = 2 ** self.ad_bits - 1
        self.type_bits = type_bits

        # constants for unpacking
        self.num_low = self.header_bits - self.ad_bits - self.priority_bits  # number of bits in low portion INCLUDES TYPE BITS
        self.low_mask = 2 ** self.num_low - 1  # also includes type bits
        self.high_mask = (2 ** self.priority_bits - 1) << (self.num_low + self.ad_bits)  # also includes type bits
        self.type_mask = 2 ** self.type_bits - 1
        
        self.packet_size = packet_size

        # constants for packing
        self.low_shft = self.num_low - self.type_bits
        self.pk_mask = 2 ** self.low_shft - 1

        # # network channel
        # self.fault = 2 ** fault_bits
        # self.nwk_l = int(2 ** header_bits / 2 ** ad_bits)
        # self.nwk_h = int(2 ** header_bits - self.nwk_l)
        # # print('channel width is ', self.nwk_l, ' h_nwk is ', self.nwk_h)
        # self.nwk_ad = 2 ** ad_bits - 1

    # ------------------------------------------------------------------------

    def unpack(self, h: int) -> tuple[int, int, int]:
        """
        unpack int header into type, address and pid
        return tuple(type, address, pid)
        """
        # print(h)
        low = h & self.low_mask
        high = h & self.high_mask
        # print('lh ', low, high)
        
        adr = h >> self.num_low & self.ad_mask
        if adr == self.num_adr:  # if adr high just move to adr low
            adr = 0
        return (
            adr,  # adr
            ((high >> self.ad_bits) + low) >> self.type_bits,  # pid
            h & self.type_mask,  # type
        )

    # ------------------------------------------------------------------------

    def pack(self, type: int, pid: int, adr: int) -> int:
        high = pid >> self.low_shft  # grab priority bits
        low = pid & self.pk_mask  # grab low bits
        hdr = ((((high << self.ad_bits) + adr) << self.low_shft) + low) << self.type_bits
        hdr |= type
        return hdr

class FakeBus():
    def __init__(self, iris):
        self.msg = iris.msg
        self.header = CanHeader(adr=3, s=iris.s)
    def subscribe(self, *a):
        pass
    def unsubscribe(self):
        pass
    def send(self, *a, **k):
        print(a, k)
    def rts(self):
        return True

Canvas = collections.namedtuple('Canvas', ['canvas_id','canvas_name'])


class Iris:
    def __init__(self):
        print('Iris initializing')
        self.id = ""
        # self.globals = {'iris': self} # the globals to be used by eval functions
        self.p = {}                 # Parameter Table with no adr
        self.s = {}                 # Subscription List {header: (pid, bundle)}

        self.n = {}                 # these are nwk and zorg functions, putting them here to keep p smaller
        
        # these are temporary until I figure out something better
        self.zorg = False
        self.locals = {'iris': self}  # namespace for repl, gene and eval functions
        
        self.ob = []                # Outbox
        self.obg = []               # Outbox generators
        
        self.webstuff = []          # Gui elements for web interface
        self.bifrost: Bifrost = Bifrost()
        
        self.core = None            # core element
        self.msg = message.Message(iris=self)
        
        self.bus = FakeBus(self)             # can bus pid
        self.buss = {}            # moving to multiple busses soon
        
        self.info = None
        try:
            self.ib = collections.deque((), 40, True)  # micopython with max len and overflow protection
        except TypeError:
            self.ib = collections.deque([])
        
        self.startup_events = 0  # are we awaiting startup events?
        
    def get_gui(self):
        
        def iter():
            for param in self.p.values():
                ws = param.gui()
                if ws:
                    yield json.dumps(ws)           
        def doit():
            yield "["
            yield ",".join(i for i in iter())
            yield "]"
        return "".join(doit())
    
    def on_startup(self, add_remove):
        if add_remove == 'add':
            self.startup_events += 1
        elif add_remove == 'remove':
            self.startup_events -= 1
            print('itss ', self.startup_events)
        else:
            pass
        
    async def wait_for_startup(self):
        while self.startup_events:
            await asyncio.sleep(.2)
            print('waiting on startup')
        return True
       
    def report(self):
        report = []
        report.append('**** Parameter Table ****')
        for pid, v in sorted(self.p.items()):
            _type = str(type(v)).replace("<class '", '').replace("'>", '')
            report.append(f'{pid}: {_type}')
        report.append('\n\n**** OUTBOX ****')
        for msg in self.ob:
            report.append(msg)
        # print('\n\n**** INTERNAL INBOX ****')
        # for msg in self.iib:
        #     print(msg)
        report.append('\n\n ********************** \n')
        return '\n'.join(report)
    
    def list_locals(self):
        return '\n'.join(f'{k}: {v}' for k,v in self.locals.items())
    
    def set_info(self, canvas_id, canvas_name):
        self.info = Canvas(canvas_id, canvas_name=canvas_name)
            
    def save(self):
        p = {}
        for pid, param in self.p.items():
            p[pid] = param.save()
        return p

    def send(self, *, pid, load, type=0, adr=None, is_generator=False) -> None:
        """ add to outbox """
        if adr is not None:
            # print('adr is not none', pid, adr, w)
            h = self.bus.header.pack(type=type, pid=pid, adr=adr)
        else:
            h = self.bus.header.pack(type=type, pid=pid, adr=self.bus.header.adr)
        # print('sending message: {} to outbox'.format(m))

        # put message in sorted order min lowest
        if is_generator:
            self.obg.append((h, load))
            return
        if len(self.ob) < 20:
            # TODO there is an overflow condition when bus is not working, fix this
            self.ob.append((h, load))

    async def cob(self):
        """ check outbox """
        while True:
            if self.ob:
                if self.bus.rts():
                    # print('sending message')
                    h, load = self.ob.pop(0)
                    self.bus.send(load, h)
            elif self.obg:  #outbox generators
                if self.bus.rts():
                    try:
                        load = next(self.obg[0][1])
                        h = self.obg[0][0]
                        self.bus.send(load, h)
                    except StopIteration:
                        print('done sending')
                        self.obg.pop(0)            
            await asyncio.sleep(.02)

    async def cib(self):
        """ check inbox """
        while True:
            if self.ib:
                msg_func, sub, load = self.ib.popleft()
                # print(msg_func, sub, load)
                msg_func(load, sub)
            await asyncio.sleep(0)

    def add_bus(self, label, bus):
        self.bus = bus
        
        self.buss[label] = bus

    def subscribe(self, header, pid, bundle):
        self.bus.subscribe(header, pid)  # busses like MQTT require subbing from broker
        if header in self.s:
            current_pid, bundle = self.s[header]
            if isinstance(pid, tuple):
                if pid in current_pid:
                    return
                subs = list(current_pid)
                subs.append(pid)
                subs = tuple(subs)
            else:
                if pid == current_pid:
                    return
                subs = (current_pid, pid)
            
            self.s[header] = (subs, bundle)
        else:
            self.s[header] = (pid, bundle)
    
    def unsubscribe(self, header):
        self.bus.unsubscribe(header)
        self.s.pop(header)

    def clear_subs(self):
        subs = list(self.s.keys())
        for sub in subs:
            print(f'unsubscribing: {sub}')
            self.bus.unsubscribe(sub)
            self.s.pop(sub)
    
    def add_hots(self, all_hots: dict[str, list[int]]):
        for pid, hots in all_hots.items():
            for hot in hots:
                self.p[int(hot)].add_hot(pid)

        
    def boot(self, start_mailboxes=False):
        pids = list(self.p.keys()) # p changes during iteration
        for pid in pids:
            self.p[pid].update()
        if start_mailboxes:
            loop = asyncio.get_event_loop()
            loop.create_task(self.cib())
            loop.create_task(self.cob())
        self.n.update(nwk.nwk)
        
        if self.core:
            self.core.boot()

        if 'on_startup' in self.locals:
            # this is a CodeBlock with name on_startup
            startup = self.locals.pop('on_startup')
            startup("None")  # event cannot be None 
                 
            



if __name__ == '__main__':
    print('iris test')
    # iris = Iris(adr=36, fault_bits=8, header_bits=29, ad_bits=10, priority_bits=3)
    # print(test := iris.msg.unpack(472186874))
    # print(iris.msg.pack(**test))



