"""
ESP32 Canbus Driver
"""
import machine
import esp32
import sys

try:
    import uasyncio as asyncio
except:
    import asyncio
import binascii, struct

import floe

ZORG_CHANNEL = 2

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
        self.type_bits = type_bits  # 0:broadcast 1:write

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

class CANBus:
    def __init__(self, *, pid, adr, iris, terminal_debug: bool=False, bus, tx, rx, baud, rx_queue, **k):
        try:
            self.can = esp32.CAN(bus, tx=tx, rx=rx, mode=esp32.CAN.NORMAL, baudrate=baud, rx_queue=rx_queue)
        except OSError:
            import machine
            machine.reset()
        self.header = CanHeader(adr=adr, s=iris.s) 
        self.iris = iris
        self.msg = iris.msg
        self._info = [0, 0, 0, 0, 0, 0, 0]
        
        # outbox stuff
        self.ob = []
        self.obg = []
        
        self.bifrost = None
        if terminal_debug:
            print('creating can bifrost')
            self.bifrost = True
            
        
        
        iris.p[pid] = self 
        iris.bus = self

    async def chk(self):
        while True:
            while self.can.any():
                h, _a, _b, buf = self.can.recv()
                if self.bifrost:
                    self.iris.bifrost.send('term', f'CAN:{h}, {buf}')
                print(h, buf)
                adr, pid, _type = self.header.unpack(h)
                do_func, sub_pid = self.msg.want(adr, pid, _type, h, self.header.adr)
                if do_func is not False:
                    try:
                        self.iris.ib.append((do_func, sub_pid, buf))
                    except IndexError:
                        print('overflowing')
            await asyncio.sleep(0)

    def rts(self):
        '''ready to send'''
        return not bool(self.can.info(self._info)[5])
    
    def send(self, load, h):
        self.can.send(list(load), h, extframe=True)
        
    def ping(self):
        h = self.header.pack(1, self.header.adr, ZORG_CHANNEL)
        self.send(self.iris.id, h)
        
    def post(self, msg):
        "send strings to zorg"
        pid = self.header.adr + 1000
        post = msg.encode()
        post = post + struct.pack("B", len(post)) + b'\x06'
        for i in range(0, len(post), 8):
            segment = post[i:i+8]
            self.iris.send(pid=pid, load=segment, type=1, adr=ZORG_CHANNEL)
                 
    def subscribe(self, pid, adr) -> int:
        pass
                            
    def unsubscribe(self, *args):
        pass

    def update(self):
        runtime = sys.implementation
        # do not run in pyscripts and other pythons
        if runtime.name == 'cpython':
            return
        if runtime._machine == 'JS with Emscripten':
            return 
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
    
    def gui(self):
        return None
    
    
    
if __name__ == "__main__":
    print('starting')
    head = CanHeader(adr=99, s={})
    def packunpackit(type, pid, adr):
        h = head.pack(type=type, pid=pid, adr=adr)
        print(h)
        print(head.unpack(h))
        


    