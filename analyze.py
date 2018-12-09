import matplotlib.pyplot as plt
import numpy as np
import settings

SIM_TIME = settings.SIM_TIME
REPLICATE = settings.REPLICATE


for device in ['cpu', 'printer', 'disk', 'io_device']:
    logs = np.array([]).reshape((0, SIM_TIME, 5))
    for i in range(REPLICATE):
        raw_log = np.loadtxt('logs/' + device + str(i) + '.csv', delimiter='\t')
        raw_log = np.array([raw_log[raw_log[:, 2] == i][-1, :] for i in np.unique(raw_log[:, 2])])
        log = np.array([]).reshape((0, 5))
        for j in range(SIM_TIME):
            if np.where(raw_log[:, 2] == j)[0].shape[0] != 0:
                log = np.concatenate((log, raw_log[raw_log[:, 2] == j]))
            else:
                log = np.concatenate((log, [log[-1, :]]))
        logs = np.concatenate((logs, [log]))
    mean_log = np.mean(logs, axis=0)

    over_all_mean = np.mean(mean_log[:, 4])

    relative_change = np.array([0])
    for i in range(1, SIM_TIME, 1):
        xl = np.mean(mean_log[i:, 4])
        relative_change = np.concatenate((relative_change, [xl / over_all_mean - 1]))

    print("Mean queue length: %.2f" % over_all_mean)

    # plotting
    plt.figure(figsize=(15, 10))
    plt.subplot(2, 1, 1, title=device)
    plt.xlabel('Time')
    plt.ylabel('Queue length')
    plt.step(mean_log[:, 2], mean_log[:, 4], where='post')
    plt.subplot(2, 1, 2)
    plt.xlabel('Time')
    plt.ylabel('Relative change')
    plt.plot(log[:, 2], relative_change)
    plt.tight_layout()
    plt.title(device)
    plt.savefig('plots/' + device + '.png')
    plt.close()