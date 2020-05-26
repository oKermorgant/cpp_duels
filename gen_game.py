#!/usr/bin/env python
import sys
import yaml
import os

class Info:
    def __init__(self, key):
        self.type, key = key.split()[:2]
        self.name = key.split('[')[0]
        self.dim = 0
        self.arr = ''
        if '[' in key:
            self.arr = key[key.index('['):]
            self.dim = int(key[key.index('[')+1:key.index(']')])
    def fifo(self, nl):
        ret = 'fifo << "{}{}: "'.format(nl and '\\n' or '', self.name)
        if not self.dim:
            ret += ' << {};'.format(self.name)
        else:
            loop = ''' << "[";
    for(size_t i=0; i < {}; ++i)
      fifo << {}[i] << (i == {}?"]":", ");'''
            ret += loop.format(self.dim, self.name, self.dim-1)
        return ret
            
def build_sendToGUI(detail, refresh, more = []):
    ret = '''  void sendToGUI({}) const
  {{
    std::ofstream fifo;
    fifo.open(fifo_name, std::ios::out);
    '''.format(', '.join(more), refresh)
    for i,key in enumerate([Info(key) for key in more] + detail):
        if i:
            ret += '\n    '
        ret += key.fifo(i)
    return ret + '''
    fifo << std::endl;
    fifo.close();
    timer.sleep();
    }\n'''
            
def msg_struct(field, content):
    
    name = field + 'Msg'
    refresh = content['refresh']
    keys = [key.replace('(','[').replace(')',']') for key in content[field]]
    l = len(keys)
    detail = [Info(key) for key in keys]
    ret = 'struct {}\n{{\n'.format(name)
    if len(keys):
        ret += '  {};\n'.format('; '.join(keys))
    if field == 'display':
        ret += build_sendToGUI(detail, refresh, ['int winner = 0'])
    if field == 'init':
        ret += build_sendToGUI(detail, refresh, ['std::string p1', 'std::string p2'])
        
    elif field == 'feedback':
        ret += '  {}() {{}}\n'.format(name)
        ret += '  {}({})\n'.format(name, ', '.join(['{} _{}{}'.format(key.type, key.name, key.arr) for key in detail]))
        ret += '    : {} {{}}\n'.format(', '.join(['{key}(_{key})'.format(key=key.name) for key in detail if key.dim == 0]))
    return ret + '};\n'

