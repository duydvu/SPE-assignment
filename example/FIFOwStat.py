import simpy
import numpy as np

class Job:
    def __init__(self, name, arrtime, duration):
        self.name = name
        self.arrtime = arrtime
        self.duration = duration

class Server:
    def __init__(self, env):
        self.Jobs = list(())
        self.serversleeping = None
        ''' statistics '''
        self.waitingTime = 0
        self.idleTime = 0
        ''' register a new server process '''
        env.process( self.serve(env) )

    def serve(self, env):
        while True:
            ''' do nothing, just change server to idle
              and then yield a wait event which takes infinite time
            '''
            if len( self.Jobs ) == 0 :
                self.serversleeping = env.process( self.waiting( env ))
                t1 = env.now
                yield self.serversleeping
                ''' accumulate the server idle time'''
                self.idleTime += env.now - t1
            else:
                ''' get the first job to be served'''
                j = self.Jobs.pop( 0 )
                ''' sum up the waiting time'''
                self.waitingTime += env.now - j.arrtime
                ''' yield an event for the job finish'''
                yield env.timeout( j.duration )

    def waiting(self, env):
        try:
            print( 'Server is idle at %d' % env.now )
            yield env.timeout(1000)
        except simpy.Interrupt as i:
            print('A new job comes. Server waken up and works now at %d' % env.now )

class JobGenerator:
    def __init__(self, env, server, nrjobs = 20):
        self.server = server
        self.nrjobs = nrjobs
        env.process( self.generatejobs(env) )

    def generatejobs(self, env):
        i = 1
        while True:
            '''yield an event for new job arrival'''
            job_interarrival = np.random.randint(1,5)
            yield env.timeout( job_interarrival )

            ''' generate service time and add job to the list'''
            job_duration = np.random.randint(2,5)
            self.server.Jobs.append( Job('Job %s' %i, env.now, job_duration) )
            print( 'job %d: t = %d, l = %d' %( i, env.now, job_duration ) )
            i += 1

            ''' if server is idle, wake it up'''
            if not self.server.serversleeping.triggered:
                self.server.serversleeping.interrupt( 'Wake up, please.' )

env = simpy.Environment()
MyServer = Server( env )
MyJobGenerator = JobGenerator( env, MyServer )
env.run( until = 50 )
print( 'Total waiting time     : %.2f' % MyServer.waitingTime )
print( 'Mean waiting time      : %.2f' % (MyServer.waitingTime/MyJobGenerator.nrjobs) )
print( 'Total server idle time : %.2f' % MyServer.idleTime )
