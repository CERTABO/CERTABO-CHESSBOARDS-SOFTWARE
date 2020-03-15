CERTABO CHESS BOARD SOFTWARE
This release includes support for polyglot book, time + increment, endgame table base, it can run emulation of all vintage ROM chess computer from '80 and '90 (the emulator require messchess and it's currently available for Windows) and several other improvements.
For emulating the rom please download and unzip the mess emulator and add it and your roms to engines directory more info for polyglot books https://python-chess.readthedocs.io/en/latest/polyglot.html
This version is the 3.3 Release and requires Python2 it is working cross platform on Windows, Unix any distro and Mac up to Mojave.
note: For Catalina users please refer to Mac-Catalina branch where the software has been adapted for it but it require Python3. 
The Python2 version will be not any longer supported please switch to Python3, in other branches you can find latest releases already ported to Python3 which will be the only one supported in the next releases

pip2 install --user pygame
pip2 install --user pystockfish
pip2 install --user pyserial
pip2 install --user python-chess==0.23.11
pip2 install --user appdirs
pip2 install --user requests
pip2 install --user win32com

python2 run.py
