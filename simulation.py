import simpy
import random
import numpy as np

INFINITE_TIME = 10000000


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

                ''' Pass the job to one of the other servers '''
                if other_servers is not None:
                    next_server_des = np.random.choice(other_servers, p=prob_dist_servers)
                    next_server_des.Jobs.append(Job(j.id, self.env.now))
                    if not next_server_des.server_sleeping.triggered:
                        next_server_des.server_sleeping.interrupt('Wake up, please.')

    def waiting(self):
        try:
            print('Server is idle at %d' % self.env.now)
            yield self.env.timeout(INFINITE_TIME)
        except simpy.Interrupt:
            print('A new job comes. Server waken up and works now at %d' % self.env.now)

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
                    % (self.nJobs, self.env.now, 1 if len(self.server.Jobs) > 0 else 0, len(self.server.Jobs)))
                self.nJobs += 1

                ''' if server is idle, wake it up'''
                if not self.server.server_sleeping.triggered:
                    self.server.server_sleeping.interrupt('Wake up, please.')
            else:
                ''' yield a infinite timeout beyond simulation time'''
                yield self.env.timeout(INFINITE_TIME)


# parameters
SIM_TIME = 2000
LAMBDA = 4
MU1 = 1/.04
MU2 = 1/.03
MU3 = 1/.06
MU4 = 1/.05
P12 = .5
P21 = 1
P31 = .6
P41 = 1
MAX_NJOBS = 10 * SIM_TIME * LAMBDA

# open the log files and write header
loggers = []
for device in ['cpu', 'printer', 'disk', 'io_device']:
    logger = open('logs/' + device + '.csv', 'w')
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

devices = [
    {
        'name': 'CPU',
        'process': CPU
    },
    {
        'name': 'PRINTER',
        'process': PRINTER
    },
    {
        'name': 'DISK',
        'process': DISK
    },
    {
        'name': 'IO_DEVICE',
        'process': IO_DEVICE
    },
]
# print simulation statistics
print('-------- Simulation performance -------------')
for device in devices:
    print(device['name'])
    print('Total waiting time     : %.2f' % device['process'].waitingTime)
    print('Average waiting time   : %.2f' % (device['process'].waitingTime / MyJobGenerator.nJobs))
    U = 1 - device['process'].idleTime/SIM_TIME
    print('Total server idle time : %.2f (U=%.2f)\n' % (device['process'].idleTime, U))
