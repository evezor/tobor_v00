from floe import make_var

class ColorChase:
    """ color animation for Neo
    """
    RGB = bytearray
    struct = 'e'  # buffer
    
    def __init__(self, pid, iris, dot_color: bytearray=None, fill_color: bytearray=None, **k) -> None:
        self.pid = pid
        # this is a hack until color picker is implimented
        if dot_color is None:
            dot_color = (0,9,3)
        if fill_color is None:
            fill_color = b'\x00\x02\x03'
        
        self.index = 0
        self.dot_color = make_var(dot_color)
        self.fill_color = make_var(fill_color)
        
        iris.p[pid] = self       

    def animate(self, neo, index):
        index %= neo.num_pix
        for pixel in range(neo.num_pix):
            if index == pixel:
                neo.neo[pixel] = self.dot_color.state
            else:
                neo.neo[pixel] = self.fill_color.state
        neo.neo.write()
    
    def update(self):
        pass
    
    def gui(self):
        pass

    