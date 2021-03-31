from collections import deque
from threading import Thread
from time import sleep

import portalocker

"""
Process 1 receives the bits from standard input and send the bits through the covert channel to p2 using the lock on file_name.
"""

file_name = 'empty.txt'
buffer = deque()

"""
Get input from stardard input and store that in buffer.
"""
def get_input(buffer): # buffer reads bits across multiple sequences character by character indefinitely
    while True:
        msg = input()
        for char in msg:
            buffer.append(char)

"""
Send the bits in buffer through the covert channel to p2 using the lock on file_name.
buffer: input data
file_name: file that p1 and p2 both can acquire lock
zero_time: length holding the lock to signal a 0
one_time: length holding the lock to signal a 1
"""
def transmit(buffer, file_name, zero_time, one_time):
    while True:
        try:
            msg = buffer.popleft()
            opened = False
            while not opened:
                try:
                    with open(file_name, 'w+') as f:
                        opened = True
                        portalocker.lock(f, portalocker.LOCK_EX)
                        # normal work
                        f.write('innocuous info\n')
                        # send a 0
                        if msg == '0':
                            sleep(zero_time)
                        # send a 1
                        elif msg == '1':
                            sleep(one_time)
                        portalocker.unlock(f)
                    sleep(zero_time * 0.4) # leave some time so that p2 can access the file
                except:
                    pass
        except IndexError:  # buffer empty
            pass


zero_time = 2
one_time = 8

# start receiving input
input_thread = Thread(target=get_input, args=(buffer,))
input_thread.start()

# start transmitting
send_thread = Thread(target=transmit, args=(buffer, file_name, zero_time, one_time,))
send_thread.start()

input_thread.join()
send_thread.join()
