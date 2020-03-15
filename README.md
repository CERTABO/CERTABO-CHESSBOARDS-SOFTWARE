CERTABO CHESS BOARD SOFTWARE
This release include support for polyglot book, time + increment, endgame table base, it can run emulation of all vintage ROM chess computer from '80 and '90 and several other improvements.
For emulating the rom please download and unzip the mess emulator and add it and your roms to engines directory
more info for plyglot books https://python-chess.readthedocs.io/en/latest/polyglot.html
This version is the 3.3 Release and has been ported to Python3 and it is working cross platform on Windows, Unix any distro and Mac up to Mojave.
note: For Catalina users please refer to Mac-Catalina branch where the software has been adapted for it. Basically latest pygame release is not compatible with Catalina (for user want to run and compile on Catalina please  replace pip3 install --user pygame with the following  pip3 install --user pygame==2.0.0.dev6)

pip3 install --user pygame
pip3 install --user pystockfish
pip3 install --user pyserial
pip3 install --user python-chess
pip3 install --user appdirs
pip3 install --user requests
pip3 install --user win32com

python3 run.py
