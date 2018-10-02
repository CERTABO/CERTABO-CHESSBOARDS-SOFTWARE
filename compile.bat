rmdir /s dist
rmdir /s build

pyinstaller -y run.py
pyinstaller -y usbtool.py
pyinstaller -y move.py

mkdir dist\result

xcopy /s /e /h /y dist\run dist\result
xcopy /s /e /h /y dist\usbtool dist\result\
xcopy /s /e /h /y dist\move dist\result\

copy stockfish.exe dist\result\
copy calibration.bin dist\result\
copy bestmove.p dist\result\
copy move_history_tmp.p dist\result
copy screen.ini dist\result\

mkdir dist\result\pics
xcopy /s /e /h /y pics dist\result\pics
mkdir dist\result\sprites_1380
xcopy /s /e /h /y sprites_1380 dist\result\sprites_1380
mkdir dist\result\sprites_1920
xcopy /s /e /h /y sprites_1920 dist\result\sprites_1920
mkdir dist\result\fonts
xcopy /s /e /h /y fonts dist\result\fonts