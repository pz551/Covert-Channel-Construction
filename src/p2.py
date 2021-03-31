import time

import portalocker

"""
Process 2 receives data from p1 through the covert channel
file_name: file that p1 and p2 both can acquire lock
zero_time: length p1 holding the lock to signal a 0
one_time: length p1 holding the lock to signal a 1
"""

file_name = 'empty.txt'

zero_time = 2
one_time = 8

prev = time.time()
while True:
    time.sleep(zero_time * 0.1) 
    try: # try to acquire the lock
        with open(file_name, 'w+') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            gap = time.time() - prev
            # detects 0
            if zero_time * 0.4 < gap < (zero_time + one_time) / 2: # a small but non-trivial gap means p1 signaled 0, while a trival gap means p2 re-opens the file right after the previous deciperment
                print("p2 detects", 0)
            # detects 1
            elif one_time * 1.5 >= gap >= (zero_time + one_time) / 2: # a large but not overlarge gap means p1 signaled 1, while an overlarge gap means not
                print("p2 detects", 1)
            portalocker.unlock(f)
        time.sleep(zero_time * 0.4) # a trivial sleep time so that the file can be constantly held by p2
        prev = time.time() # to calculate the gap
    except:
        pass
