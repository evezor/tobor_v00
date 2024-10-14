
'''
Calls from network channel or to self

'''
import struct, json, os


def add_sub(msg, iris):
    adr, pid, self_pid, bundle = struct.unpack('BHHs', msg)
    bundle = bundle.decode('utf8')
    header = iris.bus.header.pack(0, pid, adr)
    print('added sub')
    iris.subscribe(header, self_pid, bundle)

    
def narrowband(msg, iris):
    if msg == b'ping':
        iris.bus.ping()
    elif msg == b'savesubs':
        print('saving subs')
        with open('subscriptions.json', 'w') as f:
            json.dump(iris.s, f)
    elif msg == b'clrsubs':
        print('clearing subs')
        iris.clear_subs()
        if 'subscriptions.json' in os.listdir():
            os.remove('subscriptions.json')    

         
nwk = {
    100: add_sub,
    111: narrowband, # these functions to not require args
    # esp specific #500 level
    # zorg #700 level
}
