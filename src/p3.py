import random
import time

import portalocker

"""
Process 3 constantly tries to aquire the lock and holds it for a random period of time to confuse p2. 
file_name: the file that p1, p2 use to transmit data
zero_time: length p1 holding the lock to signal a 0
one_time: length p1 holding the lock to signal a 1
"""

file_name = 'empty.txt'

zero_time = 2
one_time = 8

while True:
    time.sleep(random.random() * 20 * zero_time) # it controls the frequency of interferences
    try:
        with open(file_name, 'w') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            time.sleep(random.random() * (zero_time + one_time))
            portalocker.unlock(f)
    except:
        pass
