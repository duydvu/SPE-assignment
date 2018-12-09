import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
import settings

INFINITE_TIME = settings.INFINITE_TIME
# parameters
SIM_TIME = settings.SIM_TIME
LAMBDA = settings.LAMBDA
MU1 = settings.MU1
MU2 = settings.MU2
MU3 = settings.MU3
MU4 = settings.MU4
P12 = settings.P12
P21 = settings.P21
P31 = settings.P31
P41 = settings.P41
REPLICATE = settings.REPLICATE
MAX_NJOBS = settings.MAX_NJOBS


class Job:
    def __init__(self, _id, arr_time):
        self.id = _id
        self.arr_time = arr_time

    def __str__(self):
        return 'Job %d at %d' % (self.id, self.arr_time)


def sjf(job):
    return job.duration


class Server:
    """ A server
     - env: SimPy environment
     - strategy:    - FIFO: First In First Out
                    - SJF : Shortest Job First
    """
    def __init__(self, _env, mu=1.0, logger=None, strategy='FIFO'):
        self.env = _env
        self.mu = mu
        self.logger = logger
        self.strategy = strategy
        self.Jobs = list(())
        self.server_sleeping = None
        ''' statistics '''
        self.waitingTime = 0
        self.responseTime = 0
        self.idleTime = 0
        ''' register a new server process '''

    def serve(self, other_servers=None, prob_dist_servers=None):
        while True:
            ''' do nothing, just change server to idle
              and then yield a wait event which takes infinite time
            '''
            if len(self.Jobs) == 0:
                self.server_sleeping = self.env.process(self.waiting())
                t1 = self.env.now
                yield self.server_sleeping
                ''' accumulate the server idle time'''
                self.idleTime += self.env.now - t1
            else:
                ''' get the first job to be served'''
                if self.strategy == 'SJF':
                    self.Jobs.sort(key=sjf)
                j = self.Jobs.pop(0)

                self.log('%d\t0\t%d\t%d\t%d\n'
                         % (j.id, self.env.now, 1 if len(self.Jobs) > 0 else 0, len(self.Jobs)))

                ''' sum up the waiting time'''
                self.waitingTime += self.env.now - j.arr_time
                ''' yield an event for the job finish'''
                yield self.env.timeout(random.expovariate(self.mu))
                ''' sum up the response time'''
                self.responseTime += self.env.now - j.arr_time

                ''' Pass the job to one of the other servers '''
                if other_servers is not None:
                    next_server_des = np.random.choice(other_servers, p=prob_dist_servers)
                    next_server_des.Jobs.append(Job(j.id, self.env.now))
                    next_server_des.log('%d\t1\t%d\t%d\t%d\n'
                                        % (j.id, self.env.now, 1 if len(next_server_des.Jobs) > 0 else 0,
                                        len(next_server_des.Jobs)))
                    if not next_server_des.server_sleeping.triggered:
                        next_server_des.server_sleeping.interrupt('Wake up, please.')

    def waiting(self):
        try:
            # print('Server is idle at %d' % self.env.now)
            yield self.env.timeout(INFINITE_TIME)
        except simpy.Interrupt:
            # print('A new job comes. Server waken up and works now at %d' % self.env.now)
            pass

    def log(self, message):
        if self.logger is not None:
            self.logger.write(message)


class JobGenerator:
    def __init__(self, _env, server, max_jobs=2000, lam=.1):
        self.env = _env
        self.server = server
        self.maxNJobs = max_jobs
        self.nJobs = 0
        self.lam = lam
        env.process(self.generate_jobs())

    def generate_jobs(self):
        while True:
            '''yield an event for new job arrival'''
            job_interarrival = random.expovariate(self.lam)
            yield self.env.timeout(job_interarrival)

            ''' generate service time and add job to the list'''
            if self.nJobs < self.maxNJobs:
                self.server.Jobs.append(Job(self.nJobs, self.env.now))
                print('job %d: t = %d' % (self.nJobs, self.env.now))
                self.server.log('%d\t1\t%d\t%d\t%d\n'
                                % (self.nJobs, self.env.now, 1 if len(self.server.Jobs) > 0 else 0,
                                   len(self.server.Jobs)))
                self.nJobs += 1

                ''' if server is idle, wake it up'''
                if not self.server.server_sleeping.triggered:
                    self.server.server_sleeping.interrupt('Wake up, please.')
            else:
                ''' yield a infinite timeout beyond simulation time'''
                yield self.env.timeout(INFINITE_TIME)



