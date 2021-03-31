import collections
import multiprocessing
import random
import time

import matplotlib.pyplot as plt
import numpy as np
import portalocker

"""
Process 1 send the bits in buffer through the covert channel to p2 using the lock on file_name.
buffer: input data
file_name: file that p1 and p2 both can acquire lock
zero_time: length holding the lock to signal a 0
one_time: length holding the lock to signal a 1
out_buffer: buffer to write the bandwidth
"""
def process1_function(buffer, file_name, zero_time, one_time, out_buffer):
    start = time.time()
    for elem in buffer:
        try:
            with open(file_name, "w") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                # send 0
                if elem == "0":
                    time.sleep(zero_time)
                # send 1
                else:
                    time.sleep(one_time)
                portalocker.unlock(f)
            time.sleep(zero_time * 0.4)
        except:
            pass

    # hold the lock for a long period of time to indicating the end of signaling
    with open(file_name, "w") as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        time.sleep(1.5 * one_time)
        portalocker.unlock(f)

    # compute the bandwidth
    bandwidth = len(buffer) / (time.time() - start)
    out_buffer.append(bandwidth)


"""
Process 2 receives data from p1 through the covert channel
buffer: input data (to compute fidelity rate)
file_name: file that p1 and p2 both can acquire lock
zero_time: length p1 holding the lock to signal a 0
one_time: length p1 holding the lock to signal a 1
out_buffer: buffer to write the fidelity rate
"""
def process2_function(buffer, file_name, zero_time, one_time, out_buffer):
    prev = time.time()
    messages = []
    self_open = 0
    while True:
        time.sleep(zero_time * 0.1)
        try:
            with open(file_name, "w") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                gap = time.time() - prev
                # detects a 0
                if zero_time * 0.4 < gap < (zero_time + one_time) / 2:
                    self_open = 0
                    messages.append("0")
                # detects a 1
                elif one_time * 1.5 >= gap >= (zero_time + one_time) / 2:
                    self_open = 0
                    messages.append("1")
                # test whether transmission from p1 has ended
                elif one_time * 1.5 < gap:
                    self_open = 0
                    portalocker.unlock(f)
                    break
                # for testing: when p2 continously acquires the lock for 20 times (means p1 is no longer sending message)
                # it breaks the loop 
                else:
                    self_open += 1
                    if self_open > 20:
                        self_open = 0
                        break
                portalocker.unlock(f)
            time.sleep(zero_time * 0.4)
            prev = time.time()
        except:
            pass

    print(f'zero = {zero_time}, one = {one_time}')
    correct, total = 0, 0
    # compute the fidelity rate
    for i in range(len(messages)):
        if i < len(buffer):
            if messages[i] == buffer[i]:
                correct += 1
            total += 1
    fidelity_rate = correct / max(total, len(buffer))
    print("fidelity :", fidelity_rate)
    out_buffer.append(fidelity_rate)


"""
Process 3 constantly tries to aquire the lock and holds it for a random period of time to confuse p2. 
file_name: the file that p1, p2 use to transmit data
zero_time: length p1 holding the lock to signal a 0
one_time: length p1 holding the lock to signal a 1
"""
def process3_function(file_name, zero_time, one_time):
    start = time.time()
    while time.time() - start < 150 * zero_time: 
        try:
            with open(file_name, 'w') as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                time.sleep(random.random() * (zero_time + one_time))
                portalocker.unlock(f)
        except:
            pass
        time.sleep(random.random() * 20 * zero_time)