if __name__ == '__main__':
    path = os.path.abspath(os.path.dirname(__file__)) + '/'
        
    game_path = len(sys.argv) == 2 and sys.argv[1] or '.'
    game_path = os.path.abspath(game_path) + '/'

    for msg in os.listdir(game_path):
        if msg.endswith('.yaml'):
            config = game_path + msg
            game = msg.split('.')[0].lower()
            break
    include_path = game_path + 'include/' + game
        
    # create directories
    for d in (game_path + 'include', include_path, game_path + 'src'):
        if not os.path.exists(d):
            os.mkdir(d)
            
    # generate message header
    with open(config) as f:
        content = yaml.safe_load(f)
    if 'refresh' not in content:
        content['refresh'] = 50;
    header = ['''#ifndef {GAME}_MSG_H
#define {GAME}_MSG_H
#include <fstream>
#include <thread>
#include <sys/stat.h>
namespace {game} {{
namespace {{
static constexpr const char * fifo_name = "/tmp/duels_{game}";
struct Timer
{{
  std::chrono::steady_clock::time_point last;
  const std::chrono::milliseconds ms;
  inline Timer() : last(std::chrono::steady_clock::now()), ms({refresh}) {{}}
  inline void sleep()
  {{
    std::this_thread::sleep_until(last + ms);
    last = std::chrono::steady_clock::now();
  }}
}};
Timer timer;
}}
inline void runGUI()
{{
  remove(fifo_name);
  system("python3 ../{game}_gui.py&");
  struct stat buffer;
  while(stat(fifo_name, &buffer))
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
}}'''.format(GAME = game.upper(), game = game, refresh = content['refresh'])]

    for field in ('init', 'input', 'feedback', 'display'):
        header.append(msg_struct(field, content))
    header.append('}\n#endif')
    with open(include_path + '/msg.h', 'w') as f:
        f.write('\n'.join(header))
        
    cmake_template = '''cmake_minimum_required(VERSION 2.8.3)
project({game} CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_BUILD_TYPE Debug)

include_directories(include)

add_executable({game} main.cpp src/{game}_game.cpp)
'''
    main_template = '''#include <{game}/msg.h>
#include <iostream>

using namespace {game};

int main(int argc, char** argv)
{{
  // can be commented if you run the python GUI on your own during testing
  runGUI();

  feedbackMsg fb1_msg, fb2_msg;
  initMsg init_msg;
  inputMsg input;
  displayMsg display;

  // prepare init message
  
  
  init_msg.sendToGUI("player 1", "player 2");
  
  
  // prepare first display message
  
  
  
  display.sendToGUI();

  int winner(0);
  while(winner == 0)
  {{
    // update game state including winner variable if any




    // update display
    
    
    display.sendToGUI(winner);
    if(winner)
      break;
  }}
  std::cout << "Player " << winner << " has won!\\n";
}}'''
  
    game_template = '''#include <{game}/{game}_game.h>

namespace {game} {{

{Game}Game::{Game}Game()
{{
  // can be commented if you run the python GUI on your own during testing
  runGUI();

  // prepare init message
  initMsg init_msg;

  init_msg.sendToGUI("player 1", "player 2");


  // prepare first display message
  // display.field = ...


  display.sendToGUI();
}}

feedbackMsg {Game}Game::getFeedback()
{{
  // whatever data we need to communicate to the player
  feedbackMsg msg;



  return msg;
}}

void {Game}Game::play(inputMsg msg)
{{
  // update game state according to player input



  // let the AI play
  playAI();

  // update display communicate to GUI

  display.sendToGUI(winner_);
}}

void {Game}Game::playAI()
{{



}}
}}
'''

    game_header_template = '''#ifndef {GAME}GAME_H
#define {GAME}GAME_H

#include <{game}/msg.h>

namespace {game} {{

class {Game}Game
{{
public:
  // initialize the game and send to GUI
  {Game}Game();

  feedbackMsg getFeedback();

  void play(inputMsg msg);

  bool over() const
  {{
    return winner_ != 0;
  }}

  int winner() const
  {{
    return winner_;
  }}

private:

  void playAI();


  displayMsg display;
  int winner_ = 0;





}};
}}
#endif // {GAME}GAME_H'''
  
    gui_template = '''#!/usr/bin/env python3
import os
import sys
import yaml
import pygame

class dict_to_obj(object):
  def __init__(self, adict):
    self.__dict__.update(adict)

class Listener:
    def __init__(self):
        self.fifo = '/tmp/duels_{game}'
        if os.path.exists(self.fifo):
            os.remove(self.fifo)
            
        os.mkfifo(self.fifo)
        
    def read(self, display = False):
        with open(self.fifo) as fifo:
            data = yaml.load(fifo.read())
            if display:
                print('(Python) Just read: {{}}'.format(data))
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

    print('(Python) Player {{}} has won!'.format(winner))'''
    
    created = []
    created.append((game + '_gui.py', gui_template))
    created.append(('CMakeLists.txt', cmake_template))
    created.append(('main.cpp', main_template))
    created.append(('src/{}_game.cpp'.format(game), game_template))
    created.append(('include/{game}/{game}_game.h'.format(game=game), game_header_template))
    
    for name, cont in created:
        dest = game_path + '/' + name
        if os.path.exists(dest):
            print('File {} exists, skipping'.format(dest))
        #else:
        with open(dest, 'w') as f:
            f.write(cont.format(game=game,Game=game.title(),GAME=game.upper()))