cpu_stats = []
printer_stats = []
disk_stats = []
io_device_stats = []
# lams = np.linspace(1, 7, 25)
for i in range(REPLICATE):
    # open the log files and write header
    loggers = []
    for device in ['cpu', 'printer', 'disk', 'io_device']:
        logger = open('logs/' + device + str(i) + '.csv', 'w')
        logger.write('-1\t0\t0\t0\t0\n')
        loggers.append(logger)

    # create a simulation environment
    env = simpy.Environment()

    # create servers
    SINK = Server(env)   # Dummy server used as a sink
    CPU = Server(env, MU1, loggers[0])
    PRINTER = Server(env, MU2, loggers[1])
    DISK = Server(env, MU3, loggers[2])
    IO_DEVICE = Server(env, MU4, loggers[3])

    # process the servers
    env.process(SINK.serve())
    env.process(CPU.serve([PRINTER, DISK], [P12, 1 - P12]))
    env.process(PRINTER.serve([CPU], [P21]))
    env.process(DISK.serve([CPU, SINK], [P31, 1 - P31]))
    env.process(IO_DEVICE.serve([CPU], [1]))

    MyJobGenerator = JobGenerator(env, IO_DEVICE, MAX_NJOBS, LAMBDA)

    # start the simulation
    random.seed(2018)
    env.run(until=SIM_TIME)


    # close the log file
    for logger in loggers:
        logger.close()

    # cpu_stats.append(CPU.responseTime / MyJobGenerator.nJobs)
    # printer_stats.append(PRINTER.responseTime / MyJobGenerator.nJobs)
    # disk_stats.append(DISK.responseTime / MyJobGenerator.nJobs)
    # io_device_stats.append(IO_DEVICE.responseTime / MyJobGenerator.nJobs)

    cpu_stats.append({
        'waitingTime': CPU.waitingTime,
        'responseTime': CPU.responseTime,
        'idleTime': CPU.idleTime,
    })
    printer_stats.append({
        'waitingTime': PRINTER.waitingTime,
        'responseTime': PRINTER.responseTime,
        'idleTime': PRINTER.idleTime,
    })
    disk_stats.append({
        'waitingTime': DISK.waitingTime,
        'responseTime': DISK.responseTime,
        'idleTime': DISK.idleTime,
    })
    io_device_stats.append({
        'waitingTime': IO_DEVICE.waitingTime,
        'responseTime': IO_DEVICE.responseTime,
        'idleTime': IO_DEVICE.idleTime,
    })

# plt.figure(figsize=(7, 5))
# plt.xlabel('Lambda')
# plt.ylabel('Response Time')
# plt.plot(lams, cpu_stats)
# plt.plot(lams, printer_stats)
# plt.plot(lams, disk_stats)
# plt.plot(lams, io_device_stats)
# plt.tight_layout()
# plt.legend(['CPU', 'Printer', 'Disk', 'I/O Device'], loc='upper left')
# plt.savefig('plots/1.png')
# plt.close()

devices = [
    {
        'name': 'CPU',
        'stats': {
            'waitingTime': np.mean([stats['waitingTime'] for stats in cpu_stats]),
            'responseTime': np.mean([stats['responseTime'] for stats in cpu_stats]),
            'idleTime': np.mean([stats['idleTime'] for stats in cpu_stats]),
        }
    },
    {
        'name': 'PRINTER',
        'stats': {
            'waitingTime': np.mean([stats['waitingTime'] for stats in printer_stats]),
            'responseTime': np.mean([stats['responseTime'] for stats in printer_stats]),
            'idleTime': np.mean([stats['idleTime'] for stats in printer_stats]),
        }
    },
    {
        'name': 'DISK',
        'stats': {
            'waitingTime': np.mean([stats['waitingTime'] for stats in disk_stats]),
            'responseTime': np.mean([stats['responseTime'] for stats in disk_stats]),
            'idleTime': np.mean([stats['idleTime'] for stats in disk_stats]),
        }
    },
    {
        'name': 'IO_DEVICE',
        'stats': {
            'waitingTime': np.mean([stats['waitingTime'] for stats in io_device_stats]),
            'responseTime': np.mean([stats['responseTime'] for stats in io_device_stats]),
            'idleTime': np.mean([stats['idleTime'] for stats in io_device_stats]),
        }
    },
]
# print simulation statistics
print('-------- Simulation performance -------------')
for device in devices:
    print(device['name'] + ':')
    print('Total waiting time     : %.2f' % device['stats']['waitingTime'])
    print('Average waiting time   : %.2f' % (device['stats']['waitingTime'] / MyJobGenerator.nJobs))
    print('Total response time    : %.2f' % device['stats']['responseTime'])
    print('Average response time  : %.2f' % (device['stats']['responseTime'] / MyJobGenerator.nJobs))
    U = 1 - device['stats']['idleTime'] / SIM_TIME
    print('Total server idle time : %.2f (U=%.2f)\n' % (device['stats']['idleTime'], U))

over_all_waiting_time = np.sum([device['stats']['waitingTime'] for device in devices])
over_all_response_time = np.sum([device['stats']['responseTime'] for device in devices])
over_all_idle_time = np.sum([device['stats']['responseTime'] for device in devices])
print('Overall System:')
print('Total waiting time     : %.2f' % over_all_waiting_time)
print('Average waiting time   : %.2f' % (over_all_waiting_time / MyJobGenerator.nJobs))
print('Total response time    : %.2f' % over_all_response_time)
print('Average response time  : %.2f' % (over_all_response_time / MyJobGenerator.nJobs))
U = over_all_waiting_time / over_all_response_time
print('Total server idle time : %.2f (U=%.2f)\n' % (over_all_idle_time, U))