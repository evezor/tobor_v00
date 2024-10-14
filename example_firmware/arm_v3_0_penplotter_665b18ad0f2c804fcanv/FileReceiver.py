from Parameter import Parameter
import os
import struct


class FileReceiver(Parameter):
    struct = 'e'
    """ receives files from FileSender """
    def __init__(self, **k):
        super().__init__(**k)
        self.state = b'\x06'
        self.recving = False
        self.filename = b""
        self.f = None       # file object
        self.len_fn = 0     # len filename
        self.len_fs = 0     # file size
        # self.index = 0      # not yet implimented

    def __call__(self, state: bytearray):
        if not self.recving: 
            # first frame has filename len and filesize
            self.state = b'\x06' # ACK
            self.len_fn, self.len_fs = struct.unpack('BI', state)
            print(self.len_fn, self.len_fs)
            self.f = open(f"tmp_{self.pid}", 'wb')
            self.recving = True
        else:
            self.recv(state)
        self.send()
        
    
    def recv(self, state):
        
        if state == b'':
            # this should be the closing packet
            self.f.close()
            self.verify()
        elif self.len_fn > 0: # recv filename
            seg_len = len(state)
            if self.len_fn >= seg_len: # we are done
                self.filename += state[:self.len_fn]
                self.len_fn -= seg_len
                if not self.len_fn:
                    self.filename = self.filename.decode('utf8')
                return

            # we have both filename and file data                     
            self.filename += state[:self.len_fn]
            self.filename = self.filename.decode('utf8')
            self.f.write(state[self.len_fn:])
            self.len_fn = 0
        else:
            self.f.write(state)


    def verify(self):
        temp_name = f"tmp_{self.pid}"
        if self.len_fs == os.stat(temp_name)[6]:
            os.rename(temp_name, self.filename)    
        else:
            print('corrupt file send', self.len_fs, os.stat(temp_name)[6], self.filename)
            
            # os.remove(temp_name)
        self.reset()


    def reset(self):
        self.recving = False
        self.filename = b""
        self.len_fs = 0
        self.len_fn = 0

        




    