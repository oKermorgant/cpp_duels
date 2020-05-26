#!/usr/bin/env python3
import os
import sys
import yaml
import pygame

class dict_to_obj(object):
  def __init__(self, adict):
    self.__dict__.update(adict)

class Listener:
    def __init__(self):
        fifo_file = '/tmp/duels_example'
        if os.path.exists(fifo_file):
            os.remove(fifo_file)
            
        os.mkfifo(fifo_file)
        self.fifo = fifo_file
        
    def read(self, display = False):
        with open(self.fifo) as fifo:
            data = yaml.load(fifo.read())
            if display:
                print('(Python) Just read: {}'.format(data))
            return dict_to_obj(data)
        
if __name__ == '__main__':
    
    # main function
    
    listener = Listener()
    
    # init_msg has the same structure as C++ initMsg
    init_msg = listener.read(True)
    
    # init display / structure from init_msg
    
    
    
    winner = 0
    while winner == 0:
        # display_msg has the same structure as C++ displayMsg
        display_msg = listener.read(True)

        
        # update display from display_msg
        
        
        winner = display_msg.winner

    print('(Python) Player {} has won!'.format(winner))