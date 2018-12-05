from random import randint
import simpy

TALKS_PER_PERSON = 3
TALK_LENGTH = 30
BREAK_LENGTH = 15

def attendee(env, name, knowledge = 0, hunger = 0):
    while True:
        # visit talks
        for i in range(TALKS_PER_PERSON):
            knowledge += randint( 0, 3 )/(1 + hunger)
            hunger += randint( 1, 4 )

            yield env.timeout( TALK_LENGTH )

        print( 'Attendee %s finished talks with knowledge %.2f and hunger %.2f' % (name, knowledge, hunger))

        # go buffet
        food = randint( 3, 12 )
        hunger -= min( food, hunger )

        yield env.timeout( BREAK_LENGTH )

        print( 'Attendee %s finished eating with hunger %.2f' % (name, hunger))

env = simpy.Environment()
for i in range( 3 ):
    env.process( attendee(env, i ) )
env.run( until = 2200 )
