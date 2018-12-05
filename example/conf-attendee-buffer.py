from random import randint
import simpy

TALKS_PER_PERSON = 3
TALK_LENGTH = 30
BREAK_LENGTH = 15
DURATION_EAT = 3
BUFFET_SLOTS = 2

def attendee(env, name, buffet, knowledge = 0, hunger = 0):
    while True:
        # visit talks
        for i in range(TALKS_PER_PERSON):
            knowledge += randint( 0, 3 )/(1 + hunger)
            hunger += randint( 1, 4 )

            yield env.timeout( TALK_LENGTH )

        print( 'Attendee %s finished talks with knowledge %.2f and hunger %.2f' % (name, knowledge, hunger))

        # go buffet
        start = env.now
        with buffet.request() as req:
            yield req | env.timeout( BREAK_LENGTH - DURATION_EAT )
            time_left = BREAK_LENGTH - ( env.now - start )
            if req.triggered:
                food = min( randint( 3, 12 ), time_left ) # less time -> less food
                yield env.timeout( DURATION_EAT )
                hunger -= min( food, hunger )
                time_left -= DURATION_EAT
                print( 'Attendee %s finished eating with hunger %.2f' % (name, hunger))
            else:
                hunger += 1 # penalty for only taking a look at all the food
                print( 'Attendee %s didn\'t make it to the buffet, hunger is now '
                       'at %.2f.' % (name, hunger) )
            yield env.timeout( time_left )

env = simpy.Environment()
buffet = simpy.Resource( env, capacity = BUFFET_SLOTS )
for i in range( 3 ):
    env.process( attendee(env, i, buffet ) )
env.run( until = 220 )
