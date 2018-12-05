import matplotlib.pyplot as plt
import numpy as np

# plot log files
for device in ['cpu', 'printer', 'disk', 'io_device']:
    # plot queue length log
    log = np.loadtxt('logs/' + device + '.csv', delimiter='\t')
    log = np.array([log[log[:, 2] == i][-1, :] for i in np.unique(log[:, 2])])

    plt.figure(figsize=(20, 20))
    plt.subplot(2, 1, 1)
    plt.xlabel('Time')
    plt.ylabel('Queue length')
    plt.step(log[:, 2], log[:, 4], where='post')
    plt.subplot(2, 1, 2)
    plt.xlabel('Time')
    plt.ylabel('Server state')
    plt.yticks([0, 1], ['idle', 'busy'])
    plt.step(log[:, 2], log[:, 3], where='post')
    plt.tight_layout()
    plt.title(device)
    plt.savefig('plots/' + device + '.png')
    plt.close()