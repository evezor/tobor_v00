import os
import struct, json
from Parameter import Parameter

class FileSender(Parameter):
    struct = 'e'
    """ receives files from FileSender """
    def __init__(self, name="", packet_size=8, **k):
        super().__init__(name=name, **k)
        self.sending = False
        self.remote_filename = ""
        self.gen = None
        # self.fs = 0
        self.index = 0
        self.index_divisor = 0
        self.progress = 0
        self.packet_size = packet_size
        self.remote_pid = 0
        self.remote_adr = 0
        self.header = 0
        if name != 'no_name':
            element = {"name": name, "pid": self.pid, "type": "FileSender"}
            self.iris.webstuff.append(element)

    def __call__(self, state, gui=False):
        if gui:
            state = json.loads(state.decode('utf8'))
            print('sending file', state)
            self.send_file(**state)
            return
        
        if self.sending:
            if state == b'\x06':  # ACK
                try:
                    self.state = next(self.gen)
                    self.index += 1
                    _progress = round(self.index / self.index_divisor, 2) * 100
                    if self.progress != _progress:
                        self.iris.bifrost.send(self.pid, self.progress)
                        self.progress = _progress
                except StopIteration:
                    self.state = b''
                    self.sending = False
                # print('sending', self.state)
                self.send(pid=self.remote_pid,
                          adr=self.remote_adr,
                          cmd=1)
            if not self.sending:
                self.iris.unsubscribe(header=self.header)
                self.reset()
            

    def send_file(self, 
                  local_filename: str, 
                  remote_filename: str,
                  remote_pid: int,
                  remote_adr: int):
        self.reset()
        self.remote_adr = int(remote_adr)
        self.remote_pid = int(remote_pid)
        
        # create subscription
        self.header = self.iris.bus.header.pack(type=0, pid=self.remote_pid, adr=self.remote_adr)
        print('creating sub to', self.header)
        self.iris.subscribe(header=self.header, pid=self.pid, bundle=self.struct) 
        
        
        self.remote_filename = remote_filename
        filesize = os.stat(local_filename)[6]
        self.index_divisor = filesize // self.packet_size
        # we send the length of the filename and the filesize in the first packet
        first_frame = struct.pack("BI", len(remote_filename), filesize)
        self.state = first_frame
        self.gen = self.file_gen(remote_filename, local_filename)
        self.sending = True
        self.send(pid=self.remote_pid,
                  adr=self.remote_adr,
                  cmd=1)
 
    def file_gen(self, remote_filename, local_filename: str):
        remote_filename = remote_filename.encode()
        while True:
            if len(remote_filename) > self.packet_size:
                yield remote_filename[:self.packet_size]
                remote_filename = remote_filename[self.packet_size:]
            elif len(remote_filename) <= self.packet_size:
                chunk = remote_filename
                break
        print(local_filename)
        with open(local_filename, 'rb') as f:    
            # TODO: I think there will be a bug if the remainder of the filename and the file are less than 1 packet_len
            chunk = chunk + f.read(self.packet_size - len(chunk))
            print('chunk', chunk)
            yield chunk
            while True:
                chunk = f.read(self.packet_size)
                if not chunk:
                    break
                yield chunk
        
    def reset(self):
        self.sending = False
        self.remote_filename = ""
        self.remote_pid = 0
        self.remote_adr = 0
        self.index = 0
        self.index_divisor = 0
        self.progress = 0
        self.header = 0






    