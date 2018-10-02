# README #

Raspberry Pi Chess project


### How do I get set up Stockfish at PI 3? ###

sudo apt-get install stockfish

sudo easy_install pystockfish

### How to compile files run.py and usb.py ###

cd chess

python


import py_compile

py_compile.compile('usb.py')

py_compile.compile('run.py')

quit()


### How to autolaunch the software ###
nano /home/pi/.config/lxsession/LXDE-pi/autostart

remove line by Ctrl+K:
@xscreensaver -no-splash

add line:
@sh /home/pi/chess/start_chess.sh






