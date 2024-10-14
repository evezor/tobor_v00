# actual main script when running on an ESP32
import machine
machine.freq(240000000)
from iris import Iris
import os, gc, json
import uasyncio as asyncio


iris = Iris()

import config
def main():
    config.setup(iris)
    for k, v in iris.p.items():
        print(k, v)
    
    iris.boot(start_mailboxes=True)
    gc.collect()

    if 'subscriptions.json' in os.listdir():
        with open('subscriptions.json', 'r') as f:
            subs = json.load(f)
            for header, pid_struct in subs.items():
                iris.subscribe(int(header), pid_struct[0], pid_struct[1])

    loop = asyncio.get_event_loop()
    loop.create_task(iris.cob())
    gc.collect()
    loop.run_forever()

main()



