"""
ESP32 Canbus Driver
"""
import gc

import machine

import os


class SDCard:
    def __init__(self, slot, pid, auto_mount, iris, **k):
        self.pid = pid
        self.slot = slot
        self.sd = None
        self.state = False
        self.iris = iris
        
        self.funcs = {
            'mount_sd': self.mount,
            'ls_sd': self.ls
        }
        
        self.bifrost = None
        # if config.webserver_debug:
        #     self.bifrost = floe.bifrost
        #     self.bifrost.funcs.update(self.funcs)
        
        if auto_mount:
            self.mount()
        
        iris.p[pid] = self
        
    def mount(self, *args, **kwargs):
        if not self.state:
            gc.collect()
            print(gc.mem_free())
            if 'sd' in os.listdir():
                self.state = True
                return
            try:
                self.sd = machine.SDCard(slot=self.slot)
                os.mount(self.sd, "/sd")
                self.state = True
            except OSError:
                machine.reset()

    def _open(self, file, rw):
        with open(f'/sd/{file}', rw) as f:
            for line in f:
                yield line.strip()

    def load(self, file, rw):
        return self._open(file, rw)

    def update(self):
        pass
    def gui(self):
        return None

    def ls(self, *args, **kwargs):
        file_list = tuple(file for file in uos.listdir('/sd') if file != 'System Volume Information')
        files = ', '.join(file_list)
        print(files)
        if self.bifrost is not None:
            self.bifrost.send({'cmd': 'cnc', 'msg': files})
        return file_list 



    