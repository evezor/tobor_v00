from Parameter import Parameter
import json, struct

try:
    import uasyncio as asyncio
except:
    import asyncio

try:
    import uaiohttp as aiohttp
except:
    import aiohttp

import os, struct, gc
hostname = "http://10.203.136.47:9901"
import namespace

class Zorg:
    def __init__(self, *, name, pid, iris, **k) -> None:
        self.dtypes = Parameter.datatypes
        self.pid = pid
        self.name = name
        self.iris = iris
        self.iris.zorg = self
        iris.p[self.pid] = self

        loop = asyncio.get_event_loop()
        self.loop = loop.create_task(self.chk())
        
        self.state = None  # not needed but not sure how to handle this yet
        
        self.terms = {} # holding ground for terminals
             
        self.changes = [] # holds callbacks to send to gui
        self.devices = {} # compendium of devices zorg can see
        self.names = {}   # I think this is where the board names from the ide will be put in the future
        self.posts = "" 
        self.filesender = None
        
        self.iris.locals[name] = self
    
    def gui(self):
        return {"name": self.name, "pid": self.pid, "type": "Zorg"}
    
    def __call__(self, state, gui=False):
        if gui:
          self._gui(state)
    
    def post(self, msg: str):
        if self.posts:
            self.posts = self.posts + '<br>' + msg
        else:
            self.posts = msg
            self.changes.append(self._post)
    
    def _gui(self, state):
        """Process messages from gui"""
        msg = json.loads(state)
        print(msg)
        cmd = msg['cmd']
        if cmd == 'send':
            if msg['type'] == 'string':
                payload = msg['msg'].encode()
            else:
                payload = [int(byte) for byte in msg['msg'] if byte] 
                payload = struct.pack(f'{len(payload)}B', *payload)
            
            write = 1 if msg['write'] else 0
            h = self.iris.bus.header.pack(write, int(msg['pid']), int(msg['adr']))
            self.iris.bus.send(payload, h)
        elif cmd == 'create_sub':
            self.create_sub(msg['data'])
        elif cmd == 'ide_subs':
            subs = json.loads(msg['subs'])
            for board in subs:
                self.create_sub(board)
        elif cmd == 'save_subs':
            self.narrowband(b'savesubs', "saving subs")
            with open('subscriptions.json', 'w') as f:
                json.dump(self.iris.s, f)
        elif cmd == 'clear_subs':
            self.narrowband(b'clrsubs', "clearing subs")
        elif cmd == 'ping':
            self.narrowband(b'ping', "sending ping")
        elif cmd == 'show_files':
            self.changes.append(self._files)
        elif cmd == 'cluster':
            self.changes.append(self._cluster)
        elif cmd == 'test':
            self.changes.append(self._test)
            
        elif cmd == 'send_file':
            self.post(f"sending file {msg['filename']} to adr:{msg['adr']}")
            self.filesender.send_file(
                local_filename=msg['filename'], 
                remote_filename=msg['filename'],
                remote_pid=65500,
                remote_adr=msg['adr']
            )
        elif cmd == 'get_file':
            self.get_file(msg['filename'])
        elif cmd == 'reset_self':
            import machine
            machine.reset()
        
        elif cmd == 'reset':
            self.esp32_narrowband(b'reset', "resetting all devices")
        elif cmd == 'lightshow':
            self.esp32_narrowband(b'lghtshw', "sending lightshow")

    def terminal(self, load, adr):
        end = False
        if b'\x06' in load: # this is end of text char
            end = True
            self.changes.append(lambda: self._terminal(adr))
            if len(load) > 1:
                load = load[:-1]
            else:
                load = b''
        
         
        if adr not in self.terms:
            self.terms[adr] = load
        else:
            self.terms[adr] += load

        if end:
            this_term = self.terms[adr]
            print(this_term)
            length = this_term[-1]
            msg = this_term[:-1]
            if len(msg) != length:
                self.terms[adr] = f"error: {msg}".encode()
            else:
                self.terms[adr] = msg


    def get_file(self, filename: str):
        name, ext = filename.split('.')
        url = f'{hostname}/static/Parameters/{name}/{name}.{ext}'
        loop = asyncio.get_event_loop()
        loop.create_task(self._get_file(url, filename))
    
   
    async def _get_file(self, url, filename):
        gc.collect()
        resp = await aiohttp.request("GET", url)
        gc.collect()
        with open(filename, 'wb') as f:
            f.write(await resp.read())
    
    def narrowband(self, arg, post=None):
        self.iris.send(pid=111, adr=1, load=arg)
        if post:
            self.post(post)
            
    def esp32_narrowband(self, arg, post=None):
        self.iris.send(pid=500, adr=1, load=arg)
        if post:
            self.post(post)
    
    def create_sub(self, data):
        # msg.data: [producer adr, producer pid, consumer adr, consumer pid, 'int']
        # msg.data: [16, 46518, 26, 8673, 'int']
        if isinstance(data, str):
            data = json.loads(data)
        p_adr, p_pid, c_adr, c_pid, dtype = data
        if c_adr == self.iris.bus.header.adr: # sub for zorg??
            header = self.iris.bus.header.pack(0, p_pid, p_adr)
            self.iris.subscribe(header, c_pid, self.dtypes[dtype])
            return
        payload = struct.pack("BHHs", p_adr, p_pid, c_pid, self.dtypes[dtype].encode())
        h = self.iris.bus.header.pack(1, 100, c_adr)
        self.iris.bus.send(payload, h)
        self.post(f"create sub adr:{c_adr}, {payload}")
    
    def update(self):
        core = str(type(self.iris.core))
        if core == "<class 'ESP32Core'>":
            print('creating filesender')
            from FileSender import FileSender
            FileSender(name="no_name", pid=65501, debug=False, active=True, bcast=True, iris=self.iris)
            self.filesender = self.iris.p[65501]
        
    def ping_from(self, load: str, adr):
        '''ping return from someone, load is base64id'''
        load = load.decode('utf8')
        if load in self.names:
            self.devices[adr] = [load, self.names[load]]
        self.devices[adr] = (load, 'unknown device')
        if self._devices not in self.changes:
            self.changes.append(self._devices)
    
    ##############
    #  changes callbacks
    #############
    
    def _post(self):
        msg = {'cmd': 'term', 'msg': self.posts}
        self.posts = ""
        return msg
    
    def _devices(self):
        return {'cmd': 'devices', 'devices': self.devices}
    
    def _files(self):
        return {'cmd': 'files', 'files': os.listdir()}
    
    def _cluster(self):
        return {'cmd': 'cluster', 'cluster': [[board.name, board.adr] for board in namespace.namespace.values()]}
    
    def _terminal(self, adr):
        msg = self.terms[adr].decode('utf8')
        # TODO: parse message here maybe look for |
        post = f"{adr}: {msg}"
        self.terms[adr] = b''
        self.post(post)
        
    def _test(self):
        return {'cmd': 'my_id', 'my_id': self.iris.id}
    
    
    async def chk(self):
        while True:
            if self.changes:
                callback = self.changes.pop(0)
                self.iris.bifrost.send(self.pid, callback())
            await asyncio.sleep(.5)
    