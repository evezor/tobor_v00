from Parameter import Parameter
from floe import make_var
import math, json
# from pprint import pprint
CartesianPosition = dict # this is a dict of a position
ScaraPosition = dict

class ScaraKinematics(Parameter):
    modals = ['move.linear', 'move.rapid']
    
    def __init__(self, theta_length:float, phi_length:float, max_segment_size: float, right_handed: bool, **k):
        super().__init__(**k)
        self.theta_len = theta_length
        self.phi_len = phi_length
        
        self.theta_2 = theta_length**2
        self.phi_2 = phi_length**2
        
        self.feed = 500
        self.right_handed = make_var(right_handed)
        
        
        self.work_offset = dict(x=0, y=0, z=0, a=0, b=0, c=0, rot=0)
        # self.work_offset.update(work_offset)
        # work_offset['rot'] = math.radians(work_offset['rot'])
        print(self.work_offset)

        self.max_seg = max_segment_size

        self.prev_scara: ScaraPosition = None
        self.prev_cart: CartesianPosition = dict(x=145, y=-250, z=0, a=0, b=0, c=0) 
    
    def gen(self, iterable):
        for line in iterable:
            if line:
                yield json.loads(line)
    
    def __call__(self, state):
        self.state = []
        g = self.gen(state.split('\n'))         
        for line in g:
            if line['cmd'] in self.modals:
                if 'x' in line or 'y' in line:
                    if line['cmd'] == 'move.linear':
                        line.pop('cmd')
                        for seg in self.segmentize(line):
                            self.state.append(seg)
                    else:  # line['cmd'] == 'move.rapid'
                        cart = line.copy()
                        cart.pop('cmd')
                        self.prev_cart.update(cart)
                        scara = self.ik(cart)
                        new_scara = {'cmd': 'move.rapid'}
                        new_scara.update(scara)
                        self.state.append(new_scara)
                        self.prev_scara = scara
                else:
                    self.state.append(line)
            else:
                self.state.append(line)
        
        
        self.state = '\n'.join(self.round(line) for line in self.state)
        self.send()
    
    @staticmethod 
    def round(line):
        for k, v in line.items():
            if isinstance(v, float):
                line[k] = round(v, 3)
        return json.dumps(line)
        
    def segmentize(self, end: CartesianPosition):
        """ 
        """
        if 'feed' in end:
            self.feed = end.pop('feed')
        if not self.prev_cart:
            # we are starting fresh and have no previous position
            # TODO: we must calculate this position manually
            start = dict(x=145, y=-257, z=0, a=0, b=0, c=0) 
            
        else:
            start = self.prev_cart
        
        # calculate the length of this line
        line_len = self.calc_dist(start, end)

        
        
        if line_len < self.max_seg:
            new_scara = {'cmd': 'move.linear'}
            cart = end.copy()
            scara = self.ik(cart)
            new_scara.update(scara)
            if self.prev_scara:
                try:
                    new_scara['feed'] = int(self.calc_dist(self.prev_scara, scara)/line_len * self.feed)   # feed is now a ratio of cart_dist/scara_dist
                except ZeroDivisionError:
                        new_scara['feed'] = 500    
            else:
                new_scara['feed'] = 500
            
            yield new_scara
            # print(new_scara)
            self.prev_scara = scara
            
            
        
        else:
            num_segs = int(math.ceil(line_len / self.max_seg))
            seg_len = line_len/num_segs
            for i in range(1, num_segs):
                new_scara = {'cmd': 'move.linear'}
                # interpolate
                cart = {axis: (i*end[axis]+(num_segs-i)*start[axis])/num_segs for axis in end.keys()}
                scara = self.ik(cart)
                new_scara.update(scara)
                if self.prev_scara:
                    try:
                        new_scara['feed'] = int(self.calc_dist(self.prev_scara, scara)/seg_len * self.feed) # feed is now a ratio of cart_dist/scara_dist
                    except ZeroDivisionError:
                        new_scara['feed'] = 500    
                else:
                    new_scara['feed'] = 500
                
                # print(new_scara) 
                self.prev_scara = scara
                yield new_scara
            
            new_scara = {'cmd': 'move.linear'}
            cart = end.copy()
            scara = self.ik(cart)
            new_scara.update(scara)
            new_scara['feed'] = self.calc_dist(self.prev_scara, scara)/seg_len * self.feed # feed is now a ratio of cart_dist/scara_dist
            self.prev_scara = scara
            
            yield new_scara
        
        self.prev_cart = end
        end['cmd'] = 'feed.linear'
    
    @staticmethod
    def calc_dist(start: dict, end: dict):
        if 'z' in end:
            return math.sqrt((end['x'] - start['x'])**2 + (end['y'] - start['y'])**2 + (end['z'] - start['z'])**2)
        return math.sqrt((end['x'] - start['x'])**2 + (end['y'] - start['y'])**2)
        
    def translate(self, pos: CartesianPosition):
        # rotate
        # print(f'f{pos = }')
        hyp = math.hypot(pos['x'], pos['y'])
        hyp_angle = math.atan2(pos['y'], pos['x'])
        new_hyp_angle = hyp_angle + self.work_offset['rot']
        
        pos['x'] = math.cos(new_hyp_angle) * hyp
        pos['y'] = math.sin(new_hyp_angle) * hyp

        # translate
        for axis, position in pos.items():
            pos[axis] = position + self.work_offset[axis]
            # print(f'{pos = }')
        return pos
    
    def fk(self, theta_deg, phi_deg, a_deg=None):
        theta = math.radians(theta_deg)
        phi = math.radians(phi_deg)
        c2 = (self.theta_2 + self.phi_2) - (2 * self.theta_len * self.phi_len * math.cos(math.pi-phi))
        c = math.sqrt(c2)
        B = math.acos((c2 + self.theta_2 - self.phi_2)/(2*c*self.theta_len))

        new_theta = theta + B
        # we implicitly to the coordinate tranform here
        y = -math.cos(new_theta)*c
        x = math.sin(new_theta)*c
        return x, y
    
    def ik(self, point: CartesianPosition) -> ScaraPosition:
        """ I like for 0,0 to be the arm facing straight down (-90 deg) for (theta:0, phi:0)

        Args:
            point (CartesianPosition): _description_
            right_handed (bool, optional): _description_. Defaults to True.

        Returns:
            ScaraPosition: _description_
        """
        # do the 0,0 translation
        x = -point['y']
        y = point['x']
        
        R = (x**2 + y**2) ** .5  # math.hypot(x, y)
        gamma = math.atan2(y, x)
        beta = math.acos((R**2 - self.theta_2 - self.phi_2) / (-2 * self.theta_len * self.phi_len)) 
        psi = math.pi - beta
        alpha = math.asin((self.phi_len * math.sin(psi)) / R)
        
        
        
        if self.right_handed.state:
            _x = math.degrees(gamma - alpha)
            point['x'] = _x if _x < 180 else _x - 180
            point['y'] = math.degrees(psi)
        else:
            _x =  math.degrees(gamma + alpha)
            point['x'] = _x if _x < 270 else _x - 270
            point['y'] = math.degrees(beta - math.pi)
    
        return point    


        
    