if __name__ == '__main__':
    #  test fidelity rate vs bandwdith without p3
    zero_ones = [(0.001, 0.002), (0.002, 0.004), (0.003, 0.006), (0.004, 0.008), (0.005, 0.01), (0.006, 0.012), (0.007, 0.014), (0.008, 0.016), (0.009, 0.018), (0.01, 0.02), (0.02, 0.04), (0.03, 0.06), (0.04, 0.08), (0.05, 0.1), (0.1, 0.2), (0.15, 0.3), (0.2, 0.4), (0.25, 0.5)]
    random_data = []
    manager = multiprocessing.Manager()
    without_p3_bandwidth_means = []
    without_p3_fidelity_rate_stds = []
    without_p3_fidelity_rate_means = []
    for zero, one in zero_ones:
        bandwidth_buffer = manager.list()
        fidelity_buffer = manager.list()
        current_random_data = []
        for i in range(50):
            buffer = np.random.choice(["0", "1"], 20)
            p1 = multiprocessing.Process(target=process1_function, args=(buffer, "empty.txt", zero, one, bandwidth_buffer))
            p2 = multiprocessing.Process(target=process2_function, args=(buffer, "empty.txt", zero, one, fidelity_buffer))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
            current_random_data.append(buffer)
        fidelity_rate_mean = np.mean(list(fidelity_buffer))
        fidelity_rate_std = np.std(list(fidelity_buffer))
        without_p3_fidelity_rate_means.append(fidelity_rate_mean)
        without_p3_fidelity_rate_stds.append(fidelity_rate_std)
        bandwidth_mean = np.mean(list(bandwidth_buffer))
        without_p3_bandwidth_means.append(bandwidth_mean)
        random_data.append(current_random_data)
    zipped = sorted(list(zip(without_p3_bandwidth_means, without_p3_fidelity_rate_means, without_p3_fidelity_rate_stds)))
    without_p3_bandwidth_means = list(map(lambda x: x[0], zipped))
    without_p3_fidelity_rate_means = list(map(lambda x: x[1], zipped))
    without_p3_fidelity_rate_stds = list(map(lambda x: x[2], zipped))
    
    # draw the plots
    plt.title("Fidelity Rate vs Bandwidth")
    plt.xlabel("Bandwidth")
    plt.ylabel("Fidelity Rate")
    plt.errorbar(without_p3_bandwidth_means, without_p3_fidelity_rate_means, yerr=without_p3_fidelity_rate_stds,ecolor='r',color='g',elinewidth=2,capsize=4, label="without p3")
    plt.legend(loc='upper right')
    plt.savefig("without-p3.png")
    plt.clf()

    #  test fidelity rate vs bandwdith with p3
    with_p3_bandwidth_means = []
    with_p3_fidelity_rate_stds = []
    with_p3_fidelity_rate_means = []
    for i in range(len(zero_ones)):
        zero, one = zero_ones[i]
        same_bandwidth_data = random_data[i]
        bandwidth_buffer = manager.list()
        fidelity_buffer = manager.list()
        for j in range(50):
            buffer = same_bandwidth_data[j]
            p1 = multiprocessing.Process(target=process1_function, args=(buffer, "empty.txt", zero, one, bandwidth_buffer))
            p2 = multiprocessing.Process(target=process2_function, args=(buffer, "empty.txt", zero, one, fidelity_buffer))
            p3 = multiprocessing.Process(target=process3_function, args=("empty.txt", zero, one))

            p1.start()
            p2.start()
            p3.start()
            p1.join()
            p2.join()
            p3.join()
        fidelity_rate_mean = np.mean(list(fidelity_buffer))
        fidelity_rate_std = np.std(list(fidelity_buffer))
        with_p3_fidelity_rate_means.append(fidelity_rate_mean)
        with_p3_fidelity_rate_stds.append(fidelity_rate_std)
        bandwidth_mean = np.mean(list(bandwidth_buffer))
        with_p3_bandwidth_means.append(bandwidth_mean)
    zipped = sorted(list(zip(with_p3_bandwidth_means, with_p3_fidelity_rate_means, with_p3_fidelity_rate_stds)))
    with_p3_bandwidth_means = list(map(lambda x: x[0], zipped))
    with_p3_fidelity_rate_means = list(map(lambda x: x[1], zipped))
    with_p3_fidelity_rate_stds = list(map(lambda x: x[2], zipped))
    plt.title("Fidelity Rate vs Bandwidth with and without p3")
    plt.xlabel("Bandwidth")
    plt.ylabel("Fidelity Rate")
    plt.errorbar(with_p3_bandwidth_means, with_p3_fidelity_rate_means, yerr=with_p3_fidelity_rate_stds,ecolor='b',color='y',elinewidth=2,capsize=4, label="with p3")
    plt.errorbar(without_p3_bandwidth_means, without_p3_fidelity_rate_means, yerr=without_p3_fidelity_rate_stds,ecolor='r',color='g',elinewidth=2,capsize=4, label="without p3")
    plt.legend(loc='upper right')
    plt.savefig("with-p3.png")
