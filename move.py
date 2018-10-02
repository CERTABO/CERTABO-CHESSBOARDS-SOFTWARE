from pystockfish import *
import cPickle as pickle
import os, time

params = {
        "Contempt Factor": 0,
        "Min Split Depth": 0,
        "Threads": 2,
        "Hash": 128,
        "MultiPV": 1,
        "Skill Level": 20,
        "Move Overhead": 30,
        "Minimum Thinking Time": 20, 
        "Slow Mover": 80
}  


#def get_move( q, move_history, difficulty ):
 #   global game, best_move
#    game = Engine(depth=difficulty, param=params)

#pickle.dump( favorite_color, open( "save.p", "wb" ) )
f = open( "move_history_tmp.p", "rb" )
move_history, difficulty = pickle.load( f )
f.close()

#game = Engine(depth=difficulty, param=params)
game = Engine(depth=difficulty)

game.setposition( move_history )
best_move = game.bestmove()
f = open( "bestmove.p", "wb" )
pickle.dump( best_move, f )
f.flush()
os.fsync(f)

f.close()
time.sleep(0.1)